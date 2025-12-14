"""
ÉTAPE 4 - GROUPER PATTERNS IDENTIQUES
Session 137 - Workflow LOO-CV DoubleWave_Overlap

Mission :
1. Filtrer mouvements par pattern_type (focus DOUBLE_WAVE)
2. Pour chaque mouvement : extraire événements HIGH (empirical_score ≥40)
3. Créer signature cluster (événements HIGH triés alphabétiquement)
4. Grouper mouvements avec même signature
5. Filtrer groupes ≥3 cas (minimum LOO-CV)
6. Sauvegarder groupes valides

Critères grouping :
- Signature = événements HIGH uniquement (score ≥40 pips)
- Ordre alphabétique (reproductibilité)
- Minimum 3 mouvements par groupe (LOO-CV valide)

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
INPUT_CSV = Path(__file__).parent / "step3_movements_with_patterns.csv"
OUTPUT_CSV = Path(__file__).parent / "step4_pattern_groups.csv"
OUTPUT_DETAILS_CSV = Path(__file__).parent / "step4_pattern_groups_details.csv"

# =============================================================================
# PARAMÈTRES
# =============================================================================

# Seuil événement HIGH
HIGH_SCORE_THRESHOLD = 40.0

# Minimum cas par groupe (LOO-CV)
MIN_GROUP_SIZE = 3

# Patterns à traiter (commencer par DOUBLE_WAVE)
TARGET_PATTERNS = ['DOUBLE_WAVE']

# =============================================================================
# FONCTION CHARGEMENT SCORES
# =============================================================================

def load_scores_dict(conn):
    """
    Charger tous les scores empiriques dans un dict
    
    Returns:
        Dict[str, float]: {event_key: empirical_score}
    """
    
    query = """
    SELECT event_key, empirical_score
    FROM event_families
    WHERE empirical_score IS NOT NULL
    """
    
    df_scores = conn.execute(query).df()
    
    # Créer dict
    scores_dict = {}
    for _, row in df_scores.iterrows():
        key = row['event_key'].strip().lower()
        scores_dict[key] = row['empirical_score']
    
    return scores_dict

# =============================================================================
# FONCTION CRÉATION SIGNATURE
# =============================================================================

def create_signature(event_keys_str: str, scores_dict: Dict[str, float]) -> Tuple[str, List[str], List[str]]:
    """
    Créer signature cluster à partir d'event_keys
    
    Args:
        event_keys_str: String "event1,event2,event3"
        scores_dict: Dict {event_key: empirical_score}
    
    Returns:
        Tuple[str, List[str], List[str]]: (signature, high_events, all_events)
    """
    
    if not event_keys_str or pd.isna(event_keys_str):
        return "", [], []
    
    # Parser event_keys
    all_events = [e.strip().lower() for e in event_keys_str.split(',')]
    
    # Filtrer événements HIGH (score ≥40)
    high_events = []
    for event_key in all_events:
        score = scores_dict.get(event_key, 0.0)
        if score >= HIGH_SCORE_THRESHOLD:
            high_events.append(event_key)
    
    # Trier alphabétiquement (reproductibilité)
    high_events_sorted = sorted(high_events)
    
    # Créer signature
    if len(high_events_sorted) == 0:
        signature = "NO_HIGH_EVENTS"
    else:
        signature = '|'.join(high_events_sorted)
    
    return signature, high_events_sorted, all_events

# =============================================================================
# FONCTION GROUPING
# =============================================================================

def group_movements_by_signature(df: pd.DataFrame, scores_dict: Dict[str, float], 
                                  pattern_type: str = 'DOUBLE_WAVE') -> Dict:
    """
    Grouper mouvements par signature
    
    Args:
        df: DataFrame mouvements
        scores_dict: Dict scores empiriques
        pattern_type: Pattern à traiter
    
    Returns:
        Dict: {signature: [movement_ids]}
    """
    
    # Filtrer par pattern
    df_pattern = df[df['pattern_type'] == pattern_type].copy()
    
    print(f"\n   Mouvements {pattern_type} : {len(df_pattern)}")
    
    if len(df_pattern) == 0:
        return {}
    
    # Créer signatures
    groups = defaultdict(list)
    
    for idx, row in df_pattern.iterrows():
        movement_id = row['movement_id']
        event_keys_str = row['event_keys']
        
        # Créer signature
        signature, high_events, all_events = create_signature(event_keys_str, scores_dict)
        
        # Stocker
        groups[signature].append({
            'movement_id': movement_id,
            'movement_datetime': row['movement_datetime'],
            'impact_pips': row['impact_pips'],
            'num_events': row['num_events'],
            'total_score': row['total_score'],
            'high_events': high_events,
            'all_events': all_events,
            'peak1_amplitude_pips': row.get('peak1_amplitude_pips'),
            'peak1_time_min': row.get('peak1_time_min'),
            'peak2_amplitude_pips': row.get('peak2_amplitude_pips'),
            'peak2_time_min': row.get('peak2_time_min'),
            'dip_ratio': row.get('dip_ratio')
        })
    
    return dict(groups)

# =============================================================================
# FONCTION FILTRAGE GROUPES
# =============================================================================

def filter_valid_groups(groups: Dict, min_size: int = 3) -> Dict:
    """
    Filtrer groupes avec ≥min_size cas
    
    Args:
        groups: Dict {signature: [movements]}
        min_size: Minimum cas par groupe
    
    Returns:
        Dict: Groupes valides
    """
    
    valid_groups = {
        sig: mvts for sig, mvts in groups.items()
        if len(mvts) >= min_size
    }
    
    return valid_groups

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def group_patterns():
    """
    Grouper patterns identiques
    """
    
    print("=" * 80)
    print("ÉTAPE 4 - GROUPING PATTERNS IDENTIQUES")
    print("=" * 80)
    
    # 1. Charger CSV
    print("\n📊 ÉTAPE 1 : Chargement mouvements")
    print("-" * 80)
    
    df = pd.read_csv(INPUT_CSV)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'], utc=True).dt.tz_convert('Europe/Zurich')
    
    print(f"   ✅ {len(df)} mouvements chargés")
    
    # Distribution patterns
    pattern_counts = df['pattern_type'].value_counts()
    print(f"\n   Distribution patterns :")
    for pattern, count in pattern_counts.items():
        print(f"      {pattern:25s} : {count:3d}")
    
    # 2. Connecter DB et charger scores
    print("\n📊 ÉTAPE 2 : Chargement scores empiriques")
    print("-" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    scores_dict = load_scores_dict(conn)
    
    print(f"   ✅ {len(scores_dict)} scores empiriques chargés")
    
    # Compter HIGH scores
    high_scores_count = sum(1 for score in scores_dict.values() if score >= HIGH_SCORE_THRESHOLD)
    print(f"   ✅ {high_scores_count} événements HIGH (score ≥{HIGH_SCORE_THRESHOLD} pips)")
    
    # 3. Grouper par pattern
    print("\n📊 ÉTAPE 3 : Grouping par signature")
    print("-" * 80)
    
    all_groups = {}
    
    for pattern_type in TARGET_PATTERNS:
        print(f"\n   Pattern : {pattern_type}")
        print(f"   {'─' * 60}")
        
        # Grouper
        groups = group_movements_by_signature(df, scores_dict, pattern_type)
        
        print(f"   Signatures uniques : {len(groups)}")
        
        # Filtrer groupes valides (≥3 cas)
        valid_groups = filter_valid_groups(groups, min_size=MIN_GROUP_SIZE)
        
        print(f"   Groupes valides (≥{MIN_GROUP_SIZE} cas) : {len(valid_groups)}")
        
        # Stocker
        all_groups[pattern_type] = valid_groups
        
        # Top 5 groupes
        if len(valid_groups) > 0:
            print(f"\n   Top 5 groupes (par taille) :")
            sorted_groups = sorted(valid_groups.items(), key=lambda x: len(x[1]), reverse=True)
            
            for i, (sig, mvts) in enumerate(sorted_groups[:5], 1):
                # Signature courte
                sig_short = sig if len(sig) <= 50 else sig[:47] + "..."
                print(f"      {i}. n={len(mvts):2d} | {sig_short}")
    
    # 4. Créer DataFrames output
    print("\n📊 ÉTAPE 4 : Création outputs")
    print("-" * 80)
    
    # CSV groupes (1 ligne par groupe)
    groups_data = []
    
    # CSV détails (1 ligne par mouvement)
    details_data = []
    
    group_id = 0
    
    for pattern_type, valid_groups in all_groups.items():
        for signature, movements in valid_groups.items():
            group_id += 1
            
            # Dates mouvements
            dates = [m['movement_datetime'] for m in movements]
            dates_str = ';'.join([d.strftime('%Y-%m-%d %H:%M') for d in dates])
            
            # Événements HIGH
            high_events = movements[0]['high_events']  # Même pour tous dans groupe
            high_events_str = '|'.join(high_events)
            
            # Statistiques groupe
            impacts = [m['impact_pips'] for m in movements]
            scores = [m['total_score'] for m in movements]
            
            # Ligne groupe
            groups_data.append({
                'group_id': group_id,
                'pattern_type': pattern_type,
                'signature': signature,
                'high_events': high_events_str,
                'n_high_events': len(high_events),
                'n_movements': len(movements),
                'dates': dates_str,
                'impact_mean': np.mean(impacts),
                'impact_std': np.std(impacts),
                'total_score_mean': np.mean(scores),
                'total_score_std': np.std(scores)
            })
            
            # Lignes détails (1 par mouvement)
            for movement in movements:
                details_data.append({
                    'group_id': group_id,
                    'pattern_type': pattern_type,
                    'movement_id': movement['movement_id'],
                    'movement_datetime': movement['movement_datetime'],
                    'impact_pips': movement['impact_pips'],
                    'num_events': movement['num_events'],
                    'total_score': movement['total_score'],
                    'peak1_amplitude_pips': movement['peak1_amplitude_pips'],
                    'peak1_time_min': movement['peak1_time_min'],
                    'peak2_amplitude_pips': movement['peak2_amplitude_pips'],
                    'peak2_time_min': movement['peak2_time_min'],
                    'dip_ratio': movement['dip_ratio'],
                    'high_events': '|'.join(movement['high_events']),
                    'n_high_events': len(movement['high_events'])
                })
    
    df_groups = pd.DataFrame(groups_data)
    df_details = pd.DataFrame(details_data)
    
    print(f"   ✅ {len(df_groups)} groupes créés")
    print(f"   ✅ {len(df_details)} mouvements dans groupes")
    
    # 5. Statistiques finales
    print("\n📊 ÉTAPE 5 : Statistiques finales")
    print("-" * 80)
    
    if len(df_groups) > 0:
        print(f"\n   Groupes par pattern :")
        for pattern in TARGET_PATTERNS:
            n = len(df_groups[df_groups['pattern_type'] == pattern])
            print(f"      {pattern:25s} : {n:3d} groupes")
        
        print(f"\n   Distribution tailles groupes :")
        size_dist = df_groups['n_movements'].value_counts().sort_index()
        for size, count in size_dist.items():
            print(f"      {size:2d} mouvements : {count:3d} groupes")
        
        print(f"\n   Statistiques n_high_events :")
        print(f"      Minimum   : {df_groups['n_high_events'].min():.0f}")
        print(f"      Maximum   : {df_groups['n_high_events'].max():.0f}")
        print(f"      Moyenne   : {df_groups['n_high_events'].mean():.1f}")
        print(f"      Médiane   : {df_groups['n_high_events'].median():.0f}")
    
    # 6. Sauvegarder
    print("\n📊 ÉTAPE 6 : Sauvegarde")
    print("-" * 80)
    
    df_groups.to_csv(OUTPUT_CSV, index=False)
    df_details.to_csv(OUTPUT_DETAILS_CSV, index=False)
    
    print(f"   ✅ Fichier groupes : {OUTPUT_CSV}")
    print(f"      Colonnes : {len(df_groups.columns)}")
    print(f"      Lignes   : {len(df_groups)}")
    
    print(f"\n   ✅ Fichier détails : {OUTPUT_DETAILS_CSV}")
    print(f"      Colonnes : {len(df_details.columns)}")
    print(f"      Lignes   : {len(df_details)}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ÉTAPE 4 COMPLÉTÉE !")
    print("=" * 80)
    
    if len(df_groups) == 0:
        print(f"\n⚠️  ATTENTION : 0 groupes valides (≥{MIN_GROUP_SIZE} cas)")
        print(f"   → Ajuster seuil HIGH ou min_size")
    else:
        print(f"\n📋 RÉSULTAT : {len(df_groups)} groupes prêts pour LOO-CV")
        print(f"   {len(df_details)} mouvements total dans groupes")
    
    return df_groups, df_details

if __name__ == '__main__':
    df_groups, df_details = group_patterns()
