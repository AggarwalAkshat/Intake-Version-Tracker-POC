# core/styles.py
from typing import Optional
import streamlit as st

THEMES = {
    "Dark": {
        "bg": "#050816",
        "bg_alt": "#0b1020",
        "sidebar_bg": "#050816",
        "text": "#f9fafb",
        "muted": "#9ca3af",
        "primary": "#00e0ff",
        "accent": "#6366f1",
        "border": "#1f2937",
        "chip_bg": "#111827",
    },
    "Light": {
        "bg": "#f9fafb",          # main background
        "bg_alt": "#ffffff",      # card background
        "sidebar_bg": "#e5e7eb",  # sidebar
        "text": "#020617",        # near-black
        "muted": "#6b7280",
        "primary": "#0ea5e9",     # bright cyan
        "accent": "#4f46e5",      # indigo
        "border": "#d4d4d8",
        "chip_bg": "#e5e7eb",
    },
}

def apply_theme(theme_name: str):
    theme = THEMES.get(theme_name, THEMES["Dark"])
    bg = theme["bg"]
    bg_alt = theme["bg_alt"]
    sidebar_bg = theme["sidebar_bg"]
    text = theme["text"]
    muted = theme["muted"]
    primary = theme["primary"]
    accent = theme["accent"]
    border = theme["border"]
    chip_bg = theme["chip_bg"]

    is_light = theme_name == "Light"

    # Background style differs by theme
    if is_light:
        app_bg_css = f"background: {bg};"
        sidebar_bg_css = f"background: {sidebar_bg};"
    else:
        app_bg_css = (
            f"background: radial-gradient(circle at 0% 0%, {primary}11 0, {bg} 45%, {bg} 100%);"
        )
        sidebar_bg_css = (
            f"background: linear-gradient(180deg, {sidebar_bg} 0%, {bg} 60%, {bg} 100%);"
        )

    # Extra tweaks only for light mode
    light_extras = ""
    if is_light:
        light_extras = f"""
        [data-testid="stAppViewContainer"] {{
            box-shadow: inset 0 0 0 1px {border};
        }}

        .card {{
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
        }}

        .stTable thead tr th {{
            background: {bg_alt} !important;
        }}
        """

    # BUTTON STYLES – different for dark vs light
    if is_light:
        button_css = f"""
        .stButton > button {{
            background: {primary} !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
            font-weight: 500 !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.20);
            opacity: 1 !important;
        }}

        .stButton > button:disabled {{
            background: #e5e7eb !important;
            color: #9ca3af !important;
            border: 1px solid #d4d4d8 !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }}
        """
    else:
        button_css = f"""
        .stButton > button {{
            background: linear-gradient(90deg, {primary}, {accent}) !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
            font-weight: 500 !important;
            opacity: 1 !important;
        }}

        .stButton > button:disabled {{
            background: #020617 !important;
            color: #6b7280 !important;
            border: 1px solid {border} !important;
            opacity: 1 !important;
        }}
        """

    st.markdown(
        f"""
        <style>
        /* App background + global text */
        [data-testid="stAppViewContainer"] {{
            {app_bg_css}
            color: {text};
        }}

        [data-testid="stSidebar"] {{
            {sidebar_bg_css}
            border-right: 1px solid {border};
        }}

        html, body, [data-testid="stAppViewContainer"] * {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            -webkit-font-smoothing: antialiased;
            color: {text};
        }}

        /* Titles and subtitles */
        .page-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1rem;
            border-radius: 0.9rem;
            background: linear-gradient(90deg, {primary}22, transparent);
            border: 1px solid {border};
            margin-bottom: 0.25rem;
        }}

        .page-header-icon {{
            font-size: 1.4rem;
        }}

        .page-header-text {{
            font-size: 1.15rem;
            font-weight: 600;
        }}

        .page-subtitle {{
            margin-top: 0;
            margin-bottom: 0.75rem;
            color: {muted};
            font-size: 0.9rem;
        }}

        /* Chips / pills */
        .chip {{
            display: inline-flex;
            align-items: center;
            padding: 0.1rem 0.55rem;
            border-radius: 999px;
            background: {chip_bg};
            border: 1px solid {border};
            font-size: 0.72rem;
            color: {muted};
            gap: 0.3rem;
        }}

        .chip-dot {{
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: {primary};
        }}

        /* Cards */
        .card {{
            border-radius: 0.9rem;
            border: 1px solid {border};
            padding: 0.85rem 1rem;
            background: {bg_alt};
            margin-bottom: 0.75rem;
        }}

        /* Tables */
        .stTable thead tr th {{
            background: {chip_bg} !important;
            color: {muted} !important;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .stTable tbody tr td {{
            font-size: 0.85rem;
        }}

        /* Sidebar text */
        [data-testid="stSidebar"] .stMarkdown p {{
            font-size: 0.85rem;
            color: {muted};
        }}

        /* Inputs + text areas */
        .stTextInput > div > div > input,
        .stTextArea textarea {{
            background-color: {bg_alt} !important;
            color: {text} !important;
            border-radius: 0.6rem !important;
            border: 1px solid {border} !important;
        }}

        /* Selectbox / multiselect */
        div[data-baseweb="select"] > div {{
            background-color: {bg_alt} !important;
            color: {text} !important;
            border-radius: 0.6rem !important;
            border: 1px solid {border} !important;
        }}

        /* Radio + checkbox labels */
        label, .stRadio, .stCheckbox {{
            color: {text} !important;
        }}

        /* Buttons (from theme-specific CSS) */
        {button_css}

        {light_extras}
        </style>
        """,
        unsafe_allow_html=True,
    )




def page_header(icon: str, title: str, subtitle: Optional[str] = None):
    st.markdown(
        f"""
        <div class="page-header">
            <span class="page-header-icon">{icon}</span>
            <span class="page-header-text">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(f"<p class='page-subtitle'>{subtitle}</p>", unsafe_allow_html=True)
