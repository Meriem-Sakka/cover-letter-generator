"""Core business logic modules"""

from .job_fit import analyze_job_fit, JobFitAnalyzer
from .ai_generator import generate_cover_letter, improve_cover_letter
from .resume_parser import extract_resume_text

__all__ = [
    'analyze_job_fit', 'JobFitAnalyzer',
    'generate_cover_letter', 'improve_cover_letter',
    'extract_resume_text'
]

