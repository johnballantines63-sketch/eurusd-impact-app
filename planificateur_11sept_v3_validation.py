"""
PLANIFICATEUR 11 SEPTEMBRE 2025 - V3 VALIDATION CORRECTE

SOLUTION AU BUG DOUBLE AJUSTEMENT (Session 58-59):

PROBLÈME IDENTIFIÉ:
- validation_events contient scores DÉJÀ AJUSTÉS (85.0)
- planificateur_11sept_FINAL.py les ré-ajustait → 161.5 (double ajustement)
- Résultat: 152 pips au lieu de 57

SOLUTION:
- Utiliser scores validation_events TEL QUELS (comme test_4_formules)
- NE PAS appeler calculate_adjusted_empirical_score()
- Copier logique EXACTE de test_4_formules_11sept.py

Date : 23 octobre 2025 - Session 59
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import math

# Ajouter chemins
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "fx_impact_app"))
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

from config import get_db_path

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
    """
    Détermine direction selon surprise et sentiment.
    Copié EXACTEMENT de test_4_formules_11sept.py
    """
    if abs(surprise) < 0.01:
        return 1
    sentiment = FAMILY_SENTIMENT.get(family, 1)
    return sentiment if surprise > 0 else -sentiment

def load_events_from_validation():
    """
    Charge événements depuis validation_events.
    IDENTIQUE à test_4_formules_11sept.py
    """
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path))
    
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
    """
    Calcule phases EXACTEMENT comme test_4_formules_11sept.py (Formule D).
    
    CORRECTION CRITIQUE:
    - Utilise empirical_score TEL QUEL (déjà ajusté dans validation_events)
    - NE PLUS appeler calculate_adjusted_empirical_score()
    """
    print("\n" + "="*80)
    print("📊 CALCUL DES PHASES - FORMULE D (test_4_formules)")
    print("="*80)
    
    print(f"\n✅ {len(events_df)} événements (validation_events)")
    
    # Afficher tous les événements
    print("\nLISTE DES ÉVÉNEMENTS :")
    print("-"*80)
    for idx, event in events_df.iterrows():
        surprise_pct = event['surprise_pct'] if event['surprise_pct'] is not None else 0.0
        print(f"   {idx+1:2d}. {event['family']:25s} | Score: {event['empirical_score']:5.1f} | "
              f"Surprise: {surprise_pct:5.1f}%")
    
    # === PHASE 1 : TOUS LES ÉVÉNEMENTS ===
    print("\n" + "-"*80)
    print("🚀 PHASE 1 - Calcul impact (Formule D)")
    print("-"*80)
    
    contributions = []
    surprises = []
    num_events = len(events_df)
    
    for _, event in events_df.iterrows():
        family = event['family']
        score = event['empirical_score']  # ← TEL QUEL (déjà ajusté)
        surprise = event['surprise']
        surprise_pct = event['surprise_pct'] if event['surprise_pct'] is not None else 0.0
        
        # Impact brut (formule régression C - EXACTEMENT comme test_4_formules)
        if num_events >= 2:
            impact_brut = -10.47 + 0.477 * score
        else:
            impact_brut = -7.08 + 0.419 * score
        
        # Direction
        direction = get_event_direction(family, surprise)
        contribution = impact_brut * direction
        
        contributions.append(contribution)
        surprises.append(abs(surprise_pct))
        
        print(f"   {family:25s} | Score: {score:5.1f} | "
              f"Surp: {surprise_pct:5.1f}% | Contrib: {contribution:+6.1f} pips")
    
    # Somme vectorielle
    impact_brut_total = sum(contributions)
    max_surprise = max(surprises) if surprises else 0
    
    # Amplification (EXACTEMENT comme test_4_formules)
    if max_surprise <= 5:
        amplification = 1.0
    elif max_surprise <= 15:
        amplification = 1.0 + (max_surprise - 5) / 10 * 1.5
    else:
        amplification = 2.5
    
    impact_amplifie = abs(impact_brut_total) * amplification
    impact_final = impact_amplifie * 0.758
    direction_final = 1 if impact_brut_total >= 0 else -1
    
    impact_phase1 = impact_final * direction_final
    
    print(f"\n   Impact brut       : {impact_brut_total:+6.1f} pips")
    print(f"   Surprise max      : {max_surprise:5.1f}%")
    print(f"   Amplification     : {amplification:.2f}x")
    print(f"   Impact amplifié   : {impact_amplifie:6.1f} pips")
    print(f"   Facteur 0.758     : × 0.758")
    print(f"   Impact final      : {impact_final:6.1f} pips")
    print(f"   Direction         : {'UP' if direction_final > 0 else 'DOWN'}")
    print(f"\n   ✅ PHASE 1 TOTAL  : {impact_phase1:+6.1f} pips")
    
    # === COMPARAISON MT5 ===
    print("\n" + "="*80)
    print("📊 COMPARAISON MT5")
    print("="*80)
    
    impact_reel = REFERENCE_MT5['total_pips']
    erreur = impact_phase1 - impact_reel
    mae = abs(erreur)
    precision = (1 - mae / abs(impact_reel)) * 100
    
    print(f"\n   Impact prédit     : {impact_phase1:+6.1f} pips")
    print(f"   Impact réel MT5   : {impact_reel:+6.1f} pips")
    print(f"   Erreur            : {erreur:+6.1f} pips")
    print(f"   MAE               : {mae:6.1f} pips")
    print(f"   Précision         : {precision:5.1f}%")
    
    if mae < 2:
        print(f"\n   ✅ EXCELLENT (MAE < 2 pips)")
    elif mae < 5:
        print(f"\n   ✅ BON (MAE < 5 pips)")
    elif mae < 10:
        print(f"\n   ⚠️  ACCEPTABLE (MAE < 10 pips)")
    else:
        print(f"\n   ❌ PROBLÈME (MAE > 10 pips)")
    
    return {
        'phase1_pips': impact_phase1,
        'impact_brut': impact_brut_total,
        'amplification': amplification,
        'max_surprise': max_surprise,
        'contributions': contributions,
        'erreur': erreur,
        'mae': mae,
        'precision': precision
    }

def main():
    print("\n" + "="*80)
    print("🧪 PLANIFICATEUR 11 SEPTEMBRE 2025 - V3 VALIDATION")
    print("="*80)
    print("\n✅ CORRECTION: Utilise scores validation_events TEL QUELS")
    print("   (comme test_4_formules_11sept.py qui donne 57 pips)")
    
    # Charger événements
    print("\n📂 CHARGEMENT DONNÉES...")
    events_df = load_events_from_validation()
    
    if events_df.empty:
        print("❌ Aucun événement trouvé")
        return
    
    # Calculer phases
    results = calculate_phases(events_df)
    
    # Résumé final
    print("\n" + "="*80)
    print("🎯 RÉSUMÉ FINAL")
    print("="*80)
    
    print(f"\n   Impact prédit : {results['phase1_pips']:+.1f} pips")
    print(f"   Impact réel   : {REFERENCE_MT5['total_pips']:+.1f} pips")
    print(f"   MAE           : {results['mae']:.1f} pips")
    print(f"   Précision     : {results['precision']:.1f}%")
    
    if results['mae'] < 10:
        print(f"\n   ✅ VALIDATION RÉUSSIE !")
        print(f"   🎯 Bug double ajustement CORRIGÉ !")
    else:
        print(f"\n   ⚠️  À ANALYSER...")
    
    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
