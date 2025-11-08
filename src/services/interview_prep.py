"""
Interview Preparation Assistant Service
Generates interview questions, talking points, and preparation insights
"""

import logging
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
import json

logger = logging.getLogger(__name__)


class InterviewPrepService:
    """Service for generating interview preparation content"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize interview preparation service"""
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
    
    def generate_preparation_guide(
        self,
        resume_text: str,
        job_description: str,
        language: str = 'en'
    ) -> Dict:
        """
        Generate comprehensive interview preparation guide
        
        Args:
            resume_text: Resume text
            job_description: Job description
            language: Language code ('en' or 'fr')
            
        Returns:
            Dictionary with questions, talking points, strengths, and areas to prepare
        """
        try:
            # Generate interview questions
            questions = self._generate_interview_questions(job_description, language)
            
            # Generate talking points
            talking_points = self._generate_talking_points(resume_text, job_description, language)
            
            # Analyze strengths and areas to prepare
            preparation_analysis = self._analyze_preparation_needs(resume_text, job_description, language)
            
            return {
                'interview_questions': questions,
                'talking_points': talking_points,
                'strengths': preparation_analysis.get('strengths', []),
                'areas_to_prepare': preparation_analysis.get('areas_to_prepare', []),
                'key_topics': preparation_analysis.get('key_topics', []),
                'success': True
            }
        except Exception as e:
            logger.error(f"Error generating interview preparation guide: {e}")
            return {
                'interview_questions': [],
                'talking_points': [],
                'strengths': [],
                'areas_to_prepare': [],
                'key_topics': [],
                'success': False,
                'error': str(e)
            }
    
    def _generate_interview_questions(self, job_description: str, language: str) -> List[Dict]:
        """Generate potential interview questions based on job description"""
        try:
            if language == 'fr':
                prompt = f"""
Analysez cette description de poste et générez 15-20 questions d'entretien potentielles qu'un recruteur pourrait poser. Organisez-les par catégories.

Description du poste:
{job_description}

Retournez UNIQUEMENT du JSON valide dans ce format exact:
{{
    "questions": [
        {{
            "category": "Compétences techniques|Expérience|Comportement|Culture d'entreprise",
            "question": "Question complète",
            "why_asked": "Pourquoi cette question est posée",
            "difficulty": "facile|moyen|difficile"
        }}
    ]
}}
"""
            else:
                prompt = f"""
Analyze this job description and generate 15-20 potential interview questions a recruiter might ask. Organize them by categories.

Job Description:
{job_description}

Return ONLY valid JSON in this exact format:
{{
    "questions": [
        {{
            "category": "Technical Skills|Experience|Behavioral|Company Culture",
            "question": "Complete question text",
            "why_asked": "Why this question is asked",
            "difficulty": "easy|medium|hard"
        }}
    ]
}}
"""
            
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            if response and response.text:
                response_text = response.text.strip()
                
                # Extract JSON
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif '{' in response_text and '}' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    response_text = response_text[json_start:json_end]
                
                data = json.loads(response_text)
                return data.get('questions', [])
            
            return []
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            return []
    
    def _generate_talking_points(self, resume_text: str, job_description: str, language: str) -> List[Dict]:
        """Generate talking points from resume that align with job requirements"""
        try:
            if language == 'fr':
                prompt = f"""
Analysez le CV et la description de poste pour générer des points de discussion clés que le candidat devrait mentionner lors de l'entretien. Basez-vous sur l'expérience et les compétences du CV qui correspondent aux exigences du poste.

CV:
{resume_text[:3000]}

Description du poste:
{job_description[:2000]}

Retournez UNIQUEMENT du JSON valide dans ce format exact:
{{
    "talking_points": [
        {{
            "topic": "Sujet principal",
            "point": "Point de discussion spécifique",
            "resume_evidence": "Élément du CV qui le prouve",
            "job_relevance": "Pourquoi c'est pertinent pour le poste",
            "example": "Exemple concret ou histoire à raconter"
        }}
    ]
}}
"""
            else:
                prompt = f"""
Analyze the resume and job description to generate key talking points the candidate should mention during the interview. Base these on the candidate's experience and skills from the resume that match the job requirements.

Resume:
{resume_text[:3000]}

Job Description:
{job_description[:2000]}

Return ONLY valid JSON in this exact format:
{{
    "talking_points": [
        {{
            "topic": "Main topic",
            "point": "Specific talking point",
            "resume_evidence": "Evidence from resume that supports this",
            "job_relevance": "Why this is relevant to the job",
            "example": "Concrete example or story to tell"
        }}
    ]
}}
"""
            
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            if response and response.text:
                response_text = response.text.strip()
                
                # Extract JSON
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif '{' in response_text and '}' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    response_text = response_text[json_start:json_end]
                
                data = json.loads(response_text)
                return data.get('talking_points', [])
            
            return []
        except Exception as e:
            logger.error(f"Error generating talking points: {e}")
            return []
    
    def _analyze_preparation_needs(self, resume_text: str, job_description: str, language: str) -> Dict:
        """Analyze strengths and areas that need preparation"""
        try:
            if language == 'fr':
                prompt = f"""
Analysez le CV par rapport à la description de poste pour identifier:
1. Les forces du candidat (points forts qui correspondent bien)
2. Les domaines à préparer (lacunes potentielles ou points faibles)
3. Les sujets clés à maîtriser pour l'entretien

CV:
{resume_text[:3000]}

Description du poste:
{job_description[:2000]}

Retournez UNIQUEMENT du JSON valide dans ce format exact:
{{
    "strengths": [
        {{
            "strength": "Point fort",
            "evidence": "Preuve du CV",
            "impact": "Impact pour le poste"
        }}
    ],
    "areas_to_prepare": [
        {{
            "area": "Domaine à préparer",
            "reason": "Pourquoi c'est important",
            "suggestion": "Suggestion pour se préparer"
        }}
    ],
    "key_topics": ["Sujet 1", "Sujet 2", "Sujet 3"]
}}
"""
            else:
                prompt = f"""
Analyze the resume against the job description to identify:
1. Candidate's strengths (strong points that align well)
2. Areas to prepare (potential gaps or weak points)
3. Key topics to master for the interview

Resume:
{resume_text[:3000]}

Job Description:
{job_description[:2000]}

Return ONLY valid JSON in this exact format:
{{
    "strengths": [
        {{
            "strength": "Strength point",
            "evidence": "Evidence from resume",
            "impact": "Impact for the role"
        }}
    ],
    "areas_to_prepare": [
        {{
            "area": "Area to prepare",
            "reason": "Why this is important",
            "suggestion": "Suggestion for preparation"
        }}
    ],
    "key_topics": ["Topic 1", "Topic 2", "Topic 3"]
}}
"""
            
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            if response and response.text:
                response_text = response.text.strip()
                
                # Extract JSON
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif '{' in response_text and '}' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    response_text = response_text[json_start:json_end]
                
                data = json.loads(response_text)
                return {
                    'strengths': data.get('strengths', []),
                    'areas_to_prepare': data.get('areas_to_prepare', []),
                    'key_topics': data.get('key_topics', [])
                }
            
            return {'strengths': [], 'areas_to_prepare': [], 'key_topics': []}
        except Exception as e:
            logger.error(f"Error analyzing preparation needs: {e}")
            return {'strengths': [], 'areas_to_prepare': [], 'key_topics': []}


def generate_interview_prep(
    resume_text: str,
    job_description: str,
    api_key: Optional[str] = None,
    language: str = 'en'
) -> Dict:
    """
    Main function to generate interview preparation guide
    
    Args:
        resume_text: Resume text
        job_description: Job description
        api_key: Gemini API key
        language: Language code
        
    Returns:
        Dictionary with interview preparation content
    """
    service = InterviewPrepService(api_key)
    return service.generate_preparation_guide(resume_text, job_description, language)

