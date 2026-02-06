import streamlit as st
import datetime

def render_header():
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>🌍 Intelligent Trip Planner</h1>
            <p style='color: #6b7280; font-size: 1.1rem;'>Your personal AI-created journey</p>
        </div>
    """, unsafe_allow_html=True)
    
SHOW_TOKEN_USAGE = True

def render_token_usage(plan):
    if not SHOW_TOKEN_USAGE:
        return
        
    usage_stats = plan.get('usage_stats', {})
    if not usage_stats:
        return

    st.markdown("---")
    
    with st.expander("📊 Token Usage Stats (Debug)", expanded=True):
        total_input = 0
        total_output = 0
        total_cost = 0.0
        
        data = []
        for agent, stats in usage_stats.items():
            if isinstance(stats, dict):
                inp = stats.get('input_tokens', 0)
                out = stats.get('output_tokens', 0)
                cost = stats.get('cost', 0.0)
                model = stats.get('model', 'N/A')
            else:
                 inp = getattr(stats, 'input_tokens', 0)
                 out = getattr(stats, 'output_tokens', 0)
                 cost = getattr(stats, 'cost', 0.0)
                 model = getattr(stats, 'model', 'N/A')
                 
            total_input += inp
            total_output += out
            total_cost += cost
            
            data.append({
                "Agent": agent,
                "Model": model,
                "Input Tokens": inp,
                "Output Tokens": out,
                "Cost ($)": f"${cost:.4f}"
            })
            
        st.table(data)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Input", total_input)
        col2.metric("Total Output", total_output)
        col3.metric("Total Tokens", total_input + total_output)
        col4.metric("Total Cost", f"${total_cost:.4f}")


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

def render_loading():
    with st.container():
        st.markdown('<div class="stCard" style="text-align: center; padding: 4rem;">', unsafe_allow_html=True)
        with st.spinner("AI is analyzing maps, checking connections, and finding the best attractions... 🕵️‍♂️"):
            pass
        st.info("Creating your perfect plan. Please wait...")
        st.markdown('</div>', unsafe_allow_html=True)

def render_culinary_section(plan):
    culinary = plan.get('culinary_section')
    if not culinary:
        return

    st.markdown("---")
    
    with st.expander("Culinary Inspirations", expanded=True):
        st.markdown(f"## Culinary Inspirations")
        st.markdown("### 🥘 Regional Cuisine – What to Try")
        cols = st.columns(2)

        main_dishes = culinary.get('main_dishes', [])
        if main_dishes:
            with cols[0]:
                st.markdown("#### 🍲 Main Dishes")
                for item in main_dishes:
                    st.markdown(f"""
                    **{item.get('name', 'Dish Name')}**  
                    {item.get('description', '')}  
                    💸 {item.get('price_range', '')}
                    """)

        with cols[1]:
            soups = culinary.get('soups', [])
            if soups:
                st.markdown("#### 🥣 Soups")
                for item in soups[:2]:
                    st.markdown(f"""
                    **{item.get('name', 'Soup Name')}**  
                    {item.get('description', '')}  
                    💸 {item.get('price_range', '')}
                    """)

            drinks = culinary.get('drinks', [])
            if drinks:
                st.markdown("#### 🍷 Drinks")
                for item in drinks[:2]:
                    st.markdown(f"""
                    **{item.get('name', 'Drink Name')}**  
                    {item.get('description', '')}  
                    💸 {item.get('price_range', '')}
                    """)

            desserts = culinary.get('desserts', [])
            if desserts:
                st.markdown("#### 🍰 Desserts")
                for item in desserts[:2]:
                    st.markdown(f"""
                    **{item.get('name', 'Dessert Name')}**  
                    {item.get('description', '')}  
                    💸 {item.get('price_range', '')}
                    """)

        st.markdown("### 🥂 Where to Experience Local Cuisine")
        
        v_cols = st.columns(3)

        venues_traditional = culinary.get('venues_traditional', [])
        if venues_traditional:
            with v_cols[0]:
                st.markdown(f"#### 🥩 Traditional Cuisine")
                for venue in venues_traditional:
                    st.markdown(f"""
                    **{venue.get('name', 'Venue Name')}**  
                    📍 {venue.get('district', '')} | {venue.get('type', '')}  
                    💸 {venue.get('price_range', '')}  
                    ✨ *{venue.get('signature_items', '')}*
                    """)

        venues_cafes = culinary.get('venues_cafes', [])
        if venues_cafes:
            with v_cols[1]:
                st.markdown(f"#### ☕ Cafés & Desserts")
                for venue in venues_cafes:
                    st.markdown(f"""
                    **{venue.get('name', 'Venue Name')}**  
                    📍 {venue.get('district', '')} | {venue.get('type', '')}  
                    💸 {venue.get('price_range', '')}  
                    ✨ *{venue.get('signature_items', '')}*
                    """)

        venues_bars = culinary.get('venues_bars', [])
        if venues_bars:
            with v_cols[2]:
                st.markdown(f"#### 🍷 Wine & Bars")
                for venue in venues_bars:
                    st.markdown(f"""
                    **{venue.get('name', 'Venue Name')}**  
                    📍 {venue.get('district', '')} | {venue.get('type', '')}  
                    💸 {venue.get('price_range', '')}  
                    ✨ *{venue.get('signature_items', '')}*
                    """)

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

            """, unsafe_allow_html=True)

            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)

    render_culinary_section(plan)
    render_mobility_section(plan)

    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.markdown("### 🤔 Are you happy with this plan?")

