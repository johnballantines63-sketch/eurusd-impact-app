"""
BUILD EMPIRICAL LOOKUP TABLE V2 - Session 91
CORRECTION SQL : Retirer ORDER BY dans STRING_AGG avec DISTINCT
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
print("🏗️ CONSTRUCTION TABLE EMPIRIQUE V2 - CLUSTERS EXACTS RÉPÉTÉS")
print("="*100)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# ============================================================================
# ÉTAPE 1 : IDENTIFIER CLUSTERS RÉPÉTÉS (MÊME COMPOSITION)
# ============================================================================

print("\n📊 Étape 1 : Identifier clusters qui se répètent...\n")

query_clusters = """
WITH cluster_composition AS (
    SELECT 
        DATE(e.ts_utc) as event_date,
        strftime(e.ts_utc, '%H:%M') as event_time,
        STRING_AGG(e.event_key, '|' ORDER BY e.event_key) as event_keys_signature,
        STRING_AGG(e.event_title, ' + ' ORDER BY e.event_title) as event_titles,
        COUNT(DISTINCT e.event_key) as num_events,
        e.country
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.country = 'US'
        AND ef.empirical_score > 40
        AND DATE(e.ts_utc) >= '2020-01-01'
        AND DATE(e.ts_utc) <= '2025-12-31'
    GROUP BY DATE(e.ts_utc), strftime(e.ts_utc, '%H:%M'), e.country
    HAVING COUNT(DISTINCT e.event_key) >= 3
)
SELECT 
    event_keys_signature,
    event_titles,
    num_events,
    COUNT(*) as occurrences,
    STRING_AGG(event_date::VARCHAR, ', ') as dates_list
