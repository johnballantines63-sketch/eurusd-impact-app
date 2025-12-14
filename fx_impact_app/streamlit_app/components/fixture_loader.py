"""
Module d'intégration des fixtures dans Streamlit
Permet de charger rapidement des événements de test prédéfinis
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

FIXTURES_DIR = Path(__file__).parent.parent.parent / "test_fixtures"

def get_available_fixtures():
    """Retourne la liste des fixtures disponibles"""
    if not FIXTURES_DIR.exists():
        return []
    
    fixtures = []
    for fixture_path in FIXTURES_DIR.glob("*.json"):
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        fixtures.append({
            'name': fixture_path.stem,
            'display_name': data.get('name', fixture_path.stem),
            'date': data.get('date'),
            'n_events': len(data.get('events', [])),
            'path': fixture_path
        })
    
    return sorted(fixtures, key=lambda x: x['date'], reverse=True)

def load_fixture_as_dataframe(fixture_name: str):
    """Charge une fixture et la retourne comme DataFrame"""
    fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    
    if not fixture_path.exists():
        return None
    
    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    if not events:
        return None
    
    # Convertir en DataFrame
    df = pd.DataFrame(events)
    
    # Convertir ts_utc en datetime
    df['ts_utc'] = pd.to_datetime(df['ts_utc'])
    
    return df

def show_fixture_selector():
    """
    Affiche un sélecteur de fixtures dans la sidebar
    Retourne le DataFrame des événements si une fixture est sélectionnée
    """
    fixtures = get_available_fixtures()
    
    if not fixtures:
        return None
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧪 Fixtures de Test")
    
    # Sélecteur
    fixture_options = {
        f"{f['display_name']} ({f['date']}) - {f['n_events']} events": f['name']
        for f in fixtures
    }
    
    selected_display = st.sidebar.selectbox(
        "Charger une fixture",
        ["Aucune"] + list(fixture_options.keys()),
        key='fixture_selector'
    )
    
    if selected_display == "Aucune":
        return None
    
    fixture_name = fixture_options[selected_display]
    
    if st.sidebar.button("📥 Charger fixture", type="primary", use_container_width=True):
        with st.spinner("Chargement fixture..."):
            df = load_fixture_as_dataframe(fixture_name)
            
            if df is not None:
                st.sidebar.success(f"✅ {len(df)} événements chargés")
                return df
            else:
                st.sidebar.error("❌ Erreur chargement fixture")
                return None
    
    return None

def create_fixture_from_current_selection(selected_events_df, date_str: str, name: str):
    """
    Crée une fixture à partir de la sélection actuelle
    
    Args:
        selected_events_df: DataFrame des événements sélectionnés
        date_str: Date au format 'YYYY-MM-DD'
        name: Nom de la fixture
    """
    FIXTURES_DIR.mkdir(exist_ok=True)
    
    events_data = selected_events_df.to_dict('records')
    
    # Convertir datetime en string pour JSON
    for event in events_data:
        if 'ts_utc' in event and isinstance(event['ts_utc'], pd.Timestamp):
            event['ts_utc'] = event['ts_utc'].isoformat()
    
    fixture = {
        'date': date_str,
        'name': name,
        'created_at': datetime.now().isoformat(),
        'events': events_data
    }
    
    fixture_path = FIXTURES_DIR / f"{name}.json"
    
    with open(fixture_path, 'w', encoding='utf-8') as f:
        json.dump(fixture, f, indent=2, ensure_ascii=False)
    
    return fixture_path
