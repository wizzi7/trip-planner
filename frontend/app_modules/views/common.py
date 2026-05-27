import streamlit as st

def render_header():
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>🌍 Intelligent Trip Planner tes</h1>
            <p style='color: #6b7280; font-size: 1.1rem;'>Your personal AI-created journey</p>
        </div>
    """, unsafe_allow_html=True)

def render_loading():
    with st.container():
        st.markdown('<div class="stCard" style="text-align: center; padding: 4rem;">', unsafe_allow_html=True)
        with st.spinner("AI is analyzing maps, checking connections, and finding the best attractions... 🕵️‍♂️"):
            pass
        st.info("Creating your perfect plan. Please wait...")
        st.markdown('</div>', unsafe_allow_html=True)
