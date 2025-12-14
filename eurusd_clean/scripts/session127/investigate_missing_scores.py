"""
SESSION 127 - Investigation Scores Manquants

Objectif : Analyser 24 scores manquants du CSV pour vérifier s'ils existent
          dans DB sous autres noms ou s'ils nécessitent recalcul

Auteur : André Valentin
Date : 11 novembre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path
from difflib import get_close_matches

# 24 scores manquants (du rapport audit)
MISSING_SCORES = [
    ('u_6_unemployment_rate', 63.96),
    ('gross_domestic_product', 39.70),
    ('8_week_bill_auction', 15.26),
    ('4_week_bill_auction', 15.21),
    ('10_year_note_auction', 15.10),
    ('30_year_bond_auction', 14.93),
    ('7_year_note_auction', 14.76),
    ('15_year_mortgage_rate', 14.05),
    ('30_year_mortgage_rate', 13.84),
    ('17_week_bill_auction', 13.79),
    ('6_month_bill_auction', 13.39),
    ('52_week_bill_auction', 13.35),
    ('3_month_bill_auction', 13.25),
    ('20_year_bond_auction', 11.71),
    ('2_year_frn_auction', 11.55),
    ('5_year_tips_auction', 11.06),
    ('42_day_bill_auction', 11.06),
    ('2_year_note_auction', 11.02),
    ('m2_money_supply', 10.99),
    ('3_year_note_auction', 10.97),
    ('5_year_note_auction', 10.94),
    ('10_year_tips_auction', 10.23),
    ('30_year_tips_auction', 7.25),
    ('international_monetary_market_(imm)_date', 5.86),
]

DB_PATH = Path(__file__).parents[2] / 'data' / 'warehouse.duckdb'


def normalize_name(name):
    """Normalise nom pour comparaison"""
    return name.lower().replace('_', ' ').replace('-', ' ').strip()


def search_in_db(event_name_csv, score):
    """Cherche correspondances possibles dans DB"""
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Charger tous event_key uniques USD
        query = """
        SELECT DISTINCT event_key, importance_n, COUNT(*) as count
        FROM events
        WHERE country = 'US'
        GROUP BY event_key, importance_n
        ORDER BY count DESC
        """
        
        df = conn.execute(query).df()
        all_keys = df['event_key'].tolist()
        
        # Normaliser
        normalized_search = normalize_name(event_name_csv)
        
        # 1. Recherche exacte
        exact_matches = [k for k in all_keys if normalize_name(k) == normalized_search]
        
        # 2. Recherche contient
        contains_matches = [k for k in all_keys if normalized_search in normalize_name(k) or normalize_name(k) in normalized_search]
        
        # 3. Recherche similarité (difflib)
        similar_matches = get_close_matches(normalized_search, [normalize_name(k) for k in all_keys], n=5, cutoff=0.6)
        similar_keys = [k for k in all_keys if normalize_name(k) in similar_matches]
        
        # Combiner résultats
        all_candidates = list(set(exact_matches + contains_matches + similar_keys))
        
        # Récupérer info complètes
        results = []
        for key in all_candidates[:10]:  # Limiter à 10 premiers
            row = df[df['event_key'] == key].iloc[0]
            results.append({
                'event_key': key,
                'importance_n': int(row['importance_n']),
                'importance': {1: 'LOW', 2: 'MED', 3: 'HIGH'}[int(row['importance_n'])],
                'count': int(row['count'])
            })
        
        return results
    
    finally:
        conn.close()


def categorize_missing_scores():
    """Catégorise scores manquants"""
    
    print("=" * 80)
    print("SESSION 127 - INVESTIGATION SCORES MANQUANTS")
    print("=" * 80)
    print()
    print(f"Total scores manquants : {len(MISSING_SCORES)}")
    print()
    
    categories = {
        'HIGH_priority': [],  # HIGH importance, doit être trouvé
        'MED_recalculate': [],  # Potentiel recalcul nécessaire
        'LOW_ignore': [],  # LOW importance, ignorer Session 127
        'FOUND_variant': [],  # Trouvé sous autre nom
    }
    
    for event_name, score in MISSING_SCORES:
        print(f"Recherche : {event_name} (score={score:.2f})")
        print("─" * 80)
        
        # Chercher dans DB
        matches = search_in_db(event_name, score)
        
        if matches:
            print(f"  ✅ {len(matches)} correspondances trouvées :")
            for m in matches[:5]:
                print(f"     → {m['event_key']} [{m['importance']}] (n={m['count']})")
            
            # Catégoriser comme trouvé
            categories['FOUND_variant'].append({
                'event_name': event_name,
                'score': score,
                'matches': matches[:3]
            })
        else:
            print(f"  ❌ Aucune correspondance DB")
            
            # Catégoriser selon score (proxy importance)
            if score > 40:
                categories['HIGH_priority'].append((event_name, score))
                print(f"     → CATÉGORIE : HIGH_priority (recalcul nécessaire)")
            elif score > 20:
                categories['MED_recalculate'].append((event_name, score))
                print(f"     → CATÉGORIE : MED_recalculate (considérer)")
            else:
                categories['LOW_ignore'].append((event_name, score))
                print(f"     → CATÉGORIE : LOW_ignore (ignorer S127)")
        
        print()
    
    return categories


def generate_summary_report(categories):
    """Génère rapport synthèse"""
    
    print()
    print("=" * 80)
    print("SYNTHÈSE CATÉGORISATION")
    print("=" * 80)
    print()
    
    print(f"✅ FOUND_variant (trouvés DB) : {len(categories['FOUND_variant'])}")
    if categories['FOUND_variant']:
        for item in categories['FOUND_variant'][:5]:
            print(f"   - {item['event_name']} → {item['matches'][0]['event_key']}")
    print()
    
    print(f"🔴 HIGH_priority (recalcul urgent) : {len(categories['HIGH_priority'])}")
    for name, score in categories['HIGH_priority']:
        print(f"   - {name} (score={score:.2f})")
    print()
    
    print(f"🟡 MED_recalculate (considérer) : {len(categories['MED_recalculate'])}")
    for name, score in categories['MED_recalculate'][:5]:
        print(f"   - {name} (score={score:.2f})")
    print()
    
    print(f"⚪ LOW_ignore (ignorer S127) : {len(categories['LOW_ignore'])}")
    print(f"   → {len(categories['LOW_ignore'])} scores LOW importance")
    print()
    
    # Recommandations
    print("=" * 80)
    print("RECOMMANDATIONS SESSION 127")
    print("=" * 80)
    print()
    
    if categories['HIGH_priority']:
        print("⚠️  ACTION REQUISE :")
        print(f"   {len(categories['HIGH_priority'])} scores HIGH manquants nécessitent recalcul")
        print()
    
    if categories['FOUND_variant']:
        print("✅ SUCCÈS PARTIEL :")
        print(f"   {len(categories['FOUND_variant'])} scores trouvés sous variantes")
        print("   → Ajouter au mapping rules")
        print()
    
    total_low = len(categories['LOW_ignore'])
    print(f"📊 IMPACT SESSION 127 :")
    print(f"   Scores à traiter : {len(categories['HIGH_priority']) + len(categories['MED_recalculate'])}")
    print(f"   Scores LOW ignorés : {total_low}")
    print()


def main():
    categories = categorize_missing_scores()
    generate_summary_report(categories)
    
    print("=" * 80)
    print("✅ PHASE 1.2 COMPLÉTÉE - Investigation scores manquants")
    print("=" * 80)


if __name__ == "__main__":
    main()
