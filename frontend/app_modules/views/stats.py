import streamlit as st

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
