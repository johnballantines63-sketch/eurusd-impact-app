"""
PLANIFICATEUR 11 SEPTEMBRE 2025 - VERSION FINALE CORRIGÉE

Utilise validation_events (11 événements dédupliqués) au lieu de events (19 avec doublons)

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
    'CPI': 1, 'CPI_Core': 1, 'Jobless_Claims': -1, 
    'Real_Earnings': 1, 'PPI': 1, 'Inflation_Rate': 1,
    'Trade_Balance': 1, 'Current_Account': 1, 'Other': 1
}

def get_event_direction(family: str, surprise: float) -> int:
    """Détermine direction selon surprise et sentiment."""
    if abs(surprise) < 0.01:
        return 1
    sentiment = FAMILY_SENTIMENT.get(family, 1)
    return sentiment if surprise > 0 else -sentiment

def load_events_from_validation():
    """Charge événements depuis validation_events (dédupliqués)."""
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path))
    
    # Utiliser validation_events comme dans test_4_formules_11sept.py
    query = f"""
    SELECT 
        family,
        actual,
        forecast,
        surprise,
        surprise_pct,
        empirical_score,
        event_datetime
    FROM validation_events
    WHERE event_date = '{EVENT_DATE}'
    ORDER BY event_datetime, family
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    if not df.empty:
        df['event_datetime'] = pd.to_datetime(df['event_datetime'])
    
    return df

def calculate_phases(events_df):
    """Calcule phases avec formules validées."""
    print("\n" + "="*80)
    print("📊 CALCUL DES PHASES - ÉVÉNEMENTS VALIDATION (DÉDUPLIQUÉS)")
    print("="*80)
    
    print(f"\n✅ {len(events_df)} événements (validation_events)")
    
    # Afficher tous les événements
    print("\nLISTE DES ÉVÉNEMENTS :")
    print("-"*80)
    for idx, event in events_df.iterrows():
        print(f"   {idx+1:2d}. {event['family']:25s} | Score: {event['empirical_score']:5.1f} | "
              f"Surprise: {event['surprise_pct']:5.1f}%")
    
    # === PHASE 1 : TOUS LES ÉVÉNEMENTS (simultanés à 14:30) ===
    print("\n" + "-"*80)
    print("🚀 PHASE 1 - Événements simultanés 14:30 Berne")
    print("-"*80)
    
    contributions = []
    surprises = []
    details = []
    
    for _, event in events_df.iterrows():
        family = event['family']
        score_base = event['empirical_score']
        surprise = event['surprise']
        surprise_pct = event['surprise_pct']
        
        # Ajuster score
        score_adj = calculate_adjusted_empirical_score(score_base, surprise_pct)
        
        # Impact brut (formule régression)
        num_events = len(events_df)
        if num_events >= 2:
            impact_brut = -10.47 + 0.477 * score_adj
        else:
            impact_brut = -7.08 + 0.419 * score_adj
        
        # Direction
        direction = get_event_direction(family, surprise)
        contribution = impact_brut * direction
        
        contributions.append(contribution)
        surprises.append(abs(surprise_pct))
        
        details.append({
            'family': family,
            'score_base': score_base,
            'score_adj': score_adj,
            'surprise_pct': surprise_pct,
            'impact_brut': impact_brut,
            'direction': 'UP' if direction > 0 else 'DOWN',
            'contribution': contribution
        })
        
        print(f"   {family:25s} | Score: {score_base:5.1f}→{score_adj:5.1f} | "
              f"Surp: {surprise_pct:5.1f}% | Contrib: {contribution:+6.1f} pips")
    
    # Somme vectorielle
    impact_brut_total = sum(contributions)
    max_surprise = max(surprises) if surprises else 0
    
    # Amplification
    if max_surprise <= 5:
        amplification = 1.0
    elif max_surprise <= 15:
        amplification = 1.0 + (max_surprise - 5) / 10 * 1.5
    else:
        amplification = 2.5
    
    impact_final = abs(impact_brut_total) * amplification * 0.758
    direction_final = 1 if impact_brut_total >= 0 else -1
    
    print(f"\n   📊 Somme vectorielle : {impact_brut_total:+.1f} pips")
    print(f"   📊 Surprise max      : {max_surprise:.1f}%")
    print(f"   📊 Amplification     : {amplification:.2f}x")
    print(f"   📊 Facteur correction: 0.758")
    print(f"   📊 IMPACT FINAL      : {impact_final * direction_final:+.1f} pips")
    
    # TTR
    # Latence moyenne des événements (si disponible en DB)
    # Pour simplifier, on utilise 2.0 min comme dans la validation
    latency_median = 2.0
    ttr = calculate_ttr_c(latency_median, max_surprise)
    print(f"   ⏱️  TTR              : {ttr:.1f} min")
    
    # === RÉSUMÉ ===
    print("\n" + "="*80)
    print("📊 RÉSUMÉ FINAL")
    print("="*80)
    
    print(f"\n   Impact prédit      : {impact_final * direction_final:+.1f} pips")
    print(f"   Impact réel MT5    : {REFERENCE_MT5['total_pips']:+.1f} pips")
    print(f"   " + "-"*50)
    print(f"   Écart (MAE)        : {abs((impact_final * direction_final) - REFERENCE_MT5['total_pips']):.1f} pips")
    
    mae = abs((impact_final * direction_final) - REFERENCE_MT5['total_pips'])
    precision = (1 - mae / REFERENCE_MT5['total_pips']) * 100
    print(f"   Précision          : {precision:.1f}%")
    
    return {
        'impact_predit': impact_final * direction_final,
        'impact_reel': REFERENCE_MT5['total_pips'],
        'mae': mae,
        'precision': precision,
        'details': details
    }

def main():
    print("\n" + "="*80)
    print("🚀 PLANIFICATEUR 11 SEPTEMBRE 2025 - VERSION FINALE")
    print("="*80)
    print("\n📝 Utilise validation_events (événements dédupliqués)")
    
    events = load_events_from_validation()
    
    if events.empty:
        print("\n❌ Aucun événement trouvé dans validation_events !")
        print("   Vérifier que la table existe et contient les données du 11 sept")
        return
    
    metrics = calculate_phases(events)
    
    print("\n" + "="*80)
    print("✅ VALIDATION TERMINÉE")
    print("="*80)
    
    if metrics['mae'] < 5:
        print("\n🎉 EXCELLENT ! MAE < 5 pips")
    elif metrics['mae'] < 10:
        print("\n✅ BON ! MAE < 10 pips")
    else:
        print("\n⚠️  À améliorer - MAE élevée")

if __name__ == "__main__":
    main()
