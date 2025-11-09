"""
AI-Driven Job Fit Analysis Module - Refactored
Uses modular services and analyzers for extraction, matching, and scoring
"""

import re
import streamlit as st
from typing import Dict, List, Optional, Set
import logging
import warnings

warnings.filterwarnings('ignore')

# Language detection
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import new modular components
from src.services.gemini import GeminiService
from src.analyzers.matching import MatchingAnalyzer
from src.analyzers.scoring import ScoringAnalyzer
from src.utils.normalization import (
    normalize_for_matching, normalize_for_classification,
    split_sentences, strip_accents
)
from src.config import (
    MATCHING_THRESHOLDS, SCORING_WEIGHTS, FIT_LEVEL_THRESHOLDS,
    DEGREE_KEYWORDS, ROLE_KEYWORDS, EDUCATION_CONNECTOR_KEYWORDS,
    EDUCATION_CONTEXT_KEYWORDS, INTERNSHIP_PROJECT_KEYWORDS,
    MAX_ENRICH_VARIANTS_PER_ITEM
)
from src.config import TECH_ALIASES

# Import cache store
try:
    from src.utils.cache_store import cache_get, cache_set
    
    class CacheStore:
        def get(self, key: str):
            return cache_get(key)
        def set(self, key: str, value):
            cache_set(key, value)
    
    cache_store_instance = CacheStore()
except ImportError:
    cache_store_instance = None


