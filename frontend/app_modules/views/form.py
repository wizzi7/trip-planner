import streamlit as st
import datetime

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
        
        interests = st.multiselect(
            "Preferred Attraction Types",
            [
                "Monuments", 
                "Museums / Art", 
                "Outdoor Activities", 
                "Amusement Parks", 
                "Nature / Landscapes", 
                "Gastronomy", 
                "Nightlife", 
                "Shopping", 
                "Relaxation / Spa"
            ],
            default=[]
        )
        
        other_interest = st.checkbox("Other")
        if other_interest:
            other_text = st.text_input("Enter other interests", placeholder="e.g. Street Art, Architecture")
            if other_text:
                interests.append(other_text)

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
        "interests": interests,
        "pace": pace,
        "transport": transport,
        "accommodation": accommodation,
        "extra_req": extra_req
    }
    
    return generate, form_data
