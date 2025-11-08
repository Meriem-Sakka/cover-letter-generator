"""
Data models for job fit analysis
Structured dataclasses for type safety and clarity
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SkillMatch:
    """Represents a matched skill between job and candidate"""
    job_item: str
    candidate_item: str
    similarity: float
    match_type: str  # 'exact', 'semantic', or 'partial'
    confidence: Optional[float] = None
    # Optional explainability
    evidence_snippet: Optional[str] = None  # Matched resume sentence/fragment
    evidence_type: Optional[str] = None     # 'explicit_skill', 'resume_sentence', 'hybrid'


@dataclass
class ComparisonResult:
    """Result of comparing job requirements with candidate profile"""
    matches: List[SkillMatch] = field(default_factory=list)
    unmatched_job: List[str] = field(default_factory=list)
    unmatched_candidate: List[str] = field(default_factory=list)


@dataclass
class ExtractedData:
    """Extracted structured data from job description or resume"""
    technical_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    methodologies: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    experience: List[str] = field(default_factory=list)
    experience_constraints: List[Dict] = field(default_factory=list)


@dataclass
class FitScores:
    """Category-wise fit scores"""
    technical_skills: float = 0.0
    soft_skills: float = 0.0
    methodologies: float = 0.0
    experience_education: float = 0.0
    overall_fit: float = 0.0


@dataclass
class Recommendations:
    """AI-generated recommendations"""
    learn_skills: List[str] = field(default_factory=list)
    highlight_skills: List[str] = field(default_factory=list)
    add_experience: List[str] = field(default_factory=list)
    specific_examples: List[str] = field(default_factory=list)


@dataclass
class JobFitResult:
    """Complete job fit analysis result"""
    overall_score: float
    fit_level: str  # 'Excellent', 'Good', 'Fair', 'Poor'
    fit_color: str
    detected_language: str
    technical_fit: float
    soft_fit: float
    methodology_fit: float
    experience_fit: float
    category_scores: Dict[str, float]
    matched_details: Dict[str, List[Dict]]
    missing_details: Dict[str, List[str]]
    job_requirements: ExtractedData
    candidate_profile: ExtractedData
    detailed_results: Dict[str, ComparisonResult]
    recommendations: Recommendations
    experience_constraints: List[Dict]
    rate_limited: bool = False

