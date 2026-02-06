import streamlit as st

def render_daily_activities(day):
    with st.expander(f"Day {day['day']}: {day.get('theme', 'Sightseeing')}", expanded=True):
        st.markdown(f"""
            <div class="trip-day-card">
                <h4>📅 {day['date']}</h4>
                <p><i>{day.get('summary', '')}</i></p>
        """, unsafe_allow_html=True)

        st.markdown("""
                <h5 style="padding-bottom: 5px;">🏛️ Attractions</h5>
                <ul style="margin-bottom: 0;">
        """, unsafe_allow_html=True)

        for act in day.get('activities', []):
            st.markdown(f"<li>{act}</li>", unsafe_allow_html=True)
        
        st.markdown("""
                </ul>

        """, unsafe_allow_html=True)

        st.markdown("""
                </div>
            </div>
        """, unsafe_allow_html=True)
