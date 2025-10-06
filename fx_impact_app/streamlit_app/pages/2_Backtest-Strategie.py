"""
Backtest Stratégie - Simulation de trading sur historique
Teste la performance de votre stratégie sur données passées
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from config import get_db_path
from forecaster_mvp import ForecastEngine
from scoring_engine import ScoringEngine
from event_families import FAMILY_PATTERNS, FAMILY_IMPORTANCE

st.set_page_config(page_title="Backtest Stratégie", page_icon="📈", layout="wide")

st.title("📈 Backtest de Stratégie - Validation Historique")
st.markdown("**Simulez vos trades sur l'historique pour valider votre approche**")

# Init
@st.cache_resource
def init_engines():
    return ForecastEngine(get_db_path()), ScoringEngine()

forecast_engine, scoring_engine = init_engines()

# === SIDEBAR: PARAMÈTRES DE BACKTEST ===
st.sidebar.header("⚙️ Paramètres du Backtest")

# Période de backtest
st.sidebar.subheader("📅 Période de test")
backtest_months = st.sidebar.slider("Mois à backtester", 1, 36, 12)
date_to = datetime.now()
date_from = date_to - timedelta(days=backtest_months * 30)

st.sidebar.info(f"📆 Du {date_from.strftime('%d/%m/%Y')} au {date_to.strftime('%d/%m/%Y')}")

# Filtres de sélection des trades
st.sidebar.subheader("🎯 Critères de Trade")

families = st.sidebar.multiselect(
    "Familles à trader",
    list(FAMILY_PATTERNS.keys()),
    default=['NFP', 'CPI', 'Unemployment']
)

countries = st.sidebar.multiselect(
    "Pays",
    ['US', 'EU', 'GB', 'JP', 'CH'],
    default=['US']
)

min_score = st.sidebar.slider("Score minimum pour trader", 0, 100, 50, 5)
min_importance = st.sidebar.select_slider(
    "Importance minimale",
    options=[1, 2, 3],
    value=2,
    format_func=lambda x: {1: "Low", 2: "Medium", 3: "High"}[x]
)

# Paramètres de trade
st.sidebar.subheader("💰 Gestion du Trade")

entry_offset = st.sidebar.number_input(
    "Entry (min avant événement)",
    min_value=-10,
    max_value=0,
    value=-2,
    help="Nombre de minutes AVANT l'événement pour entrer (-2 = 2 min avant)"
)

stop_loss_pips = st.sidebar.number_input("Stop Loss (pips)", 5, 50, 15)
take_profit_pips = st.sidebar.number_input("Take Profit (pips)", 10, 200, 50)

exit_strategy = st.sidebar.radio(
    "Stratégie de sortie",
    ["TP/SL fixe", "Sortie au TTR", "Sortie après X min"],
    help="TP/SL = Take Profit / Stop Loss fixes"
)

if exit_strategy == "Sortie après X min":
    exit_minutes = st.sidebar.number_input("Sortie après (min)", 5, 120, 30)
else:
    exit_minutes = 60  # Default

# Position sizing
position_size = st.sidebar.number_input("Taille position (lots)", 0.01, 10.0, 0.1, 0.01)
capital_initial = st.sidebar.number_input("Capital initial ($)", 100, 100000, 1000, 100)

# === FONCTION DE BACKTEST ===

def simulate_trade(event_ts, event_family, direction_expected, stop_loss, take_profit, exit_time):
    """
    Simule un trade sur un événement
    
    Returns:
        dict avec résultats du trade
    """
    import pandas as pd
    
    conn = duckdb.connect(get_db_path())
    
    # Normaliser event_ts (enlever timezone)
    if hasattr(event_ts, 'tz_localize'):
        event_ts_naive = event_ts.tz_localize(None) if event_ts.tzinfo else event_ts
    else:
        event_ts_naive = pd.Timestamp(event_ts).tz_localize(None) if pd.Timestamp(event_ts).tzinfo else pd.Timestamp(event_ts)
    
    # Timestamp d'entrée (X minutes avant événement)
    entry_ts = event_ts_naive + timedelta(minutes=entry_offset)
    
    # Récupérer prix d'entrée
    query_entry = f"""
    SELECT close as entry_price
    FROM prices_1m_v
    WHERE ts_utc <= '{entry_ts}'
    ORDER BY ts_utc DESC
    LIMIT 1
    """
    
    entry_result = conn.execute(query_entry).fetchdf()
    
    if len(entry_result) == 0:
        conn.close()
        return None  # Pas de données
    
    entry_price = entry_result['entry_price'].iloc[0]
    
    # Récupérer prix après événement (jusqu'à exit_time)
    exit_ts = event_ts_naive + timedelta(minutes=exit_time)
    
    query_prices = f"""
    SELECT ts_utc, close
    FROM prices_1m_v
    WHERE ts_utc >= '{entry_ts}'
      AND ts_utc <= '{exit_ts}'
    ORDER BY ts_utc
    """
    
    prices_df = conn.execute(query_prices).fetchdf()
    conn.close()
    
    if len(prices_df) < 2:
        return None
    
    # Normaliser les timestamps du DataFrame
    prices_df['ts_utc'] = pd.to_datetime(prices_df['ts_utc']).dt.tz_localize(None)
    
    # Simuler le trade tick par tick
    direction = 1 if direction_expected == 'UP' else -1
    
    max_profit_pips = 0
    max_loss_pips = 0
    exit_price = entry_price
    exit_reason = "Time"
    exit_time_actual = prices_df['ts_utc'].iloc[-1]
    
    for idx, row in prices_df.iterrows():
        if idx == 0:
            continue
        
        current_price = row['close']
        pnl_pips = (current_price - entry_price) * 10000 * direction
        
        # Track max profit/loss
        if pnl_pips > max_profit_pips:
            max_profit_pips = pnl_pips
        if pnl_pips < max_loss_pips:
            max_loss_pips = pnl_pips
        
        # Check TP
        if pnl_pips >= take_profit:
            exit_price = current_price
            exit_reason = "TP"
            exit_time_actual = row['ts_utc']
            break
        
        # Check SL
        if pnl_pips <= -stop_loss:
            exit_price = current_price
            exit_reason = "SL"
            exit_time_actual = row['ts_utc']
            break
    
    # Si aucun TP/SL touché, sortie au dernier prix
    if exit_reason == "Time":
        exit_price = prices_df['close'].iloc[-1]
    
    # Calculer P&L final
    final_pnl_pips = (exit_price - entry_price) * 10000 * direction
    final_pnl_usd = final_pnl_pips * position_size * 10  # 1 pip = $10 pour 1 lot sur EUR/USD
    
    # Durée du trade
    duration_minutes = (exit_time_actual - entry_ts).total_seconds() / 60
    
    return {
        'entry_time': entry_ts,
        'exit_time': exit_time_actual,
        'duration_min': duration_minutes,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'direction': 'LONG' if direction == 1 else 'SHORT',
        'exit_reason': exit_reason,
        'pnl_pips': final_pnl_pips,
        'pnl_usd': final_pnl_usd,
        'max_profit_pips': max_profit_pips,
        'max_loss_pips': max_loss_pips,
        'win': final_pnl_pips > 0,
        'family': event_family
    }

# === EXÉCUTION DU BACKTEST ===

if st.sidebar.button("🚀 Lancer le Backtest", type="primary", use_container_width=True):
    
    if not families:
        st.warning("⚠️ Sélectionnez au moins une famille à trader")
        st.stop()
    
    with st.spinner("🔄 Calcul des scores historiques..."):
        
        # 1. Calculer les scores pour les familles sélectionnées
        family_patterns = {f: FAMILY_PATTERNS[f] for f in families}
        
        # Utiliser 80% de la période pour calculer les stats (simulation réaliste)
        stats_period_years = int(backtest_months / 12 * 0.8)
        if stats_period_years < 1:
            stats_period_years = 1
        
        stats_results = forecast_engine.calculate_multiple_families(
            family_patterns,
            horizon_minutes=60,
            hist_years=stats_period_years,
            countries=countries
        )
        
        scored_results = scoring_engine.batch_score(stats_results, FAMILY_IMPORTANCE)
        
        # Filtrer par score minimum
        tradable_families = {
            r['family']: r for r in scored_results 
            if r['score'] >= min_score and r['metrics']['n_events'] > 0
        }
        
        if not tradable_families:
            st.error(f"❌ Aucune famille ne dépasse le score minimum de {min_score}")
            st.info("💡 Réduisez le score minimum ou élargissez les critères")
            st.stop()
    
    with st.spinner("📊 Récupération des événements de la période..."):
        
        # 2. Récupérer les événements dans la période de backtest
        conn = duckdb.connect(get_db_path())
        
        country_filter = "', '".join(countries)
        
        # Construire le pattern regex pour les familles tradables
        patterns = [FAMILY_PATTERNS[f] for f in tradable_families.keys()]
        # Combiner avec OR
        combined_pattern = '|'.join([p.replace('(?i)', '') for p in patterns])
        
        query_events = f"""
        SELECT ts_utc, event_key, country, importance_n
        FROM events
        WHERE ts_utc >= '{date_from.strftime('%Y-%m-%d')}'
          AND ts_utc <= '{date_to.strftime('%Y-%m-%d')}'
          AND country IN ('{country_filter}')
          AND importance_n >= {min_importance}
          AND event_key ~ '{combined_pattern}'
        ORDER BY ts_utc
        """
        
        events_df = conn.execute(query_events).fetchdf()
        conn.close()
        
        if len(events_df) == 0:
            st.error("❌ Aucun événement trouvé dans la période de backtest")
            st.stop()
        
        st.info(f"📅 {len(events_df)} événements identifiés pour backtest")
    
    with st.spinner(f"💹 Simulation de {len(events_df)} trades..."):
        
        # 3. Simuler chaque trade
        trades = []
        
        for idx, event in events_df.iterrows():
            # Identifier la famille
            import re
            event_family = None
            for family_name, pattern in FAMILY_PATTERNS.items():
                if family_name in tradable_families:
                    clean_pattern = pattern.replace('(?i)', '')
                    if re.search(clean_pattern, event['event_key'], re.IGNORECASE):
                        event_family = family_name
                        break
            
            if not event_family:
                continue
            
            # Déterminer direction attendue
            family_score = tradable_families[event_family]
            p_up = family_score['metrics']['p_up']
            direction = 'UP' if p_up >= 0.5 else 'DOWN'
            
            # Simuler le trade
            if exit_strategy == "Sortie au TTR":
                exit_time_min = int(family_score['metrics']['ttr_median'])
            elif exit_strategy == "Sortie après X min":
                exit_time_min = exit_minutes
            else:
                exit_time_min = 60  # Default pour TP/SL
            
            trade_result = simulate_trade(
                event['ts_utc'],
                event_family,
                direction,
                stop_loss_pips,
                take_profit_pips,
                exit_time_min
            )
            
            if trade_result:
                trades.append(trade_result)
        
        if not trades:
            st.error("❌ Aucun trade n'a pu être simulé (manque de données prix)")
            st.info("💡 Utilisez check_and_backfill_window.py pour compléter les données")
            st.stop()
    
    # === ANALYSE DES RÉSULTATS ===
    
    st.success(f"✅ {len(trades)} trades simulés avec succès !")
    
    # Calculs statistiques
    df_trades = pd.DataFrame(trades)
    
    total_trades = len(trades)
    winning_trades = df_trades[df_trades['win']].shape[0]
    losing_trades = total_trades - winning_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_pnl_pips = df_trades['pnl_pips'].sum()
    total_pnl_usd = df_trades['pnl_usd'].sum()
    
    avg_win_pips = df_trades[df_trades['win']]['pnl_pips'].mean() if winning_trades > 0 else 0
    avg_loss_pips = df_trades[~df_trades['win']]['pnl_pips'].mean() if losing_trades > 0 else 0
    
    avg_win_usd = df_trades[df_trades['win']]['pnl_usd'].mean() if winning_trades > 0 else 0
    avg_loss_usd = df_trades[~df_trades['win']]['pnl_usd'].mean() if losing_trades > 0 else 0
    
    profit_factor = abs(avg_win_usd * winning_trades / (avg_loss_usd * losing_trades)) if losing_trades > 0 and avg_loss_usd != 0 else float('inf')
    
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_streak = 0
    last_result = None
    
    for win in df_trades['win']:
        if win == last_result:
            current_streak += 1
        else:
            current_streak = 1
        
        if win:
            max_consecutive_wins = max(max_consecutive_wins, current_streak)
        else:
            max_consecutive_losses = max(max_consecutive_losses, current_streak)
        
        last_result = win
    
    # Calcul du drawdown
    df_trades['cumulative_pnl'] = df_trades['pnl_usd'].cumsum()
    df_trades['cumulative_max'] = df_trades['cumulative_pnl'].cummax()
    df_trades['drawdown'] = df_trades['cumulative_pnl'] - df_trades['cumulative_max']
    max_drawdown = df_trades['drawdown'].min()
    
    final_capital = capital_initial + total_pnl_usd
    roi = (total_pnl_usd / capital_initial * 100) if capital_initial > 0 else 0
    
    # === AFFICHAGE DES RÉSULTATS ===
    
    st.header("📊 Résultats du Backtest")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 P&L Total", f"${total_pnl_usd:,.2f}", f"{total_pnl_pips:,.0f} pips")
        st.metric("📈 ROI", f"{roi:.2f}%")
    
    with col2:
        st.metric("🎯 Win Rate", f"{win_rate:.1f}%")
        st.metric("✅ Trades Gagnants", winning_trades)
    
    with col3:
        st.metric("📊 Trades Totaux", total_trades)
        st.metric("❌ Trades Perdants", losing_trades)
    
    with col4:
        st.metric("💎 Profit Factor", f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞")
        st.metric("📉 Max Drawdown", f"${max_drawdown:,.2f}")
    
    st.divider()
    
    # Statistiques détaillées
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💚 Trades Gagnants")
        st.metric("Gain Moyen", f"{avg_win_pips:.1f} pips", f"${avg_win_usd:.2f}")
        st.metric("Meilleur Trade", f"{df_trades['pnl_pips'].max():.1f} pips")
        st.metric("Série Gagnante Max", f"{max_consecutive_wins} trades")
    
    with col2:
        st.subheader("❤️ Trades Perdants")
        st.metric("Perte Moyenne", f"{avg_loss_pips:.1f} pips", f"${avg_loss_usd:.2f}")
        st.metric("Pire Trade", f"{df_trades['pnl_pips'].min():.1f} pips")
        st.metric("Série Perdante Max", f"{max_consecutive_losses} trades")
    
    st.divider()
    
    # Graphique de courbe d'équité
    st.subheader("📈 Courbe d'Équité")
    
    equity_df = pd.DataFrame({
        'Trade #': range(1, len(df_trades) + 1),
        'Equity': capital_initial + df_trades['cumulative_pnl'].values
    })
    
    st.line_chart(equity_df.set_index('Trade #'))
    
    # Breakdown par famille
    st.subheader("🏷️ Performance par Famille")
    
    family_stats = df_trades.groupby('family').agg({
        'pnl_usd': ['sum', 'mean', 'count'],
        'win': 'mean'
    }).round(2)
    
    family_stats.columns = ['P&L Total ($)', 'P&L Moyen ($)', 'Nombre Trades', 'Win Rate']
    family_stats['Win Rate'] = (family_stats['Win Rate'] * 100).round(1).astype(str) + '%'
    
    st.dataframe(family_stats, use_container_width=True)
    
    # Breakdown par raison de sortie
    st.subheader("🚪 Raisons de Sortie")
    
    exit_stats = df_trades.groupby('exit_reason').agg({
        'pnl_usd': 'sum',
        'pnl_pips': 'mean',
        'win': ['count', 'mean']
    }).round(2)
    
    exit_stats.columns = ['P&L Total ($)', 'P&L Moyen (pips)', 'Nombre', 'Win Rate']
    exit_stats['Win Rate'] = (exit_stats['Win Rate'] * 100).round(1).astype(str) + '%'
    
    st.dataframe(exit_stats, use_container_width=True)
    
    # Liste des trades
    st.subheader("📋 Détail des Trades")
    
    display_trades = df_trades.copy()
    display_trades['entry_time'] = pd.to_datetime(display_trades['entry_time']).dt.strftime('%Y-%m-%d %H:%M')
    display_trades['Result'] = display_trades['win'].apply(lambda x: '✅ Win' if x else '❌ Loss')
    
    st.dataframe(
        display_trades[['entry_time', 'family', 'direction', 'pnl_pips', 'pnl_usd', 'exit_reason', 'duration_min', 'Result']],
        use_container_width=True,
        hide_index=True
    )
    
    # Export
    st.divider()
    st.subheader("💾 Export des Résultats")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df_trades.to_csv(index=False)
        st.download_button(
            "📥 Télécharger Trades (CSV)",
            csv,
            f"backtest_trades_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        # Rapport texte
        report = f"""RAPPORT DE BACKTEST
{'='*50}

