"""
Utility Functions Module
Contains helper functions for the cover letter generator app
"""

import streamlit as st
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Cover Letter Generator",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def apply_custom_css():
    """Apply modern, minimal, and professional CSS styling - Inspired by Notion, Linear, OpenAI"""
    from .ui_styles import MODERN_CSS
    st.markdown(MODERN_CSS, unsafe_allow_html=True)
    
    # Additional dynamic styles
    st.markdown("""
    <style>
    /* Additional Component Styles */
    .feature-card {
        background: var(--white);
        border: 1px solid var(--gray-200);
        border-radius: var(--radius-lg);
        padding: var(--space-6);
        margin: var(--space-4) 0;
        box-shadow: var(--shadow-sm);
        transition: all var(--transition-base);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
    }
    
    .feature-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
        border-color: var(--primary-light);
    }
    
    /* Status Messages */
    .stSuccess {
        background: var(--success-light);
        border-left: 4px solid var(--success);
        border-radius: var(--radius);
        padding: var(--space-4);
        margin: var(--space-4) 0;
    }
    
    .stError {
        background: var(--error-light);
        border-left: 4px solid var(--error);
        border-radius: var(--radius);
        padding: var(--space-4);
        margin: var(--space-4) 0;
    }
    
    .stWarning {
        background: var(--warning-light);
        border-left: 4px solid var(--warning);
        border-radius: var(--radius);
        padding: var(--space-4);
        margin: var(--space-4) 0;
    }
    
    .stInfo {
        background: var(--info-light);
        border-left: 4px solid var(--info);
        border-radius: var(--radius);
        padding: var(--space-4);
        margin: var(--space-4) 0;
    }
    
    /* Icon Styles */
    .icon {
        font-size: 1.25rem;
        line-height: 1;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Divider */
    .divider {
        height: 1px;
        background: var(--gray-200);
        margin: var(--space-8) 0;
        border: none;
    }
    
    /* Loading States */
    .loading-overlay {
        position: relative;
    }
    
    .loading-overlay::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(4px);
        border-radius: var(--radius);
        z-index: 1;
    }
    </style>
    """, unsafe_allow_html=True)


