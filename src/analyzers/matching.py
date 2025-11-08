"""
Matching analyzer for comparing job requirements with candidate profiles
Uses embeddings, keyword similarity, and domain-aware filtering
"""

import math
import re
import logging
from typing import Dict, List, Optional, Set

from src.models.data_models import SkillMatch, ComparisonResult
from src.utils.normalization import normalize_for_matching, normalize_for_classification, expand_with_aliases
from src.config import (
    MAX_ENRICH_VARIANTS_PER_ITEM, MATCH_TYPE_THRESHOLDS,
    HYBRID_WEIGHTS, BM25_K1, BM25_B
)
from src.config import TECH_ALIASES

logger = logging.getLogger(__name__)


class MatchingAnalyzer:
    """Handles semantic and keyword-based matching"""
    
    def __init__(self, gemini_service, cache_store=None):
        """
        Initialize matching analyzer
        
        Args:
            gemini_service: GeminiService instance for embeddings
            cache_store: Optional cache store
        """
        self.gemini_service = gemini_service
        self.cache_store = cache_store
    
    def calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(a * a for a in embedding2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def keyword_similarity_bm25(self, a: str, b: str) -> float:
        """BM25-like similarity between two texts, scaled to [0,1]"""
        def tok(s: str) -> List[str]:
            return re.findall(r"[a-z0-9+#\.\-]+", s)
        
        a_tokens = tok(a)
        b_tokens = tok(b)
        if not a_tokens or not b_tokens:
            return 0.0
        
        docs = [a_tokens, b_tokens]
        N = 2
        vocab = set(a_tokens + b_tokens)
        df = {t: sum(1 for d in docs if t in d) for t in vocab}
        idf = {t: math.log((N - df[t] + 0.5) / (df[t] + 0.5) + 1) for t in vocab}
        
        avgdl = sum(len(d) for d in docs) / N
        
        def bm25_score(query: List[str], doc: List[str]) -> float:
            score = 0.0
            doc_len = len(doc)
            tf = {}
            for t in doc:
                tf[t] = tf.get(t, 0) + 1
            for t in query:
                if t not in idf:
                    continue
                freq = tf.get(t, 0)
                denom = freq + BM25_K1 * (1 - BM25_B + BM25_B * (doc_len / (avgdl + 1e-9)))
                score += idf[t] * (freq * (BM25_K1 + 1)) / (denom + 1e-9)
            return score
        
        s1 = bm25_score(a_tokens, b_tokens)
        s2 = bm25_score(b_tokens, a_tokens)
        raw = (s1 + s2) / 2.0
        return max(0.0, min(1.0, raw / (raw + 1.5)))
    
    def _build_embedding_bundles(
        self,
        items: List[str],
        aug_map: Dict[str, List[str]],
        language: str,
        mode: str
    ) -> List[List[List[float]]]:
        """Build embeddings for items and their enriched variants"""
        bundles: List[List[List[float]]] = []
        for it in items:
            variants = [it] + (aug_map.get(it) or [])
            seen = set()
            uniq_variants = []
            for v in variants:
                nv = normalize_for_matching(v)
                if nv and nv not in seen:
                    seen.add(nv)
                    uniq_variants.append(v)
            if len(uniq_variants) > MAX_ENRICH_VARIANTS_PER_ITEM:
                uniq_variants = uniq_variants[:MAX_ENRICH_VARIANTS_PER_ITEM]
            
            emb_list: List[List[float]] = []
            for v in uniq_variants:
                # Preprocess before embedding
                from src.utils.normalization import preprocess_for_embedding
                try:
                    preprocessed = preprocess_for_embedding(v, language)
                    emb = self.gemini_service.get_embedding(preprocessed, mode)
                    if emb:
                        emb_list.append(emb)
                except Exception:
                    continue
            bundles.append(emb_list)
        return bundles
    
    def compare_embeddings(
        self,
        job_items: List[str],
        candidate_items: List[str],
        threshold: float = 0.50,
        enrich: bool = False,
        language: str = 'en',
        use_hybrid: bool = True,
        mode: str = 'Fast'
    ) -> ComparisonResult:
        """
        Compare job requirements with candidate skills using embeddings
        
        Args:
            job_items: Job requirement items
            candidate_items: Candidate skill items
            threshold: Minimum similarity threshold
            enrich: Whether to enrich terms
            language: Language code
            use_hybrid: Whether to combine semantic + keyword similarity
            mode: Analysis mode ('Fast' or 'Deep')
            
        Returns:
            ComparisonResult with matches and unmatched items
        """
        if not job_items or not candidate_items:
            return ComparisonResult()
        
        job_aug_map: Dict[str, List[str]] = {t: [] for t in job_items}
        cand_aug_map: Dict[str, List[str]] = {t: [] for t in candidate_items}
        
        if enrich:
            try:
                job_aug_map = self.gemini_service.enrich_terms(job_items, language, mode)
            except Exception:
                job_aug_map = {t: [] for t in job_items}
            try:
                cand_aug_map = self.gemini_service.enrich_terms(candidate_items, language, mode)
            except Exception:
                cand_aug_map = {t: [] for t in candidate_items}
        
        job_bundles = self._build_embedding_bundles(job_items, job_aug_map, language, mode)
        cand_bundles = self._build_embedding_bundles(candidate_items, cand_aug_map, language, mode)
        
        if not (any(any(b) for b in job_bundles) and any(any(b) for b in cand_bundles)):
            logger.error("Embeddings not available")
            return ComparisonResult(
                unmatched_job=job_items,
                unmatched_candidate=candidate_items
            )
        
        matches = []
        matched_candidate_indices = set()
        matched_job_indices = set()
        
        for i, job_item in enumerate(job_items):
            best_match_idx = -1
            best_similarity = 0.0
            
            for j, candidate_item in enumerate(candidate_items):
                if j in matched_candidate_indices:
                    continue
                
                cur_best = 0.0
                for je in job_bundles[i]:
                    if not je:
                        continue
                    for ce in cand_bundles[j]:
                        if not ce:
                            continue
                        sim = self.calculate_cosine_similarity(je, ce)
                        if sim > cur_best:
                            cur_best = sim
                
                combined = cur_best
                if use_hybrid:
                    kw = self.keyword_similarity_bm25(
                        normalize_for_matching(job_item),
                        normalize_for_matching(candidate_item)
                    )
                    combined = (
                        HYBRID_WEIGHTS['semantic'] * cur_best +
                        HYBRID_WEIGHTS['keyword'] * kw
                    )
                
                if combined > best_similarity and combined >= threshold:
                    best_similarity = combined
                    best_match_idx = j
            
            if best_match_idx != -1:
                if best_similarity >= MATCH_TYPE_THRESHOLDS['exact']:
                    match_type = 'exact'
                elif best_similarity >= MATCH_TYPE_THRESHOLDS['semantic']:
                    match_type = 'semantic'
                else:
                    match_type = 'partial'
                
                matches.append(SkillMatch(
                    job_item=job_item,
                    candidate_item=candidate_items[best_match_idx],
                    similarity=best_similarity,
                    match_type=match_type,
                    confidence=best_similarity
                ))
                matched_candidate_indices.add(best_match_idx)
                matched_job_indices.add(i)
        
        unmatched_job = [item for idx, item in enumerate(job_items) if idx not in matched_job_indices]
        unmatched_candidate = [item for idx, item in enumerate(candidate_items) if idx not in matched_candidate_indices]
        
        return ComparisonResult(
            matches=matches,
            unmatched_job=unmatched_job,
            unmatched_candidate=unmatched_candidate
        )
    
    def compare_embeddings_domain_filtered(
        self,
        job_items: List[str],
        candidate_items: List[str],
        threshold: float = 0.70,
        enrich: bool = False,
        language: str = 'en',
        use_hybrid: bool = True,
        mode: str = 'Fast'
    ) -> ComparisonResult:
        """
        Domain-aware matching with domain filtering and alias boosting
        
        Similar to compare_embeddings but filters by inferred domain clusters
        """
        # For now, delegate to compare_embeddings
        # Domain filtering can be added later if needed
        return self.compare_embeddings(
            job_items, candidate_items, threshold, enrich, language, use_hybrid, mode
        )
    
    def match_with_full_context(
        self,
        job_skill: str,
        resume_text: str,
        threshold: float = 0.55,
        language: str = 'en',
        mode: str = 'Fast'
    ) -> Optional[float]:
        """
        Match a job skill requirement against full resume context using semantic similarity.
        This checks if the skill is mentioned anywhere in the resume (explicitly or implicitly).
        
        Args:
            job_skill: Job requirement skill
            resume_text: Full resume text to search in
            threshold: Minimum similarity threshold
            language: Language code
            mode: Analysis mode
            
        Returns:
            Similarity score if match found above threshold, None otherwise
        """
        if not job_skill or not resume_text:
            return None
        
        try:
            # Get embedding for job skill
            from src.utils.normalization import preprocess_for_embedding
            job_processed = preprocess_for_embedding(job_skill, language)
            job_emb = self.gemini_service.get_embedding(job_processed, mode)
            
            if not job_emb:
                return None
            
            # Build sentence-level index once per call
            sentences = self._build_resume_sentence_index(resume_text, language, mode)
            best_similarity = 0.0
            
            for sent_text, sent_emb in sentences:
                if not sent_emb:
                    continue
                sim = self.calculate_cosine_similarity(job_emb, sent_emb)
                if sim > best_similarity:
                    best_similarity = sim
            
            # Also check explicit skill mentions (for hybrid matching)
            job_normalized = normalize_for_matching(job_skill)
            resume_normalized = normalize_for_matching(resume_text)
            
            # Check if skill name appears in resume
            if job_normalized in resume_normalized or any(
                word in resume_normalized for word in job_normalized.split() if len(word) > 3
            ):
                keyword_boost = 0.2  # Boost if keyword appears
                best_similarity = min(1.0, best_similarity + keyword_boost)
            
            # Hybrid approach: combine semantic + keyword similarity
            keyword_sim = self.keyword_similarity_bm25(job_normalized, resume_normalized)
            combined = (
                HYBRID_WEIGHTS['semantic'] * best_similarity +
                HYBRID_WEIGHTS['keyword'] * keyword_sim
            )
            
            return combined if combined >= threshold else None
            
        except Exception as e:
            logger.debug(f"Error in context-aware matching: {e}")
            return None
    
    def match_skills_with_context(
        self,
        job_skills: List[str],
        explicit_candidate_skills: List[str],
        resume_text: str,
        threshold: float = 0.55,
        language: str = 'en',
        mode: str = 'Fast'
    ) -> ComparisonResult:
        """
        Enhanced matching that considers both explicit skills AND full resume context.
        This helps match skills that are implied through experience/projects.
        
        Args:
            job_skills: List of job requirement skills
            explicit_candidate_skills: Explicitly listed candidate skills
            resume_text: Full resume text for context matching
            threshold: Similarity threshold
            language: Language code
            mode: Analysis mode
            
        Returns:
            ComparisonResult with matches from both explicit and context-based matching
        """
        if not job_skills:
            return ComparisonResult()
        
        # Expand with domain aliases to catch variants (e.g., SLAM, LiDAR variants)
        aliased_job_skills = expand_with_aliases(job_skills, TECH_ALIASES)
        aliased_candidate_skills = expand_with_aliases(explicit_candidate_skills, TECH_ALIASES)

        # First, do standard explicit matching on expanded sets
        explicit_result = self.compare_embeddings(
            aliased_job_skills, aliased_candidate_skills, threshold, False, language, True, mode
        )
        
        matched_job_indices = set()
        matches = list(explicit_result.matches)
        
        # Prepare sentence index for resume (used for explainability and re-ranking)
        sentence_index = self._build_resume_sentence_index(resume_text, language, mode)
        
        # For unmatched job skills, try context-aware matching with sentence evidence
        for i, job_skill in enumerate(job_skills):
            if i in matched_job_indices:
                continue
            
            # Compute best matching sentence for this job skill
            evidence_snippet = None
            evidence_sim = 0.0
            try:
                from src.utils.normalization import preprocess_for_embedding
                job_proc = preprocess_for_embedding(job_skill, language)
                job_emb = self.gemini_service.get_embedding(job_proc, mode)
                if job_emb:
                    for sent_text, sent_emb in sentence_index:
                        if not sent_emb:
                            continue
                        sim = self.calculate_cosine_similarity(job_emb, sent_emb)
                        if sim > evidence_sim:
                            evidence_sim = sim
                            evidence_snippet = sent_text[:300]
            except Exception:
                pass
            
            # Hybrid similarity using resume sentence evidence
            context_sim = None
            if evidence_sim > 0:
                job_norm = normalize_for_matching(job_skill)
                resume_norm = normalize_for_matching(evidence_snippet or '')
                kw = self.keyword_similarity_bm25(job_norm, resume_norm)
                context_sim = HYBRID_WEIGHTS['semantic'] * evidence_sim + HYBRID_WEIGHTS['keyword'] * kw
            
            if context_sim and context_sim >= threshold * 0.9:
                # Find best matching explicit skill as reference, or use job_skill itself
                best_candidate_ref = job_skill
                for candidate_skill in aliased_candidate_skills:
                    # Check if there's any semantic relationship
                    try:
                        from src.utils.normalization import preprocess_for_embedding
                        job_proc = preprocess_for_embedding(job_skill, language)
                        cand_proc = preprocess_for_embedding(candidate_skill, language)
                        job_emb = self.gemini_service.get_embedding(job_proc, mode)
                        cand_emb = self.gemini_service.get_embedding(cand_proc, mode)
                        if job_emb and cand_emb:
                            sim = self.calculate_cosine_similarity(job_emb, cand_emb)
                            if sim > 0.6:  # Related skill found
                                best_candidate_ref = candidate_skill
                                break
                    except Exception:
                        continue
                
                # Determine match type
                if context_sim >= MATCH_TYPE_THRESHOLDS['exact']:
                    match_type = 'exact'
                elif context_sim >= MATCH_TYPE_THRESHOLDS['semantic']:
                    match_type = 'semantic'
                else:
                    match_type = 'partial'
                
                matches.append(SkillMatch(
                    job_item=job_skill,
                    candidate_item=best_candidate_ref,
                    similarity=context_sim,
                    match_type=match_type,
                    confidence=context_sim,
                    evidence_snippet=evidence_snippet,
                    evidence_type='resume_sentence'
                ))
                matched_job_indices.add(i)
        
        # Update unmatched list
        unmatched_job = [skill for i, skill in enumerate(job_skills) if i not in matched_job_indices]
        
        return ComparisonResult(
            matches=matches,
            unmatched_job=unmatched_job,
            unmatched_candidate=explicit_result.unmatched_candidate
        )

    def _build_resume_sentence_index(self, resume_text: str, language: str, mode: str) -> List[tuple]:
        """Tokenize resume into sentences and compute embeddings (capped)."""
        try:
            from src.utils.normalization import split_sentences, preprocess_for_embedding
            sentences = split_sentences(resume_text)
            # Filter short sentences and cap for performance
            sentences = [s for s in sentences if len(s) > 20][:120]
            out: List[tuple] = []
            for s in sentences:
                try:
                    proc = preprocess_for_embedding(s, language)
                    emb = self.gemini_service.get_embedding(proc, mode)
                    out.append((s, emb))
                except Exception:
                    out.append((s, None))
            return out
        except Exception:
            return []

