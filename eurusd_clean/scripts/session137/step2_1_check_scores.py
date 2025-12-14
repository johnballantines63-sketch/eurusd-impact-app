"""
ÉTAPE 2.1 - VÉRIFIER SCORES POUR EVENT_KEYS MATCHÉS
Session 137 - Workflow LOO-CV DoubleWave_Overlap

Mission :
1. Lire liste event_keys matchés (ÉTAPE 2.0)
2. Vérifier lesquels ont scores dans event_families
3. Identifier event_keys SANS scores
4. Décider si calcul scores nécessaire

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
from pathlib import Path

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
EVENT_KEYS_FILE = Path(__file__).parent / "step2_0_unique_event_keys.txt"

# =============================================================================
# FONCTION strip_variant_suffix (Session 127)
# =============================================================================

def strip_variant_suffix(event_key: str) -> str:
    """
    Supprimer suffixes variantes (_mom, _qoq, _yoy) pour matching scores
    
    Session 127 : event_families contient clés sans suffixes
    events contient clés avec suffixes
    """
    suffixes = ['_qoq_adv', '_mom', '_yoy', '_qoq', ' mom', ' yoy', ' qoq']
    
    event_key_lower = event_key.lower()
    for suffix in suffixes:
        if event_key_lower.endswith(suffix):
            return event_key[:-len(suffix)]
    
    return event_key

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def check_scores_for_matched_keys():
    """
    Vérifier disponibilité scores pour event_keys matchés
    """
    
    print("=" * 80)
    print("ÉTAPE 2.1 - VÉRIFICATION SCORES POUR EVENT_KEYS MATCHÉS")
    print("=" * 80)
    
    # 1. Charger event_keys matchés
    print("\n📊 ÉTAPE 1 : Chargement event_keys matchés")
    print("-" * 80)
    
    with open(EVENT_KEYS_FILE, 'r') as f:
        event_keys_matched = [line.strip() for line in f if line.strip()]
    
    print(f"   ✅ {len(event_keys_matched)} event_keys matchés chargés")
    
    # 2. Connecter DB
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 3. Vérifier scores (avec et sans strip suffixes)
    print("\n📊 ÉTAPE 2 : Vérification scores (avec strip_variant_suffix)")
    print("-" * 80)
    
    keys_with_scores = []
    keys_without_scores = []
    scores_dict = {}
    
    for event_key in event_keys_matched:
        # Essayer clé originale
        query = """
        SELECT empirical_score, sample_size
        FROM event_families
        WHERE event_key = ?
        """
        result = conn.execute(query, [event_key]).fetchone()
        
        if result and result[0] is not None:
            # Score trouvé avec clé originale
            keys_with_scores.append(event_key)
            scores_dict[event_key] = {'score': result[0], 'sample_size': result[1], 'method': 'exact'}
        else:
            # Essayer avec strip_variant_suffix
            event_key_clean = strip_variant_suffix(event_key)
            result_clean = conn.execute(query, [event_key_clean]).fetchone()
            
            if result_clean and result_clean[0] is not None:
                # Score trouvé après strip
                keys_with_scores.append(event_key)
                scores_dict[event_key] = {'score': result_clean[0], 'sample_size': result_clean[1], 'method': 'stripped'}
            else:
                # Aucun score trouvé
                keys_without_scores.append(event_key)
    
    # 4. Statistiques
    print(f"\n   event_keys matchés                : {len(event_keys_matched)}")
    print(f"   Avec scores (exact)               : {sum(1 for k in keys_with_scores if scores_dict[k]['method'] == 'exact')}")
    print(f"   Avec scores (stripped)            : {sum(1 for k in keys_with_scores if scores_dict[k]['method'] == 'stripped')}")
    print(f"   TOTAL avec scores                 : {len(keys_with_scores)} ({100.0 * len(keys_with_scores) / len(event_keys_matched):.1f}%)")
    print(f"   Sans scores                       : {len(keys_without_scores)} ({100.0 * len(keys_without_scores) / len(event_keys_matched):.1f}%)")
    
    # 5. Analyser keys SANS scores
    if keys_without_scores:
        print("\n📋 EVENT_KEYS SANS SCORES (premiers 20) :")
        print("-" * 80)
        
        # Compter occurrences
        query_occurrences = """
        SELECT 
            event_key,
            COUNT(*) as occurrences,
            MIN(ts_utc) as first_date,
            MAX(ts_utc) as last_date
        FROM events
        WHERE event_key = ?
        GROUP BY event_key
        """
        
        keys_analysis = []
        for key in keys_without_scores[:20]:
            result = conn.execute(query_occurrences, [key]).fetchone()
            if result:
                keys_analysis.append({
                    'event_key': key,
                    'occurrences': result[1],
                    'first_date': result[2],
                    'last_date': result[3]
                })
        
        # Trier par occurrences
        keys_analysis.sort(key=lambda x: x['occurrences'], reverse=True)
        
        for item in keys_analysis:
            first_date_str = str(item['first_date'])[:10] if item['first_date'] else 'N/A'
            last_date_str = str(item['last_date'])[:10] if item['last_date'] else 'N/A'
            print(f"   {item['event_key'][:50]:50s} | n={item['occurrences']:4d} | {first_date_str} → {last_date_str}")
    
    # 6. Distribution scores disponibles
    print("\n📈 DISTRIBUTION SCORES DISPONIBLES :")
    print("-" * 80)
    
    scores_values = [scores_dict[k]['score'] for k in keys_with_scores]
    
    if scores_values:
        import numpy as np
        
        print(f"   Score minimum  : {min(scores_values):.1f} pips")
        print(f"   Score maximum  : {max(scores_values):.1f} pips")
        print(f"   Score moyen    : {np.mean(scores_values):.1f} pips")
        print(f"   Score médian   : {np.median(scores_values):.1f} pips")
        
        # Distribution par catégorie
        print("\n   Par catégorie :")
        low = sum(1 for s in scores_values if s < 20)
        med = sum(1 for s in scores_values if 20 <= s < 40)
        high = sum(1 for s in scores_values if s >= 40)
        
        print(f"      LOW (<20)      : {low:3d} ({100.0 * low / len(scores_values):.1f}%)")
        print(f"      MED (20-40)    : {med:3d} ({100.0 * med / len(scores_values):.1f}%)")
        print(f"      HIGH (≥40)     : {high:3d} ({100.0 * high / len(scores_values):.1f}%)")
    
    conn.close()
    
    # 7. DÉCISION
    print("\n" + "=" * 80)
    print("DÉCISION :")
    print("=" * 80)
    
    pct_complete = 100.0 * len(keys_with_scores) / len(event_keys_matched)
    
    if pct_complete >= 95:
        print(f"\n✅ EXCELLENT : {pct_complete:.1f}% event_keys ont des scores")
        print(f"   → CONTINUER ÉTAPE 2.2 avec scores existants")
        print(f"   → {len(keys_without_scores)} manquants = acceptable (utiliser 0.0)")
        decision = "CONTINUE"
    elif pct_complete >= 80:
        print(f"\n⚠️  BON : {pct_complete:.1f}% ont des scores")
        print(f"   → OPTION A : Continuer avec {len(keys_without_scores)} scores manquants")
        print(f"   → OPTION B : Calculer {len(keys_without_scores)} scores manquants d'abord")
        print(f"\n   Recommandation : Calculer scores manquants (rigueur mathématique)")
        decision = "CALCULATE_MISSING"
    else:
        print(f"\n❌ PROBLÈME : Seulement {pct_complete:.1f}% ont des scores")
        print(f"   → {len(keys_without_scores)} event_keys SANS scores")
        print(f"   → OBLIGATOIRE : Calculer scores manquants AVANT continuer")
        decision = "MUST_CALCULATE"
    
    # Sauvegarder liste keys sans scores
    if keys_without_scores:
        missing_file = Path(__file__).parent / "step2_1_missing_scores.txt"
        with open(missing_file, 'w') as f:
            for key in keys_without_scores:
                f.write(f"{key}\n")
        
        print(f"\n📄 Liste event_keys sans scores : {missing_file}")
    
    return decision, len(keys_without_scores), len(keys_with_scores)

if __name__ == '__main__':
    decision, nb_missing, nb_with = check_scores_for_matched_keys()
