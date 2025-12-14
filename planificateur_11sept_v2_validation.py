"""
PLANIFICATEUR 11 SEPTEMBRE 2025 - VERSION 2 VALIDATION

Script de validation du planificateur multi-événements.
Utilise les 4 formules validées de formulas_validated.py.

Objectif : Reproduire le graphique du 11 septembre avec :
- Graphique en chandeliers
- Toutes les métriques (impact, latence, TTR, pullback, phases, stabilisation)
- Export CSV des résultats
- Comparaison avec MT5

Données : 11 septembre 2025 hardcodé
Phase : VALIDATION avant interface évoluée

Date : 23 octobre 2025 - Session 58
Auteur : André Valentin avec Claude
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import warnings
warnings.filterwarnings('ignore')

# Ajouter chemins
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "fx_impact_app"))
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

from config import get_db_path
from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    calculate_ttr_c,
    calculate_pullback_v2
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Cas d'école : 11 septembre 2025
# NOTE: La DB stocke en heure Berne (CEST = UTC+2), pas en UTC pur
EVENT_DATE = "2025-09-11"
EVENT_TIME_BERNE_1 = "14:30:00"  # 14:30 Berne - Annonces US (CPI, Jobless Claims, etc.) - 15 événements
EVENT_TIME_BERNE_2 = "17:30:00"  # 17:30 Berne - Other (2 événements)

# Valeurs de référence MT5
REFERENCE_MT5 = {
    'start_price': 1.16816,      # 12:30:00
    'peak_price': 1.17190,       # 12:35:00 (TTR)
    'pullback_price': 1.16919,   # 12:45:00 (après pullback)
    'final_price': 1.17378,      # 13:10:00 (stabilisation)
    'phase1_pips': 37.4,
    'pullback_pips': 27.1,
    'phase2_pips': 45.9,
    'total_pips': 56.2
}

# Sentiment des familles d'événements
FAMILY_SENTIMENT = {
    'GDP': 1, 'GDP_Growth_Rate': 1, 'GDP_Sales': 1,
    'PMI': 1, 'PMI_Composite': 1, 'PMI_Manufacturing': 1, 'PMI_Services': 1,
    'CPI': 1, 'CPI_Core': 1, 'PPI': 1,
    'Unemployment_Rate': -1, 'Jobless_Claims': -1,
    'NFP': 1, 'Payrolls': 1,
    'Retail_Sales': 1, 'Consumer_Confidence': 1,
    'Industrial_Production': 1, 'Inflation_Rate': 1,
    'Interest_Rate': 1, 'Trade_Balance': 1, 'Current_Account': 1,
}

def get_event_direction(family: str, surprise: float) -> int:
    """Détermine direction selon surprise et sentiment famille."""
    if abs(surprise) < 0.01:
        return 1
    sentiment = FAMILY_SENTIMENT.get(family, 1)
    return sentiment if surprise > 0 else -sentiment

# =============================================================================
# CHARGEMENT DONNÉES
# =============================================================================

def load_events_11sept():
    """Charge les événements du 11 septembre depuis DB."""
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path))
    
    query = f"""
    SELECT 
        e.event_key,
        e.country,
        e.event_title,
        e.ts_utc as event_datetime,
        e.actual,
        e.estimate as forecast,
        e.label as family,
        ef.empirical_score,
        ef.latency_median,
        ef.ttr_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{EVENT_DATE}'
        AND e.country = 'US'
        AND e.actual IS NOT NULL
        AND ef.empirical_score IS NOT NULL
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    # Calculer surprise
    df['surprise'] = df['actual'] - df['forecast']
    df['surprise_pct'] = ((df['actual'] - df['forecast']).abs() / df['forecast'].abs() * 100)
    df['surprise_pct'] = df['surprise_pct'].fillna(0)
    
    print(f"✅ {len(df)} événements chargés")
    return df

