import os
import pytest

from src.core.job_fit import JobFitAnalyzer


JD_ROBOTICS = (
    """
    We are looking for a robotics engineer with strong technical experience in at least one of the following:
    navigation, motion planning and controls, SLAM, perception/computer vision, or manipulation.
    Familiarity with LiDAR and sensor fusion is a plus. Experience with ROS2 preferred.
    """
).strip()

CV_ROBOTICS = (
    """
    Developed a LiDAR-based SLAM pipeline for autonomous navigation using ROS2 and EKF sensor fusion; implemented
    trajectory planning and controls for a mobile robot; built computer vision modules with OpenCV for perception.
    """
).strip()


@pytest.mark.integration
def test_robotics_semantic_matching_monolithic():
    analyzer = JobFitAnalyzer(api_key=os.getenv('GEMINI_API_KEY', ''))
    result = analyzer.analyze_job_fit(CV_ROBOTICS, JD_ROBOTICS, api_key=os.getenv('GEMINI_API_KEY', ''), mode='Fast')

    # Ensure technical matches include core robotics terms via semantic/context-aware matching
    matched = [m['job_keyword'].lower() for m in result['matched_details']['technical_skills']]

    assert any('slam' in m for m in matched), 'SLAM should be matched via context'
    assert any('navigation' in m for m in matched), 'Navigation should be matched'
    assert any('motion planning' in m or 'planning' in m for m in matched), 'Motion planning should be matched'
    # LiDAR mentioned in CV should boost matching for perception / sensor fusion related requirements
    assert any('perception' in m or 'computer vision' in m for m in matched), 'Perception/Computer Vision should match'



