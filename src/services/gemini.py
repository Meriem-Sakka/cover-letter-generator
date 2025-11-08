"""
Stateless Gemini API service
Handles all Gemini API calls with retries, backoff, timeouts, and caching
"""

import os
import json
import time
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, List, Optional, Callable

# Lazy import to speed initial startup
genai = None  # type: ignore

from src.config import (
    GEMINI_API_KEY, GEMINI_MODELS, TIMEOUTS, RATE_LIMIT_MIN_INTERVAL,
    RATE_LIMIT_MAX_RETRIES, RATE_LIMIT_BASE_SLEEP, RATE_LIMIT_ENRICHMENT_RETRIES,
    RATE_LIMIT_ENRICHMENT_BASE_SLEEP, MAX_ENRICH_VARIANTS_PER_ITEM
)
from src.utils.prompts import GEMINI_PROMPTS

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter"""
    
    def __init__(self, min_interval: float = RATE_LIMIT_MIN_INTERVAL):
        self.min_interval = min_interval
        self.last_call_time = 0
        self._lock = None
    
    def wait_if_needed(self):
        """Wait if minimum interval hasn't passed"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        self.last_call_time = time.time()


class GeminiService:
    """Stateless Gemini API service"""
    
    def __init__(self, api_key: Optional[str] = None, cache_store: Optional[Callable] = None):
        """
        Initialize Gemini service
        
        Args:
            api_key: Gemini API key (uses env var if not provided)
            cache_store: Optional cache store callable (get/set methods)
        """
        self.api_key = api_key or GEMINI_API_KEY
        self.cache_store = cache_store
        self.rate_limiter = RateLimiter()
        logger.info("Gemini service initialized")

    def _ensure_genai(self):
        """Import and configure google.generativeai lazily."""
        global genai
        if genai is None:
            import google.generativeai as _genai  # type: ignore
            genai = _genai
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception:
                pass
    
    @staticmethod
    def _with_timeout(func: Callable, timeout_seconds: float):
        """Execute function with timeout"""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func)
            return future.result(timeout=timeout_seconds)
    
    def _get_cache_key(self, prefix: str, content: str, model: Optional[str] = None) -> str:
        """Generate cache key"""
        parts = [prefix]
        if model:
            parts.append(model)
        parts.append(hashlib.sha256(content.encode('utf-8')).hexdigest())
        return '|'.join(parts)
    
    def _get_from_cache(self, key: str) -> Optional[any]:
        """Get value from cache if available"""
        if not self.cache_store or not hasattr(self.cache_store, 'get'):
            return None
        try:
            return self.cache_store.get(key)
        except Exception:
            return None
    
    def _set_to_cache(self, key: str, value: any):
        """Store value in cache"""
        if not self.cache_store or not hasattr(self.cache_store, 'set'):
            return
        try:
            self.cache_store.set(key, value)
        except Exception:
            pass
    
    def extract_with_gemini(
        self,
        text: str,
        extraction_type: str,
        language: str = 'en',
        mode: str = 'Fast'
    ) -> Dict:
        """
        Extract structured data using Gemini AI
        
        Args:
            text: Input text to extract from
            extraction_type: Type of extraction ('job_extraction' or 'cv_extraction')
            language: Language code ('en' or 'fr')
            mode: Analysis mode ('Fast' or 'Deep') for timeout selection
            
        Returns:
            Extracted data dictionary
        """
        if not self.api_key:
            logger.warning("No API key available for Gemini extraction")
            return {
                'technical_skills': [], 'soft_skills': [], 'methodologies': [],
                'education': [], 'experience': []
            }
        
        prompt_template = GEMINI_PROMPTS.get(language, GEMINI_PROMPTS['en']).get(extraction_type)
        if not prompt_template:
            logger.error(f"No prompt template for {extraction_type} in {language}")
            return {
                'technical_skills': [], 'soft_skills': [], 'methodologies': [],
                'education': [], 'experience': []
            }
        
        prompt = prompt_template.format(text=text)
        
        # Model sequence: prefer Pro, fallback to Flash
        model_sequence = (
            [GEMINI_MODELS['extraction_pro'], GEMINI_MODELS['extraction_flash']]
            if extraction_type in ('job_extraction', 'cv_extraction')
            else [GEMINI_MODELS['extraction_flash']]
        )
        
        timeout = TIMEOUTS.get(mode, TIMEOUTS['Fast'])['extraction']
        content_hash = hashlib.sha256((language + '|' + extraction_type + '|' + text).encode('utf-8')).hexdigest()
        
        for model_name in model_sequence:
            cache_key = self._get_cache_key('extraction', f"{model_name}|{content_hash}", model_name)
            cached = self._get_from_cache(cache_key)
            if isinstance(cached, dict) and any(k in cached for k in ('technical_skills', 'education', 'experience')):
                logger.debug(f"Cache hit for extraction: {extraction_type}")
                return cached
            
            last_error = None
            for attempt in range(RATE_LIMIT_MAX_RETRIES):
                try:
                    self.rate_limiter.wait_if_needed()
                    self._ensure_genai()
                    model = genai.GenerativeModel(model_name)
                    self._ensure_genai()
                    model = genai.GenerativeModel(model_name)
                    response = self._with_timeout(
                        lambda: model.generate_content(prompt),
                        timeout
                    )
                    
                    response_text = getattr(response, 'text', None)
                    if not isinstance(response_text, str) or not response_text.strip():
                        logger.error("Empty or invalid response from Gemini extraction")
                        continue
                    
                    response_text = response_text.strip()
                    
                    # Extract JSON
                    if '```json' in response_text:
                        json_start = response_text.find('```json') + 7
                        json_end = response_text.find('```', json_start)
                        response_text = response_text[json_start:json_end].strip()
                    elif '{' in response_text and '}' in response_text:
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        response_text = response_text[json_start:json_end]
                    
                    result = json.loads(response_text)
                    self._set_to_cache(cache_key, result)
                    logger.debug(f"Successfully extracted {extraction_type} data")
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON parse failed: {str(e)}")
                    last_error = e
                    if attempt < RATE_LIMIT_MAX_RETRIES - 1:
                        time.sleep(RATE_LIMIT_BASE_SLEEP * (2 ** attempt))
                    continue
                except Exception as e:
                    msg = str(e)
                    last_error = e
                    if '429' in msg or 'Resource exhausted' in msg or 'rate' in msg.lower():
                        logger.warning("Rate limit encountered")
                    if attempt < RATE_LIMIT_MAX_RETRIES - 1:
                        time.sleep(RATE_LIMIT_BASE_SLEEP * (2 ** attempt))
                        continue
            
            if last_error:
                logger.error(f"Failed to extract with {model_name}: {str(last_error)}")
        
        logger.error("All Gemini extraction attempts failed")
        return {
            'technical_skills': [], 'soft_skills': [], 'methodologies': [],
            'education': [], 'experience': []
        }
    
    def get_embedding(self, text: str, mode: str = 'Fast') -> List[float]:
        """
        Get embedding for text using Gemini embeddings
        
        Args:
            text: Text to embed
            mode: Analysis mode for timeout selection
            
        Returns:
            Embedding vector
        """
        if not self.api_key:
            logger.warning("No API key available for embeddings")
            return []
        
        clean_text = text.strip()
        timeout = TIMEOUTS.get(mode, TIMEOUTS['Fast'])['embedding']
        content_hash = hashlib.sha256(clean_text.encode('utf-8')).hexdigest()
        
        models_to_try = [GEMINI_MODELS['embedding'], GEMINI_MODELS['embedding_fallback']]
        
        for model_name in models_to_try:
            cache_key = self._get_cache_key('embedding', content_hash, model_name)
            cached = self._get_from_cache(cache_key)
            if isinstance(cached, list) and cached:
                return cached
            
            for attempt in range(2):
                try:
                    self.rate_limiter.wait_if_needed()
                    self._ensure_genai()
                    result = self._with_timeout(
                        lambda: genai.embed_content(model=model_name, content=clean_text),
                        timeout
                    )
                    
                    emb = result.get('embedding') if isinstance(result, dict) else None
                    if isinstance(emb, dict) and 'values' in emb:
                        self._set_to_cache(cache_key, emb['values'])
                        return emb['values']
                    if isinstance(emb, list):
                        self._set_to_cache(cache_key, emb)
                        return emb
                except Exception as e:
                    msg = str(e)
                    if '429' in msg or 'Resource exhausted' in msg or 'rate' in msg.lower():
                        logger.warning("Rate limit encountered for embeddings")
                    if attempt < 1:
                        time.sleep(0.5 * (2 ** attempt))
                        continue
                    break
        
        logger.warning("Failed to get embedding")
        return []
    
    def enrich_terms(self, terms: List[str], language: str = 'en', mode: str = 'Fast') -> Dict[str, List[str]]:
        """
        Generate related terms/synonyms for each term
        
        Args:
            terms: List of terms to enrich
            language: Language code
            mode: Analysis mode for timeout
            
        Returns:
            Dictionary mapping term to list of related terms
        """
        if not self.api_key or not terms:
            return {t: [] for t in terms}
        
        prompt_template = GEMINI_PROMPTS.get(language, GEMINI_PROMPTS['en']).get('enrichment', '')
        if not prompt_template:
            return {t: [] for t in terms}
        
        items_payload = json.dumps(
            list(dict.fromkeys([t for t in terms if isinstance(t, str) and t.strip()])),
            ensure_ascii=False
        )
        text_prompt = prompt_template.format(items=items_payload)
        timeout = TIMEOUTS.get(mode, TIMEOUTS['Fast'])['enrichment']
        
        for attempt in range(RATE_LIMIT_ENRICHMENT_RETRIES):
            try:
                self.rate_limiter.wait_if_needed()
                self._ensure_genai()
                model = genai.GenerativeModel(GEMINI_MODELS['enrichment'])
                response = self._with_timeout(
                    lambda: model.generate_content(text_prompt),
                    timeout
                )
                
                response_text = getattr(response, 'text', '') or ''
                response_text = response_text.strip()
                
                if '```json' in response_text:
                    s = response_text.find('```json') + 7
                    e = response_text.find('```', s)
                    response_text = response_text[s:e].strip()
                elif '{' in response_text and '}' in response_text:
                    s = response_text.find('{')
                    e = response_text.rfind('}') + 1
                    response_text = response_text[s:e]
                
                data = json.loads(response_text)
                out: Dict[str, List[str]] = {}
                for t in terms:
                    vals = data.get(t) or data.get(t.lower()) or []
                    if isinstance(vals, list):
                        trimmed = [v for v in vals if isinstance(v, str)]
                        if len(trimmed) > (MAX_ENRICH_VARIANTS_PER_ITEM - 1):
                            trimmed = trimmed[:MAX_ENRICH_VARIANTS_PER_ITEM - 1]
                        out[t] = trimmed
                    else:
                        out[t] = []
                return out
            except Exception as e:
                if attempt < RATE_LIMIT_ENRICHMENT_RETRIES - 1:
                    time.sleep(RATE_LIMIT_ENRICHMENT_BASE_SLEEP * (2 ** attempt))
                    continue
                logger.debug(f"Enrichment failed: {str(e)}")
                return {t: [] for t in terms}
        
        return {t: [] for t in terms}
    
    def generate_recommendations(
        self,
        job_skills: Dict,
        candidate_skills: Dict,
        fit_scores: Dict,
        language: str = 'en'
    ) -> Dict:
        """Generate AI recommendations"""
        if not self.api_key:
            return {
                'learn_skills': [], 'highlight_skills': [],
                'add_experience': [], 'specific_examples': []
            }
        
        prompt_template = GEMINI_PROMPTS.get(language, GEMINI_PROMPTS['en']).get('recommendations')
        if not prompt_template:
            return {
                'learn_skills': [], 'highlight_skills': [],
                'add_experience': [], 'specific_examples': []
            }
        
        prompt = prompt_template.format(
            job_skills=json.dumps(job_skills, ensure_ascii=False),
            candidate_skills=json.dumps(candidate_skills, ensure_ascii=False),
            fit_scores=json.dumps(fit_scores, ensure_ascii=False)
        )
        
        try:
            self.rate_limiter.wait_if_needed()
            self._ensure_genai()
            model = genai.GenerativeModel(GEMINI_MODELS['recommendations'])
            response = model.generate_content(prompt)
            
            response_text = response.text.strip()
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                response_text = response_text[json_start:json_end]
            
            return json.loads(response_text)
        except Exception as e:
            logger.warning(f"Error generating recommendations: {str(e)}")
            return {
                'learn_skills': [], 'highlight_skills': [],
                'add_experience': [], 'specific_examples': []
            }
    
    def infer_dynamic_weights(self, job_text: str, language: str = 'en') -> Optional[Dict[str, float]]:
        """Infer dynamic weights from job description"""
        if not self.api_key:
            return None
        
        prompt_template = GEMINI_PROMPTS.get(language, GEMINI_PROMPTS['en']).get('dynamic_weights')
        if not prompt_template:
            return None
        
        prompt = prompt_template.format(job_text=job_text)
        
        try:
            self.rate_limiter.wait_if_needed()
            self._ensure_genai()
            model = genai.GenerativeModel(GEMINI_MODELS['dynamic_weights'])
            response = model.generate_content(prompt)
            
            txt = getattr(response, 'text', '') or ''
            txt = txt.strip()
            if '```json' in txt:
                s = txt.find('```json') + 7
                e = txt.find('```', s)
                txt = txt[s:e].strip()
            elif '{' in txt and '}' in txt:
                s = txt.find('{')
                e = txt.rfind('}') + 1
                txt = txt[s:e]
            
            data = json.loads(txt)
            keys = ['technical_skills', 'soft_skills', 'methodologies', 'experience_education']
            vals = [max(0.0, float(data.get(k, 0))) for k in keys]
            total = sum(vals)
            if total <= 0:
                return None
            return {k: v/total for k, v in zip(keys, vals)}
        except Exception:
            return None
    
    def identify_missing_skills(
        self,
        job_skills: List[str],
        candidate_skills: List[str],
        language: str = 'en'
    ) -> List[str]:
        """Identify critical missing skills"""
        if not self.api_key:
            return []
        
        prompt_template = GEMINI_PROMPTS.get(language, GEMINI_PROMPTS['en']).get('missing_skills')
        if not prompt_template:
            return []
        
        prompt = prompt_template.format(
            job_skills=json.dumps(job_skills, ensure_ascii=False),
            candidate_skills=json.dumps(candidate_skills, ensure_ascii=False)
        )
        
        try:
            self.rate_limiter.wait_if_needed()
            self._ensure_genai()
            model = genai.GenerativeModel(GEMINI_MODELS['missing_skills'])
            response = model.generate_content(prompt)
            
            txt = getattr(response, 'text', '') or ''
            txt = txt.strip()
            if '```json' in txt:
                s = txt.find('```json') + 7
                e = txt.find('```', s)
                txt = txt[s:e].strip()
            elif '{' in txt and '}' in txt:
                s = txt.find('{')
                e = txt.rfind('}') + 1
                txt = txt[s:e]
            
            data = json.loads(txt)
            arr = data.get('missing', [])
            if isinstance(arr, list):
                return [x for x in arr if isinstance(x, str)]
            return []
        except Exception:
            return []

