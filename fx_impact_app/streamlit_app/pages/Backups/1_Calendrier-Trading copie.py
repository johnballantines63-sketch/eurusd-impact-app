import streamlit as st
import pandas as pd
import duckdb
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"

# ============================================================================
# FONCTIONS DE CACHE OPTIMISÉES
# ============================================================================

@st.cache_data(ttl=3600, show_spinner=False)  # Cache 1 heure
def load_all_events_cached(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Charge TOUS les événements pour une période donnée.
    Mise en cache pour éviter les requêtes répétées.
    
    Args:
        start_date: Date début format 'YYYY-MM-DD'
        end_date: Date fin format 'YYYY-MM-DD'
    
    Returns:
        DataFrame avec tous les événements
    """
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        query = f"""
        SELECT 
            event_datetime,
            currency,
            event_name,
            impact,
            actual,
            estimate,
            previous,
            event_id
        FROM events
        WHERE event_datetime >= '{start_date}'
          AND event_datetime <= '{end_date}'
          AND currency IN ('EUR', 'USD')
        ORDER BY event_datetime ASC
        """
        
        df = conn.execute(query).df()
        conn.close()
        
        # Conversion types
        df['event_datetime'] = pd.to_datetime(df['event_datetime'])
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur chargement événements : {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def get_events_by_date_cached(df_all_events: pd.DataFrame, target_date: str) -> pd.DataFrame:
    """
    Filtre les événements pour une date spécifique depuis le cache.
    Ultra-rapide car tout est déjà en mémoire.
    
    Args:
        df_all_events: DataFrame complet (depuis cache)
        target_date: Date format 'YYYY-MM-DD'
    
    Returns:
        DataFrame filtré pour la date
    """
    if df_all_events.empty:
        return pd.DataFrame()
    
    target_dt = pd.to_datetime(target_date)
    mask = df_all_events['event_datetime'].dt.date == target_dt.date()
    
    return df_all_events[mask].copy()


@st.cache_data(ttl=3600, show_spinner=False)
def get_high_impact_events_cached(df_all_events: pd.DataFrame) -> pd.DataFrame:
    """
    Filtre uniquement les événements High Impact depuis le cache.
    
    Args:
        df_all_events: DataFrame complet
    
    Returns:
        DataFrame avec seulement High Impact
    """
    if df_all_events.empty:
        return pd.DataFrame()
    
    return df_all_events[df_all_events['impact'] == 'High'].copy()


# ============================================================================
# EXEMPLE D'UTILISATION DANS STREAMLIT
# ============================================================================

def main():
    st.title("📅 Calendrier Trading - Événements à Surveiller")
    st.caption("🚀 Version optimisée avec cache")
    
    # ========================================================================
    # 1. SÉLECTION PÉRIODE
    # ========================================================================
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "📅 Date début",
            value=datetime.now().date(),
            key="start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "📅 Date fin",
            value=(datetime.now() + timedelta(days=7)).date(),
            key="end_date"
        )
    
    # ========================================================================
    # 2. CHARGEMENT AVEC CACHE (1 seule fois)
    # ========================================================================
    
    with st.spinner("⏳ Chargement événements..."):
        df_all = load_all_events_cached(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
    
    if df_all.empty:
        st.warning("⚠️ Aucun événement trouvé pour cette période")
        return
    
    # ========================================================================
    # 3. STATISTIQUES RAPIDES
    # ========================================================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total événements", len(df_all))
    
    with col2:
        high_impact = len(df_all[df_all['impact'] == 'High'])
        st.metric("🔴 High Impact", high_impact)
    
    with col3:
        eur_events = len(df_all[df_all['currency'] == 'EUR'])
        st.metric("🇪🇺 EUR", eur_events)
    
    with col4:
        usd_events = len(df_all[df_all['currency'] == 'USD'])
        st.metric("🇺🇸 USD", usd_events)
    
    st.divider()
    
    # ========================================================================
    # 4. FILTRES INTERACTIFS (ultra-rapides car en mémoire)
    # ========================================================================
    
    st.subheader("🔍 Filtres")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_currency = st.multiselect(
            "Devise",
            options=['EUR', 'USD'],
            default=['EUR', 'USD']
        )
    
    with col2:
        selected_impact = st.multiselect(
            "Impact",
            options=['High', 'Medium', 'Low'],
            default=['High', 'Medium', 'Low']
        )
    
    with col3:
        selected_date = st.date_input(
            "📅 Date spécifique (optionnel)",
            value=None,
            key="specific_date"
        )
    
    # ========================================================================
    # 5. FILTRAGE RAPIDE EN MÉMOIRE
    # ========================================================================
    
    df_filtered = df_all.copy()
    
    # Filtre devise
    if selected_currency:
        df_filtered = df_filtered[df_filtered['currency'].isin(selected_currency)]
    
    # Filtre impact
    if selected_impact:
        df_filtered = df_filtered[df_filtered['impact'].isin(selected_impact)]
    
    # Filtre date spécifique
    if selected_date:
        df_filtered = get_events_by_date_cached(df_filtered, selected_date.strftime('%Y-%m-%d'))
    
    # ========================================================================
    # 6. AFFICHAGE RÉSULTATS
    # ========================================================================
    
    st.subheader(f"📋 Événements trouvés : {len(df_filtered)}")
    
    if df_filtered.empty:
        st.info("ℹ️ Aucun événement ne correspond aux filtres")
        return
    
    # Grouper par date pour affichage organisé
    df_filtered['date'] = df_filtered['event_datetime'].dt.date
    df_filtered['time'] = df_filtered['event_datetime'].dt.strftime('%H:%M')
    
    for date in sorted(df_filtered['date'].unique()):
        with st.expander(f"📅 {date.strftime('%A %d %B %Y')}", expanded=True):
            df_day = df_filtered[df_filtered['date'] == date].sort_values('event_datetime')
            
            for _, event in df_day.iterrows():
                # Emoji impact
                impact_emoji = {
                    'High': '🔴',
                    'Medium': '🟡',
                    'Low': '🟢'
                }.get(event['impact'], '⚪')
                
                # Emoji devise
                currency_emoji = {
                    'EUR': '🇪🇺',
                    'USD': '🇺🇸'
                }.get(event['currency'], '🌍')
                
                col1, col2, col3 = st.columns([1, 4, 2])
                
                with col1:
                    st.write(f"**{event['time']}**")
                
                with col2:
                    st.write(f"{impact_emoji} {currency_emoji} {event['event_name']}")
                
                with col3:
                    if pd.notna(event['actual']):
                        st.write(f"Act: {event['actual']:.2f}")
                    elif pd.notna(event['estimate']):
                        st.write(f"Est: {event['estimate']:.2f}")
    
    # ========================================================================
    # 7. BOUTON RAFRAÎCHIR CACHE
    # ========================================================================
    
    st.divider()
    
    if st.button("🔄 Rafraîchir les données", type="secondary"):
        st.cache_data.clear()
        st.success("✅ Cache vidé ! Rechargement...")
        st.rerun()


# ============================================================================
# MÉTRIQUES DE PERFORMANCE
# ============================================================================

def show_performance_metrics():
    """Affiche les métriques de performance du cache"""
    
    st.sidebar.divider()
    st.sidebar.subheader("⚡ Performance")
    
    cache_stats = st.cache_data.get_stats()
    
    st.sidebar.metric(
        "Cache hits",
        len([s for s in cache_stats if s.get('hit_count', 0) > 0])
    )
    
    st.sidebar.caption("Cache TTL : 1 heure")


if __name__ == "__main__":
    main()
    show_performance_metrics()
