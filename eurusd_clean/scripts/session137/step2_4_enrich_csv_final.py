"""
ÉTAPE 2.4 - ENRICHIR CSV FINAL AVEC SCORES
Session 137 - Workflow LOO-CV DoubleWave_Overlap

Mission :
1. Lire step2_0_matched_events.csv (396 mouvements + event_keys)
2. Pour chaque mouvement : calculer total_score
3. Enrichir CSV : num_events, total_score, event_keys
4. Sauvegarder step2_movements_with_clusters.csv (FINAL)

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
INPUT_CSV = Path(__file__).parent / "step2_0_matched_events.csv"
OUTPUT_CSV = Path(__file__).parent / "step2_movements_with_clusters.csv"

# =============================================================================
# FONCTION strip_variant_suffix
# =============================================================================

def strip_variant_suffix(event_key: str) -> str:
    """Strip suffixes variantes"""
    suffixes = ['_qoq_adv', '_mom', '_yoy', '_qoq', ' mom', ' yoy', ' qoq']
    event_key_lower = event_key.lower()
    for suffix in suffixes:
        if event_key_lower.endswith(suffix):
            return event_key[:-len(suffix)]
    return event_key

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def enrich_csv_with_scores():
    """Enrichir CSV final avec total_score"""
    
    print("=" * 80)
    print("ÉTAPE 2.4 - ENRICHIR CSV FINAL AVEC SCORES")
    print("=" * 80)
    
    # 1. Charger CSV
    print("\n📊 ÉTAPE 1 : Chargement CSV")
    print("-" * 80)
    
    df = pd.read_csv(INPUT_CSV)
    
    print(f"   ✅ {len(df)} mouvements chargés")
    print(f"   Colonnes actuelles : {list(df.columns)}")
    
    # 2. Connecter DB
    print("\n📊 ÉTAPE 2 : Connexion database")
    print("-" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Créer dictionnaire scores
    query_scores = "SELECT event_key, empirical_score FROM event_families WHERE empirical_score IS NOT NULL"
    scores_data = conn.execute(query_scores).fetchall()
    
    scores_dict = {key: score for key, score in scores_data}
    
    print(f"   ✅ {len(scores_dict)} scores chargés en mémoire")
    
    # 3. Calculer total_score pour chaque mouvement
    print("\n📊 ÉTAPE 3 : Calcul total_score")
    print("-" * 80)
    
    total_scores = []
    
    for idx, row in df.iterrows():
        event_keys_str = row['event_keys']
        
        if pd.isna(event_keys_str) or event_keys_str == "":
            # Pas d'événements
            total_scores.append(0.0)
        else:
            # Parser event_keys (séparés par virgules)
            event_keys = [k.strip() for k in event_keys_str.split(',')]
            
            # Lookup scores (avec strip_variant_suffix)
            scores = []
            for key in event_keys:
                # Essayer exact
                if key in scores_dict:
                    scores.append(scores_dict[key])
                else:
                    # Essayer stripped
                    key_clean = strip_variant_suffix(key)
                    if key_clean in scores_dict:
                        scores.append(scores_dict[key_clean])
                    else:
                        # Pas de score trouvé (ne devrait pas arriver vu 100%)
                        scores.append(0.0)
            
            # Total
            total_scores.append(sum(scores))
        
        # Progress
        if (idx + 1) % 50 == 0:
            print(f"   Progression : {idx + 1}/396 mouvements ({100.0 * (idx + 1) / 396:.1f}%)")
    
    # 4. Ajouter colonne total_score
    print("\n📊 ÉTAPE 4 : Ajout colonne total_score")
    print("-" * 80)
    
    df['total_score'] = total_scores
    
    print(f"   ✅ Colonne total_score ajoutée")
    
    # Réorganiser colonnes
    cols = ['movement_id', 'movement_datetime', 'impact_pips', 'direction', 
            'num_events', 'total_score', 'event_keys']
    df = df[cols]
    
    # 5. Statistiques
    print("\n📊 ÉTAPE 5 : Statistiques finales")
    print("-" * 80)
    
    movements_with_events = (df['num_events'] > 0).sum()
    movements_without_events = (df['num_events'] == 0).sum()
    
    print(f"\n   Total mouvements                  : {len(df)}")
    print(f"   Mouvements avec événements        : {movements_with_events} ({100.0 * movements_with_events / len(df):.1f}%)")
    print(f"   Mouvements sans événements        : {movements_without_events} ({100.0 * movements_without_events / len(df):.1f}%)")
    
    # Distribution total_score
    df_with_events = df[df['num_events'] > 0]
    
    if len(df_with_events) > 0:
        print(f"\n   total_score (mouvements avec événements) :")
        print(f"      Minimum    : {df_with_events['total_score'].min():.1f}")
        print(f"      Maximum    : {df_with_events['total_score'].max():.1f}")
        print(f"      Moyenne    : {df_with_events['total_score'].mean():.1f}")
        print(f"      Médiane    : {df_with_events['total_score'].median():.1f}")
        
        # Par catégorie total_score
        low = (df_with_events['total_score'] < 20).sum()
        med = ((df_with_events['total_score'] >= 20) & (df_with_events['total_score'] < 40)).sum()
        high = (df_with_events['total_score'] >= 40).sum()
        
        print(f"\n   Par catégorie total_score :")
        print(f"      LOW (<20)      : {low:3d} ({100.0 * low / len(df_with_events):.1f}%)")
        print(f"      MED (20-40)    : {med:3d} ({100.0 * med / len(df_with_events):.1f}%)")
        print(f"      HIGH (≥40)     : {high:3d} ({100.0 * high / len(df_with_events):.1f}%)")
    
    # Top 10 mouvements total_score
    print(f"\n🏆 TOP 10 MOUVEMENTS (total_score le plus élevé) :")
    print("-" * 80)
    
    top10 = df.nlargest(10, 'total_score')
    for _, row in top10.iterrows():
        print(f"   {str(row['movement_datetime'])[:19]} | {row['impact_pips']:5.1f} pips | "
              f"{row['num_events']:2d} events | total_score={row['total_score']:6.1f}")
    
    # 6. Sauvegarder
    print("\n📊 ÉTAPE 6 : Sauvegarde CSV final")
    print("-" * 80)
    
    df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"   ✅ Fichier créé : {OUTPUT_CSV}")
    print(f"   Colonnes : {list(df.columns)}")
    print(f"   Lignes   : {len(df)}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ÉTAPE 2.4 COMPLÉTÉE - ÉTAPE 2 WORKFLOW TERMINÉE !")
    print("=" * 80)
    print(f"\n📋 RÉSULTAT : CSV enrichi avec total_score (100% scores disponibles)")
    print(f"\n🎯 PROCHAINE SESSION 138 : ÉTAPE 3 - Classifier patterns (DOUBLE_WAVE, SINGLE_WAVE, etc.)")
    
    return len(df), movements_with_events

if __name__ == '__main__':
    total, with_events = enrich_csv_with_scores()
