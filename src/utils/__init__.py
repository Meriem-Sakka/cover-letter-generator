"""Utility functions and helpers"""

from .normalization import (
    normalize_for_matching, normalize_for_classification,
    split_sentences, strip_accents, preprocess_for_embedding
)
from .prompts import GEMINI_PROMPTS
from .cache_store import cache_get, cache_set

# Import UI helpers (keep backward compatible)
from .helpers import (
    setup_page_config, apply_custom_css, create_database,
    save_cover_letter, get_cover_letter_history, get_cover_letter_by_id,
    generate_pdf, validate_api_key, format_file_size,
    show_success_message, show_error_message, show_warning_message,
    show_info_message, display_metric_card, display_fit_score_card,
    display_skill_match_card, display_progress_bar,
    generate_analysis_markdown, generate_analysis_pdf
)

__all__ = [
    'normalize_for_matching', 'normalize_for_classification',
    'split_sentences', 'strip_accents', 'preprocess_for_embedding',
    'GEMINI_PROMPTS', 'cache_get', 'cache_set',
    'setup_page_config', 'apply_custom_css', 'create_database',
    'save_cover_letter', 'get_cover_letter_history', 'get_cover_letter_by_id',
    'generate_pdf', 'validate_api_key', 'format_file_size',
    'show_success_message', 'show_error_message', 'show_warning_message',
    'show_info_message', 'display_metric_card', 'display_fit_score_card',
    'display_skill_match_card', 'display_progress_bar',
    'generate_analysis_markdown', 'generate_analysis_pdf'
]

