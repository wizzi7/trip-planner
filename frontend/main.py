import streamlit as st
from app_modules import views, api_service
import os

st.set_page_config(
    page_title="Intelligent Trip Planner",
    page_icon="🌍",
    layout="wide"
)

def local_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)
    with open(file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("assets/styles.css")

if 'page' not in st.session_state:
    st.session_state.page = 'form'
if 'plan_history' not in st.session_state:
    st.session_state.plan_history = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'feedback_loop' not in st.session_state:
    st.session_state.feedback_loop = None

def main():
    views.render_header()

    with st.sidebar:
        with st.expander("⚙️ AI Settings", expanded=False):
            model_options = ["gemini-3.5-flash", "gpt-5.4", "claude-sonnet-4-6"]
            model_name = st.selectbox(
                "Model", 
                model_options,
                index=0
            )
            temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
            max_tokens = st.number_input("Max Tokens", min_value=100, max_value=8000, value=2000, step=100)
            
            if "gpt" in model_name:
                provider = "openai"
            elif "claude" in model_name:
                provider = "claude"
            else:
                provider = "gemini"
            
            st.session_state.llm_settings = {
                "model": model_name,
                "provider": provider,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

        st.header("🗂️ Trip History")
        if not st.session_state.plan_history:
            st.write("No plans generated in this session.")
        else:
            for i, plan in enumerate(reversed(st.session_state.plan_history)):
                if plan is None:
                    continue
                label = f"{plan.get('destination', 'Plan')} #{len(st.session_state.plan_history)-i}"
                if st.button(label, key=f"hist_{i}"):
                    st.session_state.current_plan = plan
                    st.session_state.page = 'results'
                    st.rerun()


    if st.session_state.page == 'form':
        generate_clicked, form_data = views.render_form()
        
        if generate_clicked:
            if not form_data['destination']:
                st.error("Please enter a destination!")
            else:
                st.session_state.page = 'loading'
                st.session_state.form_data = form_data
                st.session_state.feedback_loop = None
                st.rerun()
                
    elif st.session_state.page == 'loading':
        views.render_loading()

        data = st.session_state.form_data
        feedback = st.session_state.feedback_loop
        
        llm_settings = st.session_state.get('llm_settings', {})
        
        if feedback:
            current_plan = st.session_state.get('current_plan')
            plan = api_service.update_plan(current_plan, data, feedback)
        else:
            plan = api_service.generate_plan(data, llm_settings=llm_settings)
        
        if plan:
            st.session_state.current_plan = plan
            st.session_state.plan_history.append(plan)
            st.session_state.page = 'results'
            st.rerun()
        else:
            st.error("Failed to generate plan. Please try again.")
            if st.button("Go Back"):
                st.session_state.page = 'form'
                st.rerun()
        
    elif st.session_state.page == 'results':
        if 'current_plan' in st.session_state:
            regenerate_feedback = views.render_results(st.session_state.current_plan)

            if regenerate_feedback == "__regenerate__":
                st.session_state.feedback_loop = None
                st.session_state.page = 'loading'
                st.rerun()
            elif regenerate_feedback:
                st.session_state.feedback_loop = regenerate_feedback
                st.session_state.page = 'loading'
                st.rerun()
                
            col1, col2 = st.columns(2)
            with col1:
                pass 
            with col2:
                 if st.button("New Trip (Reset)"):
                    st.session_state.page = 'form'
                    st.session_state.form_data = {}
                    st.rerun()
                    
        else:
            st.error("Error: No plan to display.")
            if st.button("Go Back"):
                st.session_state.page = 'form'
                st.rerun()

if __name__ == "__main__":
    main()
