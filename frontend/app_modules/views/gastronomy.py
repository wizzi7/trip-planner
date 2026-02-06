import streamlit as st

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
