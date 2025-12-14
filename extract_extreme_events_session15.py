"""
PHASE 1 : EXTRACTION ÉVÉNEMENTS - SESSION 15
Extraction intelligente de 30 événements pour validation multiplicateur

Critères de sélection :
- Événements avec estimate ET empirical_score (utilisables)
- Surprises raisonnables (< 500% pour éviter aberrations)
- Échantillonnage par tranches : 0-5%, 5-10%, >10%
- Priorité aux événements HIGH importance
"""

import duckdb
import pandas as pd
from datetime import datetime

# Connexion
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("="*80)
print("📊 PHASE 1 : EXTRACTION ÉVÉNEMENTS - SESSION 15")
print("="*80)

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Compter événements utilisables par tranche
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 1 : Comptage événements utilisables")
print("─"*80)

count_query = """
WITH surprises AS (
    SELECT 
        e.ts_utc,
        e.event_title,
        e.country,
        e.actual,
        e.estimate,
        ef.empirical_score,
        ef.impact_level,
        CASE 
            WHEN e.estimate IS NOT NULL AND e.estimate != 0 
            THEN ABS((e.actual - e.estimate) / e.estimate) * 100
            ELSE NULL
        END as surprise_pct
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.estimate IS NOT NULL 
      AND e.actual IS NOT NULL
      AND ef.empirical_score IS NOT NULL
),
tranche_data AS (
    SELECT 
        CASE 
            WHEN surprise_pct < 5 THEN '0-5%'
            WHEN surprise_pct < 10 THEN '5-10%'
            WHEN surprise_pct < 20 THEN '10-20%'
            WHEN surprise_pct < 50 THEN '20-50%'
            WHEN surprise_pct < 500 THEN '50-500%'
            ELSE '>500% (aberrant)'
        END as tranche_surprise,
        CASE 
            WHEN surprise_pct < 5 THEN 1
            WHEN surprise_pct < 10 THEN 2
            WHEN surprise_pct < 20 THEN 3
            WHEN surprise_pct < 50 THEN 4
            WHEN surprise_pct < 500 THEN 5
            ELSE 6
        END as sort_order,
        impact_level
    FROM surprises
    WHERE surprise_pct IS NOT NULL
)
SELECT 
    tranche_surprise,
    COUNT(*) as nb_events,
    COUNT(CASE WHEN impact_level = 'HIGH' THEN 1 END) as nb_high
FROM tranche_data
GROUP BY tranche_surprise, sort_order
ORDER BY sort_order
"""

counts = conn.execute(count_query).fetchdf()
print(counts.to_string(index=False))

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Extraction échantillon stratifié
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 2 : Extraction échantillon (10 par tranche)")
print("─"*80)

# Tranche 1 : 0-5% (baseline, pas d'amplification attendue)
print("\n🔹 Tranche 1 : 0-5% (baseline)")
sample_0_5 = conn.execute("""
    WITH surprises AS (
        SELECT 
            e.ts_utc,
            e.event_title,
            e.country,
            e.event_key,
            e.actual,
            e.estimate,
            ef.empirical_score,
            ef.impact_level,
            ABS((e.actual - e.estimate) / e.estimate) * 100 as surprise_pct
        FROM events e
        LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
        WHERE e.estimate IS NOT NULL 
          AND e.estimate != 0
          AND e.actual IS NOT NULL
          AND ef.empirical_score IS NOT NULL
          AND ABS((e.actual - e.estimate) / e.estimate) * 100 < 5
    )
    SELECT *
    FROM surprises
    ORDER BY 
        CASE WHEN impact_level = 'HIGH' THEN 1 ELSE 2 END,
        RANDOM()
    LIMIT 10
""").fetchdf()

print(f"✅ {len(sample_0_5)} événements extraits")

# Tranche 2 : 5-10% (amplification modérée ×1.4-3.0)
print("\n🔹 Tranche 2 : 5-10% (amplification modérée)")
sample_5_10 = conn.execute("""
    WITH surprises AS (
        SELECT 
            e.ts_utc,
            e.event_title,
            e.country,
            e.event_key,
            e.actual,
            e.estimate,
            ef.empirical_score,
            ef.impact_level,
            ABS((e.actual - e.estimate) / e.estimate) * 100 as surprise_pct
        FROM events e
        LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
        WHERE e.estimate IS NOT NULL 
          AND e.estimate != 0
          AND e.actual IS NOT NULL
          AND ef.empirical_score IS NOT NULL
          AND ABS((e.actual - e.estimate) / e.estimate) * 100 >= 5
          AND ABS((e.actual - e.estimate) / e.estimate) * 100 < 10
    )
    SELECT *
    FROM surprises
    ORDER BY 
        CASE WHEN impact_level = 'HIGH' THEN 1 ELSE 2 END,
        RANDOM()
    LIMIT 10
""").fetchdf()

