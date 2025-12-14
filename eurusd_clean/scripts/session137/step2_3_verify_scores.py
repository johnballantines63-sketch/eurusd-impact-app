"""
ÉTAPE 2.3 - VÉRIFICATION SCORES APRÈS CALCUL
Session 137 - Validation complétude scores

Mission :
1. Re-vérifier 694 event_keys matchés
2. Confirmer 100% ont des scores
3. Statistiques finales distribution

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
EVENT_KEYS_FILE = Path(__file__).parent / "step2_0_unique_event_keys.txt"

def strip_variant_suffix(event_key: str) -> str:
    """Strip suffixes variantes"""
    suffixes = ['_qoq_adv', '_mom', '_yoy', '_qoq', ' mom', ' yoy', ' qoq']
    event_key_lower = event_key.lower()
    for suffix in suffixes:
        if event_key_lower.endswith(suffix):
            return event_key[:-len(suffix)]
    return event_key

def verify_scores_completeness():
    """Vérifier complétude scores après calcul"""
    
    print("=" * 80)
    print("ÉTAPE 2.3 - VÉRIFICATION COMPLÉTUDE SCORES")
    print("=" * 80)
    
    # 1. Charger event_keys
    print("\n📊 CHARGEMENT event_keys matchés")
    print("-" * 80)
    
    with open(EVENT_KEYS_FILE, 'r') as f:
        event_keys = [line.strip() for line in f if line.strip()]
    
    print(f"   ✅ {len(event_keys)} event_keys à vérifier")
    
    # 2. Connecter DB
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 3. Vérifier scores (avec strip)
    print("\n📊 VÉRIFICATION SCORES (avec strip_variant_suffix)")
    print("-" * 80)
    
    with_scores = []
    without_scores = []
    scores_dict = {}
    
    for event_key in event_keys:
        # Essayer exact
        query = "SELECT empirical_score, sample_size FROM event_families WHERE event_key = ?"
        result = conn.execute(query, [event_key]).fetchone()
        
        if result and result[0] is not None:
            with_scores.append(event_key)
            scores_dict[event_key] = {'score': result[0], 'n': result[1], 'method': 'exact'}
        else:
            # Essayer stripped
            key_clean = strip_variant_suffix(event_key)
            result_clean = conn.execute(query, [key_clean]).fetchone()
            
            if result_clean and result_clean[0] is not None:
                with_scores.append(event_key)
                scores_dict[event_key] = {'score': result_clean[0], 'n': result_clean[1], 'method': 'stripped'}
            else:
                without_scores.append(event_key)
    
    # 4. Statistiques
    pct = 100.0 * len(with_scores) / len(event_keys)
    
    print(f"\n   Total event_keys                  : {len(event_keys)}")
    print(f"   Avec scores                       : {len(with_scores)} ({pct:.1f}%)")
    print(f"   Sans scores                       : {len(without_scores)} ({100.0 - pct:.1f}%)")
    
    if without_scores:
        print(f"\n⚠️  EVENT_KEYS ENCORE SANS SCORES :")
        for key in without_scores[:10]:
            print(f"      {key}")
    
    # 5. Distribution scores globale
    print("\n📈 DISTRIBUTION SCORES GLOBALE (694 event_keys)")
    print("-" * 80)
    
    scores_values = [scores_dict[k]['score'] for k in with_scores]
    
    import numpy as np
    
    print(f"\n   Score minimum  : {min(scores_values):.1f} pips")
    print(f"   Score maximum  : {max(scores_values):.1f} pips")
    print(f"   Score moyen    : {np.mean(scores_values):.1f} pips")
    print(f"   Score médian   : {np.median(scores_values):.1f} pips")
    
    # Par catégorie
    low = sum(1 for s in scores_values if s < 20)
    med = sum(1 for s in scores_values if 20 <= s < 40)
    high = sum(1 for s in scores_values if s >= 40)
    
    print(f"\n   Par catégorie :")
    print(f"      LOW (<20)      : {low:3d} ({100.0 * low / len(scores_values):.1f}%)")
    print(f"      MED (20-40)    : {med:3d} ({100.0 * med / len(scores_values):.1f}%)")
    print(f"      HIGH (≥40)     : {high:3d} ({100.0 * high / len(scores_values):.1f}%)")
    
    # 6. Top 20 scores
    print("\n🏆 TOP 20 SCORES (694 event_keys matchés)")
    print("-" * 80)
    
    top_keys = sorted(with_scores, key=lambda k: scores_dict[k]['score'], reverse=True)[:20]
    
    for key in top_keys:
        data = scores_dict[key]
        print(f"   {key[:50]:50s} | {data['score']:5.1f} pips | n={data['n']:3d}")
    
    conn.close()
    
    # 7. DÉCISION FINALE
    print("\n" + "=" * 80)
    print("DÉCISION FINALE :")
    print("=" * 80)
    
    if pct >= 99:
        print(f"\n✅ PARFAIT : {pct:.1f}% event_keys ont des scores")
        print(f"   → CONTINUER ÉTAPE 2.4 : Enrichir CSV final avec scores")
        decision = "CONTINUE"
    elif pct >= 95:
        print(f"\n✅ EXCELLENT : {pct:.1f}% ont des scores")
        print(f"   → {len(without_scores)} manquants acceptables")
        print(f"   → CONTINUER ÉTAPE 2.4")
        decision = "CONTINUE"
    else:
        print(f"\n⚠️  {pct:.1f}% ont des scores")
        print(f"   → {len(without_scores)} encore manquants")
        print(f"   → Investiguer pourquoi")
        decision = "INVESTIGATE"
    
    return decision, len(with_scores), len(without_scores)

if __name__ == '__main__':
    decision, with_s, without_s = verify_scores_completeness()
