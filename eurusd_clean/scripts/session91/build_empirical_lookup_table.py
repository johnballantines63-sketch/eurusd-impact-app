"""
BUILD EMPIRICAL LOOKUP TABLE - Session 91
Construire table de référence (Type, Num_Events) → Impact Moyen

Basé sur découverte Session 91 :
- Le cluster (Type + Nombre événements) est plus prédictif que la surprise
- Corrélation cluster → impact : 0.838
- Corrélation surprise → impact : 0.531

Objectif : Remplacer amplification théorique par lookup empirique
"""

import duckdb
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict

# Configuration
DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

print("="*100)
print("🏗️ CONSTRUCTION TABLE EMPIRIQUE LOOKUP")
print("="*100)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# ============================================================================
# ÉTAPE 1 : SCANNER TOUS LES ÉVÉNEMENTS MULTI-EVENTS
# ============================================================================

print("\n📊 Étape 1 : Scanner événements groupés par date/heure...\n")

# Query : Trouver tous les clusters d'événements HIGH
query = """
WITH event_clusters AS (
    SELECT 
        DATE(e.ts_utc) as event_date,
        strftime(e.ts_utc, '%H:%M') as event_time,
        e.country,
        ef.family,
        COUNT(DISTINCT e.event_key) as num_events,
        AVG(ef.empirical_score) as score_avg,
        MAX(ef.empirical_score) as score_max,
        STRING_AGG(DISTINCT e.event_title, ', ') as event_list
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.country = 'US'
        AND ef.empirical_score > 40
        AND DATE(e.ts_utc) >= '2020-01-01'
        AND DATE(e.ts_utc) <= '2025-12-31'
    GROUP BY DATE(e.ts_utc), strftime(e.ts_utc, '%H:%M'), e.country, ef.family
    HAVING COUNT(DISTINCT e.event_key) >= 3
)
SELECT * FROM event_clusters
ORDER BY event_date DESC, event_time
LIMIT 100
"""

df_clusters = conn.execute(query).df()

print(f"   Clusters trouvés : {len(df_clusters)}")
print(f"   Période : 2020-2025")
print(f"   Critères : score > 40, ≥3 événements, US\n")

# ============================================================================
# ÉTAPE 2 : CALCULER IMPACT RÉEL POUR CHAQUE CLUSTER
# ============================================================================

print("📈 Étape 2 : Calculer impact réel depuis prices_1m...\n")

lookup_table = defaultdict(list)
processed = 0
skipped_no_prices = 0

for idx, cluster in df_clusters.iterrows():
    date = cluster['event_date']
    time = cluster['event_time']
    family = cluster['family']
    num_events = cluster['num_events']
    
    # Déterminer type événement simplifié
    if 'NFP' in family or 'nonfarm' in family.lower():
        event_type = 'NFP'
    elif 'CPI' in family or 'inflation' in family.lower():
        event_type = 'CPI'
    elif 'ISM' in family:
        event_type = 'ISM'
    elif 'FOMC' in family or 'Fed' in family:
        event_type = 'FOMC'
    elif 'Jobless' in family or 'Claims' in family:
        event_type = 'JOBLESS'
    elif 'Retail' in family:
        event_type = 'RETAIL'
    else:
        event_type = 'OTHER'
    
    # Récupérer prix réels
    query_prices = f"""
    SELECT datetime, open, high, low 
    FROM prices_1m
    WHERE datetime >= '{date} {time}:00+02:00'::TIMESTAMP
      AND datetime <= '{date} {time}:00+02:00'::TIMESTAMP + INTERVAL '60 minutes'
    ORDER BY datetime
    LIMIT 60
    """
    
    try:
        df_prices = conn.execute(query_prices).df()
        
        if not df_prices.empty and len(df_prices) >= 5:
            start_price = df_prices.iloc[0]['open']
            impact_down = abs(start_price - df_prices['low'].min()) * 10000
            impact_up = abs(df_prices['high'].max() - start_price) * 10000
            impact_real = max(impact_down, impact_up)
            
            # Stocker dans table
            key = (event_type, num_events)
            lookup_table[key].append({
                'date': date,
                'impact': impact_real,
                'score_avg': cluster['score_avg'],
                'num_events': num_events
            })
            
            processed += 1
            
            if processed % 10 == 0:
                print(f"   Traité : {processed} clusters...")
        else:
            skipped_no_prices += 1
            
    except Exception as e:
        skipped_no_prices += 1
        continue

conn.close()

print(f"\n✅ Traitement terminé :")
print(f"   Clusters avec prix : {processed}")
print(f"   Clusters sans prix : {skipped_no_prices}")

# ============================================================================
# ÉTAPE 3 : CALCULER STATISTIQUES PAR CLUSTER TYPE
# ============================================================================

print("\n" + "="*100)
print("📊 TABLE DE RÉFÉRENCE EMPIRIQUE")
print("="*100)

results = []

