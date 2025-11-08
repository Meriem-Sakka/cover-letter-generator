"""
Cover Letter Generator
Main Streamlit Application
"""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules
from src.core.resume_parser import extract_resume_text
from src.core.ai_generator import generate_cover_letter, improve_cover_letter
from src.core.job_fit import analyze_job_fit
from src.services.ab_testing import generate_cover_letter_variations
from src.services.interview_prep import generate_interview_prep
from src.utils import (
    setup_page_config, apply_custom_css, create_database, save_cover_letter,
    get_cover_letter_history, get_cover_letter_by_id, generate_pdf,
    validate_api_key, format_file_size, show_success_message, show_error_message,
    show_warning_message, show_info_message, display_metric_card,
    display_fit_score_card, display_skill_match_card, display_progress_bar,
    generate_analysis_markdown, generate_analysis_pdf
)
from src.config import SUPPORTED_MODES, DEFAULT_ANALYSIS_MODE

# Page configuration
setup_page_config()
apply_custom_css()

# Initialize database
create_database()

# Load API key from environment
def get_api_key():
    """Load API key from environment variables"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None, "No API key found in .env file"
    elif not validate_api_key(api_key):
        return None, "Invalid API key format in .env file"
    else:
        return api_key, "API key loaded successfully"

# Check API key status
api_key, api_status = get_api_key()

# Main header
st.markdown("""
<div style="text-align: center; margin-bottom: 3rem;">
    <h1 class="main-header">Cover Letter Generator</h1>
    <p style="color: var(--gray-600); font-size: 1.125rem; margin-top: 1rem; max-width: 600px; margin-left: auto; margin-right: auto;">
        AI-powered cover letter generation tailored to your resume and job description
    </p>
