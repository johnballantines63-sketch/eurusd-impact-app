"""
PLANIFICATEUR 11 SEPTEMBRE 2025 - VERSION CORRIGÉE

Correction : Les événements sont à 14:30 Berne (pas 12:30 UTC) dans la DB

Date : 23 octobre 2025 - Session 58
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

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

# Configuration
EVENT_DATE = "2025-09-11"
REFERENCE_MT5 = {
    'total_pips': 56.2,
    'phase1_pips': 37.4,
    'pullback_pips': 27.1
}

# Sentiment familles
FAMILY_SENTIMENT = {
    'CPI': 1, 'Jobless_Claims': -1, 'Real_Earnings': 1,
    'Trade_Balance': 1, 'Monthly_Budget_Statement': 1,
    'Other': 1
}

def get_event_direction(family: str, surprise: float) -> int:
    """Détermine direction selon surprise et sentiment."""
    if abs(surprise) < 0.01:
        return 1
    sentiment = FAMILY_SENTIMENT.get(family, 1)
    return sentiment if surprise > 0 else -sentiment

def load_events():
    """Charge événements 11 septembre."""
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path))
    
    query = f"""
    SELECT 
        e.ts_utc as event_datetime,
        COALESCE(e.label, ef.family) as family,
        e.actual,
        e.estimate as forecast,
        ef.empirical_score,
        ef.latency_median
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
    df['event_datetime'] = pd.to_datetime(df['event_datetime'])
    
    return df