FROM cluster_composition
GROUP BY event_keys_signature, event_titles, num_events
HAVING COUNT(*) >= 3
ORDER BY COUNT(*) DESC, num_events DESC
LIMIT 50
"""

df_repeated = conn.execute(query_clusters).df()

print(f"   Clusters répétés trouvés : {len(df_repeated)}")
print(f"   Critères : ≥3 occurrences, même composition exacte\n")

# Afficher top 10
print("🔝 TOP 10 CLUSTERS RÉPÉTÉS :\n")
print(f"{'N°':>3} {'Occur':>6} {'Events':>7} {'Composition':<50}")
print("-"*90)

for idx, row in df_repeated.head(10).iterrows():
    title_short = row['event_titles'][:47] + "..." if len(row['event_titles']) > 50 else row['event_titles']
    print(f"{idx+1:3d} {row['occurrences']:6d} {row['num_events']:7d} {title_short:<50}")

# ============================================================================
# ÉTAPE 2 : POUR CHAQUE CLUSTER RÉPÉTÉ, CALCULER IMPACTS ET SURPRISES
# ============================================================================

print("\n\n📈 Étape 2 : Analyser chaque occurrence des clusters répétés...\n")

cluster_analysis = []

for idx, cluster_row in df_repeated.iterrows():
    signature = cluster_row['event_keys_signature']
    num_events = cluster_row['num_events']
    occurrences = cluster_row['occurrences']
    
    print(f"   [{idx+1}/{len(df_repeated)}] Cluster {num_events} events, {occurrences} occurrences...")
    
    # Récupérer toutes les dates de ce cluster
    query_dates = f"""
    SELECT DISTINCT
        DATE(e.ts_utc) as event_date,
        strftime(e.ts_utc, '%H:%M') as event_time
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.country = 'US'
        AND ef.empirical_score > 40
    GROUP BY DATE(e.ts_utc), strftime(e.ts_utc, '%H:%M')
    HAVING STRING_AGG(e.event_key, '|' ORDER BY e.event_key) = '{signature}'
    ORDER BY event_date DESC
    """
    
    df_dates = conn.execute(query_dates).df()
    
    impacts_list = []
    surprises_list = []
    
    for _, date_row in df_dates.iterrows():
        date = date_row['event_date']
        time = date_row['event_time']
        
        # Calculer surprise max pour cette occurrence
        query_surprise = f"""
        SELECT 
            e.event_key,
            e.actual,
            e.estimate,
            e.forecast,
            e.previous
        FROM events e
        WHERE DATE(e.ts_utc) = '{date}'
            AND strftime(e.ts_utc, '%H:%M') = '{time}'
            AND e.country = 'US'
        """
        
        df_events = conn.execute(query_surprise).df()
        
        # Calculer surprise (logique simplifiée)
        surprises = []
        for _, evt in df_events.iterrows():
            actual = evt['actual']
            estimate = evt['estimate'] if pd.notna(evt['estimate']) else evt.get('previous')
            
            if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
                surprise = abs((actual - estimate) / estimate) * 100
                surprises.append(min(surprise, 500))  # Cap 500%
        
        surprise_max = max(surprises) if surprises else 0
        
        # Mesurer impact réel
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
                
                impacts_list.append(impact_real)
                surprises_list.append(surprise_max)
        except:
            continue
    
    # Analyser si cluster a impacts stables
    if len(impacts_list) >= 3:
        impacts_array = np.array(impacts_list)
        surprises_array = np.array(surprises_list)
        
        impact_mean = np.mean(impacts_array)
        impact_std = np.std(impacts_array)
        impact_cv = (impact_std / impact_mean * 100) if impact_mean > 0 else 0
        
        surprise_mean = np.mean(surprises_array)
        surprise_std = np.std(surprises_array)
        
        # Corrélation surprise → impact
        if len(impacts_array) >= 3 and surprise_std > 0:
            correlation = np.corrcoef(surprises_array, impacts_array)[0, 1]
        else:
            correlation = 0
        
        cluster_analysis.append({
            'signature': signature[:50],
            'num_events': num_events,
            'occurrences': len(impacts_list),
            'impact_mean': impact_mean,
            'impact_std': impact_std,
            'impact_cv': impact_cv,
            'surprise_mean': surprise_mean,
            'surprise_std': surprise_std,
            'correlation': correlation,
            'event_titles': cluster_row['event_titles'][:60]
        })

conn.close()

# ============================================================================
# ÉTAPE 3 : RÉSULTATS - VALIDATION HYPOTHÈSE
# ============================================================================

print("\n\n" + "="*100)
print("🎯 VALIDATION HYPOTHÈSE : Cluster stable malgré surprises variables ?")
print("="*100)

df_analysis = pd.DataFrame(cluster_analysis)
df_analysis = df_analysis.sort_values('occurrences', ascending=False)

print("\nCluster                   N    Impact     CV%    Surpr   Surpr  Corr")
print("                              Moyen             Moy     Std    S→I")
print("-"*90)

for _, row in df_analysis.head(20).iterrows():
    cv_flag = "✅" if row['impact_cv'] < 50 else "⚠️" if row['impact_cv'] < 100 else "❌"
    corr_flag = "🔴" if abs(row['correlation']) > 0.7 else "⚠️" if abs(row['correlation']) > 0.4 else "✅"
    
    print(f"{row['event_titles'][:25]:25} {row['occurrences']:3d}   {row['impact_mean']:5.1f}p   "
          f"{row['impact_cv']:5.1f}% {cv_flag}  {row['surprise_mean']:5.1f}%  {row['surprise_std']:5.1f}%  "
          f"{row['correlation']:5.2f} {corr_flag}")

print("\n\n📊 INTERPRÉTATION :")
print("   CV% < 50%  = ✅ Impact stable (hypothèse validée)")
print("   CV% > 50%  = ❌ Impact variable (surprise importante)")
print("\n   Corr < 0.4 = ✅ Surprise peu prédictive (hypothèse validée)")
print("   Corr > 0.7 = 🔴 Surprise très prédictive (hypothèse rejetée)")

# Statistiques globales
stable_clusters = len(df_analysis[df_analysis['impact_cv'] < 50])
low_corr_clusters = len(df_analysis[abs(df_analysis['correlation']) < 0.4])

print(f"\n\n✅ RÉSULTATS GLOBAUX :")
print(f"   Clusters stables (CV<50%) : {stable_clusters}/{len(df_analysis)} ({stable_clusters/len(df_analysis)*100:.0f}%)")
print(f"   Clusters à faible corrélation surprise (|r|<0.4) : {low_corr_clusters}/{len(df_analysis)} ({low_corr_clusters/len(df_analysis)*100:.0f}%)")

if stable_clusters / len(df_analysis) > 0.6 and low_corr_clusters / len(df_analysis) > 0.6:
    print("\n🎉 HYPOTHÈSE VALIDÉE !")
    print("   La majorité des clusters ont impacts stables malgré surprises variables.")
else:
    print("\n⚠️ HYPOTHÈSE PARTIELLEMENT VALIDÉE")
    print("   Certains clusters dépendent de la surprise, d'autres non.")

# Sauvegarder
output_path = Path(__file__).parent / "cluster_analysis_validation.csv"
df_analysis.to_csv(output_path, index=False)
print(f"\n💾 Analyse sauvegardée : {output_path}")

print("\n" + "="*100)
print("✅ ANALYSE TERMINÉE")
print("="*100)