def render_mobility_section(plan):
    mobility = plan.get('mobility_section')
    if not mobility:
        return

    st.markdown("---")
    
    with st.expander(f"🚆 Getting Around {plan['destination']}", expanded=True):
        st.markdown(f"## 🚆 Getting Around {plan['destination']}")

        if mobility.get('quick_recommendations'):
            recs = mobility['quick_recommendations']
            st.info(f"""
            ⭐ **Quick Guide**:  
            **Best Overall**: {recs.get('best_overall', 'N/A')}  
            **Cheapest**: {recs.get('cheapest', 'N/A')}  
            **Most Convenient**: {recs.get('most_convenient', 'N/A')}  
            **Avoid**: {recs.get('avoid', 'N/A')}
            """)

        col1, col2 = st.columns(2)
        
        def format_mobility_field(field_value):
            if isinstance(field_value, list):
                return ", ".join(field_value)
            elif isinstance(field_value, dict):
                return ", ".join([f"{k}: {v}" for k,v in field_value.items()])
            return str(field_value)

        with col1:
            pt = mobility.get('public_transport')
            if pt:
                st.markdown("### 🚇 Public Transport")
                st.markdown(f"""
                **Options**: {', '.join(pt.get('available_options', []))} ({pt.get('price_level', '')})  
                **Tickets**: {format_mobility_field(pt.get('ticket_types', ''))}  
                **Prices**: {format_mobility_field(pt.get('approximate_prices', ''))}   
                **Apps**: {', '.join(pt.get('useful_apps', []))} ({pt.get('best_use_cases', '')})
                """)
                if pt.get('website_url'):
                    st.markdown(f"🔗 [Official Info & Prices]({pt.get('website_url')})")

            walk = mobility.get('walking')
            if walk:
                st.markdown("### 🚶 Walking")
                st.markdown(f"""
                **Walkable?**: {'✅ Yes' if walk.get('is_walkable') else '❌ No'}  
                **Best Areas**: {walk.get('best_areas', '')}
                """)

        with col2:
            taxi = mobility.get('taxis')
            if taxi:
                st.markdown("### 🚕 Ride-Hailing & Taxis")
                st.markdown(f"""
                **Apps**: {', '.join(taxi.get('available_apps', []))} ({taxi.get('typical_pricing_level', '')})  
                **Safety**: {taxi.get('safety_notes', '')}  
                **When to use**: {taxi.get('when_to_use', '')}
                """)

            bikes = mobility.get('bikes')
            if bikes and bikes.get('available'):
                st.markdown("### 🚲 Bikes & Scooters")
                st.markdown(f"""
                **Providers**: {', '.join(bikes.get('providers', []))}  
                **Convenience**: {bikes.get('convenience', '')}  
                **Note**: {bikes.get('cautions', '')}
                """)

        ferry = mobility.get('ferries')
        if ferry and ferry.get('is_relevant'):
            st.markdown("### 🚢 Ferries / Boats")
            st.markdown(f"""
            **Routes**: {ferry.get('routes', '')}  
            **Cost**: {ferry.get('cost_level', '')}  
            **Info**: {ferry.get('tourist_vs_commuter', '')}
            """)

        car = mobility.get('car_rental')
        if car and car.get('recommended'):
             st.markdown("### 🚗 Car Rental")
             st.markdown(f"""
             **Parking**: {car.get('parking_difficulty', '')}  
             **Notes**: {car.get('notes', '')}
             """)

    
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