Période: {date_from.strftime('%Y-%m-%d')} à {date_to.strftime('%Y-%m-%d')}
Stratégie: Score minimum {min_score}, {exit_strategy}

RÉSULTATS GLOBAUX
{'-'*50}
Trades totaux: {total_trades}
Trades gagnants: {winning_trades} ({win_rate:.1f}%)
Trades perdants: {losing_trades}

P&L Total: ${total_pnl_usd:,.2f} ({total_pnl_pips:,.0f} pips)
ROI: {roi:.2f}%
Profit Factor: {profit_factor:.2f}
Max Drawdown: ${max_drawdown:,.2f}

Capital initial: ${capital_initial:,.2f}
Capital final: ${final_capital:,.2f}

STATISTIQUES
{'-'*50}
Gain moyen: {avg_win_pips:.1f} pips (${avg_win_usd:.2f})
Perte moyenne: {avg_loss_pips:.1f} pips (${avg_loss_usd:.2f})
Meilleur trade: {df_trades['pnl_pips'].max():.1f} pips
Pire trade: {df_trades['pnl_pips'].min():.1f} pips
"""
        
        st.download_button(
            "📄 Rapport (TXT)",
            report,
            f"backtest_report_{date_from.strftime('%Y%m%d')}.txt",
            "text/plain",
            use_container_width=True
        )

else:
    # Page d'accueil
    st.info("👈 Configurez les paramètres et cliquez sur **Lancer le Backtest**")
    
    st.markdown("""
    ### 🎯 Objectif du Backtest
    
    Valider votre stratégie de trading d'événements en simulant des trades réels sur données historiques.
    
    ### 📋 Méthodologie
    
    1. **Sélection** : Événements avec score ≥ minimum dans la période
    2. **Entrée** : X minutes avant l'événement (paramétrable)
    3. **Direction** : Basée sur probabilité historique (P(↑) > 50% = LONG)
    4. **Sortie** : TP/SL fixe, au TTR médian, ou après X minutes
    5. **Calcul P&L** : Simulation tick-par-tick avec les prix réels
    
    ### 💡 Conseils
    
    - **Score minimum 50-60** : Bon équilibre nombre de trades / qualité
    - **Stop Loss 15 pips** : Limite le risque sur faux signaux
    - **Take Profit 50+ pips** : Capture les gros mouvements
    - **Sortie au TTR** : Plus réaliste que TP/SL fixes
    
    ### ⚠️ Limitations
    
    - Simulation simplifiée (pas de slippage, spreads fixes)
    - Manque de données prix = trades non simulés
    - Performance passée ≠ performance future
    """)
