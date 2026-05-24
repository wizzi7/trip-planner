import streamlit as st
from .stats import render_token_usage
from .gastronomy import render_culinary_section
from .transport import render_mobility_section
from .attractions import render_daily_activities
from .city_overview import render_city_header, render_city_history_culture

def render_results(plan):
    st.success(f"Your trip plan to: **{plan['destination']}** is ready!")

    col1, col2, col3 = st.columns(3)
    col1.metric("Duration", f"{len(plan['days'])} days")
    col2.metric("Est. Cost", f"{plan['total_cost']} PLN")
    col3.metric("Activities", sum(len(d.get('activities', [])) for d in plan['days']))

    st.markdown("---")
    if plan.get('city_overview'):
        render_city_header(plan['city_overview'])

    for i in range(0, len(plan['days']), 2):
        cols = st.columns(2)
        with cols[0]:
            render_daily_activities(plan['days'][i])
        if i + 1 < len(plan['days']):
            with cols[1]:
                render_daily_activities(plan['days'][i + 1])

    render_culinary_section(plan)
    render_mobility_section(plan)

    if plan.get('city_overview'):
        render_city_history_culture(plan['city_overview'])

    st.markdown('<div class="stCard">', unsafe_allow_html=True)

    header_col, regen_col = st.columns([4, 1])
    with header_col:
        st.markdown("### 🤔 Are you happy with this plan?")
    with regen_col:
        regenerate_clicked = st.button("🔁 Regenerate", help="Generate a new plan using the same inputs", use_container_width=True)

    regenerate_data = None

    if regenerate_clicked:
        regenerate_data = "__regenerate__"

    col_yes, col_no = st.columns(2)

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
