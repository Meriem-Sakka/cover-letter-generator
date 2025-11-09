"""
Modern UI Styles - SaaS-inspired design system
Provides enhanced styling for a professional, modern interface
"""

MODERN_CSS = """
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Design System Variables */
:root {
    /* Primary Colors */
    --primary: #6366f1;
    --primary-hover: #4f46e5;
    --primary-light: #818cf8;
    --primary-bg: #eef2ff;
    
    /* Neutral Palette */
    --gray-50: #fafafa;
    --gray-100: #f5f5f5;
    --gray-200: #e5e5e5;
    --gray-300: #d4d4d4;
    --gray-400: #a3a3a3;
    --gray-500: #737373;
    --gray-600: #525252;
    --gray-700: #404040;
    --gray-800: #262626;
    --gray-900: #171717;
    
    /* Semantic Colors */
    --success: #10b981;
    --success-light: #d1fae5;
    --warning: #f59e0b;
    --warning-light: #fef3c7;
    --error: #ef4444;
    --error-light: #fee2e2;
    --info: #3b82f6;
    --info-light: #dbeafe;
    
    /* UI */
    --white: #ffffff;
    --radius: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    
    /* Shadows */
    --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    
    /* Spacing */
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-5: 1.25rem;
    --space-6: 1.5rem;
    --space-8: 2rem;
    --space-10: 2.5rem;
    --space-12: 3rem;
    
    /* Transitions */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Additional Legacy Variable Support */
:root {
    --primary-color: var(--primary);
    --primary-dark: var(--primary-hover);
    --border-radius: var(--radius);
    --border-radius-lg: var(--radius-lg);
}

/* Base Styles */
.stApp {
    background: var(--white);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    min-height: 100vh;
}

.main .block-container {
    padding-top: var(--space-10);
    padding-bottom: var(--space-12);
    padding-left: var(--space-10);
    padding-right: var(--space-10);
    max-width: 1400px;
    background: transparent;
}

/* Hide Streamlit Branding - but keep header for sidebar toggle */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
/* Keep header visible so sidebar toggle button is accessible */

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.2;
    color: var(--gray-900);
}

/* Modern Header */
.main-header {
    font-size: 3.5rem;
    font-weight: 800;
    text-align: center;
    margin-bottom: var(--space-6);
    background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 50%, var(--primary-light) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.04em;
    text-shadow: 0 4px 20px rgba(99, 102, 241, 0.1);
    animation: fadeInDown 0.6s ease-out;
}

.sub-header {
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--gray-900);
    margin: var(--space-8) 0 var(--space-6) 0;
    display: flex;
    align-items: center;
    gap: var(--space-3);
}

.section-header {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--gray-800);
    margin: var(--space-8) 0 var(--space-4) 0;
    display: flex;
    align-items: center;
    gap: var(--space-2);
}

/* Modern Cards */
.modern-card {
    background: var(--white);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-base);
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
}

.modern-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
    transform: scaleX(0);
    transition: transform var(--transition-base);
}

.modern-card:hover::before {
    transform: scaleX(1);
}

.modern-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-4px);
    border-color: var(--primary-light);
}

/* Enhanced Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: var(--space-2);
    background: transparent;
    padding: var(--space-2);
    border-bottom: 2px solid var(--gray-200);
    margin-bottom: var(--space-6);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: var(--radius) var(--radius) 0 0;
    padding: var(--space-3) var(--space-6);
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 0.95rem;
    color: var(--gray-600);
    border: none;
    border-bottom: 2px solid transparent;
    transition: all var(--transition-base);
    margin-right: var(--space-2);
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--primary);
    background: var(--primary-bg);
}

.stTabs [aria-selected="true"] {
    color: var(--primary);
    background: transparent;
    border-bottom-color: var(--primary);
    font-weight: 600;
}

/* Enhanced Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
    color: var(--white);
    border: none;
    border-radius: var(--radius);
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.875rem;
    padding: var(--space-3) var(--space-6);
    transition: all var(--transition-base);
    box-shadow: var(--shadow-sm);
    height: auto;
    min-height: 2.5rem;
    letter-spacing: 0.01em;
    position: relative;
    overflow: hidden;
    white-space: nowrap;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.stButton > button:hover::before {
    left: 100%;
}

.stButton > button:hover {
    background: linear-gradient(135deg, var(--primary-hover) 0%, var(--primary) 100%);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.stButton > button:active {
    transform: translateY(0);
    box-shadow: var(--shadow-sm);
}

/* Primary Button */
button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%) !important;
    box-shadow: var(--shadow-lg) !important;
    font-weight: 600 !important;
}

/* Input Fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
    border-radius: var(--radius);
    border: 1.5px solid var(--gray-300);
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    background: var(--white);
    padding: var(--space-3) var(--space-4);
    transition: all var(--transition-base);
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    outline: none;
}

/* File Uploader */
.uploadedFile {
    background: var(--white);
    border: 1.5px solid var(--gray-200);
    border-radius: var(--radius);
    padding: var(--space-4);
    margin: var(--space-4) 0;
    box-shadow: var(--shadow-xs);
}

/* Progress Bars */
.stProgress > div > div > div {
    background: var(--primary);
    border-radius: var(--radius);
}

/* Spinner */
.stSpinner > div {
    border-color: var(--primary) transparent transparent transparent;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    color: var(--gray-800);
    padding: var(--space-4);
    background: var(--white);
    border-radius: var(--radius);
    border: 1px solid var(--gray-200);
}

.streamlit-expanderContent {
    background: var(--gray-50);
    padding: var(--space-4);
    margin-top: var(--space-2);
    border-radius: var(--radius);
}

/* Metric Cards */
.metric-card {
    background: var(--white);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    text-align: center;
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-base);
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
}

.metric-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

/* Loading Animation */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.loading-shimmer {
    animation: shimmer 2s infinite;
    background: linear-gradient(to right, var(--gray-100) 0%, var(--gray-200) 50%, var(--gray-100) 100%);
    background-size: 1000px 100%;
}

/* Tooltip Styles */
.tooltip {
    position: relative;
    cursor: help;
}

.tooltip:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    padding: var(--space-2) var(--space-3);
    background: var(--gray-900);
    color: var(--white);
    border-radius: var(--radius);
    font-size: 0.875rem;
    white-space: nowrap;
    z-index: 1000;
    margin-bottom: var(--space-2);
    box-shadow: var(--shadow-lg);
}

/* Badge/Pill */
.badge {
    display: inline-flex;
    align-items: center;
    padding: var(--space-1) var(--space-3);
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
}

.badge-success {
    background: var(--success-light);
    color: var(--success);
}

.badge-warning {
    background: var(--warning-light);
    color: var(--warning);
}

.badge-error {
    background: var(--error-light);
    color: var(--error);
}

.badge-info {
    background: var(--info-light);
    color: var(--info);
}

/* Responsive Design */
@media (max-width: 768px) {
    .main .block-container {
        padding-left: var(--space-4);
        padding-right: var(--space-4);
    }
    
    .main-header {
        font-size: 2rem;
    }
    
    .sub-header {
        font-size: 1.5rem;
    }
    
    .section-header {
        font-size: 1.125rem;
    }
    
    .metric-card {
        padding: var(--space-4);
    }
}

/* Smooth Scrolling */
html {
    scroll-behavior: smooth;
}

/* Selection */
::selection {
    background: var(--primary-bg);
    color: var(--primary);
}

/* Animations */
@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Smooth fade-in for content */
.stMarkdown, .stTextArea, .stTextInput {
    animation: fadeIn 0.4s ease-out;
}

/* Enhanced Text Areas */
.stTextArea > div > div > textarea {
    border: 2px solid var(--gray-300);
    border-radius: var(--radius-lg);
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    line-height: 1.6;
    padding: var(--space-4);
    transition: all var(--transition-base);
    background: var(--white);
}

.stTextArea > div > div > textarea:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
    outline: none;
}

/* Enhanced File Uploader */
.uploadedFile {
    background: linear-gradient(135deg, var(--white) 0%, var(--gray-50) 100%);
    border: 2px dashed var(--primary-light);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    margin: var(--space-4) 0;
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-base);
}

.uploadedFile:hover {
    border-color: var(--primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

/* Glass morphism effect for cards */
.glass-card {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}

/* Gradient backgrounds */
.gradient-bg-primary {
    background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
}

.gradient-bg-success {
    background: linear-gradient(135deg, var(--success) 0%, #059669 100%);
}

.gradient-bg-warning {
    background: linear-gradient(135deg, var(--warning) 0%, #d97706 100%);
}

/* Enhanced tabs with better visual feedback */
.stTabs [data-baseweb="tab"] {
    position: relative;
}

.stTabs [data-baseweb="tab"]::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--primary);
    transform: scaleX(0);
    transition: transform var(--transition-base);
}

.stTabs [aria-selected="true"]::after {
    transform: scaleX(1);
}

/* Improved spacing for sections */
section[data-testid="stVerticalBlock"] > div {
    gap: var(--space-6);
}

/* Better focus states */
*:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
    border-radius: var(--radius);
}
</style>
"""

