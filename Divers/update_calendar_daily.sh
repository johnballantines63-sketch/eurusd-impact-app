import streamlit as st
import pandas as pd
import duckdb
from datetime import datetime, timedelta
from pathlib import Path
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"

# Configuration cache
CACHE_TTL = 3600  # 1 heure
CACHE_MAX_ENTRIES = 128  # Limite mémoire

# ============================================================================
# FONCTIONS DE CACHE OPTIMISÉES
# ============================================================================

@st.cache_data(ttl=CACHE_TTL, max_entries=CACHE_MAX_ENTRIES, show_spinner=False)
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
    start_time = time.time()
    
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
        
        # Métriques performance
        load_time = time.time() - start_time
        if 'perf_metrics' not in st.session_state:
            st.session_state.perf_metrics = {}
        st.session_state.perf_metrics['last_load_time'] = load_time
        st.session_state.perf_metrics['events_loaded'] = len(df)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur chargement événements : {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_events_by_date_cached(df_all_events: pd.DataFrame, target_date: str) -> pd.DataFrame:
    """
    Filtre les événements pour une date spécifique depuis le cache.
    Ultra-rapide car tout est déjà en mémoire.
    """
    if df_all_events.empty:
        return pd.DataFrame()
    
    target_dt = pd.to_datetime(target_date)
    mask = df_all_events['event_datetime'].dt.date == target_dt.date()
    
    return df_all_events[mask].copy()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_high_impact_events_cached(df_all_events: pd.DataFrame) -> pd.DataFrame:
    """
    Filtre uniquement les événements High Impact depuis le cache.
    """
    if df_all_events.empty:
        return pd.DataFrame()
    
    return df_all_events[df_all_events['impact'] == 'High'].copy()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_events_with_surprise_cached(df_all_events: pd.DataFrame, min_surprise_pct: float = 10.0) -> pd.DataFrame:
    """
    Filtre les événements avec surprise significative.
    """
    if df_all_events.empty:
        return pd.DataFrame()
    
    df = df_all_events.copy()
    
    # Calcul surprise
    mask = (df['actual'].notna()) & (df['estimate'].notna()) & (df['estimate'] != 0)
    df_with_data = df[mask].copy()
    
    df_with_data['surprise_pct'] = abs(
        (df_with_data['actual'] - df_with_data['estimate']) / df_with_data['estimate'] * 100
    )
    
    return df_with_data[df_with_data['surprise_pct'] >= min_surprise_pct]


# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

def main():
    st.title("📅 Calendrier Trading - Événements à Surveiller")
    st.caption("🚀 Version optimisée avec cache intelligent")
    
    # ========================================================================
    # SIDEBAR - Configuration
    # ========================================================================
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Preset périodes
        period_preset = st.selectbox(
            "Période rapide",
            ["Personnalisé", "Aujourd'hui", "Cette semaine", "Ce mois", "Prochain mois"],
            key="period_preset"
        )
        
        # Calcul dates selon preset
        today = datetime.now().date()
        
        if period_preset == "Aujourd'hui":
            default_start = today
            default_end = today
        elif period_preset == "Cette semaine":
            default_start = today
            default_end = today + timedelta(days=7)
        elif period_preset == "Ce mois":
            default_start = today
            default_end = today.replace(day=1) + timedelta(days=32)
            default_end = default_end.replace(day=1) - timedelta(days=1)
        elif period_preset == "Prochain mois":
            next_month = today.replace(day=1) + timedelta(days=32)
            default_start = next_month.replace(day=1)
            default_end = (default_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            default_start = today
            default_end = today + timedelta(days=7)
    
    # ========================================================================
    # 1. SÉLECTION PÉRIODE
    # ========================================================================
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "📅 Date début",
            value=default_start,
            key="start_date",
            disabled=(period_preset != "Personnalisé")
        )
    
    with col2:
        end_date = st.date_input(
            "📅 Date fin",
            value=default_end,
            key="end_date",
            disabled=(period_preset != "Personnalisé")
        )
    
    # Validation période
    if start_date > end_date:
        st.error("❌ La date de début doit être avant la date de fin")
        return
    
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
    
    # Métriques additionnelles
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        events_with_estimate = len(df_all[df_all['estimate'].notna()])
        st.metric("📈 Avec estimate", events_with_estimate)
    
    with col2:
        events_with_actual = len(df_all[df_all['actual'].notna()])
        st.metric("✅ Avec actual", events_with_actual)
    
    with col3:
        medium_impact = len(df_all[df_all['impact'] == 'Medium'])
        st.metric("🟡 Medium Impact", medium_impact)
    
    with col4:
        low_impact = len(df_all[df_all['impact'] == 'Low'])
        st.metric("🟢 Low Impact", low_impact)
    
    st.divider()
    
    # ========================================================================
    # 4. FILTRES INTERACTIFS (ultra-rapides car en mémoire)
    # ========================================================================
    
    st.subheader("🔍 Filtres avancés")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_currency = st.multiselect(
            "Devise",
            options=['EUR', 'USD'],
            default=['EUR', 'USD'],
            key="filter_currency"
        )
    
    with col2:
        selected_impact = st.multiselect(
            "Impact",
            options=['High', 'Medium', 'Low'],
            default=['High', 'Medium', 'Low'],
            key="filter_impact"
        )
    
    with col3:
        filter_with_estimate = st.checkbox(
            "Seulement avec estimate",
            value=False,
            key="filter_estimate"
        )
    
    with col4:
        min_surprise = st.slider(
            "Surprise min (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            key="min_surprise",
            help="Filtre les événements avec surprise >= X%"
        )
    
    # Date spécifique (optionnel)
    show_date_filter = st.checkbox("Filtrer par date spécifique", value=False)
    
    if show_date_filter:
        selected_date = st.date_input(
            "📅 Date spécifique",
            value=start_date,
            min_value=start_date,
            max_value=end_date,
            key="specific_date"
        )
    else:
        selected_date = None
    
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
    
    # Filtre estimate
    if filter_with_estimate:
        df_filtered = df_filtered[df_filtered['estimate'].notna()]
    
    # Filtre surprise
    if min_surprise > 0:
        df_surprise = get_events_with_surprise_cached(df_filtered, min_surprise)
        df_filtered = df_surprise
    
    # Filtre date spécifique
    if selected_date:
        df_filtered = get_events_by_date_cached(df_filtered, selected_date.strftime('%Y-%m-%d'))
    
    # ========================================================================
    # 6. AFFICHAGE RÉSULTATS
    # ========================================================================
    
    st.divider()
    
    # Options d'affichage
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader(f"📋 Événements : {len(df_filtered)}")
    
    with col2:
        view_mode = st.radio(
            "Mode affichage",
            ["Groupé par date", "Liste complète", "Tableau"],
            horizontal=True,
            key="view_mode"
        )
    
    with col3:
        if st.button("📥 Export CSV", type="secondary"):
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                "⬇️ Télécharger",
                csv,
                f"events_{start_date}_{end_date}.csv",
                "text/csv"
            )
    
    if df_filtered.empty:
        st.info("ℹ️ Aucun événement ne correspond aux filtres")
        return
    
    # ========================================================================
    # MODE: Groupé par date
    # ========================================================================
    
    if view_mode == "Groupé par date":
        # Grouper par date
        df_filtered['date'] = df_filtered['event_datetime'].dt.date
        df_filtered['time'] = df_filtered['event_datetime'].dt.strftime('%H:%M')
        
        for date in sorted(df_filtered['date'].unique()):
            df_day = df_filtered[df_filtered['date'] == date].sort_values('event_datetime')
            
            # Compte par impact
            high_count = len(df_day[df_day['impact'] == 'High'])
            medium_count = len(df_day[df_day['impact'] == 'Medium'])
            low_count = len(df_day[df_day['impact'] == 'Low'])
            
            title = f"📅 {date.strftime('%A %d %B %Y')} - {len(df_day)} événements"
            if high_count > 0:
                title += f" (🔴 {high_count})"
            
            with st.expander(title, expanded=(len(df_filtered['date'].unique()) <= 3)):
                for _, event in df_day.iterrows():
                    display_event_card(event)
    
    # ========================================================================
    # MODE: Liste complète
    # ========================================================================
    
    elif view_mode == "Liste complète":
        df_display = df_filtered.sort_values('event_datetime')
        df_display['time'] = df_display['event_datetime'].dt.strftime('%Y-%m-%d %H:%M')
        
        for _, event in df_display.iterrows():
            display_event_card(event)
    
    # ========================================================================
    # MODE: Tableau
    # ========================================================================
    
    else:  # Tableau
        df_table = df_filtered.copy()
        df_table['datetime'] = df_table['event_datetime'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Calcul surprise si possible
        mask = (df_table['actual'].notna()) & (df_table['estimate'].notna()) & (df_table['estimate'] != 0)
        df_table.loc[mask, 'surprise_%'] = (
            (df_table.loc[mask, 'actual'] - df_table.loc[mask, 'estimate']) / 
            df_table.loc[mask, 'estimate'] * 100
        ).round(2)
        
        columns_display = ['datetime', 'currency', 'event_name', 'impact', 
                          'actual', 'estimate', 'previous', 'surprise_%']
        
        st.dataframe(
            df_table[columns_display].sort_values('datetime'),
            use_container_width=True,
            hide_index=True
        )
    
    # ========================================================================
    # 7. ACTIONS
    # ========================================================================
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Rafraîchir les données", type="secondary"):
            st.cache_data.clear()
            st.success("✅ Cache vidé ! Rechargement...")
            st.rerun()
    
    with col2:
        if st.button("🎯 Voir événements High Impact", type="primary"):
            st.session_state.filter_impact = ['High']
            st.rerun()


def display_event_card(event):
    """Affiche une carte d'événement avec tous les détails"""
    
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
    
    # Calcul surprise si possible
    surprise_text = ""
    if pd.notna(event['actual']) and pd.notna(event['estimate']) and event['estimate'] != 0:
        surprise_pct = (event['actual'] - event['estimate']) / event['estimate'] * 100
        surprise_emoji = "📈" if surprise_pct > 0 else "📉"
        surprise_text = f" {surprise_emoji} **{surprise_pct:+.1f}%**"
    
    col1, col2, col3 = st.columns([1, 5, 2])
    
    with col1:
        time_str = event.get('time', event['event_datetime'].strftime('%H:%M'))
        st.write(f"**{time_str}**")
    
    with col2:
        st.write(f"{impact_emoji} {currency_emoji} **{event['event_name']}**{surprise_text}")
    
    with col3:
        values = []
        if pd.notna(event['actual']):
            values.append(f"Act: **{event['actual']:.2f}**")
        if pd.notna(event['estimate']):
            values.append(f"Est: {event['estimate']:.2f}")
        if pd.notna(event['previous']):
            values.append(f"Prev: {event['previous']:.2f}")
        
        if values:
            st.write(" | ".join(values))


# ============================================================================
# MÉTRIQUES DE PERFORMANCE
# ============================================================================

def show_performance_metrics():
    """Affiche les métriques de performance du cache"""
    
    st.sidebar.divider()
    st.sidebar.subheader("⚡ Performance")
    
    # Métriques de chargement
    if 'perf_metrics' in st.session_state:
        metrics = st.session_state.perf_metrics
        
        if 'last_load_time' in metrics:
            load_time_ms = metrics['last_load_time'] * 1000
            st.sidebar.metric(
                "Temps chargement",
                f"{load_time_ms:.0f} ms"
            )
        
        if 'events_loaded' in metrics:
            st.sidebar.metric(
                "Événements chargés",
                metrics['events_loaded']
            )
    
    # Statut cache
    st.sidebar.caption(f"🔄 Cache TTL: {CACHE_TTL//60} minutes")
    st.sidebar.caption(f"💾 Max entries: {CACHE_MAX_ENTRIES}")
    
    # Bouton clear cache sidebar
    if st.sidebar.button("🗑️ Vider cache", key="clear_cache_sidebar"):
        st.cache_data.clear()
        st.sidebar.success("✅ Cache vidé")


if __name__ == "__main__":
    st.set_page_config(
        page_title="Calendrier Trading",
        page_icon="📅",
        layout="wide"
    )
    
    main()
    show_performance_metrics()
