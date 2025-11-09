"""
A/B Testing Service for Cover Letters
Generates multiple variations of cover letters with different tones and focus points
"""

import logging
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ABTestingService:
    """Service for generating cover letter variations"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize A/B testing service"""
        if not api_key:
            raise ValueError("API key is required for A/B testing service")
        self.api_key = api_key
        genai.configure(api_key=api_key)
    
    def generate_variations(
        self,
        resume_text: str,
        job_description: str,
        base_tone: str,
        language: str,
        num_variations: int = 3,
        user_prompt: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate multiple cover letter variations
        
        Args:
            resume_text: Resume text
            job_description: Job description
            base_tone: Base tone (professional, friendly, etc.)
            language: Language code
            num_variations: Number of variations to generate (2-3)
            user_prompt: Optional custom instructions
            
        Returns:
            List of variation dictionaries with 'text', 'name', 'description'
        """
        variations = []
        
        # Define variation strategies
        strategies = self._get_variation_strategies(base_tone, num_variations)
        
        for i, strategy in enumerate(strategies[:num_variations], 1):
            try:
                variation = self._generate_single_variation(
                    resume_text,
                    job_description,
                    strategy,
                    language,
                    user_prompt,
                    variation_num=i
                )
                if variation:
                    variations.append(variation)
            except Exception as e:
                logger.error(f"Error generating variation {i}: {e}")
                continue
        
        return variations
    
    def _get_variation_strategies(self, base_tone: str, num_variations: int) -> List[Dict]:
        """Get variation strategies based on base tone"""
        all_strategies = [
            {
                'name': 'Professional & Formal',
                'tone': 'professional',
                'focus': 'Emphasize qualifications, experience, and professional achievements. Use formal language and structure.',
                'description': 'Traditional, formal approach highlighting credentials'
            },
            {
                'name': 'Results-Driven & Confident',
                'tone': 'confident',
                'focus': 'Lead with achievements, metrics, and quantifiable results. Show confidence and impact.',
                'description': 'Highlights measurable achievements and impact'
            },
            {
                'name': 'Personable & Engaging',
                'tone': 'friendly',
                'focus': 'Show personality, cultural fit, and enthusiasm. Balance professionalism with warmth.',
                'description': 'Warmer tone emphasizing cultural fit and enthusiasm'
            },
            {
                'name': 'Innovative & Creative',
                'tone': 'creative',
                'focus': 'Stand out with unique perspectives, creative problem-solving, and innovative approaches.',
                'description': 'Creative approach that differentiates from standard letters'
            },
            {
                'name': 'Concise & Direct',
                'tone': 'professional',
                'focus': 'Be brief, direct, and to the point. Focus on most relevant 2-3 points only.',
                'description': 'Short, impactful version for busy recruiters'
            }
        ]
        
        # Select strategies based on base tone
        if base_tone == 'Professional':
            # Mix of professional, results-driven, concise
            selected = [all_strategies[0], all_strategies[1], all_strategies[4]]
        elif base_tone == 'Friendly':
            # Mix of friendly, professional, personable
            selected = [all_strategies[2], all_strategies[0], all_strategies[1]]
        elif base_tone == 'Formal':
            # Formal, professional, results-driven
            selected = [all_strategies[0], all_strategies[1], all_strategies[4]]
        elif base_tone == 'Enthusiastic':
            # Enthusiastic, personable, creative
            selected = [all_strategies[2], all_strategies[3], all_strategies[1]]
        else:
            # Default mix
            selected = all_strategies[:num_variations]
        
        return selected[:num_variations]
    
    def _generate_single_variation(
        self,
        resume_text: str,
        job_description: str,
        strategy: Dict,
        language: str,
        user_prompt: Optional[str],
        variation_num: int
    ) -> Optional[Dict]:
        """Generate a single cover letter variation"""
        try:
            prompt = self._create_variation_prompt(
                resume_text,
                job_description,
                strategy,
                language,
                user_prompt
            )
            
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            if response and response.text:
                return {
                    'text': response.text.strip(),
                    'name': strategy['name'],
                    'description': strategy['description'],
                    'tone': strategy['tone'],
                    'focus': strategy['focus'],
                    'variation_num': variation_num
                }
            return None
        except Exception as e:
            logger.error(f"Error in _generate_single_variation: {e}")
            return None
    
    def _create_variation_prompt(
        self,
        resume_text: str,
        job_description: str,
        strategy: Dict,
        language: str,
        user_prompt: Optional[str]
    ) -> str:
        """Create prompt for variation generation"""
        language_instructions = {
            'English': "Write the cover letter in English.",
            'French': "Write the cover letter in French.",
            'Arabic': "Write the cover letter in Arabic."
        }
        
        prompt = f"""
You are an AI assistant specialized in generating professional cover letters. Create a cover letter variation with a specific strategic approach.

RESUME CONTENT:
{resume_text}

JOB DESCRIPTION:
{job_description}

VARIATION STRATEGY:
- Name: {strategy['name']}
- Tone: {strategy['tone']}
- Focus: {strategy['focus']}

REQUIREMENTS:
- Language: {language_instructions.get(language, 'Write in English')}
- Tone: {strategy['tone']} - {strategy['focus']}
- Length: Keep it concise (3-4 paragraphs, approximately 200-300 words)
- Structure: Include proper greeting, body paragraphs, and closing
- Strategic Focus: {strategy['focus']}
- Keywords: Naturally incorporate relevant keywords from the job description
- Format: Use proper paragraph breaks and professional formatting
"""
        
        if user_prompt and user_prompt.strip():
            prompt += f"""
CUSTOM INSTRUCTIONS:
{user_prompt.strip()}
"""
        
        prompt += """
INSTRUCTIONS:
1. Start with a professional greeting
2. First paragraph: Express interest using the strategic focus approach
3. Second paragraph: Highlight achievements/skills matching the strategic focus
4. Third paragraph: Show enthusiasm and contribution aligned with the strategy
5. End with a professional closing

IMPORTANT:
- Do not include placeholder text
- Make it specific to the job requirements
- Follow the strategic variation approach closely
- Ensure the tone matches the strategy
- Write in the specified language

Generate the cover letter variation now:
"""
        
        return prompt


def generate_cover_letter_variations(
    resume_text: str,
    job_description: str,
    base_tone: str,
    language: str,
    api_key: Optional[str] = None,
    num_variations: int = 3,
    user_prompt: Optional[str] = None
) -> List[Dict]:
    """
    Main function to generate cover letter variations
    
    Args:
        resume_text: Resume text
        job_description: Job description
        base_tone: Base tone
        language: Language code
        api_key: Gemini API key
        num_variations: Number of variations (2-3)
        user_prompt: Optional custom instructions
        
    Returns:
        List of variation dictionaries
    """
    service = ABTestingService(api_key)
    return service.generate_variations(
        resume_text,
        job_description,
        base_tone,
        language,
        min(max(num_variations, 2), 3),  # Limit to 2-3
        user_prompt
    )

