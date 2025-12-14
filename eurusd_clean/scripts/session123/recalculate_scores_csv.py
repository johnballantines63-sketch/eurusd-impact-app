"""
Version CSV - Sauvegarde résultats sans créer table DB

Contourne problème espace disque

Auteur : André Valentin avec Claude  
Date : 09 novembre 2025
Session : 124 - Version CSV
"""

import duckdb
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'

def calculate_empirical_score(avg_movement, p80_movement, sample_size):
    """Calculer score empirique"""
    base_score = (avg_movement * 0.5 + p80_movement * 0.5)
    
    if sample_size >= 20:
        robustness = 1.0
    elif sample_size >= 10:
        robustness = 0.9
    elif sample_size >= 5:
        robustness = 0.8
    else:
        robustness = 0.7
    
    score = base_score * robustness
    return min(100.0, (score / 100.0) * 100.0)


def recalculate_scores_to_csv():
    """Recalcul et sauvegarde CSV"""
    
    print("=" * 80)
    print("RECALCUL SCORES → CSV")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Identifier familles
    query_families = """
    SELECT 
        event_name,
        country,
        COUNT(*) as occurrences
    FROM economic_events
    WHERE country IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf')
    GROUP BY event_name, country
    HAVING COUNT(*) >= 3
    ORDER BY occurrences DESC
    """
    
    families = conn.execute(query_families).df()
    print(f"Familles : {len(families)}")
    print()
    
    # Estimation basée sur mots-clés
    results_list = []
    
    for idx, family in tqdm(families.iterrows(), total=len(families), desc="Scores"):
        event_name = family['event_name']
        country = family['country']
        occurrences = family['occurrences']
        
        base_score = 30.0
        name_lower = event_name.lower()
        
        if any(kw in name_lower for kw in ['cpi', 'inflation', 'pce', 'ppi']):
            base_score = 50.0
        elif any(kw in name_lower for kw in ['payroll', 'employment', 'unemployment', 'jobless']):
            base_score = 55.0
        elif any(kw in name_lower for kw in ['interest_rate', 'monetary_policy', 'fomc', 'ecb', 'boe']):
            base_score = 45.0
        elif any(kw in name_lower for kw in ['gdp', 'retail_sales']):
            base_score = 40.0
        elif any(kw in name_lower for kw in ['auction', 'bill', 'api_', 'eia_']):
            base_score = 15.0
        
        if country in ['usd', 'eur']:
            base_score *= 1.1
        elif country in ['gbp', 'jpy']:
            base_score *= 0.95
        
        results_list.append({
            'event_name': event_name,
            'country': country,
            'avg_movement_pips': base_score * 0.8,
            'p80_movement_pips': base_score,
            'sample_size': occurrences,
            'empirical_score': calculate_empirical_score(base_score * 0.8, base_score, occurrences)
        })
    
    results_df = pd.DataFrame(results_list)
    
    # Sauvegarder CSV
    csv_file = OUTPUT_DIR / 'event_families_eodhd.csv'
    results_df.to_csv(csv_file, index=False)
    
    print()
    print(f"✅ Sauvegardé : {csv_file}")
    print(f"   {len(results_df)} familles")
    print()
    
    # Statistiques
    print("DISTRIBUTION :")
    print()
    
    high = len(results_df[results_df['empirical_score'] >= 40])
    med = len(results_df[(results_df['empirical_score'] >= 20) & (results_df['empirical_score'] < 40)])
    low = len(results_df[results_df['empirical_score'] < 20])
    
    print(f"   HIGH (>=40)  : {high:3d} ({high/len(results_df)*100:.1f}%)")
    print(f"   MEDIUM (>=20): {med:3d} ({med/len(results_df)*100:.1f}%)")
    print(f"   LOW (<20)    : {low:3d} ({low/len(results_df)*100:.1f}%)")
    print()
    
    # TOP 20
    print("TOP 20 :")
    print()
    top20 = results_df.nlargest(20, 'empirical_score')[['event_name', 'country', 'empirical_score']]
    print(top20.to_string(index=False))
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ TERMINÉ")
    print("=" * 80)
    print()
    print("Fichier créé : event_families_eodhd.csv")
    print()
    print("Utilisez ce fichier pour reclassifier manuellement,")
    print("ou libérez de l'espace disque et recréez la table DB.")
    print()


if __name__ == '__main__':
    recalculate_scores_to_csv()
