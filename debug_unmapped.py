file_path = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

with open(file_path, 'r') as f:
    content = f.read()

# Ajouter debug avant la condition
old = '''    if 'all_events' in st.session_state and len(st.session_state.all_events['unmapped']) > 0:'''

new = '''    # DEBUG
    st.write("DEBUG: all_events in session_state?", 'all_events' in st.session_state)
    if 'all_events' in st.session_state:
        st.write("DEBUG: unmapped count:", len(st.session_state.all_events['unmapped']))
        st.write("DEBUG: unmapped keys:", st.session_state.all_events['unmapped'].columns.tolist() if hasattr(st.session_state.all_events['unmapped'], 'columns') else 'Not a DataFrame')
    
    if 'all_events' in st.session_state and len(st.session_state.all_events['unmapped']) > 0:'''

content = content.replace(old, new)

with open(file_path, 'w') as f:
    f.write(content)

print("✅ Debug ajouté, relance streamlit")
