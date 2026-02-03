import streamlit as st
import datetime

def render_header():
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>🌍 Intelligent Trip Planner</h1>
            <p style='color: #6b7280; font-size: 1.1rem;'>Your personal AI-created journey</p>
        </div>
    """, unsafe_allow_html=True)

def render_form():
    with st.container():
        st.markdown('<div class="stCard">', unsafe_allow_html=True)

        st.markdown("### 📍 Destination & Dates")
        col1, col2 = st.columns(2)
        with col1:
            destination = st.text_input("Where do you want to go?", placeholder="e.g. Rome, Barcelona")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            arr_date = st.date_input("Arrival Date", datetime.date.today() + datetime.timedelta(days=1))
            arr_time = st.time_input("Arrival Time", datetime.time(10, 0))
        with col_d2:
            dep_date = st.date_input("Departure Date", datetime.date.today() + datetime.timedelta(days=4))
            dep_time = st.time_input("Departure Time", datetime.time(18, 0))

        st.markdown("### 🧑‍🤝‍🧑Travellers & Budget")
        col3, col4 = st.columns(2)
        with col3:
            guests = st.number_input("Guests", min_value=1, value=2)
        with col4:
            budget = st.number_input("Budget per person (PLN)", min_value=100, value=2000, step=100)

        st.markdown("### 🎨 Preferences")
        
        pace = st.select_slider("Pace", options=["Relaxed", "Moderate", "Fast (Intense)"], value="Moderate")
        
        transport = st.multiselect(
            "Preferred Transport",
            ["Walking", "Public Transport", "Taxi/Uber", "Car Rental", "Bike"],
            default=["Walking", "Public Transport"]
        )
        
        accommodation = st.text_input("Accommodation (Optional)", placeholder="e.g. Hotel Marriott or address")
        
        extra_req = st.text_area("Extra Requirements", placeholder="e.g. vegetarian food, interested in art...")

        st.markdown("---")
        generate = st.button("Generate Trip Plan 🚀")
        st.markdown('</div>', unsafe_allow_html=True)

    form_data = {
        "destination": destination,
        "arrival": f"{arr_date} {arr_time}",
        "departure": f"{dep_date} {dep_time}",
        "guests": guests,
        "budget": budget,
        "pace": pace,
        "transport": transport,
        "accommodation": accommodation,
        "extra_req": extra_req
    }
    
    return generate, form_data

def render_loading():
    with st.container():
        st.markdown('<div class="stCard" style="text-align: center; padding: 4rem;">', unsafe_allow_html=True)
        with st.spinner("AI is analyzing maps, checking connections, and finding the best attractions... 🕵️‍♂️"):
            pass
        st.info("Creating your perfect plan. Please wait...")
        st.markdown('</div>', unsafe_allow_html=True)

def render_results(plan):
    st.success(f"Your trip plan to: **{plan['destination']}** is ready!")

    col1, col2, col3 = st.columns(3)
    col1.metric("Duration", f"{len(plan['days'])} days")
    col2.metric("Est. Cost", f"{plan['total_cost']} PLN")
    col3.metric("Activities", sum(len(d.get('activities', [])) for d in plan['days']))

    st.markdown("---")

    for day in plan['days']:
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
                    
                    <h5 style="margin-top: 20px;">🍽️ Gastronomy</h5>
            """, unsafe_allow_html=True)
            
            meals = day.get('meals', {})
            if meals:
                 st.markdown(f"<b>🍳 Breakfast:</b> {meals.get('breakfast', 'N/A')}<br>", unsafe_allow_html=True)
                 st.markdown(f"<b>🥗 Lunch:</b> {meals.get('lunch', 'N/A')}<br>", unsafe_allow_html=True)
                 st.markdown(f"<b>🍰 Snack:</b> {meals.get('snack', 'N/A')}<br>", unsafe_allow_html=True)
                 st.markdown(f"<b>🍷 Dinner:</b> {meals.get('dinner', 'N/A')}", unsafe_allow_html=True)
            else:
                 st.markdown("<i>No specific meal recommendations for today.</i>", unsafe_allow_html=True)

            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)

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
    
    return regenerate_data
