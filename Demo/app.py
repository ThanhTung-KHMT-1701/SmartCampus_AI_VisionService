"""
SmartCampus AI Vision - Main Entry Point
Dynamically discovers and displays pages from the `pages/` directory.
"""
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Define the pages directory
PAGES_DIR = Path(__file__).parent / "pages"

# Dynamically discover all .py files in pages/, sorted by filename
def discover_pages():
    pages = []
    if PAGES_DIR.exists():
        for f in sorted(PAGES_DIR.glob("*.py")):
            # Extract display name from filename: "1_Dashboard.py" -> "Dashboard"
            name = f.stem.split("_", 1)[-1].replace("_", " ")
            pages.append(st.Page(f, title=name, icon="📄"))
    return pages

st.set_page_config(
    page_title="SmartCampus AI Vision",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #E3F2FD; }
    /* Hiển thị đầy đủ text, không cắt dấu ... */
    [data-testid="stDataFrame"] [data-testid="stMarkdownContainer"] *,
    .element-container p,
    .stDataFrame td, .stDataFrame th {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
</style>
""", unsafe_allow_html=True)

# Build navigation only from discovered pages (entry page hidden)
pages = discover_pages()
pg = st.navigation(pages)
pg.run()