class JobFitAnalyzer:
    """Main job fit analyzer orchestrating extraction, matching, and scoring"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize analyzer with stateless services"""
        self.gemini_service = GeminiService(api_key, cache_store_instance)
        self.matching_analyzer = MatchingAnalyzer(self.gemini_service, cache_store_instance)
        self.scoring_analyzer = ScoringAnalyzer()
        logger.info("Job Fit Analyzer initialized")
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        if not LANGDETECT_AVAILABLE:
            return 'en'
        
        try:
            clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
            clean_text = ' '.join(clean_text.split())
            if len(clean_text) < 10:
                return 'en'
            detected_lang = detect(clean_text)
            return detected_lang if detected_lang in ['en', 'fr'] else 'en'
        except Exception:
            return 'en'
    
    def _summarize_edu_exp_items(self, items: List[str]) -> List[str]:
        """Summarize education/experience entries to core titles"""
        if not items:
            return []
        
        summaries: List[str] = []
        for raw in items:
            if not isinstance(raw, str):
                continue
            text = raw.strip()
            if not text:
                continue
            
            # Remove parentheses and dates
            text = re.sub(r"\s*[\(\[].*?[\)\]]\s*", " ", text)
            text = re.sub(r"\b\d{1,2}[\./-]\d{1,2}[\./-]\d{2,4}\s*[-–—toau]+\s*\d{1,2}[\./-]\d{1,2}[\./-]\d{2,4}\b", " ", text, flags=re.IGNORECASE)
            text = re.sub(r"\b\d{4}\s*[-–—toau]+\s*\d{4}\b", " ", text, flags=re.IGNORECASE)
            text = re.sub(r"\s+", " ", text).strip()
            norm = normalize_for_classification(text)
            
            # Extract core title
            cut = text
            for c in EDUCATION_CONNECTOR_KEYWORDS:
                idx = norm.find(normalize_for_classification(c))
                if idx != -1:
                    cut = text.split(c)[0].strip()
                    break
            
            if ',' in cut:
                first_clause = cut.split(',')[0].strip()
            else:
                first_clause = cut
            
            norm_first = normalize_for_classification(first_clause)
            if any(w in norm_first for w in DEGREE_KEYWORDS + ROLE_KEYWORDS):
                core = first_clause
            elif any(w in norm for w in DEGREE_KEYWORDS):
                core = text.split(',')[0].strip()
            else:
                core = ' '.join(text.split()[:8]).strip()
            
            core = core.rstrip(' .') + '.'
            summaries.append(core)
        
        # Deduplicate
        seen = set()
        out: List[str] = []
        for s in summaries:
            k = normalize_for_classification(s)
            if k and k not in seen:
                seen.add(k)
                out.append(s)
        return out
    
    def _is_technical_term(self, text: str) -> bool:
        """Check if text is a technical term"""
        nt = normalize_for_classification(text)
        if not nt:
            return False
        tech_pattern = r"\b(c\+\+|c#|ros2|ros|python|tensorflow|pytorch|keras|sql|react|node|node\.js|docker|kubernetes|linux|git|matlab|simulink|arduino|raspberry pi|opencv|scikit-learn|sklearn|pandas|numpy|aws|azure|gcp|bash|shell|ansible|terraform|jenkins|ci/cd|graphql|rest|fastapi|django|flask|spring|java|typescript|javascript|html|css)\b"
        return bool(re.search(tech_pattern, nt, flags=re.IGNORECASE))

    def _canonicalize_skill(self, term: str) -> str:
        """Map a term to a canonical concept key using normalization and TECH_ALIASES."""
        if not isinstance(term, str):
            return ''
        nt = normalize_for_matching(term)
        # Try alias map
        for canon, aliases in (TECH_ALIASES or {}).items():
            c = normalize_for_matching(canon)
            if nt == c:
                return c
            for a in aliases:
                if nt == normalize_for_matching(a):
                    return c
        return nt
    
    def _fix_sentence_splitting(self, result: Dict, job_text: str) -> Dict:
        """
        Post-process extracted data to fix common sentence splitting issues.
        Fixes cases where sentences like "Strong technical experience in X, Y, Z" 
        were incorrectly split.
        """
        # Look for technical skills that appear in experience/education that shouldn't
        tech_skills = set(normalize_for_classification(s) for s in result.get('technical_skills', []))
        
        # Patterns that indicate technical skills in wrong categories
        skill_indicators = [
            'experience in', 'proficiency with', 'knowledge of', 'familiarity with',
            'expertise in', 'working with', 'using', 'experience with'
        ]
        
        # Check experience items for misclassified skills
        fixed_experience = []
        moved_to_tech = []
        
        for exp_item in result.get('experience', []):
            exp_lower = exp_item.lower()
            
            # If it contains skill indicators, check if it's actually a skill requirement
            if any(indicator in exp_lower for indicator in skill_indicators):
                # Extract potential skills from this item
                import re
                
                # Check for list patterns after skill indicators
                for indicator in skill_indicators:
                    pattern = rf"{re.escape(indicator)}\s*([^:]+?)(?:\.|$|or|and)"
                    matches = re.findall(pattern, exp_item, re.IGNORECASE)
                    for match in matches:
                        # Split by comma, semicolon, or "or"/"and"
                        potential_skills = re.split(r'[,;]|\s+or\s+|\s+and\s+', match.strip())
                        for skill in potential_skills:
                            skill = skill.strip()
                            if len(skill) > 2 and not skill.lower().startswith(('years', 'year', 'plus')):
                                # Check if it looks like a technical skill
                                if self._is_technical_term(skill) or len(skill.split()) <= 3:
                                    moved_to_tech.append(skill)
                                    if normalize_for_classification(skill) not in tech_skills:
                                        result['technical_skills'].append(skill)
                                else:
                                    fixed_experience.append(exp_item)
                                    break
                        if potential_skills:
                            break
                    if matches:
                        break
                else:
                    # No skill pattern found, keep as experience
                    fixed_experience.append(exp_item)
            else:
                # Doesn't look like a skill requirement, keep as experience
                fixed_experience.append(exp_item)
        
        # Update result
        if moved_to_tech:
            logger.debug(f"Fixed sentence splitting: moved {len(moved_to_tech)} items from experience to technical_skills")
        
        result['experience'] = fixed_experience if fixed_experience else result.get('experience', [])
        
        # Deduplicate technical skills
        seen_tech = set()
        unique_tech = []
        for skill in result.get('technical_skills', []):
            norm = normalize_for_classification(skill)
            if norm and norm not in seen_tech:
                seen_tech.add(norm)
                unique_tech.append(skill)
        result['technical_skills'] = unique_tech
        
        return result
    
    def _reclassify_tech_from_edu_exp(self, result: Dict) -> Dict:
        """Move technical terms from education/experience back to technical_skills"""
        tech = list(result.get('technical_skills', []))
        edu = list(result.get('education', []))
        exp = list(result.get('experience', []))
        new_edu: List[str] = []
        new_exp: List[str] = []
        
        for item in edu:
            if self._is_technical_term(item) and len(item.split()) <= 4:
                tech.append(item)
            else:
                new_edu.append(item)
        
        for item in exp:
            if self._is_technical_term(item) and len(item.split()) <= 4:
                tech.append(item)
            else:
                new_exp.append(item)
        
        # Deduplicate
        tech_seen = set()
        dedup_tech: List[str] = []
        for t in tech:
            k = normalize_for_classification(t)
            if k not in tech_seen:
                tech_seen.add(k)
                dedup_tech.append(t)
        
        result['technical_skills'] = dedup_tech
        result['education'] = new_edu
        result['experience'] = new_exp
        return result
    
    def _reclassify_education_fields(self, job_text: str, result: Dict, language: str = 'en') -> Dict:
        """Move items to education when they appear in education-context sentences"""
        tech = list(result.get('technical_skills', []))
        meth = list(result.get('methodologies', []))
        edu = list(result.get('education', []))
        
        if not job_text:
            return result
        
        sentences = split_sentences(job_text)
        edu_sentences = []
        for s in sentences:
            ns = normalize_for_classification(s)
            if any(w in ns for w in EDUCATION_CONTEXT_KEYWORDS):
                edu_sentences.append((s, ns))
        
        if not edu_sentences:
            return result
        
        def occurs_in_edu_sentence(term: str) -> bool:
            nt = normalize_for_classification(term)
            if not nt:
                return False
            for _, ns in edu_sentences:
                if nt in ns:
                    return True
            return False
        
        new_tech = []
        for item in tech:
            if occurs_in_edu_sentence(item):
                edu.append(item)
            else:
                new_tech.append(item)
        
        new_meth = []
        for item in meth:
            if occurs_in_edu_sentence(item):
                edu.append(item)
            else:
                new_meth.append(item)
        
        # Deduplicate education
        seen_norm = set()
        dedup_edu = []
        for item in edu:
            k = normalize_for_classification(item)
            if k not in seen_norm:
                seen_norm.add(k)
                dedup_edu.append(item)
        
        result['technical_skills'] = new_tech
        result['methodologies'] = new_meth
        result['education'] = dedup_edu
        return result
    
    def _is_duration_phrase(self, text: str) -> bool:
        """Check if text is a duration-only phrase"""
        if not isinstance(text, str):
            return False
        nt = normalize_for_classification(text)
        if not nt:
            return False
        years_kw = r"years|yrs|ans|annees|ann?ees|année|annee"
        patterns = [
            rf"\b\d+\s*(\+)?\s*({years_kw})\b",
            rf"\b(au moins|min(?:imum)?\s+de|at least|minimum\s+of)\s+\d+\s*({years_kw})\b",
        ]
        return any(re.search(pat, nt, flags=re.IGNORECASE) for pat in patterns)
    
    def _is_internship_or_project(self, text: str) -> bool:
        """Check if text describes an internship or project"""
        if not isinstance(text, str):
            return False
        nt = normalize_for_classification(text)
        if not nt:
            return False
        return any(k in nt for k in INTERNSHIP_PROJECT_KEYWORDS)
    
    def _extract_experience_constraints(self, text: str, language: str = 'en') -> List[Dict]:
        """Extract explicit experience constraints from job description"""
        constraints: List[Dict] = []
        if not text:
            return constraints
        
        normalized = re.sub(r"\s+", " ", text)
        years_kw = r"years|yrs|ans|années"
        exp_kw = r"experience|expérience"
        in_kw = r"in|en|dans|with|avec|using|utilisant"
        of_kw = r"of|de|d'"
        minimum_kw = r"minimum of|at least|au moins|min\.?"
        plus_sign = r"\+?"
        
        patterns = [
            rf"(\b\d+){plus_sign}\s*(?:{years_kw})\s*(?:{of_kw})?\s*(?:{exp_kw})?(?:\s*(?:{in_kw}))\s+([A-Za-z0-9\-\&\./\s]+?)(?=[\.,;\)\n]|$)",
            rf"(?:{minimum_kw})\s*(\d+)\s*(?:{years_kw})(?:\s*(?:{in_kw}))\s+([A-Za-z0-9\-\&\./\s]+?)(?=[\.,;\)\n]|$)",
            rf"(\b\d+)\s*(?:{years_kw})\s*(?:{exp_kw})?(?:\s*(?:{in_kw}))?\s+(with\s+|en\s+|avec\s+|utilisant\s+)?([A-Za-z0-9\-\&\./\s]+?)(?=[\.,;\)\n]|$)"
        ]
        
        for pat in patterns:
            for m in re.finditer(pat, normalized, flags=re.IGNORECASE):
                try:
                    years_val = int(m.group(1))
                except Exception:
                    continue
                field_text = m.group(2) if len(m.groups()) >= 2 else ""
                field_text = field_text.strip().strip('.;,):(')
                field_text = re.sub(r"^(with|en|dans|avec|using|utilisant)\s+", "", field_text, flags=re.IGNORECASE)
                if field_text:
                    constraints.append({
                        'type': 'years',
                        'years': years_val,
                        'comparator': '>=',
                        'field': field_text,
                        'raw': m.group(0).strip()
                    })
        
        level_words = r"expert|senior|proficient|strong|advanced|confirmé|expert\.?|avancé"
        level_pat = rf"\b({level_words})\s+(?:in|en|dans)\s+([A-Za-z0-9\-\&\./\s]+?)(?=[\.,;\)\n]|$)"
        for m in re.finditer(level_pat, normalized, flags=re.IGNORECASE):
            level = m.group(1).lower()
            field_text = m.group(2).strip().strip('.;,):(')
            constraints.append({
                'type': 'level',
                'level': level,
                'field': field_text,
                'raw': m.group(0).strip()
            })
        
        # Deduplicate
        seen = set()
        deduped: List[Dict] = []
        for c in constraints:
            key = (c.get('type'), c.get('years') or c.get('level'), c.get('field', '').lower())
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        return deduped
    
    def extract_job_requirements(self, job_text: str, language: str = 'en', mode: str = 'Fast') -> Dict:
        """Extract job requirements using Gemini"""
        logger.info("Extracting job requirements")
        
        extracted_data = self.gemini_service.extract_with_gemini(
            job_text, 'job_extraction', language, mode
        )
        
        result = {
            'technical_skills': extracted_data.get('technical_skills', []),
            'soft_skills': extracted_data.get('soft_skills', []),
            'methodologies': extracted_data.get('methodologies', []),
            'education': self._summarize_edu_exp_items(extracted_data.get('education', [])),
            'experience': self._summarize_edu_exp_items(extracted_data.get('experience', []))
        }
        
        # Optional enrichment
        if mode == 'Deep':
            try:
                tech_enrich = self.gemini_service.enrich_terms(result['technical_skills'], language, mode)
                meth_enrich = self.gemini_service.enrich_terms(result['methodologies'], language, mode)
                
                def merge_enrich(base: List[str], mapping: Dict[str, List[str]]) -> List[str]:
                    items = list(base)
                    seen = set(normalize_for_matching(x) for x in items)
                    for k, vals in mapping.items():
                        for v in vals or []:
                            nv = normalize_for_matching(v)
                            if nv and nv not in seen:
                                seen.add(nv)
                                items.append(v)
                    return items
                
                result['technical_skills'] = merge_enrich(result['technical_skills'], tech_enrich)
                result['methodologies'] = merge_enrich(result['methodologies'], meth_enrich)
            except Exception:
                pass
        
        # Extract experience constraints
        constraints = self._extract_experience_constraints(job_text, language)
        result['experience_constraints'] = constraints if constraints else []
        
        # Reclassify fields
        result = self._reclassify_education_fields(job_text, result, language)
        result = self._reclassify_tech_from_edu_exp(result)
        
        # Post-process to fix common misclassifications (context-aware fixes)
        result = self._fix_sentence_splitting(result, job_text)
        
        return result
    
    def extract_candidate_profile(self, cv_text: str, language: str = 'en', mode: str = 'Fast') -> Dict:
        """Extract candidate profile using Gemini"""
        logger.info("Extracting candidate profile")
        
        extracted_data = self.gemini_service.extract_with_gemini(
            cv_text, 'cv_extraction', language, mode
        )
        
        result = {
            'technical_skills': extracted_data.get('technical_skills', []),
            'soft_skills': extracted_data.get('soft_skills', []),
            'methodologies': extracted_data.get('methodologies', []),
            'education': self._summarize_edu_exp_items(extracted_data.get('education', [])),
            'experience': self._summarize_edu_exp_items(extracted_data.get('experience', []))
        }
        
        # Optional enrichment
        if mode == 'Deep':
            try:
                tech_enrich = self.gemini_service.enrich_terms(result['technical_skills'], language, mode)
                meth_enrich = self.gemini_service.enrich_terms(result['methodologies'], language, mode)
                
                def merge_enrich(base: List[str], mapping: Dict[str, List[str]]) -> List[str]:
                    items = list(base)
                    seen = set(normalize_for_matching(x) for x in items)
                    for k, vals in mapping.items():
                        for v in vals or []:
                            nv = normalize_for_matching(v)
                            if nv and nv not in seen:
                                seen.add(nv)
                                items.append(v)
                    return items
                
                result['technical_skills'] = merge_enrich(result['technical_skills'], tech_enrich)
                result['methodologies'] = merge_enrich(result['methodologies'], meth_enrich)
            except Exception:
                pass
        
        result = self._reclassify_tech_from_edu_exp(result)
        return result
    
    def calculate_weighted_fit(
        self,
        job_requirements: Dict,
        candidate_profile: Dict,
        weights: Optional[Dict[str, float]] = None,
        detected_language: str = 'en',
        mode: str = 'Fast',
        resume_text: Optional[str] = None
    ) -> Dict:
        """Calculate weighted fit scores"""
        logger.info("Calculating weighted fit scores")
        
        fit_scores = {}
        detailed_results = {}
        
        # Compare each category
        categories = ['technical_skills', 'soft_skills', 'methodologies']
        thresholds = MATCHING_THRESHOLDS.get(mode, MATCHING_THRESHOLDS['Fast'])
        enrich = (mode == 'Deep')
        use_hybrid = (mode == 'Deep')
        
        # Store resume text for context-aware matching
        resume_text_for_context = resume_text
        
        for category in categories:
            job_items = job_requirements.get(category, [])
            candidate_items = candidate_profile.get(category, [])
            threshold = thresholds.get(category.replace('_', ''), 0.50)
            
            # Use context-aware matching for technical skills (most important for semantic understanding)
            if category == 'technical_skills' and resume_text_for_context:
                try:
                    comparison = self.matching_analyzer.match_skills_with_context(
                        job_items, candidate_items, resume_text_for_context,
                        threshold, detected_language, mode
                    )
                except Exception as e:
                    logger.debug(f"Context-aware matching failed, falling back to standard: {e}")
                    comparison = self.matching_analyzer.compare_embeddings(
                        job_items, candidate_items, threshold, enrich, detected_language, use_hybrid, mode
                    )
            else:
                comparison = self.matching_analyzer.compare_embeddings(
                    job_items, candidate_items, threshold, enrich, detected_language, use_hybrid, mode
                )
            
            # Convert ComparisonResult to dict for backward compatibility
            comparison_dict = {
                'matches': [
                    {
                        'job_item': m.job_item,
                        'candidate_item': m.candidate_item,
                        'similarity': m.similarity,
                        'match_type': m.match_type
                    }
                    for m in comparison.matches
                ],
                'unmatched_job': comparison.unmatched_job,
                'unmatched_candidate': comparison.unmatched_candidate
            }
            
            fit_score = self.scoring_analyzer.calculate_fit_score(comparison, len(job_items))
            fit_scores[category] = round(fit_score, 1)
            detailed_results[category] = comparison_dict
        
        # Handle experience & education
        job_edu = job_requirements.get('education', [])
        job_exp_raw = job_requirements.get('experience', [])
        job_exp = [e for e in job_exp_raw if not self._is_duration_phrase(e)]
        job_exp_edu = job_edu + job_exp
        
        cand_edu = candidate_profile.get('education', [])
        cand_exp_raw = candidate_profile.get('experience', [])
        cand_exp = [e for e in cand_exp_raw if not self._is_duration_phrase(e)]
        candidate_exp_edu = cand_edu + cand_exp
        
        exp_threshold = thresholds.get('experience_education', 0.70)
        exp_edu_comparison = self.matching_analyzer.compare_embeddings_domain_filtered(
            job_exp_edu, candidate_exp_edu, exp_threshold, enrich, detected_language, use_hybrid, mode
        )
        
        # Convert to dict
        exp_edu_dict = {
            'matches': [
                {
                    'job_item': m.job_item,
                    'candidate_item': m.candidate_item,
                    'similarity': m.similarity,
                    'match_type': m.match_type
                }
                for m in exp_edu_comparison.matches
            ],
            'unmatched_job': exp_edu_comparison.unmatched_job,
            'unmatched_candidate': exp_edu_comparison.unmatched_candidate
        }
        
        # Calculate weighted score with internship weighting
        exp_score = self.scoring_analyzer.calculate_experience_education_score(
            exp_edu_comparison, len(job_exp_edu), candidate_exp_edu
        )
        
        fit_scores['experience_education'] = round(exp_score, 1)
        detailed_results['experience_education'] = exp_edu_dict
        
        # Calculate overall weighted score
        overall_fit = self.scoring_analyzer.calculate_weighted_fit(fit_scores, weights)
        
        return {
            'overall_fit': round(overall_fit, 1),
            'technical_fit': fit_scores['technical_skills'],
            'soft_fit': fit_scores['soft_skills'],
            'methodology_fit': fit_scores['methodologies'],
            'experience_fit': fit_scores['experience_education'],
            'detailed_results': detailed_results
        }
    
    def generate_ai_recommendations(
        self,
        job_requirements: Dict,
        candidate_profile: Dict,
        fit_scores: Dict,
        language: str = 'en'
    ) -> Dict:
        """Generate AI recommendations"""
        logger.info("Generating AI recommendations")
        
        job_skills_summary = {
            'technical_skills': job_requirements.get('technical_skills', []),
            'soft_skills': job_requirements.get('soft_skills', []),
            'methodologies': job_requirements.get('methodologies', [])
        }
        
        candidate_skills_summary = {
            'technical_skills': candidate_profile.get('technical_skills', []),
            'soft_skills': candidate_profile.get('soft_skills', []),
            'methodologies': candidate_profile.get('methodologies', [])
        }
        
        return self.gemini_service.generate_recommendations(
            job_skills_summary, candidate_skills_summary, fit_scores, language
        )
    
    def analyze_job_fit(
        self,
        resume_text: str,
        job_text: str,
        api_key: Optional[str] = None,
        mode: str = 'Fast'
    ) -> Dict:
        """Main function to analyze job fit"""
        logger.info("Starting AI-driven job fit analysis")
        
        # Detect language
        detected_language = self.detect_language(resume_text)
        logger.info(f"Detected language: {detected_language}")
        
        # Try dynamic weighting
        dynamic_weights = self.gemini_service.infer_dynamic_weights(job_text, detected_language)
        
        # Extract requirements and profile
        job_requirements = self.extract_job_requirements(job_text, detected_language, mode)
        candidate_profile = self.extract_candidate_profile(resume_text, detected_language, mode)
        
        # Calculate weighted fit (pass resume_text for context-aware matching)
        fit_analysis = self.calculate_weighted_fit(
            job_requirements, candidate_profile, dynamic_weights, detected_language, mode,
            resume_text=resume_text  # Pass for context-aware matching
        )
        
        # Generate recommendations
        recommendations = self.generate_ai_recommendations(
            job_requirements, candidate_profile, fit_analysis, detected_language
        )
        
        # Augment with missing skills
        try:
            missing_from_tech = self.gemini_service.identify_missing_skills(
                job_requirements.get('technical_skills', []),
                candidate_profile.get('technical_skills', []),
                detected_language
            )
            if missing_from_tech:
                existing = set(recommendations.get('learn_skills', []))
                for x in missing_from_tech:
                    if x not in existing:
                        recommendations.setdefault('learn_skills', []).append(x)
        except Exception:
            pass
        
        # Determine fit level
        overall_score = fit_analysis['overall_fit']
        fit_level, fit_color = self.scoring_analyzer.determine_fit_level(overall_score)
        
        logger.info(f"Analysis completed. Overall score: {overall_score}%")
        
        # Convert to expected format for app.py
        category_scores = {
            'technical_skills': fit_analysis['technical_fit'],
            'soft_skills': fit_analysis['soft_fit'],
            'methodologies': fit_analysis['methodology_fit'],
            'experience_education': fit_analysis['experience_fit']
        }
        
        matched_details = {}
        missing_details = {}
        for category, result in fit_analysis['detailed_results'].items():
            # Deduplicate matches by canonical job concept (keep highest confidence)
            best_by_concept = {}
            for match in result.get('matches', []):
                job_kw = match['job_item']
                concept = self._canonicalize_skill(job_kw)
                prev = best_by_concept.get(concept)
                if (not prev) or (match['similarity'] > prev['confidence']):
                    best_by_concept[concept] = {
                        'resume_keyword': match['candidate_item'],
                        'job_keyword': job_kw,
                        'match_type': match['match_type'],
                        'confidence': match['similarity']
                    }
            matched_list = list(best_by_concept.values())

            # Build missing list, excluding any concept already matched
            matched_concepts = set(best_by_concept.keys())
            raw_missing = result.get('unmatched_job', []) or []
            dedup_missing = []
            seen_missing = set()
            for item in raw_missing:
                concept = self._canonicalize_skill(item)
                if concept in matched_concepts:
                    continue
                if concept not in seen_missing:
                    seen_missing.add(concept)
                    dedup_missing.append(item)
            
            matched_details[category] = matched_list
            missing_details[category] = dedup_missing
        
        return {
            'overall_score': overall_score,
            'fit_level': fit_level,
            'fit_color': fit_color,
            'detected_language': detected_language,
            'technical_fit': fit_analysis['technical_fit'],
            'soft_fit': fit_analysis['soft_fit'],
            'methodology_fit': fit_analysis['methodology_fit'],
            'experience_fit': fit_analysis['experience_fit'],
            'category_scores': category_scores,
            'matched_details': matched_details,
            'missing_details': missing_details,
            'job_requirements': job_requirements,
            'candidate_profile': candidate_profile,
            'detailed_results': fit_analysis['detailed_results'],
            'recommendations': recommendations,
            'experience_constraints': job_requirements.get('experience_constraints', []),
            'rate_limited': False  # Rate limiting is handled in service layer
        }