def load_prices_11sept():
    """Charge les prix du 11 septembre depuis DB."""
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path))
    
    # Charger de 12:00 à 14:00 UTC (10:00 à 16:00 Berne)
    query = f"""
    SELECT 
        datetime,
        open,
        high,
        low,
        close,
        volume
    FROM prices_1m
    WHERE DATE(datetime) = '{EVENT_DATE}'
        AND datetime >= '{EVENT_DATE} 12:00:00'
        AND datetime <= '{EVENT_DATE} 14:00:00'
    ORDER BY datetime
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    if not df.empty:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
    
    print(f"✅ {len(df)} chandeliers chargés")
    return df

# =============================================================================
# CALCUL PHASES
# =============================================================================

def calculate_phases_with_validated_formulas(events_df):
    """
    Calcule les phases en utilisant les formules validées.
    
    Returns:
        dict avec toutes les métriques calculées
    """
    print("\n" + "="*80)
    print("📊 CALCUL DES PHASES - FORMULES VALIDÉES")
    print("="*80)
    
    # Séparer événements par horaire
    events_1230 = events_df[events_df['event_datetime'].dt.strftime('%H:%M:%S') == EVENT_TIME_UTC_1]
    events_1245 = events_df[events_df['event_datetime'].dt.strftime('%H:%M:%S') == EVENT_TIME_UTC_2]
    
    print(f"\n📅 Événements 12:30 UTC : {len(events_1230)}")
    print(f"📅 Événements 12:45 UTC : {len(events_1245)}")
    
    # =========================================================================
    # PHASE 1 : Événements 12:30
    # =========================================================================
    
    print("\n" + "-"*80)
    print("🚀 PHASE 1 - Événements 12:30 UTC")
    print("-"*80)
    
    contributions_phase1 = []
    phase1_surprises = []
    phase1_details = []
    
    for idx, event in events_1230.iterrows():
        family = event['family']
        score_base = event['empirical_score']
        surprise = event['surprise']
        surprise_pct = event['surprise_pct']
        
        # 1. Ajuster score selon surprise
        score_adjusted = calculate_adjusted_empirical_score(score_base, surprise_pct)
        
        # 2. Calculer impact brut (formule régression)
        num_events = len(events_1230)
        if num_events >= 2:
            impact_brut = -10.47 + 0.477 * score_adjusted
        else:
            impact_brut = -7.08 + 0.419 * score_adjusted
        
        # 3. Direction avec sentiment
        direction = get_event_direction(family, surprise)
        
        # Contribution vectorielle
        contribution = impact_brut * direction
        contributions_phase1.append(contribution)
        phase1_surprises.append(abs(surprise_pct))
        
        phase1_details.append({
            'family': family,
            'score_base': score_base,
            'surprise_pct': surprise_pct,
            'score_adjusted': score_adjusted,
            'impact_brut': impact_brut,
            'direction': 'UP' if direction > 0 else 'DOWN',
            'contribution': contribution
        })
        
        print(f"   {family:30s} | Score: {score_base:5.1f} → {score_adjusted:5.1f} | "
              f"Surprise: {surprise_pct:5.1f}% | Contrib: {contribution:+6.1f} pips")
    
    # Somme vectorielle Phase 1
    impact_phase1_brut = sum(contributions_phase1)
    
    # Amplification selon surprise max
    max_surprise_pct = max(phase1_surprises) if phase1_surprises else 0
    
    if max_surprise_pct <= 5:
        amplification = 1.0
    elif max_surprise_pct <= 15:
        amplification = 1.0 + (max_surprise_pct - 5) / 10 * 1.5
    else:
        amplification = 2.5
    
    # Impact final Phase 1
    impact_phase1 = abs(impact_phase1_brut) * amplification * 0.758
    direction_phase1 = 1 if impact_phase1_brut >= 0 else -1
    
    print(f"\n   📊 Somme vectorielle : {impact_phase1_brut:+.1f} pips")
    print(f"   📊 Surprise max      : {max_surprise_pct:.1f}%")
    print(f"   📊 Amplification     : {amplification:.2f}x")
    print(f"   📊 IMPACT PHASE 1    : {impact_phase1:+.1f} pips ({['DOWN', 'UP'][direction_phase1 > 0]})")
    
    # TTR Phase 1
    latency_median = events_1230['latency_median'].mean() / 60  # secondes → minutes
    ttr_phase1 = calculate_ttr_c(latency_median, max_surprise_pct)
    
    print(f"   ⏱️  Latence médiane   : {latency_median:.1f} min")
    print(f"   ⏱️  TTR PHASE 1       : {ttr_phase1:.1f} min")
    
    # =========================================================================
    # PULLBACK : Entre Phase 1 (12:35) et Phase 2 (12:45)
    # =========================================================================
    
    print("\n" + "-"*80)
    print("📉 PULLBACK - 12:35 → 12:45")
    print("-"*80)
    
    # Temps écoulé : 10 minutes entre peak (12:35) et event 2 (12:45)
    minutes_since_peak = 10
    minutes_to_next_phase = 15  # 12:30 → 12:45
    
    pullback_pips = calculate_pullback_v2(
        phase1_impact=impact_phase1,
        minutes_since_peak=minutes_since_peak,
        minutes_to_next_phase=minutes_to_next_phase
    )
    
    print(f"   📊 Impact Phase 1     : {impact_phase1:.1f} pips")
    print(f"   ⏱️  Minutes depuis peak : {minutes_since_peak} min")
    print(f"   ⏱️  Intervalle phases   : {minutes_to_next_phase} min")
    print(f"   📉 PULLBACK          : {pullback_pips:.1f} pips")
    
    # =========================================================================
    # PHASE 2 : Événements 12:45
    # =========================================================================
    
    print("\n" + "-"*80)
    print("🚀 PHASE 2 - Événements 12:45 UTC")
    print("-"*80)
    
    if len(events_1245) > 0:
        contributions_phase2 = []
        phase2_surprises = []
        phase2_details = []
        
        for idx, event in events_1245.iterrows():
            family = event['family']
            score_base = event['empirical_score']
            surprise = event['surprise']
            surprise_pct = event['surprise_pct']
            
            # 1. Ajuster score
            score_adjusted = calculate_adjusted_empirical_score(score_base, surprise_pct)
            
            # 2. Calculer impact brut
            num_events = len(events_1245)
            if num_events >= 2:
                impact_brut = -10.47 + 0.477 * score_adjusted
            else:
                impact_brut = -7.08 + 0.419 * score_adjusted
            
            # 3. Direction
            direction = get_event_direction(family, surprise)
            
            contribution = impact_brut * direction
            contributions_phase2.append(contribution)
            phase2_surprises.append(abs(surprise_pct))
            
            phase2_details.append({
                'family': family,
                'score_base': score_base,
                'surprise_pct': surprise_pct,
                'score_adjusted': score_adjusted,
                'impact_brut': impact_brut,
                'direction': 'UP' if direction > 0 else 'DOWN',
                'contribution': contribution
            })
            
            print(f"   {family:30s} | Score: {score_base:5.1f} → {score_adjusted:5.1f} | "
                  f"Surprise: {surprise_pct:5.1f}% | Contrib: {contribution:+6.1f} pips")
        
        # Somme vectorielle Phase 2
        impact_phase2_brut = sum(contributions_phase2)
        
        # Amplification
        max_surprise_pct_2 = max(phase2_surprises) if phase2_surprises else 0
        
        if max_surprise_pct_2 <= 5:
            amplification_2 = 1.0
        elif max_surprise_pct_2 <= 15:
            amplification_2 = 1.0 + (max_surprise_pct_2 - 5) / 10 * 1.5
        else:
            amplification_2 = 2.5
        
        impact_phase2 = abs(impact_phase2_brut) * amplification_2 * 0.758
        direction_phase2 = 1 if impact_phase2_brut >= 0 else -1
        
        print(f"\n   📊 Somme vectorielle : {impact_phase2_brut:+.1f} pips")
        print(f"   📊 Surprise max      : {max_surprise_pct_2:.1f}%")
        print(f"   📊 Amplification     : {amplification_2:.2f}x")
        print(f"   📊 IMPACT PHASE 2    : {impact_phase2:+.1f} pips ({['DOWN', 'UP'][direction_phase2 > 0]})")
        
        # TTR Phase 2
        latency_median_2 = events_1245['latency_median'].mean() / 60
        ttr_phase2 = calculate_ttr_c(latency_median_2, max_surprise_pct_2)
        
        print(f"   ⏱️  Latence médiane   : {latency_median_2:.1f} min")
        print(f"   ⏱️  TTR PHASE 2       : {ttr_phase2:.1f} min")
    else:
        impact_phase2 = 0
        direction_phase2 = 1
        ttr_phase2 = 0
        phase2_details = []
    
    # =========================================================================
    # IMPACT TOTAL
    # =========================================================================
    
    print("\n" + "="*80)
    print("📊 RÉSUMÉ GLOBAL")
    print("="*80)
    
    # Impact net total (vectoriel)
    impact_total = (impact_phase1 * direction_phase1) - pullback_pips + (impact_phase2 * direction_phase2)
    
    print(f"\n   Phase 1 (12:30-12:35) : {impact_phase1 * direction_phase1:+.1f} pips")
    print(f"   Pullback (12:35-12:45): {-pullback_pips:+.1f} pips")
    print(f"   Phase 2 (12:45-13:10) : {impact_phase2 * direction_phase2:+.1f} pips")
    print(f"   " + "-"*50)
    print(f"   IMPACT TOTAL          : {impact_total:+.1f} pips")
    print(f"\n   🎯 Référence MT5      : {REFERENCE_MT5['total_pips']:+.1f} pips")
    print(f"   📊 Écart              : {abs(impact_total - REFERENCE_MT5['total_pips']):.1f} pips")
    
    # Retourner toutes les métriques
    return {
        'phase1': {
            'impact': impact_phase1 * direction_phase1,
            'impact_abs': impact_phase1,
            'direction': direction_phase1,
            'ttr': ttr_phase1,
            'latency': latency_median,
            'surprise_max': max_surprise_pct,
            'amplification': amplification,
            'details': phase1_details
        },
        'pullback': {
            'pips': pullback_pips,
            'minutes_since_peak': minutes_since_peak
        },
        'phase2': {
            'impact': impact_phase2 * direction_phase2,
            'impact_abs': impact_phase2,
            'direction': direction_phase2,
            'ttr': ttr_phase2 if len(events_1245) > 0 else 0,
            'details': phase2_details
        },
        'total': {
            'impact': impact_total,
            'reference_mt5': REFERENCE_MT5['total_pips'],
            'error': abs(impact_total - REFERENCE_MT5['total_pips'])
        }
    }

# =============================================================================
# GRAPHIQUE CHANDELIERS
# =============================================================================

def plot_candlestick_chart(prices_df, metrics):
    """Génère graphique chandeliers avec annotations."""
    print("\n" + "="*80)
    print("📈 GÉNÉRATION GRAPHIQUE CHANDELIERS")
    print("="*80)
    
    if prices_df.empty:
        print("❌ Pas de données de prix disponibles")
        return
    
    # Créer figure
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Style chandeliers
    mc = mpf.make_marketcolors(
        up='green', down='red',
        edge='inherit',
        wick='inherit',
        volume='in'
    )
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', gridcolor='lightgray')
    
    # Tracer chandeliers
    mpf.plot(
        prices_df,
        type='candle',
        style=s,
        ax=ax,
        volume=False,
        show_nontrading=False
    )
    
    # Annoter événements clés
    event_times = {
        '12:30': 'Phase 1 Start',
        '12:35': 'TTR Phase 1',
        '12:45': 'Phase 2 Start',
        '13:10': 'Stabilisation'
    }
    
    for time_str, label in event_times.items():
        time_obj = pd.Timestamp(f'{EVENT_DATE} {time_str}:00')
        if time_obj in prices_df.index:
            idx = prices_df.index.get_loc(time_obj)
            price = prices_df.loc[time_obj, 'close']
            ax.axvline(x=idx, color='blue', linestyle='--', alpha=0.5, linewidth=1)
            ax.text(idx, price, f' {label}', rotation=90, va='bottom', fontsize=8)
    
    # Titre et labels
    ax.set_title(
        f'EUR/USD - 11 Septembre 2025 - Planificateur V2 Validation\n'
        f'Impact Total Prédit: {metrics["total"]["impact"]:+.1f} pips | '
        f'MT5: {metrics["total"]["reference_mt5"]:+.1f} pips | '
        f'Écart: {metrics["total"]["error"]:.1f} pips',
        fontsize=14,
        fontweight='bold'
    )
    ax.set_xlabel('Temps (UTC)', fontsize=12)
    ax.set_ylabel('Prix EUR/USD', fontsize=12)
    
    # Grille
    ax.grid(True, alpha=0.3)
    
    # Sauvegarder
    output_path = project_root / 'planificateur_11sept_v2_validation.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ Graphique sauvegardé : {output_path}")
    
    plt.close()

# =============================================================================
# EXPORT CSV
# =============================================================================

def export_results_to_csv(metrics):
    """Exporte tous les résultats en CSV."""
    print("\n" + "="*80)
    print("💾 EXPORT CSV")
    print("="*80)
    
    # Phase 1
    df_phase1 = pd.DataFrame(metrics['phase1']['details'])
    df_phase1.to_csv(
        project_root / 'planificateur_11sept_phase1_details.csv',
        index=False
    )
    print("✅ Phase 1 détails exportés")
    
    # Phase 2
    if metrics['phase2']['details']:
        df_phase2 = pd.DataFrame(metrics['phase2']['details'])
        df_phase2.to_csv(
            project_root / 'planificateur_11sept_phase2_details.csv',
            index=False
        )
        print("✅ Phase 2 détails exportés")
    
    # Résumé global
    summary = {
        'Métrique': [
            'Phase 1 Impact (pips)',
            'Phase 1 TTR (min)',
            'Pullback (pips)',
            'Phase 2 Impact (pips)',
            'Impact Total Prédit (pips)',
            'Impact Total MT5 (pips)',
            'Écart (pips)',
            'Précision (%)'
        ],
        'Valeur': [
            metrics['phase1']['impact'],
            metrics['phase1']['ttr'],
            metrics['pullback']['pips'],
            metrics['phase2']['impact'],
            metrics['total']['impact'],
            metrics['total']['reference_mt5'],
            metrics['total']['error'],
            100 - (metrics['total']['error'] / metrics['total']['reference_mt5'] * 100)
        ]
    }
    
    df_summary = pd.DataFrame(summary)
    df_summary.to_csv(
        project_root / 'planificateur_11sept_summary.csv',
        index=False
    )
    print("✅ Résumé global exporté")

# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "="*80)
    print("🚀 PLANIFICATEUR 11 SEPTEMBRE 2025 - VERSION 2 VALIDATION")
    print("="*80)
    print(f"\n📅 Date : {EVENT_DATE}")
    print(f"⏰ Événements : {EVENT_TIME_UTC_1} et {EVENT_TIME_UTC_2} UTC")
    print(f"🎯 Objectif : Validation graphique + métriques complètes")
    
    # 1. Charger données
    print("\n📂 CHARGEMENT DONNÉES...")
    events_df = load_events_11sept()
    prices_df = load_prices_11sept()
    
    # 2. Calculer phases
    metrics = calculate_phases_with_validated_formulas(events_df)
    
    # 3. Générer graphique
    plot_candlestick_chart(prices_df, metrics)
    
    # 4. Export CSV
    export_results_to_csv(metrics)
    
    print("\n" + "="*80)
    print("✅ VALIDATION TERMINÉE")
    print("="*80)
    print("\n📁 Fichiers générés :")
    print("   - planificateur_11sept_v2_validation.png")
    print("   - planificateur_11sept_phase1_details.csv")
    print("   - planificateur_11sept_phase2_details.csv")
    print("   - planificateur_11sept_summary.csv")
    print("\n🎯 Prochaine étape : Validation visuelle avec MT5")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
