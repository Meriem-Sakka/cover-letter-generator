"""
Text normalization and preprocessing utilities
Handles text cleaning, accent removal, lemmatization, and alias normalization
"""

import re
import unicodedata
from typing import List, Optional, Dict

try:
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


def strip_accents(s: str) -> str:
    """Remove accents from string"""
    if not isinstance(s, str):
        return s
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def normalize_for_classification(s: str) -> str:
    """Normalize text for classification (lowercase, accents removed, spaces unified)"""
    if not s:
        return ''
    s = strip_accents(s.lower())
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_for_matching(text: str) -> str:
    """Normalize text for matching: lowercase, accents removed, unified spaces, alias normalization."""
    if not text:
        return ""
    s = text.strip().lower()
    # Remove accents
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    # Alias normalization
    s = s.replace('react.js', 'react').replace('reactjs', 'react')
    s = s.replace('node.js', 'node').replace('nodejs', 'node')
    s = s.replace('scikit learn', 'scikit-learn').replace('sklearn', 'scikit-learn')
    s = s.replace('c plus plus', 'c++').replace('c sharp', 'c#')
    s = s.replace('google cloud platform', 'gcp')
    # Robotics & systems common variants
    s = s.replace('ros 1', 'ros1').replace('ros-1', 'ros1')
    s = s.replace('ros 2', 'ros2').replace('ros-2', 'ros2')
    s = s.replace('li dar', 'lidar').replace('li-dar', 'lidar')
    s = s.replace('laser radar', 'lidar')
    # C-family variants
    s = s.replace('c/c++', 'c++').replace('c / c++', 'c++')
    # Remove duplicate punctuation around pluses
    s = s.replace('c-++', 'c++').replace('c ++', 'c++')
    # Unify spaces
    s = re.sub(r"\s+", " ", s)
    return s


def lemmatize_en_optional(text: str) -> str:
    """Optionally lemmatize English text using NLTK if available. Fallback: return as-is."""
    if not NLTK_AVAILABLE:
        return text
    try:
        lemmatizer = WordNetLemmatizer()
        tokens = re.findall(r"[a-zA-Z+#\.\-]+", text)
        lemmas = [lemmatizer.lemmatize(tok) for tok in tokens]
        return ' '.join(lemmas)
    except Exception:
        return text


def preprocess_for_embedding(text: str, language: str = 'en') -> str:
    """Preprocess text before embedding (normalize + optional lemmatization)"""
    s = normalize_for_matching(text)
    if language == 'en':
        s = lemmatize_en_optional(s)
    return s


def split_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    if not text:
        return []
    parts = re.split(r"(?<=[\.!?;])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def expand_with_aliases(items: List[str], aliases: Dict[str, List[str]]) -> List[str]:
    """Expand a list of items with configured aliases/synonyms.
    Keeps originals and adds unique aliases.
    """
    if not items:
        return []
    seen = set()
    out: List[str] = []
    for it in items:
        if not isinstance(it, str):
            continue
        norm = normalize_for_classification(it)
        if norm not in seen:
            seen.add(norm)
            out.append(it)
        # add aliases when canonical appears in text
        for canon, alist in (aliases or {}).items():
            if canon in norm or norm == canon:
                for a in alist:
                    na = normalize_for_classification(a)
                    if na not in seen:
                        seen.add(na)
                        out.append(a)
    return out


