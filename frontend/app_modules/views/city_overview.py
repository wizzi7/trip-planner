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

    st.markdown("---")

    with st.expander("📜 History & Culture", expanded=True):
        history_text = overview.get('history_summary', '')
        culture_text = overview.get('cultural_identity', '')
        st.markdown(f"""
            <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3>📜 History & Culture</h3>
                <p style="margin-bottom: 10px;"><strong>History:</strong> {history_text}</p>
                <p style="margin-bottom: 0;"><strong>Culture:</strong> {culture_text}</p>
            </div>
        """, unsafe_allow_html=True)
