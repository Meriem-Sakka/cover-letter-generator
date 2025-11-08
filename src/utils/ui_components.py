"""
UI Component Helpers for Modern Interface
Provides reusable components for better UX
"""

import streamlit as st
from typing import Optional

def create_feature_card(icon: str, title: str, description: str, tooltip: Optional[str] = None):
    """Create a modern feature card with icon, title, and description"""
    tooltip_attr = f'data-tooltip="{tooltip}"' if tooltip else ''
    return f"""
    <div class="feature-card" {tooltip_attr}>
        <div style="display: flex; align-items: start; gap: 1rem;">
            <div style="font-size: 2rem; line-height: 1;">{icon}</div>
            <div style="flex: 1;">
                <h3 style="margin: 0 0 0.5rem 0; font-size: 1.25rem; font-weight: 600; color: var(--gray-900);">
                    {title}
                </h3>
                <p style="margin: 0; color: var(--gray-600); font-size: 0.95rem; line-height: 1.6;">
                    {description}
                </p>
            </div>
        </div>
    </div>
    """

def create_info_banner(icon: str, message: str, type: str = "info"):
    """Create an informational banner with icon and message"""
    colors = {
        "info": {"bg": "var(--info-light)", "border": "var(--info)", "text": "var(--gray-800)"},
        "success": {"bg": "var(--success-light)", "border": "var(--success)", "text": "var(--gray-800)"},
        "warning": {"bg": "var(--warning-light)", "border": "var(--warning)", "text": "var(--gray-800)"},
        "error": {"bg": "var(--error-light)", "border": "var(--error)", "text": "var(--gray-800)"}
    }
    color = colors.get(type, colors["info"])
    
    return f"""
    <div style="background: {color['bg']}; border-left: 4px solid {color['border']}; 
                border-radius: var(--radius); padding: var(--space-4); margin: var(--space-4) 0; 
                box-shadow: var(--shadow-xs);">
        <div style="display: flex; align-items: center; gap: var(--space-3);">
            <span style="font-size: 1.5rem;">{icon}</span>
            <p style="margin: 0; color: {color['text']}; font-size: 0.95rem; line-height: 1.6;">
                {message}
            </p>
        </div>
    </div>
    """

def create_metric_display(label: str, value: str, subtitle: Optional[str] = None, color: Optional[str] = None):
    """Create a metric display card"""
    value_color = color if color else "var(--gray-900)"
    return f"""
    <div class="metric-card">
        <div style="font-size: 0.875rem; font-weight: 500; color: var(--gray-600); 
                    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: var(--space-2);">
            {label}
        </div>
        <div style="font-size: 2.5rem; font-weight: 700; color: {value_color}; 
                    letter-spacing: -0.02em; line-height: 1; margin: var(--space-2) 0;">
            {value}
        </div>
        {f'<div style="font-size: 0.875rem; color: var(--gray-500); margin-top: var(--space-2);">{subtitle}</div>' if subtitle else ''}
    </div>
    """

def create_section_header(icon: str, title: str, description: Optional[str] = None):
    """Create a section header with icon and optional description"""
    desc_html = f'<p style="margin: 0.5rem 0 0 0; color: var(--gray-600); font-size: 0.95rem;">{description}</p>' if description else ''
    return f"""
    <div style="margin: var(--space-8) 0 var(--space-6) 0;">
        <h2 class="section-header">
            <span style="font-size: 1.5rem; margin-right: var(--space-2);">{icon}</span>
            {title}
        </h2>
        {desc_html}
    </div>
    """

def create_progress_indicator(current: int, total: int, label: str = ""):
    """Create a progress indicator"""
    percentage = (current / total) * 100 if total > 0 else 0
    return f"""
    <div style="margin: var(--space-4) 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
            <span style="font-size: 0.875rem; font-weight: 500; color: var(--gray-700);">{label}</span>
            <span style="font-size: 0.875rem; font-weight: 600; color: var(--primary);">{current}/{total}</span>
        </div>
        <div style="background: var(--gray-200); border-radius: var(--radius); height: 8px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%); 
                        height: 100%; width: {percentage}%; transition: width 0.3s ease; border-radius: var(--radius);">
            </div>
        </div>
    </div>
    """

def create_tooltip(text: str, tooltip: str):
    """Create an element with tooltip"""
    return f"""
    <span class="tooltip" data-tooltip="{tooltip}" style="cursor: help; border-bottom: 1px dotted var(--gray-400);">
        {text}
    </span>
    """

def create_status_badge(text: str, status: str = "info"):
    """Create a status badge"""
    styles = {
        "success": "badge-success",
        "warning": "badge-warning",
        "error": "badge-error",
        "info": "badge-info"
    }
    badge_class = styles.get(status, "badge-info")
    return f'<span class="badge {badge_class}">{text}</span>'


