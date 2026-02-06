import streamlit as st
from .stats import render_token_usage
from .gastronomy import render_culinary_section
from .transport import render_mobility_section
from .attractions import render_daily_activities

def render_results(plan):
    st.success(f"Your trip plan to: **{plan['destination']}** is ready!")

    col1, col2, col3 = st.columns(3)
    col1.metric("Duration", f"{len(plan['days'])} days")
    col2.metric("Est. Cost", f"{plan['total_cost']} PLN")
    col3.metric("Activities", sum(len(d.get('activities', [])) for d in plan['days']))

    st.markdown("---")

    for day in plan['days']:
        render_daily_activities(day)

    render_culinary_section(plan)
    render_mobility_section(plan)

    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.markdown("### 🤔 Are you happy with this plan?")
    
    col_yes, col_no = st.columns(2)
    
    regenerate_data = None
    
    with col_yes:
        if st.button("Yes, I love it! 👍"):
            st.balloons()
            st.success("Great! Enjoy your trip!")

    with col_no:
        if st.checkbox("No, I want changes"):
            feedback = st.text_area("What should we improve?", placeholder="e.g. too many museums, I want more beach time...")
            if st.button("Regenerate with Feedback 🔄"):
                if feedback:
                    regenerate_data = feedback
                else:
                    st.warning("Please enter your feedback before regenerating.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    render_token_usage(plan)
    
    return regenerate_data
