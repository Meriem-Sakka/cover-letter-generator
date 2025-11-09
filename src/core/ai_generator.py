"""
AI Generator Module
Handles Gemini API integration for cover letter generation
"""

import google.generativeai as genai
import streamlit as st
from typing import Optional, Tuple
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def initialize_gemini(api_key: Optional[str] = None) -> bool:
    """
    Initialize Gemini API with API key
    
    Args:
        api_key: Gemini API key (required - should be provided from user input)
        
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Require API key to be provided (no fallback to environment)
        if not api_key:
            logger.warning("No API key provided to initialize_gemini")
            return False
        
        genai.configure(api_key=api_key)
        logger.info("Gemini API initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {str(e)}")
        return False


def create_cover_letter_prompt(resume_text: str, job_description: str, 
                              tone: str, language: str, user_prompt: Optional[str] = None) -> str:
    """
    Create a comprehensive prompt for cover letter generation
    
    Args:
        resume_text: Extracted text from resume
        job_description: Job description text
        tone: Selected tone (professional, friendly, confident, creative, custom)
        language: Selected language (English, French, Arabic)
        user_prompt: Optional custom instructions from user
        
    Returns:
        Formatted prompt string
    """
    
    # Tone instructions
    tone_instructions = {
        'professional': "Use a formal, professional tone with clear structure and business language.",
        'friendly': "Use a warm, approachable tone while maintaining professionalism.",
        'confident': "Use an assertive, confident tone that showcases your strengths boldly.",
        'creative': "Use a creative, engaging tone that stands out while remaining professional.",
        'custom': "Use a balanced tone that is professional yet personal."
    }
    
    # Language instructions
    language_instructions = {
        'English': "Write the cover letter in English.",
        'French': "Write the cover letter in French.",
        'Arabic': "Write the cover letter in Arabic."
    }
    
    # Build the base prompt
    prompt = f"""
You are an AI assistant specialized in generating professional cover letters. Create a personalized cover letter based on the provided resume and job description.

RESUME CONTENT:
{resume_text}

JOB DESCRIPTION:
{job_description}

REQUIREMENTS:
- Language: {language_instructions.get(language, 'Write in English')}
- Tone: {tone_instructions.get(tone, 'Use a professional tone')}
- Length: Keep it concise (3-4 paragraphs, approximately 200-300 words)
- Structure: Include proper greeting, body paragraphs, and closing
- Personalization: Highlight specific skills and experiences from the resume that match the job requirements
- Keywords: Naturally incorporate relevant keywords from the job description
- Format: Use proper paragraph breaks and professional formatting
"""

    # Add custom user instructions if provided
    if user_prompt and user_prompt.strip():
        prompt += f"""
CUSTOM INSTRUCTIONS:
{user_prompt.strip()}

Please incorporate these specific instructions into the cover letter while maintaining professionalism and following all other requirements.
"""

    prompt += """
INSTRUCTIONS:
1. Start with a professional greeting
2. First paragraph: Express interest in the position and briefly mention your most relevant qualification
3. Second paragraph: Highlight 2-3 key achievements or skills that match the job requirements
4. Third paragraph: Show enthusiasm for the company/role and mention how you can contribute
5. End with a professional closing and call to action

IMPORTANT:
- Do not include any placeholder text like [Your Name] or [Company Name]
- Make it specific to the job requirements
- Ensure the tone matches the selected style
- Write in the specified language
- Keep it professional and engaging

Generate the cover letter now:
"""
    
    return prompt


def generate_cover_letter(resume_text: str, job_description: str, 
                         tone: str, language: str, api_key: Optional[str] = None, 
                         user_prompt: Optional[str] = None) -> Tuple[str, bool, str]:
    """
    Generate cover letter using Gemini API
    
    Args:
        resume_text: Extracted text from resume
        job_description: Job description text
        tone: Selected tone
        language: Selected language
        api_key: Gemini API key
        user_prompt: Optional custom instructions from user
        
    Returns:
        Tuple of (generated_cover_letter, success_flag, error_message)
    """
    try:
        # Initialize Gemini
        if not initialize_gemini(api_key):
            return "", False, "Failed to initialize Gemini API"
        
        # Create prompt
        prompt = create_cover_letter_prompt(resume_text, job_description, tone, language, user_prompt)
        
        # Generate content using Gemini (use a supported public model)
        # Based on your account's available models, prefer the stable non-preview id
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip(), True, ""
        else:
            return "", False, "Failed to generate cover letter. Please try again."
            
    except Exception as e:
        error_msg = f"Error generating cover letter: {str(e)}"
        st.error(error_msg)
        return "", False, error_msg


def improve_cover_letter(cover_letter: str, improvement_request: str, 
                        api_key: Optional[str] = None) -> Tuple[str, bool, str]:
    """
    Improve existing cover letter based on user feedback
    
    Args:
        cover_letter: Current cover letter text
        improvement_request: User's improvement request
        api_key: Gemini API key
        
    Returns:
        Tuple of (improved_cover_letter, success_flag, error_message)
    """
    try:
        # Initialize Gemini
        if not initialize_gemini(api_key):
            return "", False, "Failed to initialize Gemini API"
        
        prompt = f"""
You are an AI assistant specialized in improving cover letters. Please improve the following cover letter based on the user's request.

CURRENT COVER LETTER:
{cover_letter}

IMPROVEMENT REQUEST:
{improvement_request}

INSTRUCTIONS:
- Maintain the same length and structure
- Keep the same tone and language
- Address the specific improvement request
- Ensure the improved version is professional and engaging
- Do not change the overall message or key points unless specifically requested

Provide the improved cover letter:
"""
        
        # Generate improved content
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip(), True, ""
        else:
            return "", False, "Failed to improve cover letter. Please try again."
            
    except Exception as e:
        error_msg = f"Error improving cover letter: {str(e)}"
        st.error(error_msg)
        return "", False, error_msg
