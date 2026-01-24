import requests

API_URL = "http://localhost:8000"

def generate_plan(form_data, llm_settings=None):
    payload = form_data.copy()
    if llm_settings:
        payload['llm_settings'] = llm_settings
        
    try:
        response = requests.post(f"{API_URL}/generate_plan", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return None

def update_plan(current_plan, form_data, feedback):
    payload = {
        "current_plan": current_plan,
        "user_input": form_data,
        "feedback": feedback
    }
    
    try:
        response = requests.post(f"{API_URL}/update_plan", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return None
