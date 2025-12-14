"""
STEP 4-BIS : GROUPING PATTERNS V2 (Direction-Aware)
====================================================

Session 139 - 14 novembre 2025
Objectif : Créer groupes (pattern_type, score_range) pour LOO-CV

ENTRÉE :
- step3_movements_with_patterns_v2.csv (396 mouvements avec patterns v2)

SORTIE :
- step4_pattern_groups_v2.csv (groupes avec ≥3 cas)

LOGIQUE :
1. Charger CSV v2
2. Créer score_range : 0-100, 100-200, 200-300, 300-400, 400-500, 500+
3. Grouper par (pattern_type, score_range)
4. Filtrer groupes ≥3 cas
5. Calculer statistiques par groupe (mean, std, count)
6. Exporter

CRITÈRES GROUPING :
- Minimum 3 cas par groupe (robustesse statistique)
- Score ranges fixes (éviter sur-segmentation)
- Séparation UP/DOWN (direction-awareness)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_FILE = Path(__file__).parent.parent / "session137" / "step3_movements_with_patterns_v2.csv"
OUTPUT_FILE = Path(__file__).parent / "step4_pattern_groups_v2.csv"
MIN_CASES_PER_GROUP = 3  # Minimum statistiquement robuste

# Score ranges (pips)
SCORE_RANGES = [
    (0, 100, "0-100"),
    (100, 200, "100-200"),
    (200, 300, "200-300"),
    (300, 400, "300-400"),
    (400, 500, "400-500"),
    (500, 10000, "500+")  # 10000 = infinity pratique
]

# ============================================================================
# FONCTIONS
# ============================================================================

def assign_score_range(score):
    """Assigne un score à une range."""
    for min_val, max_val, label in SCORE_RANGES:
        if min_val <= score < max_val:
            return label
    return "500+"  # Par défaut si score très élevé

def load_movements():
    """Charge les mouvements avec patterns v2."""
    print(f"📂 Chargement : {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"✅ {len(df)} mouvements chargés")
    return df

def create_groups(df):
    """Crée les groupes (pattern_type, score_range)."""
    print("\n🔧 Création score_range...")
    
    # Créer colonne score_range
    df['score_range'] = df['total_score'].apply(assign_score_range)
    
    print("\n📊 Distribution score_ranges :")
    print(df['score_range'].value_counts().sort_index())
    
    # Grouper par (pattern_type, score_range)
    print("\n🔧 Grouping par (pattern_type, score_range)...")
    grouped = df.groupby(['pattern_type', 'score_range']).agg({
        'impact_pips': ['mean', 'std', 'count'],
        'total_score': ['mean', 'std'],
        'movement_datetime': 'first'  # Pour debug
    }).reset_index()
    
    # Flatten multi-index columns
    grouped.columns = ['_'.join(col).strip('_') for col in grouped.columns.values]
    
    # Renommer pour clarté
    grouped.rename(columns={
        'impact_pips_mean': 'mean_impact_pips',
        'impact_pips_std': 'std_impact_pips',
        'impact_pips_count': 'count',
        'total_score_mean': 'mean_score',
        'total_score_std': 'std_score',
        'movement_datetime_first': 'example_date'
    }, inplace=True)
    
    print(f"✅ {len(grouped)} groupes créés (avant filtrage)")
    
    return grouped

def filter_groups(grouped):
    """Filtre les groupes avec ≥ MIN_CASES_PER_GROUP cas."""
    print(f"\n🔧 Filtrage groupes (≥{MIN_CASES_PER_GROUP} cas)...")
    
    filtered = grouped[grouped['count'] >= MIN_CASES_PER_GROUP].copy()
    
    print(f"✅ {len(filtered)} groupes conservés (≥{MIN_CASES_PER_GROUP} cas)")
    print(f"❌ {len(grouped) - len(filtered)} groupes exclus (<{MIN_CASES_PER_GROUP} cas)")
    
    return filtered

def analyze_groups(filtered):
    """Analyse les groupes créés."""
    print("\n" + "="*80)
    print("📊 ANALYSE GROUPES FINAUX")
    print("="*80)
    
    # Statistiques globales
    total_cases = filtered['count'].sum()
    print(f"\n📈 Statistiques globales :")
    print(f"  • Nombre de groupes : {len(filtered)}")
    print(f"  • Total cas couverts : {total_cases}")
    print(f"  • Cases par groupe (moyenne) : {filtered['count'].mean():.1f}")
    print(f"  • Cases par groupe (min) : {filtered['count'].min()}")
    print(f"  • Cases par groupe (max) : {filtered['count'].max()}")
    
    # Distribution par pattern_type
    print(f"\n📊 Distribution par pattern_type :")
    pattern_dist = filtered.groupby('pattern_type')['count'].sum().sort_values(ascending=False)
    for pattern, count in pattern_dist.items():
        pct = (count / total_cases) * 100
        print(f"  • {pattern:30s} : {count:3d} cas ({pct:5.1f}%)")
    
    # Distribution par score_range
    print(f"\n📊 Distribution par score_range :")
    score_dist = filtered.groupby('score_range')['count'].sum().sort_index()
    for score_range, count in score_dist.items():
        pct = (count / total_cases) * 100
        print(f"  • {score_range:10s} : {count:3d} cas ({pct:5.1f}%)")
    
    # Top 10 groupes
    print(f"\n🏆 Top 10 groupes (par nombre de cas) :")
    top10 = filtered.nlargest(10, 'count')[['pattern_type', 'score_range', 'count', 'mean_impact_pips', 'std_impact_pips']]
    for idx, row in top10.iterrows():
        print(f"  • {row['pattern_type']:30s} | {row['score_range']:10s} | {row['count']:3d} cas | μ={row['mean_impact_pips']:6.1f} pips | σ={row['std_impact_pips']:6.1f}")

def save_groups(filtered):
    """Sauvegarde les groupes dans CSV."""
    print(f"\n💾 Sauvegarde : {OUTPUT_FILE}")
    
    # Trier par pattern_type puis score_range
    filtered_sorted = filtered.sort_values(['pattern_type', 'score_range'])
    
    # Exporter
    filtered_sorted.to_csv(OUTPUT_FILE, index=False)
    
    print(f"✅ {len(filtered_sorted)} groupes sauvegardés")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Fonction principale."""
    print("="*80)
    print("STEP 4-BIS : GROUPING PATTERNS V2")
    print("="*80)
    
    # 1. Charger mouvements
    df = load_movements()
    
    # 2. Créer groupes
    grouped = create_groups(df)
    
    # 3. Filtrer groupes
    filtered = filter_groups(grouped)
    
    # 4. Analyser groupes
    analyze_groups(filtered)
    
    # 5. Sauvegarder
    save_groups(filtered)
    
    print("\n" + "="*80)
    print("✅ STEP 4-BIS TERMINÉ")
    print("="*80)
    print(f"\n📁 Fichier créé : {OUTPUT_FILE}")
    print(f"📊 Prochaine étape : LOO-CV sur {len(filtered)} groupes")

if __name__ == "__main__":
    main()
