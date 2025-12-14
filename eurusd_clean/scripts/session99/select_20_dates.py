"""
SÉLECTION 20 DATES CPI POUR VALIDATION ÉTENDUE
===============================================

Session 99 - Validation formule amplification dynamique sur échantillon élargi

OBJECTIF :
- Sélectionner 20 dates CPI US (10 testées S98 + 10 nouvelles)
- Vérifier disponibilité prix MT5 pour chaque date
- Créer fichier dates_validation_20.csv

CRITÈRES :
- Country = 'US'
- Score > 40 (HIGH impact)
- Clusters ≥ 5 événements simultanés
- Prix disponibles dans prices_1m

Date : 29 octobre 2025
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

import pandas as pd
import duckdb
from config import get_db_path

print("="*80)
print("🎯 SÉLECTION 20 DATES CPI POUR VALIDATION ÉTENDUE")
print("="*80)

# Dates testées Session 98 (10 dates)
dates_s98 = [
    '2025-09-11',
    '2025-01-15',
    '2025-05-13',
    '2025-07-15',
    '2025-08-12',
    '2025-06-11',
    '2025-04-10',
    '2025-02-12',
    '2024-12-11',
    '2024-11-13'
]

print(f"\n✅ Dates testées Session 98 : {len(dates_s98)}")
for i, date in enumerate(dates_s98, 1):
    print(f"   {i:2}. {date}")

# Charger tous les clusters disponibles
clusters_file = Path(__file__).parent.parent / "session98" / "clusters_cpi_nfp_disponibles.csv"
clusters = pd.read_csv(clusters_file)

print(f"\n📊 Clusters CPI disponibles : {len(clusters)}")

# Sélectionner 10 nouvelles dates (plus récentes + diversité temporelle)
nouvelles_dates = []

# Filtrer dates non testées
clusters_non_testes = clusters[~clusters['date'].isin(dates_s98)].copy()
print(f"\n🆕 Clusters non testés : {len(clusters_non_testes)}")

# Stratégie : Prendre les 10 plus récentes non testées
clusters_non_testes = clusters_non_testes.sort_values('date', ascending=False)
nouvelles_dates_selected = clusters_non_testes['date'].head(10).tolist()

print(f"\n✅ 10 nouvelles dates sélectionnées :")
for i, date in enumerate(nouvelles_dates_selected, 1):
    print(f"   {i:2}. {date}")

# Combiner les 20 dates
dates_20 = dates_s98 + nouvelles_dates_selected
dates_20.sort(reverse=True)  # Trier du plus récent au plus ancien

print(f"\n🎯 TOTAL : {len(dates_20)} dates sélectionnées")

# Vérifier disponibilité prix pour chaque date
print(f"\n🔍 VÉRIFICATION DISPONIBILITÉ PRIX...")
print(f"   {'Date':12} {'Heure':10} {'Prix Disponibles':20} {'Status':10}")
print(f"   {'-'*60}")

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

dates_valides = []

for date_str in dates_20:
    # Récupérer info cluster
    cluster_info = clusters[clusters['date'] == date_str].iloc[0]
    heure = cluster_info['heure']
    
    # Construire timestamp événement (UTC+2 Bern time)
    dt = datetime.strptime(f"{date_str} {heure}", "%Y-%m-%d %H:%M:%S")
    
    # Vérifier prix disponibles (±2h autour événement)
    start_time = dt - timedelta(hours=2)
    end_time = dt + timedelta(hours=2)
    
    query = f"""
    SELECT COUNT(*) as count
    FROM prices_1m
    WHERE timestamp >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
        AND timestamp <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
    """
    
    result = conn.execute(query).fetchone()
    prix_count = result[0] if result else 0
    
    status = "✅ OK" if prix_count > 100 else "❌ MANQUANT"
    
    print(f"   {date_str:12} {heure:10} {prix_count:>8} prix {status:10}")
    
    if prix_count > 100:
        dates_valides.append({
            'date': date_str,
            'heure': heure,
            'timestamp': cluster_info['timestamp_complet'],
            'num_events': cluster_info['num_events'],
            'score_moyen': cluster_info['score_moyen'],
            'tested_s98': 'OUI' if date_str in dates_s98 else 'NON'
        })

conn.close()

print(f"\n✅ Dates avec prix disponibles : {len(dates_valides)}")

# Si moins de 20 dates valides, alerter
if len(dates_valides) < 20:
    print(f"\n⚠️ ATTENTION : Seulement {len(dates_valides)} dates avec prix disponibles")
    print(f"   Cible : 20 dates")
    print(f"   Manquantes : {20 - len(dates_valides)} dates")

# Sauvegarder liste finale
output_file = Path(__file__).parent / "dates_validation_20.csv"
df_dates = pd.DataFrame(dates_valides)
df_dates.to_csv(output_file, index=False)

print(f"\n💾 Fichier sauvegardé : {output_file}")

# Statistiques
print(f"\n📊 STATISTIQUES :")
print(f"   Dates Session 98     : {df_dates[df_dates['tested_s98']=='OUI'].shape[0]}")
print(f"   Nouvelles dates      : {df_dates[df_dates['tested_s98']=='NON'].shape[0]}")
print(f"   Total                : {len(df_dates)}")

print("\n" + "="*80)
print("✅ SÉLECTION 20 DATES TERMINÉE")
print("="*80)