for key, data_list in sorted(lookup_table.items()):
    event_type, num_events = key
    impacts = [d['impact'] for d in data_list]
    
    if len(impacts) >= 2:  # Minimum 2 observations
        mean_impact = np.mean(impacts)
        std_impact = np.std(impacts)
        median_impact = np.median(impacts)
        min_impact = np.min(impacts)
        max_impact = np.max(impacts)
        n_obs = len(impacts)
        
        # Coefficient de variation (pour mesurer stabilité)
        cv = (std_impact / mean_impact * 100) if mean_impact > 0 else 0
        
        results.append({
            'type': event_type,
            'num_events': num_events,
            'n_observations': n_obs,
            'impact_mean': mean_impact,
            'impact_std': std_impact,
            'impact_median': median_impact,
            'impact_min': min_impact,
            'impact_max': max_impact,
            'cv_pct': cv
        })

df_results = pd.DataFrame(results)
df_results = df_results.sort_values(['type', 'num_events'])

print("\nType    Events   N    Impact Moyen  Std    Médiane   Min    Max    CV%")
print("-"*90)

for _, row in df_results.iterrows():
    cv_flag = "✅" if row['cv_pct'] < 50 else "⚠️" if row['cv_pct'] < 100 else "❌"
    print(f"{row['type']:7} {row['num_events']:6}   {row['n_observations']:3}    "
          f"{row['impact_mean']:6.1f}p   {row['impact_std']:5.1f}p  "
          f"{row['impact_median']:6.1f}p  {row['impact_min']:5.1f}p  {row['impact_max']:6.1f}p  "
          f"{row['cv_pct']:5.1f}% {cv_flag}")

# ============================================================================
# ÉTAPE 4 : GÉNÉRER CODE PYTHON POUR INTÉGRATION
# ============================================================================

print("\n" + "="*100)
print("🔧 CODE PYTHON GÉNÉRÉ (copier dans formulas_validated.py)")
print("="*100)

print("\n# TABLE EMPIRIQUE LOOKUP - Générée Session 91")
print("# Format : (type, num_events) → impact_mean")
print("EMPIRICAL_LOOKUP_TABLE = {")

for _, row in df_results.iterrows():
    if row['n_observations'] >= 3:  # Minimum 3 observations pour confiance
        print(f"    ('{row['type']}', {row['num_events']}): {row['impact_mean']:.1f},  "
              f"# N={row['n_observations']}, CV={row['cv_pct']:.0f}%")

print("}")

# Sauvegarder code dans fichier
code_output = Path(__file__).parent / "formulas_empirical_lookup.py"
with open(code_output, 'w') as f:
    f.write('"""\nEMPIRICAL LOOKUP TABLE - Session 91\nGénérée automatiquement depuis historique DB\n"""\n\n')
    f.write('# TABLE EMPIRIQUE LOOKUP\n')
    f.write('# Format : (type, num_events) → impact_mean\n')
    f.write('EMPIRICAL_LOOKUP_TABLE = {\n')
    for _, row in df_results.iterrows():
        if row['n_observations'] >= 3:
            f.write(f"    ('{row['type']}', {row['num_events']}): {row['impact_mean']:.1f},  "
                   f"# N={row['n_observations']}, CV={row['cv_pct']:.0f}%\n")
    f.write('}\n\n')
    f.write('def calculate_impact_empirical(event_type, num_events, surprise_max=None):\n')
    f.write('    """\n')
    f.write('    Prédiction impact basée sur table empirique historique\n')
    f.write('    """\n')
    f.write('    key = (event_type, num_events)\n')
    f.write('    \n')
    f.write('    if key in EMPIRICAL_LOOKUP_TABLE:\n')
    f.write('        impact_base = EMPIRICAL_LOOKUP_TABLE[key]\n')
    f.write('        \n')
    f.write('        # Ajustement fin selon surprise (±15% max)\n')
    f.write('        if surprise_max is not None:\n')
    f.write('            surprise_factor = 1.0 + (surprise_max - 50) / 500\n')
    f.write('            surprise_factor = max(0.85, min(1.15, surprise_factor))\n')
    f.write('            impact = impact_base * surprise_factor\n')
    f.write('        else:\n')
    f.write('            impact = impact_base\n')
    f.write('        \n')
    f.write('        return {"impact": impact, "method": "empirical", "confidence": "HIGH"}\n')
    f.write('    else:\n')
    f.write('        return {"impact": None, "method": "no_data", "confidence": "NONE"}\n')

print(f"\n💾 Code sauvegardé : {code_output}")

# ============================================================================
# ÉTAPE 5 : SAUVEGARDER RÉSULTATS
# ============================================================================

output_path = Path(__file__).parent / "empirical_lookup_table.csv"
df_results.to_csv(output_path, index=False)

print(f"💾 Table sauvegardée : {output_path}")

print("\n" + "="*100)
print("✅ CONSTRUCTION TERMINÉE")
print("="*100)

print("\n📊 RÉSUMÉ :")
print(f"   Clusters analysés : {processed}")
print(f"   Combinaisons uniques : {len(df_results)}")
print(f"   Combinaisons fiables (N≥3) : {len(df_results[df_results['n_observations'] >= 3])}")
print(f"   Combinaisons stables (CV<50%) : {len(df_results[df_results['cv_pct'] < 50])}")

print("\n🎯 PROCHAINE ÉTAPE :")
print("   Exécuter : python3 build_empirical_lookup_table.py")
print("   Puis utiliser formulas_empirical_lookup.py dans tests")
