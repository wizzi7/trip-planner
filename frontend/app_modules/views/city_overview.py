import streamlit as st

def render_city_header(overview):
    if not overview:
        return

    st.markdown("""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="margin-top: 0;">🏙️ City Overview: {}</h2>
            <p style="font-size: 1.1em; font-weight: 500;">{}</p>
        </div>
    """.format(overview.get('city_name', 'Unknown'), overview.get('short_description', '')), unsafe_allow_html=True)

def render_city_history_culture(overview):
    if not overview:
        return

    with st.expander("📜 History & Culture", expanded=True):
        st.markdown(f"## 📜 History & Culture")
        history_text = overview.get('history_summary', '')
        culture_text = overview.get('cultural_identity', '')
        st.markdown(f"**History:** {history_text}")
        st.markdown(f"**Culture:** {culture_text}")
