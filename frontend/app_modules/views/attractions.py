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
                <ul style="list-style-type: none; padding-left: 0;">
        """, unsafe_allow_html=True)

        for act in day.get('activities', []):
            if isinstance(act, str):
                st.markdown(f"<li>{act}</li>", unsafe_allow_html=True)
            else:
                if hasattr(act, 'model_dump'):
                    act = act.model_dump()
                elif hasattr(act, '__dict__'):
                     act = act.__dict__

                if isinstance(act, dict):
                    name = act.get('name', 'Unknown')
                    desc = act.get('description', '')
                    duration = act.get('duration', '')
                    
                    st.markdown(
                        f"""
                        <li style="margin-bottom: 10px; border-left: 3px solid #FF4B4B; padding-left: 10px;">
                            <strong>{name}</strong> <span style="color: gray;">({duration})</span><br>
                            <span style="font-size: 0.9em;">{desc}</span>
                        </li>
                        """, 
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<li>{str(act)}</li>", unsafe_allow_html=True)
        
        st.markdown("""
                </ul>
        """, unsafe_allow_html=True)

        st.markdown("""
                </div>
            </div>
        """, unsafe_allow_html=True)
