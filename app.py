import streamlit as st

from src.config.defaults import APP_DESCRIPTION, APP_NAME, BASE_CURRENCY
from src.utils.money import format_currency


def render_header() -> None:
    """Render the main headers and introductory copy."""
    st.title(APP_NAME)
    st.caption(APP_DESCRIPTION)


def render_metrics() -> None:
    """Show placeholder metrics to prove the scaffold runs end-to-end."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cash", format_currency(10_000, BASE_CURRENCY))
    with col2:
        st.metric("Exposure", format_currency(25_000, BASE_CURRENCY))
    with col3:
        st.metric("Leverage", "1.5x")


def main() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon=":bar_chart:")
    st.sidebar.title(APP_NAME)
    st.sidebar.caption(APP_DESCRIPTION)

    render_header()
    render_metrics()
    st.info("Risk analytics coming soon. This is the initial scaffold.")


if __name__ == "__main__":
    main()
