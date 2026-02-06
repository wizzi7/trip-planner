import streamlit as st

def format_mobility_field(field_value):
    if isinstance(field_value, list):
        return ", ".join(field_value)
    elif isinstance(field_value, dict):
        return ", ".join([f"{k}: {v}" for k,v in field_value.items()])
    return str(field_value)

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
