"""
PLANIFICATEUR 11 SEPTEMBRE 2025 - V4 EVENTS + EVENT_FAMILIES

OPTION A : Utiliser events + event_families (comme Session 51 originale)

APPROCHE CORRECTE:
1. Charger events + event_families (scores BRUTS de la famille)
2. Calculer surprise pour CHAQUE événement individuel
3. Ajuster score selon surprise INDIVIDUELLE avec calculate_adjusted_empirical_score()
4. Appliquer Formule D complète

POURQUOI validation_events ne fonctionne pas:
- Tous les scores à 85.0 (scores pré-ajustés de manière incorrecte)
- Pas de variation selon les surprises individuelles
- Créée après Session 51 et mal remplie

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
from formulas_validated import calculate_adjusted_empirical_score

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

def load_events_from_events_and_families():
    """
    Charge événements depuis events + event_families.
    Approche originale Session 51.
    """
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path))
    
    # Query originale : events + event_families
    query = f"""
    SELECT 
        e.ts_utc,
        e.event_key,
        e.event_title,
        COALESCE(e.label, ef.family) as family,
        e.actual,
        e.forecast,
        e.estimate,
        ef.empirical_score as base_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{EVENT_DATE}'
        AND e.country = 'US'
        AND e.actual IS NOT NULL
        AND ef.empirical_score IS NOT NULL
    ORDER BY e.ts_utc, e.event_key
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    if not df.empty:
        df['ts_utc'] = pd.to_datetime(df['ts_utc'])
        
        # Calculer surprise pour CHAQUE événement
        df['surprise'] = df['actual'] - df['forecast']
        
        # Calculer surprise_pct
        df['surprise_pct'] = df.apply(
            lambda row: (row['surprise'] / row['forecast'] * 100) if row['forecast'] != 0 else 0,
            axis=1
        )
        
        # Ajuster score selon surprise INDIVIDUELLE
        df['adjusted_score'] = df.apply(
            lambda row: calculate_adjusted_empirical_score(row['base_score'], row['surprise_pct']),
            axis=1
        )
    
    return df

def calculate_phases(events_df):
    """
    Calcule phases avec Formule D.
    Utilise scores AJUSTÉS individuellement pour chaque événement.
    """
    print("\n" + "="*80)
    print("📊 CALCUL DES PHASES - FORMULE D (events + event_families)")
    print("="*80)
    
    print(f"\n✅ {len(events_df)} événements (events + event_families)")
    
    # Afficher tous les événements
    print("\nLISTE DES ÉVÉNEMENTS :")
    print("-"*80)
    print(f"{'#':<3} {'Famille':<25} {'Base':>6} {'Surp%':>7} {'Ajusté':>7}")
    print("-"*80)
    
    for idx, event in events_df.iterrows():
        print(f"{idx+1:2d}. {event['family']:25s} | "
              f"{event['base_score']:5.1f} → {event['surprise_pct']:6.1f}% → {event['adjusted_score']:6.1f}")
    
    # === PHASE 1 : FORMULE D ===
    print("\n" + "-"*80)
    print("🚀 PHASE 1 - Calcul impact (Formule D)")
    print("-"*80)
    
    contributions = []
    surprises = []
    num_events = len(events_df)
    
    for _, event in events_df.iterrows():
        family = event['family']
        score_adjusted = event['adjusted_score']  # ← Score ajusté individuellement
        surprise = event['surprise']
        surprise_pct = event['surprise_pct']
        
        # Impact brut (formule régression C)
        if num_events >= 2:
            impact_brut = -10.47 + 0.477 * score_adjusted
        else:
            impact_brut = -7.08 + 0.419 * score_adjusted
        
        # Direction avec sentiment
        direction = get_event_direction(family, surprise)
        contribution = impact_brut * direction
        
        contributions.append(contribution)
        surprises.append(abs(surprise_pct))
        
        print(f"   {family:25s} | Score: {score_adjusted:6.1f} | "
              f"Surp: {surprise_pct:6.1f}% | Contrib: {contribution:+7.1f} pips")
    
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
    
    print(f"\n   Impact brut       : {impact_brut_total:+7.1f} pips")
    print(f"   Surprise max      : {max_surprise:6.1f}%")
    print(f"   Amplification     : {amplification:.2f}x")
    print(f"   Impact amplifié   : {impact_amplifie:7.1f} pips")
    print(f"   Facteur 0.758     : × 0.758")
    print(f"   Impact final      : {impact_final:7.1f} pips")
    print(f"   Direction         : {'UP' if direction_final > 0 else 'DOWN'}")
    print(f"\n   ✅ PHASE 1 TOTAL  : {impact_phase1:+7.1f} pips")
    
    # === COMPARAISON MT5 ===
    print("\n" + "="*80)
    print("📊 COMPARAISON MT5")
    print("="*80)
    
    impact_reel = REFERENCE_MT5['total_pips']
    erreur = impact_phase1 - impact_reel
    mae = abs(erreur)
    precision = (1 - mae / abs(impact_reel)) * 100 if impact_reel != 0 else 0
    
    print(f"\n   Impact prédit     : {impact_phase1:+7.1f} pips")
    print(f"   Impact réel MT5   : {impact_reel:+7.1f} pips")
    print(f"   Erreur            : {erreur:+7.1f} pips")
    print(f"   MAE               : {mae:7.1f} pips")
    print(f"   Précision         : {precision:6.1f}%")
    
    if mae < 2:
        print(f"\n   ✅ EXCELLENT (MAE < 2 pips)")
        status = "EXCELLENT"
    elif mae < 5:
        print(f"\n   ✅ BON (MAE < 5 pips)")
        status = "BON"
    elif mae < 10:
        print(f"\n   ⚠️  ACCEPTABLE (MAE < 10 pips)")
        status = "ACCEPTABLE"
    else:
        print(f"\n   ❌ PROBLÈME (MAE > 10 pips)")
        status = "PROBLEME"
    
    return {
        'phase1_pips': impact_phase1,
        'impact_brut': impact_brut_total,
        'amplification': amplification,
        'max_surprise': max_surprise,
        'contributions': contributions,
        'erreur': erreur,
        'mae': mae,
        'precision': precision,
        'status': status
    }

def main():
    print("\n" + "="*80)
    print("🧪 PLANIFICATEUR 11 SEPTEMBRE 2025 - V4 OPTION A")
    print("="*80)
    print("\n✅ OPTION A: events + event_families (scores bruts + ajustement individuel)")
    print("   Comme Session 51 originale")
    
    # Charger événements
    print("\n📂 CHARGEMENT DONNÉES...")
    events_df = load_events_from_events_and_families()
    
    if events_df.empty:
        print("❌ Aucun événement trouvé")
        return
    
    print(f"✅ {len(events_df)} événements chargés depuis events + event_families")
    
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
    print(f"   Status        : {results['status']}")
    
    if results['mae'] < 10:
        print(f"\n   ✅ VALIDATION RÉUSSIE !")
        print(f"   🎯 Option A fonctionne correctement !")
        print(f"\n   💡 Leçon : validation_events est mal remplie")
        print(f"      → Toujours utiliser events + event_families")
        print(f"      → Ajuster scores individuellement selon surprise")
    else:
        print(f"\n   ⚠️  À ANALYSER...")
    
    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