def create_database():
    """Create SQLite database for storing cover letters"""
    db_path = os.path.join(os.getcwd(), 'data', 'cover_letters.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            resume_text TEXT,
            job_description TEXT,
            tone TEXT,
            language TEXT,
            cover_letter TEXT,
            job_fit_score REAL,
            file_name TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def save_cover_letter(resume_text: str, job_description: str, tone: str, 
                     language: str, cover_letter: str, job_fit_score: float, 
                     file_name: str = "") -> bool:
    """
    Save cover letter to database
    
    Args:
        resume_text: Resume text
        job_description: Job description
        tone: Selected tone
        language: Selected language
        cover_letter: Generated cover letter
        job_fit_score: Job fit score
        file_name: Original file name
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        db_path = os.path.join(os.getcwd(), 'data', 'cover_letters.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cover_letters 
            (resume_text, job_description, tone, language, cover_letter, job_fit_score, file_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (resume_text, job_description, tone, language, cover_letter, job_fit_score, file_name))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Failed to save cover letter: {str(e)}")
        return False


def get_cover_letter_history() -> list:
    """
    Retrieve cover letter history from database
    
    Returns:
        List of cover letter records
    """
    try:
        db_path = os.path.join(os.getcwd(), 'data', 'cover_letters.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, tone, language, job_fit_score, file_name
            FROM cover_letters
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        
        records = cursor.fetchall()
        conn.close()
        
        return records
        
    except Exception as e:
        st.error(f"Failed to retrieve history: {str(e)}")
        return []


def get_cover_letter_by_id(letter_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve specific cover letter by ID
    
    Args:
        letter_id: Cover letter ID
        
    Returns:
        Cover letter data or None if not found
    """
    try:
        db_path = os.path.join(os.getcwd(), 'data', 'cover_letters.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM cover_letters WHERE id = ?
        ''', (letter_id,))
        
        record = cursor.fetchone()
        conn.close()
        
        if record:
            return {
                'id': record[0],
                'timestamp': record[1],
                'resume_text': record[2],
                'job_description': record[3],
                'tone': record[4],
                'language': record[5],
                'cover_letter': record[6],
                'job_fit_score': record[7],
                'file_name': record[8]
            }
        
        return None
        
    except Exception as e:
        st.error(f"Failed to retrieve cover letter: {str(e)}")
        return None


def generate_pdf(cover_letter: str, filename: str = None) -> str:
    """
    Generate PDF from cover letter text
    
    Args:
        cover_letter: Cover letter text
        filename: Output filename (optional)
        
    Returns:
        Path to generated PDF file
    """
    # Ensure output directory exists
    output_dir = os.path.join(os.getcwd(), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cover_letter_{timestamp}.pdf"
    
    # Ensure filename ends with .pdf
    if not filename.endswith('.pdf'):
        filename = f"{filename}.pdf"
    
    # Create full path in output directory
    filepath = os.path.join(output_dir, filename)
    
    # Create PDF document with comfortable margins
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()
    
    # Typography: modern, readable spacing
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=24,
        spaceAfter=14,
    )
    cover_letter_style = ParagraphStyle(
        'CoverLetter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11.5,
        leading=16.5,  # increased line spacing
        spaceBefore=2,
        spaceAfter=10,
    )
    
    # Split text into paragraphs
    paragraphs = cover_letter.split('\n\n')
    
    # Create story (content for PDF)
    story = []
    # Optional title for clarity
    story.append(Paragraph("Cover Letter", title_style))
    story.append(Spacer(1, 6))
    
    for para_text in paragraphs:
        if para_text.strip():
            para = Paragraph(para_text.strip(), cover_letter_style)
            story.append(para)
            story.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(story)
    
    return filepath


def generate_analysis_markdown(fit_analysis: dict) -> str:
    """
    Build a concise Markdown report from the job fit analysis result.
    """
    lines = []
    lines.append(f"# Job Fit Analysis\n")
    lines.append(f"Overall Fit: {fit_analysis.get('overall_score', 0):.1f}% ({fit_analysis.get('fit_level', '')})\n")
    cs = fit_analysis.get('category_scores', {})
    lines.append("## Category Breakdown")
    lines.append(f"- Technical Skills: {cs.get('technical_skills', 0):.1f}%")
    lines.append(f"- Experience & Education: {cs.get('experience_education', 0):.1f}%\n")

    # Experience constraints
    constraints = fit_analysis.get('experience_constraints', [])
    if constraints:
        lines.append("## Key Experience Requirements")
        for c in constraints:
            if isinstance(c, dict):
                if c.get('type') == 'years' and c.get('years') and c.get('field'):
                    lines.append(f"- Requires {c['years']}+ years in {c['field']}")
                elif c.get('type') == 'level' and c.get('level') and c.get('field'):
                    lines.append(f"- Expects {c['level']} level in {c['field']}")
        lines.append("")

    def block_for(name: str):
        lines.append(f"## {name}")
        md = fit_analysis.get('matched_details', {})
        mi = fit_analysis.get('missing_details', {})
        matches = md.get(name.lower().replace(' & ', '_').replace(' ', '_'), [])
        missing = mi.get(name.lower().replace(' & ', '_').replace(' ', '_'), [])
        if matches:
            lines.append("### Matched")
            for m in matches[:20]:
                if isinstance(m, dict):
                    lines.append(f"- {m.get('resume_keyword','')} → {m.get('job_keyword','')} ({m.get('match_type','')}, {m.get('confidence',0):.2f})")
        if missing:
            lines.append("### Missing")
            for x in missing[:20]:
                lines.append(f"- {x}")
        lines.append("")

    block_for("Technical Skills")
    block_for("Experience & Education")

    rec = fit_analysis.get('recommendations', {})
    if any(rec.values()):
        lines.append("## Recommendations")
        for k in ['learn_skills','highlight_skills','add_experience','specific_examples']:
            v = rec.get(k, [])
            if v:
                pretty = k.replace('_',' ').title()
                lines.append(f"### {pretty}")
                for item in v:
                    lines.append(f"- {item}")
                lines.append("")
    return "\n".join(lines)


def generate_analysis_pdf(fit_analysis: dict, filename: str = None) -> str:
    """
    Generate a PDF report from the job fit analysis using ReportLab.
    """
    # Ensure output directory exists
    output_dir = os.path.join(os.getcwd(), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_fit_analysis_{timestamp}.pdf"
    
    # Ensure filename ends with .pdf
    if not filename.endswith('.pdf'):
        filename = f"{filename}.pdf"
    
    # Create full path in output directory
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        'H1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, leading=26, spaceAfter=14
    )
    h2 = ParagraphStyle(
        'H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14.5, leading=20, spaceAfter=10
    )
    h3 = ParagraphStyle(
        'H3', parent=styles['Heading3'], fontName='Helvetica-Bold', fontSize=12.5, leading=18, spaceAfter=8
    )
    body = ParagraphStyle(
        'Body', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16.5, spaceAfter=8
    )
    bullet = ParagraphStyle(
        'Bullet', parent=body, leftIndent=14, bulletIndent=0, spaceBefore=2, spaceAfter=6
    )

    story = []
    story.append(Paragraph("Job Fit Analysis", h1))
    story.append(Paragraph(f"Overall Fit: {fit_analysis.get('overall_score', 0):.1f}% ({fit_analysis.get('fit_level','')})", body))
    cs = fit_analysis.get('category_scores', {})
    story.append(Paragraph("Category Breakdown", h2))
    story.append(Paragraph(f"• Technical Skills: {cs.get('technical_skills', 0):.1f}%", body))
    story.append(Paragraph(f"• Experience & Education: {cs.get('experience_education', 0):.1f}%", body))
    story.append(Spacer(1, 8))

    constraints = fit_analysis.get('experience_constraints', [])
    if constraints:
        story.append(Paragraph("Key Experience Requirements", h2))
        for c in constraints:
            if isinstance(c, dict):
                if c.get('type') == 'years' and c.get('years') and c.get('field'):
                    story.append(Paragraph(f"• Requires {c['years']}+ years in {c['field']}", body))
                elif c.get('type') == 'level' and c.get('level') and c.get('field'):
                    story.append(Paragraph(f"• Expects {c['level']} level in {c['field']}", body))
        story.append(Spacer(1, 8))

    def section(title: str, key: str):
        story.append(Paragraph(title, h2))
        md = fit_analysis.get('matched_details', {})
        mi = fit_analysis.get('missing_details', {})
        matches = md.get(key, [])
        missing = mi.get(key, [])
        if matches:
            story.append(Paragraph("Matched", h3))
            for m in matches[:20]:
                if isinstance(m, dict):
                    story.append(Paragraph(
                        f"• {m.get('resume_keyword','')} → {m.get('job_keyword','')} "
                        f"({m.get('match_type','')}, {m.get('confidence',0):.2f})",
                        body
                    ))
        if missing:
            story.append(Paragraph("Missing", h3))
            for x in missing[:20]:
                story.append(Paragraph(f"• {x}", body))
        story.append(Spacer(1, 8))

    section("Technical Skills", 'technical_skills')
    section("Experience & Education", 'experience_education')

    rec = fit_analysis.get('recommendations', {})
    if any(rec.values()):
        story.append(Paragraph("Recommendations", h2))
        for k in ['learn_skills','highlight_skills','add_experience','specific_examples']:
            v = rec.get(k, [])
            if v:
                story.append(Paragraph(k.replace('_',' ').title(), h3))
                for item in v:
                    story.append(Paragraph(f"• {item}", body))
        story.append(Spacer(1, 8))

    doc.build(story)
    return filepath


def validate_api_key(api_key: str) -> bool:
    """
    Validate Gemini API key format
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not api_key:
        return False
    
    # Basic validation - Gemini API keys typically start with 'AIza'
    if api_key.startswith('AIza') and len(api_key) > 20:
        return True
    
    return False


def get_api_key_file_path() -> str:
    """
    Get the path to the API key storage file
    
    Returns:
        Path to the API key file
    """
    config_dir = os.path.join(os.getcwd(), 'data', 'config')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'api_key.txt')


def save_api_key(api_key: str) -> bool:
    """
    Save API key to local file
    
    Args:
        api_key: API key to save
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        if not validate_api_key(api_key):
            return False
        
        file_path = get_api_key_file_path()
        # Save with restricted permissions (owner read/write only)
        with open(file_path, 'w') as f:
            f.write(api_key.strip())
        
        # Set file permissions to be readable/writable only by owner (Unix-like systems)
        try:
            os.chmod(file_path, 0o600)
        except (AttributeError, OSError):
            # Windows doesn't support chmod the same way, skip
            pass
        
        return True
    except Exception as e:
        st.error(f"Failed to save API key: {str(e)}")
        return False


def load_api_key_from_file() -> Optional[str]:
    """
    Load API key from local file
    
    Returns:
        API key if found and valid, None otherwise
    """
    try:
        file_path = get_api_key_file_path()
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            api_key = f.read().strip()
        
        if validate_api_key(api_key):
            return api_key
        return None
    except Exception:
        return None


def delete_api_key_file() -> bool:
    """
    Delete the saved API key file
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        file_path = get_api_key_file_path()
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception:
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension (lowercase)
    """
    return os.path.splitext(filename)[1].lower()


def is_supported_file(filename: str) -> bool:
    """
    Check if file type is supported
    
    Args:
        filename: Name of the file
        
    Returns:
        True if supported, False otherwise
    """
    supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    extension = get_file_extension(filename)
    return extension in supported_extensions


def create_progress_bar(progress: float, label: str = "") -> None:
    """
    Create a progress bar with label
    
    Args:
        progress: Progress value (0-1)
        label: Label for progress bar
    """
    if label:
        st.write(label)
    
    progress_bar = st.progress(progress)
    return progress_bar


def display_fit_score_card(score: float, title: str, description: str = "") -> None:
    """
    Display a modern fit score card with color coding
    
    Args:
        score: Score value (0-100)
        title: Card title
        description: Optional description
    """
    # Determine color class based on score
    if score >= 80:
        color_class = "fit-score-excellent"
        color = "var(--success)"
        icon = "🎯"
    elif score >= 60:
        color_class = "fit-score-good"
        color = "var(--info)"
        icon = "✅"
    elif score >= 40:
        color_class = "fit-score-fair"
        color = "var(--warning)"
        icon = "⚠️"
    else:
        color_class = "fit-score-poor"
        color = "var(--error)"
        icon = "❌"
    
    st.markdown(f"""
    <div class="fit-score-card {color_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0 0 0.5rem 0; color: var(--gray-900); font-family: 'Inter', sans-serif; font-weight: 600; font-size: 1.125rem;">{icon} {title}</h3>
                <p style="margin: 0; color: var(--gray-600); font-family: 'Inter', sans-serif; font-size: 0.875rem;">{description}</p>
            </div>
            <div style="text-align: right;">
                <div style="color: {color}; font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 700; line-height: 1;">{score:.1f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_skill_match_card(skill: str, match_type: str, confidence: float = None, is_matched: bool = True) -> None:
    """
    Display a skill match card with color coding and visual indicators
    
    Args:
        skill: Skill name
        match_type: Type of match (exact, semantic, partial)
        confidence: Confidence score (0-1)
        is_matched: Whether the skill is matched or missing
    """
    if is_matched:
        if match_type == 'exact':
            card_class = "skill-matched"
            icon = "✅"
            bg_color = "#f0fdf4"
            border_color = "#10b981"
            match_label = "Exact Match"
        elif match_type == 'semantic':
            card_class = "skill-matched"
            icon = "🎯"
            bg_color = "#f0fdf4"
            border_color = "#10b981"
            match_label = "Semantic Match"
        elif match_type == 'partial':
            card_class = "skill-partial"
            icon = "⚠️"
            bg_color = "#fefce8"
            border_color = "#f59e0b"
            match_label = "Partial Match"
        else:
            card_class = "skill-matched"
            icon = "✅"
            bg_color = "#f0fdf4"
            border_color = "#10b981"
            match_label = "Match"
    else:
        card_class = "skill-missing"
        icon = "❌"
        bg_color = "#fef2f2"
        border_color = "#ef4444"
        match_label = "Missing"
    
    confidence_text = f" ({confidence:.2f})" if confidence else ""
    
    st.markdown(f"""
    <div class="skill-match-card {card_class}">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.25rem;">{icon}</span>
            <div style="flex: 1;">
                <div style="color: var(--gray-900); font-family: 'Inter', sans-serif; font-weight: 500; font-size: 0.875rem;">{skill}</div>
                <div style="color: var(--gray-500); font-family: 'Inter', sans-serif; font-size: 0.75rem; margin-top: 0.25rem;">{match_label}{confidence_text}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_progress_bar(value: float, max_value: float = 100, label: str = "") -> None:
    """
    Display a modern progress bar
    
    Args:
        value: Current value
        max_value: Maximum value
        label: Optional label
    """
    percentage = (value / max_value) * 100
    
    st.markdown(f"""
    <div class="progress-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-family: 'Inter', sans-serif; font-weight: 500; color: var(--gray-800); font-size: 0.875rem;">{label}</span>
            <span style="font-family: 'Inter', sans-serif; font-weight: 600; color: var(--gray-600); font-size: 0.875rem;">{value:.1f}/{max_value}</span>
        </div>
        <div style="background: var(--gray-200); border-radius: var(--border-radius); height: 8px; overflow: hidden;">
            <div class="progress-bar" style="width: {percentage}%; height: 100%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_metric_card(title: str, value: str, delta: str = None) -> None:
    """
    Display a metric card
    
    Args:
        title: Card title
        value: Main value
        delta: Delta value (optional)
    """
    delta_html = f'<div style="color: var(--gray-500); font-family: \'Inter\', sans-serif; font-size: 0.75rem; margin-top: 0.5rem;">{delta}</div>' if delta else ''
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def show_success_message(message: str) -> None:
    """Display success message"""
    st.markdown(f"""
    <div class="success-box">
        {message}
    </div>
    """, unsafe_allow_html=True)


def show_error_message(message: str) -> None:
    """Display error message"""
    st.markdown(f"""
    <div class="error-box">
        {message}
    </div>
    """, unsafe_allow_html=True)


def show_warning_message(message: str) -> None:
    """Display warning message"""
    st.markdown(f"""
    <div class="warning-box">
        {message}
    </div>
    """, unsafe_allow_html=True)


def show_info_message(message: str) -> None:
    """Display info message"""
    st.markdown(f"""
    <div class="info-box">
        {message}
    </div>
    """, unsafe_allow_html=True)
