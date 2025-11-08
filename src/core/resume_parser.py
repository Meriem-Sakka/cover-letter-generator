"""
Resume Parser Module
Handles text extraction from PDF and image files
"""

import pdfplumber
import PyPDF2
import pytesseract
from PIL import Image
import io
import streamlit as st
from typing import Optional, Tuple


def extract_text_from_pdf(file_content: bytes) -> Tuple[str, bool]:
    """
    Extract text from PDF file using pdfplumber and PyPDF2 as fallback
    
    Args:
        file_content: PDF file content as bytes
        
    Returns:
        Tuple of (extracted_text, success_flag)
    """
    try:
        # Try pdfplumber first (better for complex layouts)
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if text.strip():
                return text.strip(), True
                
    except Exception as e:
        st.warning(f"pdfplumber failed: {str(e)}")
    
    try:
        # Fallback to PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        if text.strip():
            return text.strip(), True
            
    except Exception as e:
        st.error(f"PyPDF2 failed: {str(e)}")
    
    return "", False


def extract_text_from_image(file_content: bytes) -> Tuple[str, bool]:
    """
    Extract text from image using OCR (pytesseract)
    
    Args:
        file_content: Image file content as bytes
        
    Returns:
        Tuple of (extracted_text, success_flag)
    """
    try:
        # Open image with PIL
        image = Image.open(io.BytesIO(file_content))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image)
        
        if text.strip():
            return text.strip(), True
        else:
            return "", False
            
    except Exception as e:
        st.error(f"OCR extraction failed: {str(e)}")
        return "", False


def validate_file(file_content: bytes, file_type: str, max_size_mb: float = 10.0) -> Tuple[bool, str]:
    """
    Validate uploaded file
    
    Args:
        file_content: File content as bytes
        file_type: MIME type of the file
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
    
    # Check file type
    allowed_types = {
        'application/pdf': ['.pdf'],
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/jpg': ['.jpg']
    }
    
    if file_type not in allowed_types:
        return False, f"Unsupported file type: {file_type}. Supported types: PDF, JPG, PNG, JPEG"
    
    return True, ""


def extract_resume_text(file_content: bytes, file_type: str) -> Tuple[str, bool, str]:
    """
    Main function to extract text from resume file
    
    Args:
        file_content: File content as bytes
        file_type: MIME type of the file
        
    Returns:
        Tuple of (extracted_text, success_flag, error_message)
    """
    # Validate file
    is_valid, error_msg = validate_file(file_content, file_type)
    if not is_valid:
        return "", False, error_msg
    
    # Extract text based on file type
    if file_type == 'application/pdf':
        text, success = extract_text_from_pdf(file_content)
    elif file_type in ['image/jpeg', 'image/png', 'image/jpg']:
        text, success = extract_text_from_image(file_content)
    else:
        return "", False, f"Unsupported file type: {file_type}"
    
    if success and text.strip():
        return text, True, ""
    else:
        return "", False, "Failed to extract text from the file. Please ensure the file contains readable text."