</div>
""", unsafe_allow_html=True)

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["Generate", "Analysis", "History", "Interview Prep"])

with tab1:
    st.markdown("""
    <div style="margin-bottom: 2.5rem;">
        <h2 class="sub-header">✨ Generate Your Cover Letter</h2>
        <p style="color: var(--gray-600); font-size: 1.05rem; margin-top: 0.5rem; line-height: 1.7;">
            Upload your resume, paste the job description, and let AI create a personalized cover letter tailored to the position.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for layout with better spacing
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div class="section-header">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">📄</span>
            Upload Resume
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <p style="color: var(--gray-600); font-size: 0.9rem; margin: 0.5rem 0 1rem 0;">
            Supported formats: PDF, JPG, PNG, JPEG (Max 10MB)
        </p>
        """, unsafe_allow_html=True)
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Upload your resume file to extract information",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            # Display file info in a modern card
            file_size = format_file_size(uploaded_file.size)
            st.markdown(f"""
            <div style="background: var(--white); border: 1px solid var(--gray-200); 
                        border-radius: var(--radius-lg); padding: var(--space-5); 
                        margin: var(--space-4) 0; box-shadow: var(--shadow-sm);">
                <div style="display: flex; align-items: center; gap: var(--space-3);">
                    <span style="font-size: 2rem;">📎</span>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: var(--gray-900); margin-bottom: 0.25rem;">
                            {uploaded_file.name}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--gray-500);">
                            Size: {file_size}
                        </div>
                    </div>
                    <span style="color: var(--success); font-size: 1.25rem;">✓</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Extract text from resume
            with st.spinner("Extracting text from resume..."):
                resume_text, success, error_msg = extract_resume_text(
                    uploaded_file.read(), uploaded_file.type
                )
                
                if success:
                    st.session_state['resume_text'] = resume_text
                    st.session_state['resume_filename'] = uploaded_file.name
                    st.success("✓ Resume text extracted successfully!")
                    
                    # Show extracted text preview in an expander
                    with st.expander("📋 Preview Extracted Text", expanded=False):
                        st.text_area("Resume Text", resume_text, height=200, disabled=True, label_visibility="collapsed")
                else:
                    show_error_message(f"Failed to extract text: {error_msg}")
                    st.session_state['resume_text'] = None
        else:
            st.session_state['resume_text'] = None
            st.markdown("""
            <div style="background: var(--info-light); border-left: 4px solid var(--info); 
                        border-radius: var(--radius); padding: var(--space-4); margin: var(--space-4) 0;">
                <p style="margin: 0; color: var(--gray-700); font-size: 0.95rem;">
                    💡 Please upload your resume to get started
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="section-header">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">💼</span>
            Job Description
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <p style="color: var(--gray-600); font-size: 0.9rem; margin: 0.5rem 0 1rem 0;">
            <span class="tooltip" data-tooltip="More details = better tailored cover letter">💡</span>
            The more detailed the job description, the better your cover letter will be personalized.
        </p>
        """, unsafe_allow_html=True)
        
        # Job description input
        job_description = st.text_area(
            "Paste the job description here",
            height=200,
            placeholder="Paste the complete job description including:\n• Job title and company\n• Key requirements\n• Responsibilities\n• Qualifications\n• Skills needed",
            help="Include all relevant details from the job posting for best results",
            label_visibility="collapsed"
        )
        
        if job_description:
            st.session_state['job_description'] = job_description
            word_count = len(job_description.split())
            if word_count < 50:
                st.warning("⚠️ Job description seems short. Adding more details will improve the cover letter quality.")
        else:
            st.session_state['job_description'] = None
            st.markdown("""
            <div style="background: var(--info-light); border-left: 4px solid var(--info); 
                        border-radius: var(--radius); padding: var(--space-4); margin: var(--space-4) 0;">
                <p style="margin: 0; color: var(--gray-700); font-size: 0.95rem;">
                    💡 Please paste the job description to continue
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Customization section with modern card design
    st.markdown("""
    <div style="margin: var(--space-8) 0 var(--space-6) 0;">
        <h2 class="section-header">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">⚙️</span>
            Customization Options
        </h2>
        <p style="color: var(--gray-600); font-size: 0.95rem; margin-top: 0.5rem;">
            Customize the tone, language, and add specific instructions to tailor your cover letter.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create modern card for customization
    st.markdown("""
    <div class="modern-card" style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.9) 100%); 
                border: 1px solid var(--gray-200); 
                border-radius: var(--radius-lg); padding: var(--space-6); 
                margin: var(--space-4) 0; box-shadow: var(--shadow-md);">
    """, unsafe_allow_html=True)
    
    # Create three columns for options
    opt_col1, opt_col2, opt_col3 = st.columns([1, 1, 1], gap="medium")
    
    with opt_col1:
        tone = st.selectbox(
            "🎨 Tone",
            ["Professional", "Friendly", "Formal", "Enthusiastic"],
            help="Choose the tone for your cover letter",
            key="tone_select"
        )
    
    with opt_col2:
        language = st.selectbox(
            "🌐 Language",
            ["English", "French", "Arabic"],
            help="Select the language for your cover letter",
            key="language_select"
        )
    
    with opt_col3:
        st.markdown("""
        <div style="padding: 0.75rem 0;">
            <label style="font-size: 0.875rem; font-weight: 500; color: var(--gray-700); margin-bottom: 0.5rem; display: block;">
                💬 Custom Instructions
            </label>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)  # Close customization card
    
    # Custom instructions in full width
    user_prompt = st.text_area(
        "Add custom instructions or preferences:",
        placeholder="e.g., Emphasize teamwork and adaptability\nMake it sound more formal and concise\nHighlight leadership experience and project results",
        help="Add specific instructions to customize your cover letter. Leave blank to use default AI generation.",
        height=100,
        label_visibility="collapsed",
        key="custom_prompt"
    )
    
    # Generate button section with better styling
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create a prominent button section
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn2:
        can_generate = st.session_state.get('resume_text') and st.session_state.get('job_description')
        
        if not can_generate:
            st.markdown("""
            <div style="background: var(--warning-light); border-left: 4px solid var(--warning); 
                        border-radius: var(--radius); padding: var(--space-4); margin: var(--space-4) 0;">
                <p style="margin: 0; color: var(--gray-700); font-size: 0.9rem;">
                    ⚠️ Please upload a resume and enter a job description before generating
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        generate_button = st.button(
            "🚀 Generate Cover Letter",
            type="primary",
            use_container_width=True,
            disabled=not can_generate,
            key="generate_btn_main"
        )
    
    if generate_button:
        # Validate inputs
        if not st.session_state.get('resume_text'):
            show_error_message("Please upload a resume file")
        elif not st.session_state.get('job_description'):
            show_error_message("Please enter a job description")
        elif not api_key:
            show_error_message("Gemini API key not found. Please create a .env file with GEMINI_API_KEY=your_key")
        else:
            # Generate cover letter
            with st.spinner("Generating your personalized cover letter..."):
                cover_letter, success, error_msg = generate_cover_letter(
                    st.session_state['resume_text'],
                    st.session_state['job_description'],
                    tone,
                    language,
                    api_key,
                    user_prompt
                )
                
                if success:
                    st.session_state['cover_letter'] = cover_letter
                    st.session_state['tone'] = tone
                    st.session_state['language'] = language
                    show_success_message("Cover letter generated successfully!")
                else:
                    show_error_message(f"Failed to generate cover letter: {error_msg}")
    
    # Display generated cover letter
    if st.session_state.get('cover_letter'):
        st.subheader("Your Cover Letter")
        
        # Editable text area
        edited_cover_letter = st.text_area(
            "Edit your cover letter",
            value=st.session_state['cover_letter'],
            height=400,
            help="You can edit the generated cover letter here"
        )
        
        # Update session state with edited version
        st.session_state['cover_letter'] = edited_cover_letter
        
        # A/B Testing Section
        st.markdown("""
        <div style="margin: 3rem 0 2rem 0; padding-top: 2rem; border-top: 2px solid var(--gray-200);">
            <h3 class="section-header" style="margin-top: 0;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">🧪</span>
                A/B Testing - Compare Variations
            </h3>
            <div class="modern-card" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%); 
                        border-left: 4px solid var(--primary); padding: 1.25rem; margin: 1rem 0; border-radius: var(--radius-lg);">
                <p style="margin: 0; color: var(--gray-700); font-size: 0.95rem; line-height: 1.6;">
                    Generate 2-3 variations with different tones and focus points. Compare them side-by-side to find the most effective version.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Generate Variations", type="primary", use_container_width=True, key="generate_variations"):
            if not api_key:
                show_error_message("Gemini API key required for A/B testing. Please add GEMINI_API_KEY to .env file.")
            else:
                with st.spinner("Generating cover letter variations (this may take a minute)..."):
                    try:
                        variations = generate_cover_letter_variations(
                            st.session_state['resume_text'],
                            st.session_state['job_description'],
                            tone,
                            language,
                            api_key,
                            num_variations=3,
                            user_prompt=user_prompt
                        )
                        if variations:
                            st.session_state['cover_letter_variations'] = variations
                            show_success_message(f"Generated {len(variations)} variations successfully!")
                        else:
                            show_error_message("Failed to generate variations. Please try again.")
                    except Exception as e:
                        show_error_message(f"Error generating variations: {str(e)}")
        
        # Display Variations
        if st.session_state.get('cover_letter_variations'):
            variations = st.session_state['cover_letter_variations']
            
            # Create tabs for each variation
            if len(variations) == 2:
                var_tab1, var_tab2 = st.tabs([f"Variation 1: {variations[0]['name']}", f"Variation 2: {variations[1]['name']}"])
                tabs = [var_tab1, var_tab2]
            elif len(variations) == 3:
                var_tab1, var_tab2, var_tab3 = st.tabs([
                    f"Variation 1: {variations[0]['name']}", 
                    f"Variation 2: {variations[1]['name']}",
                    f"Variation 3: {variations[2]['name']}"
                ])
                tabs = [var_tab1, var_tab2, var_tab3]
            else:
                tabs = []
            
            for i, (tab, variation) in enumerate(zip(tabs, variations), 1):
                with tab:
                    st.markdown(f"**{variation['description']}**")
                    st.info(variation.get('focus', ''))
                    
                    # Display variation text
                    variation_text = st.text_area(
                        f"Variation {i}",
                        value=variation['text'],
                        height=300,
                        key=f"variation_{i}_text",
                        label_visibility="collapsed"
                    )
                    
                    # Action buttons for each variation
                    var_col1, var_col2, var_col3 = st.columns(3)
                    with var_col1:
                        if st.button(f"Select This", key=f"select_var_{i}", use_container_width=True):
                            st.session_state['cover_letter'] = variation_text
                            show_success_message(f"Selected Variation {i}: {variation['name']}")
                            st.rerun()
                    with var_col2:
                        pass  # Placeholder for future features
                    with var_col3:
                        # Generate PDF only when user explicitly requests download (on-demand)
                        pdf_filename = f"cover_letter_variation_{i}_{variation['name'].lower().replace(' ', '_')}.pdf"
                        pdf_key = f'pdf_var_{i}'
                        
                        # Check if PDF is already generated and cached
                        if pdf_key not in st.session_state:
                            # Show button to generate PDF (only generates when clicked)
                            if st.button("📥 Generate & Download PDF", key=f"generate_pdf_var_{i}", use_container_width=True):
                                with st.spinner("Generating PDF..."):
                                    try:
                                        pdf_path = generate_pdf(variation_text, filename=f"variation_{i}.pdf")
                                        with open(pdf_path, "rb") as pdf_file:
                                            pdf_bytes = pdf_file.read()
                                        # Store in session state for download
                                        st.session_state[pdf_key] = pdf_bytes
                                        # Clean up temporary file immediately
                                        try:
                                            os.remove(pdf_path)
                                        except:
                                            pass
                                        st.rerun()
                                    except Exception as e:
                                        show_error_message(f"Failed to generate PDF: {str(e)}")
                        else:
                            # PDF is ready, show download button
                            st.download_button(
                                label="📥 Download PDF",
                                data=st.session_state[pdf_key],
                                file_name=pdf_filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"download_var_{i}"
                            )
                            # Optional: Clear cached PDF after showing download button to save memory
                            # (Uncomment if memory is a concern)
                            # del st.session_state[pdf_key]
        
        # Action buttons
        col5, col6, col7 = st.columns([1, 1, 1])
        
        with col5:
            if st.button("Regenerate", use_container_width=True):
                if not api_key:
                    show_error_message("Gemini API key not found. Please create a .env file with GEMINI_API_KEY=your_key")
                else:
                    with st.spinner("Regenerating cover letter..."):
                        cover_letter, success, error_msg = generate_cover_letter(
                            st.session_state['resume_text'],
                            st.session_state['job_description'],
                            tone,
                            language,
                            api_key,
                            user_prompt
                        )
                        
                        if success:
                            st.session_state['cover_letter'] = cover_letter
                            st.rerun()
                        else:
                            show_error_message(f"Failed to regenerate: {error_msg}")
        
        with col6:
            if st.button("Save Letter", use_container_width=True):
                # Calculate job fit score with spinner
                with st.spinner("💾 Saving cover letter and analyzing job fit..."):
                    fit_analysis = analyze_job_fit(
                        st.session_state['resume_text'],
                        st.session_state['job_description'],
                        api_key
                    )
                # Save to database
                if save_cover_letter(
                    st.session_state['resume_text'],
                    st.session_state['job_description'],
                    st.session_state['tone'],
                    st.session_state['language'],
                    st.session_state['cover_letter'],
                    fit_analysis['overall_score'],
                    st.session_state.get('resume_filename', '')
                ):
                    show_success_message("Cover letter saved successfully!")
                else:
                    show_error_message("Failed to save cover letter")
        
        with col7:
            # Generate PDF on-demand when download is requested
            cover_letter_pdf_key = 'cover_letter_pdf'
            if cover_letter_pdf_key not in st.session_state:
                # Show button to generate PDF
                if st.button("📥 Generate & Download PDF", key="generate_main_pdf", use_container_width=True):
                    with st.spinner("Generating PDF..."):
                        try:
                            pdf_path = generate_pdf(st.session_state['cover_letter'])
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                            st.session_state[cover_letter_pdf_key] = pdf_bytes
                            # Clean up temporary file
                            try:
                                os.remove(pdf_path)
                            except:
                                pass
                            st.rerun()
                        except Exception as e:
                            show_error_message(f"Failed to generate PDF: {str(e)}")
            else:
                # PDF is ready, show download button
                st.download_button(
                    label="📥 Download PDF",
                    data=st.session_state[cover_letter_pdf_key],
                    file_name=f"cover_letter_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_main_cover_letter"
                )

with tab2:
    st.markdown('<h2 class="sub-header">Job Fit Analysis</h2>', unsafe_allow_html=True)
    
    if st.session_state.get('resume_text') and st.session_state.get('job_description'):
        # Analysis options
        opt_col_a, opt_col_b = st.columns([1,1])
        with opt_col_a:
            analysis_mode = st.selectbox("Analysis Mode", SUPPORTED_MODES, index=SUPPORTED_MODES.index(DEFAULT_ANALYSIS_MODE))
        # Show API key status for analysis
        if not api_key:
            show_warning_message("Analysis running in fallback mode (no AI features). Add GEMINI_API_KEY to .env for enhanced analysis.")
        
        # Perform analysis with simple spinner
        with st.spinner("Analyzing job fit..."):
            fit_analysis = analyze_job_fit(
                st.session_state['resume_text'],
                st.session_state['job_description'],
                api_key,
                analysis_mode
            )
        
        # Show success message
        st.success("Analysis complete!")
        # Warn if rate-limited (partial results possible)
        try:
            if fit_analysis.get('rate_limited'):
                show_warning_message("Rate limit reached on AI service. Results may be partial; please retry in a moment.")
        except Exception:
            pass
        
        # Overall Fit Score - Large Display
        st.markdown('<h3 class="section-header">Overall Fit Score</h3>', unsafe_allow_html=True)
        display_fit_score_card(
            fit_analysis['overall_score'],
            f"Overall Match: {fit_analysis['fit_level']}",
            f"Language: {fit_analysis.get('detected_language', 'en').upper()}"
        )
        
        # Category Breakdown
        st.markdown('<h3 class="section-header">Category Breakdown</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Technical Skills
            display_progress_bar(
                fit_analysis['category_scores']['technical_skills'],
                label="Technical Skills",
                max_value=100
            )
        
        with col2:
            # Experience & Education
            display_progress_bar(
                fit_analysis['category_scores']['experience_education'],
                label="Experience & Education",
                max_value=100
            )
        
        # Detailed Analysis in Tabs
        st.markdown('<h3 class="section-header">Detailed Analysis</h3>', unsafe_allow_html=True)
        
        # Check if methodologies exist in job requirements or candidate profile
        has_methodologies = (
            len(fit_analysis.get('job_requirements', {}).get('methodologies', [])) > 0 or
            len(fit_analysis.get('candidate_profile', {}).get('methodologies', [])) > 0 or
            len(fit_analysis['matched_details']['methodologies']) > 0 or
            len(fit_analysis['missing_details']['methodologies']) > 0
        )
        
        # Create tabs conditionally
        if has_methodologies:
            analysis_tab1, analysis_tab2, analysis_tab3, analysis_tab4 = st.tabs([
                "Technical Skills", 
                "Methodologies", 
                "Experience & Education",
                "Recommendations"
            ])
        else:
            analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
                "Technical Skills", 
                "Experience & Education",
                "Recommendations"
            ])
        
        with analysis_tab1:
            st.markdown("#### Matched Skills")
            if fit_analysis['matched_details']['technical_skills']:
                for match in fit_analysis['matched_details']['technical_skills']:
                    display_skill_match_card(
                        f"{match['resume_keyword']} → {match['job_keyword']}",
                        match['match_type'],
                        match['confidence'],
                        is_matched=True
                    )
            else:
                st.info("No technical skills matched.")
            
            st.markdown("#### Missing Skills")
            if fit_analysis['missing_details']['technical_skills']:
                for skill in fit_analysis['missing_details']['technical_skills'][:10]:  # Limit to 10
                    display_skill_match_card(skill, "missing", is_matched=False)
            else:
                st.success("All required technical skills are covered!")
        
        with analysis_tab2:
            if has_methodologies:
                st.markdown("#### Matched Methodologies")
                if fit_analysis['matched_details']['methodologies']:
                    for match in fit_analysis['matched_details']['methodologies']:
                        display_skill_match_card(
                            f"{match['resume_keyword']} → {match['job_keyword']}",
                            match['match_type'],
                            match['confidence'],
                            is_matched=True
                        )
                else:
                    st.info("No methodologies matched.")
                
                st.markdown("#### Missing Methodologies")
                if fit_analysis['missing_details']['methodologies']:
                    for method in fit_analysis['missing_details']['methodologies'][:10]:
                        display_skill_match_card(method, "missing", is_matched=False)
                else:
                    st.success("All required methodologies are covered!")
            else:
                # Experience & Education tab when methodologies don't exist
                # Key experience constraints
                constraints = fit_analysis.get('experience_constraints', [])
                if constraints:
                    st.markdown("#### Key Experience Requirements")
                    for c in constraints:
                        try:
                            if c.get('type') == 'years' and c.get('years') and c.get('field'):
                                show_info_message(f"This job requires {c['years']}+ years in {c['field']}.")
                            elif c.get('type') == 'level' and c.get('level') and c.get('field'):
                                show_info_message(f"This job expects {c['level']} level in {c['field']}.")
                        except Exception:
                            pass
                st.markdown("#### Matched Experience & Education")
                if fit_analysis['matched_details']['experience_education']:
                    for match in fit_analysis['matched_details']['experience_education']:
                        display_skill_match_card(
                            f"{match['resume_keyword']} → {match['job_keyword']}",
                            match['match_type'],
                            match['confidence'],
                            is_matched=True
                        )
                else:
                    st.info("No experience or education matched.")
                
                st.markdown("#### Missing Experience & Education")
                if fit_analysis['missing_details']['experience_education']:
                    for item in fit_analysis['missing_details']['experience_education'][:10]:
                        display_skill_match_card(item, "missing", is_matched=False)
                else:
                    st.success("All required experience and education are covered!")
        
        with analysis_tab3:
            if has_methodologies:
                # Experience & Education tab when methodologies exist
                # Key experience constraints
                constraints = fit_analysis.get('experience_constraints', [])
                if constraints:
                    st.markdown("#### Key Experience Requirements")
                    for c in constraints:
                        try:
                            if c.get('type') == 'years' and c.get('years') and c.get('field'):
                                show_info_message(f"This job requires {c['years']}+ years in {c['field']}.")
                            elif c.get('type') == 'level' and c.get('level') and c.get('field'):
                                show_info_message(f"This job expects {c['level']} level in {c['field']}.")
                        except Exception:
                            pass
                st.markdown("#### Matched Experience & Education")
                if fit_analysis['matched_details']['experience_education']:
                    for match in fit_analysis['matched_details']['experience_education']:
                        display_skill_match_card(
                            f"{match['resume_keyword']} → {match['job_keyword']}",
                            match['match_type'],
                            match['confidence'],
                            is_matched=True
                        )
                else:
                    st.info("No experience or education matched.")
                
                st.markdown("#### Missing Experience & Education")
                if fit_analysis['missing_details']['experience_education']:
                    for item in fit_analysis['missing_details']['experience_education'][:10]:
                        display_skill_match_card(item, "missing", is_matched=False)
                else:
                    st.success("All required experience and education are covered!")
            else:
                # Recommendations tab when methodologies don't exist
                st.markdown("#### AI-Generated Recommendations")
                recommendations = fit_analysis.get('recommendations', {})
                
                if recommendations.get('learn_skills'):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.125rem;">
                            📚 Skills to Learn
                        </h4>
                        <div style="color: white; font-family: 'Inter', sans-serif;">
                    """, unsafe_allow_html=True)
                    for skill in recommendations['learn_skills']:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; 
                                        padding: 0.75rem 1rem; margin: 0.5rem 0; 
                                        backdrop-filter: blur(10px);">
                                <span style="font-weight: 500;">• {skill}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                if recommendations.get('highlight_skills'):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                                border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.125rem;">
                            ✨ Skills to Highlight
                        </h4>
                        <div style="color: white; font-family: 'Inter', sans-serif;">
                    """, unsafe_allow_html=True)
                    for skill in recommendations['highlight_skills']:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; 
                                        padding: 0.75rem 1rem; margin: 0.5rem 0; 
                                        backdrop-filter: blur(10px);">
                                <span style="font-weight: 500;">• {skill}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                if recommendations.get('add_experience'):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                                border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.125rem;">
                            💼 Experience to Add
                        </h4>
                        <div style="color: white; font-family: 'Inter', sans-serif;">
                    """, unsafe_allow_html=True)
                    for exp in recommendations['add_experience']:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; 
                                        padding: 0.75rem 1rem; margin: 0.5rem 0; 
                                        backdrop-filter: blur(10px);">
                                <span style="font-weight: 500;">• {exp}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                if recommendations.get('specific_examples'):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                                border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.125rem;">
                            🎯 Specific Examples to Include
                        </h4>
                        <div style="color: white; font-family: 'Inter', sans-serif;">
                    """, unsafe_allow_html=True)
                    for example in recommendations['specific_examples']:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; 
                                        padding: 0.75rem 1rem; margin: 0.5rem 0; 
                                        backdrop-filter: blur(10px);">
                                <span style="font-weight: 500;">• {example}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                if not any(recommendations.values()):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                                border-radius: 12px; padding: 2rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
                        <h4 style="color: white; margin: 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.25rem;">
                            🎉 Excellent Match!
                        </h4>
                        <p style="color: white; margin: 0.5rem 0 0 0; font-family: 'Inter', sans-serif;">
                            No specific recommendations available. Your profile looks well-matched!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Only show analysis_tab4 if methodologies exist
        if has_methodologies:
            with analysis_tab4:
                st.markdown("#### AI-Generated Recommendations")
                recommendations = fit_analysis.get('recommendations', {})
                
                if recommendations.get('learn_skills'):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.125rem;">
                            📚 Skills to Learn
                        </h4>
                        <div style="color: white; font-family: 'Inter', sans-serif;">
                    """, unsafe_allow_html=True)
                    for skill in recommendations['learn_skills']:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; 
                                        padding: 0.75rem 1rem; margin: 0.5rem 0; 
                                        backdrop-filter: blur(10px);">
                                <span style="font-weight: 500;">• {skill}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                if recommendations.get('highlight_skills'):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                                border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.125rem;">
                            ✨ Skills to Highlight
                        </h4>
                        <div style="color: white; font-family: 'Inter', sans-serif;">
                    """, unsafe_allow_html=True)
                    for skill in recommendations['highlight_skills']:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; 
                                        padding: 0.75rem 1rem; margin: 0.5rem 0; 
                                        backdrop-filter: blur(10px);">
                                <span style="font-weight: 500;">• {skill}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                if recommendations.get('add_experience'):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                                border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.125rem;">
                            💼 Experience to Add
                        </h4>
                        <div style="color: white; font-family: 'Inter', sans-serif;">
                    """, unsafe_allow_html=True)
                    for exp in recommendations['add_experience']:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; 
                                        padding: 0.75rem 1rem; margin: 0.5rem 0; 
                                        backdrop-filter: blur(10px);">
                                <span style="font-weight: 500;">• {exp}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                if recommendations.get('specific_examples'):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                                border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h4 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.125rem;">
                            🎯 Specific Examples to Include
                        </h4>
                        <div style="color: white; font-family: 'Inter', sans-serif;">
                    """, unsafe_allow_html=True)
                    for example in recommendations['specific_examples']:
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.15); border-radius: 8px; 
                                        padding: 0.75rem 1rem; margin: 0.5rem 0; 
                                        backdrop-filter: blur(10px);">
                                <span style="font-weight: 500;">• {example}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                if not any(recommendations.values()):
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                                border-radius: 12px; padding: 2rem; margin: 1rem 0; 
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
                        <h4 style="color: white; margin: 0; font-family: 'Inter', sans-serif; 
                                   font-weight: 600; font-size: 1.25rem;">
                            🎉 Excellent Match!
                        </h4>
                        <p style="color: white; margin: 0.5rem 0 0 0; font-family: 'Inter', sans-serif;">
                            No specific recommendations available. Your profile looks well-matched!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Export analysis
        exp_c1, exp_c2 = st.columns([1,1])
        with exp_c1:
            md_bytes = generate_analysis_markdown(fit_analysis).encode('utf-8')
            st.download_button(
                label="Download Analysis (Markdown)",
                data=md_bytes,
                file_name="job_fit_analysis.md",
                mime="text/markdown",
                use_container_width=True
            )
        with exp_c2:
            # Generate analysis PDF on-demand when download is clicked
            analysis_pdf_key = 'analysis_pdf'
            if analysis_pdf_key not in st.session_state:
                # Show button to generate PDF
                if st.button("📥 Generate Analysis PDF", key="generate_analysis_pdf_btn", use_container_width=True):
                    with st.spinner("Generating PDF..."):
                        try:
                            pdf_path = generate_analysis_pdf(fit_analysis)
                            with open(pdf_path, "rb") as f:
                                pdf_data = f.read()
                            st.session_state[analysis_pdf_key] = pdf_data
                            # Clean up temporary file
                            try:
                                os.remove(pdf_path)
                            except:
                                pass
                            st.rerun()
                        except Exception as e:
                            show_error_message(f"Unable to generate PDF: {e}")
            else:
                # PDF is ready, show download button
                st.download_button(
                    label="📥 Download Analysis (PDF)",
                    data=st.session_state[analysis_pdf_key],
                    file_name="job_fit_analysis.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_analysis_pdf"
                )

        # Summary Statistics
        st.markdown('<h3 class="section-header">Summary Statistics</h3>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_matched = sum(len(fit_analysis['matched_details'][cat]) for cat in ['technical_skills', 'soft_skills', 'methodologies'])
            display_metric_card("Total Matches", str(total_matched), "Skills Found")
        with col2:
            total_missing = sum(len(fit_analysis['missing_details'][cat]) for cat in ['technical_skills', 'soft_skills', 'methodologies'])
            display_metric_card("Missing Skills", str(total_missing), "Need Attention")
        with col3:
            tech_matches = len(fit_analysis['matched_details']['technical_skills'])
            display_metric_card("Tech Matches", str(tech_matches), "Technical Skills")
        with col4:
            soft_matches = len(fit_analysis['matched_details']['soft_skills'])
            display_metric_card("Soft Matches", str(soft_matches), "Soft Skills")
    
    else:
        st.info("Please upload your resume and enter a job description in the Generate tab to see the analysis.")

with tab3:
    st.markdown('<h2 class="sub-header">Cover Letter History</h2>', unsafe_allow_html=True)
    
    # Get history
    history = get_cover_letter_history()
    
    if history:
        st.subheader("Recent Cover Letters")
        
        for record in history:
            with st.expander(f"{record[5] or 'Untitled'} - {record[1][:19]}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Tone:** {record[2]}")
                    st.write(f"**Language:** {record[3]}")
                    st.write(f"**Job Fit Score:** {record[4]}%")
                
                with col2:
                    # Generate PDF on-demand for history items
                    history_pdf_key = f'history_pdf_{record[0]}'
                    letter_data_for_download = get_cover_letter_by_id(record[0])
                    
                    if letter_data_for_download and letter_data_for_download.get('cover_letter'):
                        if history_pdf_key not in st.session_state:
                            # Show button to generate PDF
                            if st.button("📥 Generate PDF", key=f"generate_history_{record[0]}", use_container_width=True):
                                with st.spinner("Generating PDF..."):
                                    try:
                                        pdf_path = generate_pdf(
                                            letter_data_for_download['cover_letter'],
                                            filename=f"cover_letter_{record[0]}.pdf"
                                        )
                                        with open(pdf_path, "rb") as pdf_file:
                                            pdf_bytes = pdf_file.read()
                                        st.session_state[history_pdf_key] = pdf_bytes
                                        # Clean up temporary file
                                        try:
                                            os.remove(pdf_path)
                                        except:
                                            pass
                                        st.rerun()
                                    except Exception as e:
                                        show_error_message(f"Failed to generate PDF: {str(e)}")
                        else:
                            # PDF is ready, show download button
                            pdf_filename = f"cover_letter_{record[0]}.pdf"
                            st.download_button(
                                "📥 Download PDF",
                                data=st.session_state[history_pdf_key],
                                file_name=pdf_filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"download_history_{record[0]}"
                            )

                    if st.button("View", key=f"view_{record[0]}"):
                        letter_data = get_cover_letter_by_id(record[0])
                        if letter_data:
                            st.session_state['cover_letter'] = letter_data['cover_letter']
                            st.session_state['resume_text'] = letter_data['resume_text']
                            st.session_state['job_description'] = letter_data['job_description']
                            st.session_state['tone'] = letter_data['tone']
                            st.session_state['language'] = letter_data['language']
                            st.rerun()
    else:
        show_info_message("No cover letters saved yet. Generate and save your first cover letter!")

with tab4:
    st.markdown('<h2 class="sub-header">🎤 Interview Preparation Assistant</h2>', unsafe_allow_html=True)
    
    if st.session_state.get('resume_text') and st.session_state.get('job_description'):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="color: white; margin: 0 0 0.5rem 0; font-family: 'Inter', sans-serif; 
                       font-weight: 600; font-size: 1.125rem;">
                Prepare for Your Interview
            </h4>
            <p style="color: white; margin: 0; font-family: 'Inter', sans-serif; font-size: 0.95rem;">
                Get personalized interview questions, talking points from your resume, and insights on your strengths and areas to prepare.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Generate Interview Prep Guide", type="primary", use_container_width=True):
            if not api_key:
                show_error_message("Gemini API key required. Please add GEMINI_API_KEY to .env file.")
            else:
                with st.spinner("Generating interview preparation guide (this may take a minute)..."):
                    try:
                        prep_guide = generate_interview_prep(
                            st.session_state['resume_text'],
                            st.session_state['job_description'],
                            api_key,
                            'en'  # Can be made dynamic based on language setting
                        )
                        if prep_guide.get('success'):
                            st.session_state['interview_prep'] = prep_guide
                            show_success_message("Interview preparation guide generated successfully!")
                        else:
                            show_error_message(f"Failed to generate guide: {prep_guide.get('error', 'Unknown error')}")
                    except Exception as e:
                        show_error_message(f"Error generating interview prep: {str(e)}")
        
        # Display Interview Prep Guide
        if st.session_state.get('interview_prep'):
            prep = st.session_state['interview_prep']
            
            # Key Topics Overview
            if prep.get('key_topics'):
                st.markdown('<h3 style="margin-top: 2rem;">🎯 Key Topics to Master</h3>', unsafe_allow_html=True)
                topics_cols = st.columns(min(len(prep['key_topics']), 4))
                for i, topic in enumerate(prep['key_topics'][:8]):  # Limit to 8 topics
                    col_idx = i % len(topics_cols)
                    with topics_cols[col_idx]:
                        st.markdown(f"""
                        <div style="background: white; border-left: 4px solid #667eea; 
                                    border-radius: 4px; padding: 0.75rem; margin: 0.5rem 0; 
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <strong style="color: #212529;">{topic}</strong>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Interview Questions
            if prep.get('interview_questions'):
                st.markdown('<h3 style="margin-top: 2rem;">❓ Potential Interview Questions</h3>', unsafe_allow_html=True)
                
                # Group questions by category
                questions_by_category = {}
                for q in prep['interview_questions']:
                    category = q.get('category', 'General')
                    if category not in questions_by_category:
                        questions_by_category[category] = []
                    questions_by_category[category].append(q)
                
                # Display questions in expandable sections by category
                for category, questions in questions_by_category.items():
                    with st.expander(f"📂 {category} ({len(questions)} questions)", expanded=False):
                        for i, q in enumerate(questions, 1):
                            difficulty = q.get('difficulty', 'medium')
                            diff_color = {'easy': '#28a745', 'medium': '#ffc107', 'hard': '#dc3545'}.get(difficulty, '#6c757d')
                            
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 8px; padding: 1rem; margin: 1rem 0; 
                                        border-left: 4px solid {diff_color};">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                    <strong style="color: #212529; font-size: 1rem;">Q{i}: {q.get('question', 'N/A')}</strong>
                                    <span style="background: {diff_color}; color: white; padding: 0.25rem 0.75rem; 
                                                border-radius: 12px; font-size: 0.75rem; font-weight: 500;">
                                        {difficulty.upper()}
                                    </span>
                                </div>
                                <div style="color: #6c757d; font-size: 0.9rem; margin-top: 0.5rem;">
                                    <strong>Why asked:</strong> {q.get('why_asked', 'N/A')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Talking Points
            if prep.get('talking_points'):
                st.markdown('<h3 style="margin-top: 2rem;">💬 Key Talking Points</h3>', unsafe_allow_html=True)
                st.markdown("""
                <div style="background: #f8f9fa; border-left: 4px solid #667eea; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
                    <p style="margin: 0; color: #495057; font-size: 0.9rem;">
                        Use these talking points to highlight your relevant experience and skills during the interview.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                for i, point in enumerate(prep['talking_points'], 1):
                    st.markdown(f"""
                    <div style="background: white; border-radius: 8px; padding: 1.25rem; margin: 1rem 0; 
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: start; margin-bottom: 0.75rem;">
                            <span style="background: #667eea; color: white; border-radius: 50%; width: 24px; height: 24px; 
                                        display: flex; align-items: center; justify-content: center; font-weight: bold; 
                                        font-size: 0.9rem; margin-right: 0.75rem; flex-shrink: 0;">
                                {i}
                            </span>
                            <div style="flex: 1;">
                                <strong style="color: #212529; font-size: 1.1rem; display: block; margin-bottom: 0.5rem;">
                                    {point.get('topic', 'N/A')}
                                </strong>
                                <p style="color: #495057; margin: 0.5rem 0;">
                                    <strong>Point:</strong> {point.get('point', 'N/A')}
                                </p>
                                <p style="color: #6c757d; margin: 0.5rem 0; font-size: 0.9rem;">
                                    <strong>From your resume:</strong> {point.get('resume_evidence', 'N/A')}
                                </p>
                                <p style="color: #495057; margin: 0.5rem 0;">
                                    <strong>Why it matters:</strong> {point.get('job_relevance', 'N/A')}
                                </p>
                                {f'<p style="color: #28a745; margin: 0.5rem 0; font-style: italic;"><strong>Example to share:</strong> {point.get("example", "N/A")}</p>' if point.get('example') else ''}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Strengths and Areas to Prepare (Side by Side)
            strengths = prep.get('strengths', [])
            areas_to_prepare = prep.get('areas_to_prepare', [])
            
            if strengths or areas_to_prepare:
                st.markdown('<h3 style="margin-top: 2rem;">📊 Preparation Analysis</h3>', unsafe_allow_html=True)
                
                prep_col1, prep_col2 = st.columns(2)
                
                with prep_col1:
                    if strengths:
                        st.markdown('<h4 style="color: #28a745;">✅ Your Strengths</h4>', unsafe_allow_html=True)
                        for strength in strengths:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                                        border-radius: 8px; padding: 1rem; margin: 0.75rem 0; 
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <strong style="color: #155724; font-size: 1rem; display: block; margin-bottom: 0.5rem;">
                                    {strength.get('strength', 'N/A')}
                                </strong>
                                <p style="color: #155724; margin: 0.25rem 0; font-size: 0.9rem;">
                                    <strong>Evidence:</strong> {strength.get('evidence', 'N/A')}
                                </p>
                                <p style="color: #155724; margin: 0.25rem 0; font-size: 0.9rem;">
                                    <strong>Impact:</strong> {strength.get('impact', 'N/A')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                
                with prep_col2:
                    if areas_to_prepare:
                        st.markdown('<h4 style="color: #ffc107;">⚠️ Areas to Prepare</h4>', unsafe_allow_html=True)
                        for area in areas_to_prepare:
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
                                        border-radius: 8px; padding: 1rem; margin: 0.75rem 0; 
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <strong style="color: #856404; font-size: 1rem; display: block; margin-bottom: 0.5rem;">
                                    {area.get('area', 'N/A')}
                                </strong>
                                <p style="color: #856404; margin: 0.25rem 0; font-size: 0.9rem;">
                                    <strong>Why:</strong> {area.get('reason', 'N/A')}
                                </p>
                                <p style="color: #856404; margin: 0.25rem 0; font-size: 0.9rem;">
                                    <strong>Suggestion:</strong> {area.get('suggestion', 'N/A')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
    else:
        st.info("💡 Please upload your resume and enter a job description in the Generate tab to get started with interview preparation.")

