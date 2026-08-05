from pathlib import Path
import streamlit as st


def load_css(css_file="assets/style.css"):
    """
    Load external CSS into Streamlit.
    """

    css_path = Path(css_file)

    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True,
            )
    else:
        st.warning(f"CSS file not found: {css_file}")