print(f"✅ {len(sample_5_10)} événements extraits")

# Tranche 3 : 10-50% (amplification forte ×3.0+)
print("\n🔹 Tranche 3 : 10-50% (amplification forte)")
sample_10_50 = conn.execute("""
    WITH surprises AS (
        SELECT 
            e.ts_utc,
            e.event_title,
            e.country,
            e.event_key,
            e.actual,
            e.estimate,
            ef.empirical_score,
            ef.impact_level,
            ABS((e.actual - e.estimate) / e.estimate) * 100 as surprise_pct
        FROM events e
        LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
        WHERE e.estimate IS NOT NULL 
          AND e.estimate != 0
          AND e.actual IS NOT NULL
          AND ef.empirical_score IS NOT NULL
          AND ABS((e.actual - e.estimate) / e.estimate) * 100 >= 10
          AND ABS((e.actual - e.estimate) / e.estimate) * 100 < 50
    )
    SELECT *
    FROM surprises
    ORDER BY 
        CASE WHEN impact_level = 'HIGH' THEN 1 ELSE 2 END,
        RANDOM()
    LIMIT 10
""").fetchdf()

print(f"✅ {len(sample_10_50)} événements extraits")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Fusion et enrichissement
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 3 : Fusion et enrichissement")
print("─"*80)

# Ajouter une colonne de tranche
sample_0_5['tranche'] = '0-5%'
sample_5_10['tranche'] = '5-10%'
sample_10_50['tranche'] = '10-50%'

# Fusionner
all_samples = pd.concat([sample_0_5, sample_5_10, sample_10_50], ignore_index=True)

# Calculer facteur d'amplification attendu
def calculate_amplification_factor(surprise_pct):
    """Facteur d'amplification selon formule v8.7.1"""
    surprise_abs = abs(surprise_pct)
    
    if surprise_abs < 5.0:
        return 1.0
    elif surprise_abs < 10.0:
        return 1.0 + (surprise_abs - 5.0) * 0.4
    else:
        import numpy as np
        return 3.0 + np.log1p(surprise_abs - 10.0) * 2.0

all_samples['amplification_factor'] = all_samples['surprise_pct'].apply(calculate_amplification_factor)

# Arrondir surprise_pct
all_samples['surprise_pct'] = all_samples['surprise_pct'].round(2)
all_samples['amplification_factor'] = all_samples['amplification_factor'].round(2)

print(f"\n✅ Total événements extraits : {len(all_samples)}")
print(f"   • Tranche 0-5%   : {len(sample_0_5)} événements")
print(f"   • Tranche 5-10%  : {len(sample_5_10)} événements")
print(f"   • Tranche 10-50% : {len(sample_10_50)} événements")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Sauvegarde CSV
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 4 : Sauvegarde CSV")
print("─"*80)

# Réorganiser colonnes
output_cols = [
    'ts_utc', 'event_title', 'country', 'event_key',
    'actual', 'estimate', 'surprise_pct',
    'empirical_score', 'impact_level',
    'tranche', 'amplification_factor'
]

all_samples = all_samples[output_cols]

# Sauvegarder
csv_path = 'extracted_events_session15.csv'
all_samples.to_csv(csv_path, index=False)

print(f"✅ Fichier sauvegardé : {csv_path}")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Aperçu des données
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 5 : Aperçu des données extraites")
print("─"*80)

print("\n📊 STATISTIQUES PAR TRANCHE :")
stats = all_samples.groupby('tranche').agg({
    'surprise_pct': ['min', 'max', 'mean'],
    'amplification_factor': ['min', 'max', 'mean'],
    'empirical_score': 'mean'
}).round(2)
print(stats)

print("\n📋 ÉCHANTILLON (5 premiers) :")
print(all_samples.head(5)[['ts_utc', 'event_title', 'surprise_pct', 'amplification_factor', 'tranche']].to_string(index=False))

print("\n" + "="*80)
print("✅ PHASE 1 TERMINÉE")
print("="*80)
print("\n📁 Fichier créé : extracted_events_session15.csv")
print("🚀 Prochaine étape : Phase 2 - Mesure impacts")

conn.close()