@st.cache_data(ttl=3600)
def analyze_job_fit(resume_text: str, job_text: str, api_key: Optional[str] = None, mode: str = 'Fast') -> Dict:
    """
    Main function to analyze job fit (backward compatible wrapper)
    
    Args:
        resume_text: Resume text
        job_text: Job description text
        api_key: Optional Gemini API key
        mode: Analysis mode ('Fast' or 'Deep')
        
    Returns:
        Dictionary containing complete fit analysis
    """
    logger.info("Starting AI-driven job fit analysis")
    logger.info(f"API key provided: {'Yes' if api_key and len(api_key) > 0 else 'No'}")
    
    if not api_key:
        logger.warning("No API key provided - extraction will return empty results")
        # Return a fallback result structure with warning
        return {
            'overall_score': 0.0,
            'fit_level': 'Poor',
            'fit_color': '#ef4444',
            'detected_language': 'en',
            'technical_fit': 0.0,
            'soft_fit': 0.0,
            'methodology_fit': 0.0,
            'experience_fit': 0.0,
            'category_scores': {
                'technical_skills': 0.0,
                'soft_skills': 0.0,
                'methodologies': 0.0,
                'experience_education': 0.0
            },
            'matched_details': {
                'technical_skills': [],
                'soft_skills': [],
                'methodologies': [],
                'experience_education': []
            },
            'missing_details': {
                'technical_skills': [],
                'soft_skills': [],
                'methodologies': [],
                'experience_education': []
            },
            'job_requirements': {
                'technical_skills': [],
                'soft_skills': [],
                'methodologies': [],
                'education': [],
                'experience': []
            },
            'candidate_profile': {
                'technical_skills': [],
                'soft_skills': [],
                'methodologies': [],
                'education': [],
                'experience': []
            },
            'detailed_results': {},
            'recommendations': {},
            'rate_limited': False,
            'api_key_missing': True  # Flag to indicate API key issue
        }
    
    analyzer = JobFitAnalyzer(api_key)
    result = analyzer.analyze_job_fit(resume_text, job_text, api_key, mode)
    logger.info(f"Analysis completed. Overall score: {result['overall_score']}%")
    
    # Log extraction results for debugging
    job_req = result.get('job_requirements', {})
    candidate_prof = result.get('candidate_profile', {})
    logger.info(f"Extracted {len(job_req.get('technical_skills', []))} job technical skills")
    logger.info(f"Extracted {len(candidate_prof.get('technical_skills', []))} candidate technical skills")
    
    return result