def calculate_phases(events_df):
    """Calcule phases avec formules validées."""
    print("\n" + "="*80)
    print("📊 CALCUL DES PHASES")
    print("="*80)
    
    # Groupe par heure
    events_df['hour_minute'] = events_df['event_datetime'].dt.strftime('%H:%M')
    
    # Phase 1 : 14:30 (15 événements)
    phase1_events = events_df[events_df['hour_minute'] == '14:30']
    
    # Phase 2 : 17:30 (2 événements)  
    phase2_events = events_df[events_df['hour_minute'] == '17:30']
    
    print(f"\n📅 Phase 1 (14:30 Berne) : {len(phase1_events)} événements")
    print(f"📅 Phase 2 (17:30 Berne) : {len(phase2_events)} événements")
    
    # === PHASE 1 ===
    print("\n" + "-"*80)
    print("🚀 PHASE 1 - 14:30 Berne")
    print("-"*80)
    
    contributions_p1 = []
    surprises_p1 = []
    
    for _, event in phase1_events.iterrows():
        family = event['family']
        score_base = event['empirical_score']
        surprise = event['surprise']
        surprise_pct = event['surprise_pct']
        
        # Ajuster score
        score_adj = calculate_adjusted_empirical_score(score_base, surprise_pct)
        
        # Impact brut (formule régression)
        num_events = len(phase1_events)
        if num_events >= 2:
            impact_brut = -10.47 + 0.477 * score_adj
        else:
            impact_brut = -7.08 + 0.419 * score_adj
        
        # Direction
        direction = get_event_direction(family, surprise)
        contribution = impact_brut * direction
        
        contributions_p1.append(contribution)
        surprises_p1.append(abs(surprise_pct))
        
        print(f"   {family:25s} | Score: {score_base:5.1f}→{score_adj:5.1f} | "
              f"Surp: {surprise_pct:5.1f}% | Contrib: {contribution:+6.1f} pips")
    
    # Somme vectorielle
    impact_brut_p1 = sum(contributions_p1)
    max_surprise_p1 = max(surprises_p1) if surprises_p1 else 0
    
    # Amplification
    if max_surprise_p1 <= 5:
        amplification = 1.0
    elif max_surprise_p1 <= 15:
        amplification = 1.0 + (max_surprise_p1 - 5) / 10 * 1.5
    else:
        amplification = 2.5
    
    impact_p1 = abs(impact_brut_p1) * amplification * 0.758
    direction_p1 = 1 if impact_brut_p1 >= 0 else -1
    
    print(f"\n   📊 Somme vectorielle : {impact_brut_p1:+.1f} pips")
    print(f"   📊 Surprise max      : {max_surprise_p1:.1f}%")
    print(f"   📊 Amplification     : {amplification:.2f}x")
    print(f"   📊 IMPACT PHASE 1    : {impact_p1 * direction_p1:+.1f} pips")
    
    # TTR
    latency_median = phase1_events['latency_median'].mean() / 60
    ttr_p1 = calculate_ttr_c(latency_median, max_surprise_p1)
    print(f"   ⏱️  TTR              : {ttr_p1:.1f} min")
    
    # === PULLBACK ===
    print("\n" + "-"*80)
    print("📉 PULLBACK")
    print("-"*80)
    
    # Temps entre 14:30 et 17:30 = 180 minutes > 30 min
    # Donc pas de pullback selon formule
    pullback = calculate_pullback_v2(impact_p1, 10, 180)
    print(f"   📊 Pullback (180 min > 30) : {pullback:.1f} pips")
    
    # === PHASE 2 ===
    print("\n" + "-"*80)
    print("🚀 PHASE 2 - 17:30 Berne")
    print("-"*80)
    
    if len(phase2_events) > 0:
        contributions_p2 = []
        surprises_p2 = []
        
        for _, event in phase2_events.iterrows():
            family = event['family']
            score_base = event['empirical_score']
            surprise = event['surprise']
            surprise_pct = event['surprise_pct']
            
            score_adj = calculate_adjusted_empirical_score(score_base, surprise_pct)
            
            num_events = len(phase2_events)
            if num_events >= 2:
                impact_brut = -10.47 + 0.477 * score_adj
            else:
                impact_brut = -7.08 + 0.419 * score_adj
            
            direction = get_event_direction(family, surprise)
            contribution = impact_brut * direction
            
            contributions_p2.append(contribution)
            surprises_p2.append(abs(surprise_pct))
            
            print(f"   {family:25s} | Score: {score_base:5.1f}→{score_adj:5.1f} | "
                  f"Surp: {surprise_pct:5.1f}% | Contrib: {contribution:+6.1f} pips")
        
        impact_brut_p2 = sum(contributions_p2)
        max_surprise_p2 = max(surprises_p2) if surprises_p2 else 0
        
        if max_surprise_p2 <= 5:
            amplification_2 = 1.0
        elif max_surprise_p2 <= 15:
            amplification_2 = 1.0 + (max_surprise_p2 - 5) / 10 * 1.5
        else:
            amplification_2 = 2.5
        
        impact_p2 = abs(impact_brut_p2) * amplification_2 * 0.758
        direction_p2 = 1 if impact_brut_p2 >= 0 else -1
        
        print(f"\n   📊 IMPACT PHASE 2 : {impact_p2 * direction_p2:+.1f} pips")
    else:
        impact_p2 = 0
        direction_p2 = 1
    
    # === TOTAL ===
    print("\n" + "="*80)
    print("📊 RÉSUMÉ GLOBAL")
    print("="*80)
    
    impact_total = (impact_p1 * direction_p1) - pullback + (impact_p2 * direction_p2)
    
    print(f"\n   Phase 1 (14:30)    : {impact_p1 * direction_p1:+.1f} pips")
    print(f"   Pullback           : {-pullback:+.1f} pips")
    print(f"   Phase 2 (17:30)    : {impact_p2 * direction_p2:+.1f} pips")
    print(f"   " + "-"*50)
    print(f"   IMPACT TOTAL       : {impact_total:+.1f} pips")
    print(f"\n   🎯 Référence MT5   : {REFERENCE_MT5['total_pips']:+.1f} pips")
    print(f"   📊 Écart           : {abs(impact_total - REFERENCE_MT5['total_pips']):.1f} pips")
    
    return {
        'phase1_impact': impact_p1 * direction_p1,
        'pullback': pullback,
        'phase2_impact': impact_p2 * direction_p2,
        'total_impact': impact_total,
        'error': abs(impact_total - REFERENCE_MT5['total_pips'])
    }

def main():
    print("\n" + "="*80)
    print("🚀 PLANIFICATEUR 11 SEPTEMBRE 2025 - VERSION CORRIGÉE")
    print("="*80)
    
    events = load_events()
    print(f"\n✅ {len(events)} événements chargés")
    
    metrics = calculate_phases(events)
    
    print("\n" + "="*80)
    print("✅ VALIDATION TERMINÉE")
    print("="*80)

if __name__ == "__main__":
    main()
