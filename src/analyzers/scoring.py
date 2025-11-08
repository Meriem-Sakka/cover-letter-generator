"""
Scoring analyzer for calculating weighted fit scores
"""

import logging
from typing import Dict, Optional, List

from src.models.data_models import FitScores, ComparisonResult
from src.config import SCORING_WEIGHTS, FIT_LEVEL_THRESHOLDS
from src.utils.normalization import normalize_for_classification

logger = logging.getLogger(__name__)


class ScoringAnalyzer:
    """Handles scoring and weighting calculations"""
    
    def __init__(self):
        """Initialize scoring analyzer"""
        pass
    
    def calculate_fit_score(
        self,
        comparison_result: ComparisonResult,
        total_requirements: int
    ) -> float:
        """
        Calculate fit score from comparison result
        
        Args:
            comparison_result: Result of matching
            total_requirements: Total number of job requirements
            
        Returns:
            Fit score (0-100)
        """
        if total_requirements == 0:
            return 100.0
        
        matched_count = len(comparison_result.matches)
        return (matched_count / total_requirements) * 100
    
    def calculate_weighted_fit(
        self,
        category_scores: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate overall weighted fit score
        
        Args:
            category_scores: Dictionary of category -> score
            weights: Optional custom weights (uses config default if None)
            
        Returns:
            Overall weighted score
        """
        effective_weights = weights or SCORING_WEIGHTS
        overall = sum(
            category_scores.get(category, 0.0) * effective_weights.get(category, 0.0)
            for category in SCORING_WEIGHTS.keys()
        )
        return overall
    
    def determine_fit_level(self, score: float) -> tuple[str, str]:
        """
        Determine fit level and color from score
        
        Args:
            score: Overall fit score (0-100)
            
        Returns:
            Tuple of (level, color)
        """
        if score >= FIT_LEVEL_THRESHOLDS['Excellent']:
            return ('Excellent', 'green')
        elif score >= FIT_LEVEL_THRESHOLDS['Good']:
            return ('Good', 'orange')
        elif score >= FIT_LEVEL_THRESHOLDS['Fair']:
            return ('Fair', 'yellow')
        else:
            return ('Poor', 'red')
    
    def calculate_experience_education_score(
        self,
        comparison_result: ComparisonResult,
        total_requirements: int,
        candidate_items: List[str]
    ) -> float:
        """
        Calculate experience/education score with internship weighting
        
        Args:
            comparison_result: Matching result
            total_requirements: Total job requirements
            candidate_items: Candidate experience/education items
            
        Returns:
            Weighted score
        """
        if total_requirements == 0:
            return 100.0
        
        # Check for internship/project keywords
        from src.config import INTERNSHIP_PROJECT_KEYWORDS
        
        internship_set = set()
        for item in candidate_items:
            norm = normalize_for_classification(item)
            if any(k in norm for k in INTERNSHIP_PROJECT_KEYWORDS):
                internship_set.add(norm)
        
        weighted_matches = 0.0
        for match in comparison_result.matches:
            cand_item = match.candidate_item
            norm = normalize_for_classification(cand_item)
            if norm in internship_set:
                weighted_matches += 0.5
            else:
                weighted_matches += 1.0
        
        return (weighted_matches / total_requirements) * 100
    
    def create_fit_scores(
        self,
        technical_score: float,
        soft_score: float,
        methodology_score: float,
        experience_score: float,
        overall_score: float
    ) -> FitScores:
        """Create FitScores dataclass"""
        return FitScores(
            technical_skills=technical_score,
            soft_skills=soft_score,
            methodologies=methodology_score,
            experience_education=experience_score,
            overall_fit=overall_score
        )

