"""
VALIDATION ÉTENDUE - Session 90
Tester coefficient 0.55 sur 10-15 dates diversifiées

Objectifs :
- MAE global < 30 pips sur ≥10 dates
- MAE NFP < 40 pips sur ≥3 dates NFP
- 0 cas > 80 pips (outliers)
- Comprendre comportement par type événement
"""

import duckdb
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ajouter path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent / "session89"))
from surprise_utils import calculate_surprise_robust

# Import formules validées
sys.path.insert(0, "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src")
from formulas_validated import calculate_amplification_extended

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

print("="*100)
print("🔬 VALIDATION ÉTENDUE - Coefficient 0.55")
print("="*100)

# Dates à tester (sélection diversifiée)
TEST_DATES = [
    # Dates déjà testées Session 89
    ('2025-08-01', 'NFP', 'Déjà testé (0.3 pips)'),
    ('2025-09-17', 'Standard', 'Déjà testé (0.3 pips)'),
    ('2025-09-05', 'NFP', 'PROBLÈME (75.1 pips)'),
    
    # Nouvelles dates à ajouter (exemples - à ajuster selon list_available_dates)
    # Ces dates seront identifiées par le script list_available_dates.py
]

# Fonction test une date
def test_date(date_str, conn):
    """Teste une date et retourne MAE"""
    
    print(f"\n{'='*100}")
    print(f"📅 TEST DATE : {date_str}")
    print(f"{'='*100}")
    
    # 1. Charger événements
    query = """
    SELECT 
        e.event_key,
        e.event_title,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.family,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    events = conn.execute(query, [date_str]).df()
    
    if len(events) == 0:
        print(f"   ⚠️ Aucun événement trouvé")
        return None, None, 0, 0
    
    print(f"   Événements : {len(events)}")
    
    # 2. Calculer surprises
    surprises = []
    for idx, row in events.iterrows():
        surprise = calculate_surprise_robust(
            row['actual'],
            row['estimate'],
            row['forecast'],
            row['previous']
        )
        surprises.append(surprise)
    
    surprise_max = max(surprises) if surprises else 0
    surprise_cumule = sum(surprises)
    
    print(f"   Surprise MAX : {surprise_max:.1f}%")
    print(f"   Surprise cumulée : {surprise_cumule:.1f}%")
    
    # 3. Calculer amplification avec coefficient 0.55
    amplification = calculate_amplification_extended(surprise_max)
    print(f"   Amplification (0.55) : {amplification:.2f}x")
    
    # 4. Calculer impact prédit (formule Session 51)
    # Simplifié : score_moyen × amplification × 0.758 (facteur vectoriel)
    score_moyen = events['empirical_score'].mean()
    
    # Formule D simplifiée (multi-événements)
    impact_brut = -10.47 + 0.477 * score_moyen
    impact_predit = abs(impact_brut) * amplification * 0.758
    
    print(f"   Score moyen : {score_moyen:.1f}")
    print(f"   Impact prédit : {impact_predit:.1f} pips")
    
    # 5. Récupérer impact réel depuis DB (si disponible)
    # Note : Pour validation complète, il faudrait extraire depuis prices_1m
    # Pour l'instant, on retourne les prédictions
    
    # Placeholder pour impact réel (à implémenter avec prices_1m)
    impact_reel = None
    mae = None
    
    print(f"   Impact réel : [À mesurer depuis prices_1m]")
    print(f"   MAE : [À calculer]")
    
    return impact_predit, impact_reel, surprise_max, len(events)

# Fonction principale
def main():
    """Exécute validation étendue"""
    
    print("\n📋 DATES À TESTER :")
    print(f"   Total : {len(TEST_DATES)} dates")
    
    # Note importante
    print("\n⚠️ NOTE IMPORTANTE :")
    print("   Ce script nécessite 2 phases :")
    print("   Phase 1 : Exécuter list_available_dates.py → Identifier dates optimales")
    print("   Phase 2 : Ajouter ces dates dans TEST_DATES ci-dessus")
    print("   Phase 3 : Implémenter extraction impact réel depuis prices_1m")
    print("\n   Pour l'instant, ce script calcule UNIQUEMENT les prédictions.")
    print("   L'impact réel doit être mesuré via script dédié (voir Session 86).")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    results = []
    
    for date_str, event_type, note in TEST_DATES:
        impact_pred, impact_real, surprise, n_events = test_date(date_str, conn)
        
        results.append({
            'date': date_str,
            'type': event_type,
            'note': note,
            'n_events': n_events,
            'surprise_max': surprise,
            'impact_predit': impact_pred,
            'impact_reel': impact_real,
            'mae': None  # À calculer quand impact_reel disponible
        })
    
    conn.close()
    
    # Créer DataFrame résultats
    df_results = pd.DataFrame(results)
    
    # Sauvegarder
    output_path = Path(__file__).parent / "validation_results_session90.csv"
    df_results.to_csv(output_path, index=False)
    
    print("\n" + "="*100)
    print("📊 RÉSUMÉ VALIDATION :")
    print("="*100)
    
    print(f"\n   Dates testées : {len(results)}")
    print(f"   Avec prédictions : {df_results['impact_predit'].notna().sum()}")
    print(f"   Avec impacts réels : {df_results['impact_reel'].notna().sum()}")
    
    if df_results['impact_reel'].notna().sum() > 0:
        mae_global = df_results['mae'].mean()
        print(f"\n   ✅ MAE GLOBAL : {mae_global:.1f} pips")
        
        # Analyse par type
        for event_type in df_results['type'].unique():
            subset = df_results[df_results['type'] == event_type]
            mae_type = subset['mae'].mean()
            print(f"   MAE {event_type:<12} : {mae_type:.1f} pips ({len(subset)} dates)")
    else:
        print(f"\n   ⚠️ Impacts réels non disponibles")
        print(f"   → Exécuter script mesure impact réel (prices_1m)")
    
    print(f"\n💾 Résultats sauvegardés : {output_path}")
    
    print("\n" + "="*100)
    print("✅ Validation étendue terminée")
    print("="*100)
    
    print("\n🎯 PROCHAINES ÉTAPES :")
    print("   1. Exécuter list_available_dates.py → Identifier 10-15 dates optimales")
    print("   2. Ajouter ces dates dans TEST_DATES")
    print("   3. Implémenter extraction impact réel depuis prices_1m")
    print("   4. Relancer ce script pour calcul MAE complet")
    print("   5. Analyser résultats et décider intégration production")

if __name__ == "__main__":
    main()
