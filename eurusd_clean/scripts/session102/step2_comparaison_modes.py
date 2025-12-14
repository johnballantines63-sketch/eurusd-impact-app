#!/usr/bin/env python3
"""
STEP2 FLEXIBLE - COMPARAISON OR vs OR_JOBLESS
==============================================

Mesurer impacts réels et comparer les performances
des deux modes de filtrage sur les 30 clusters
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 80)
print("STEP2 FLEXIBLE - COMPARAISON OR vs OR_JOBLESS")
print("=" * 80)
print()

# ============================================================================
# CHARGER PRÉDICTIONS DES DEUX MODES
# ============================================================================

data_dir = Path(__file__).parent / "data"

file_or = data_dir / "step1_impacts_OR.csv"
file_or_jobless = data_dir / "step1_impacts_OR_JOBLESS.csv"

if not file_or.exists():
    print(f"❌ Fichier manquant : {file_or.name}")
    sys.exit(1)

if not file_or_jobless.exists():
    print(f"❌ Fichier manquant : {file_or_jobless.name}")
    sys.exit(1)

df_or = pd.read_csv(file_or)
df_or_jobless = pd.read_csv(file_or_jobless)

print(f"✅ Chargé : {len(df_or)} prédictions (mode OR)")
print(f"✅ Chargé : {len(df_or_jobless)} prédictions (mode OR_JOBLESS)")
print()

# ============================================================================
# MESURER IMPACTS RÉELS SUR CHAQUE CLUSTER
# ============================================================================

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("MESURE IMPACTS RÉELS (MT5 M1)")
print("=" * 80)
print()

results = []

for idx, row_or in df_or.iterrows():
    event_date = row_or['event_date']
    event_hour = row_or['event_hour']
    
    # Trouver ligne correspondante OR_JOBLESS
    row_jobless = df_or_jobless[
        (df_or_jobless['event_date'] == event_date) &
        (df_or_jobless['event_hour'] == event_hour)
    ]
    
    if len(row_jobless) == 0:
        print(f"⚠️  {event_date} {event_hour} : pas de correspondance, skip")
        continue
    
    row_jobless = row_jobless.iloc[0]
    
    # Construire timestamps pour mesure
    # prices_1m.datetime est en Europe/Zurich timezone
    dt_event = pd.Timestamp(f"{event_date} {event_hour}:00", tz='Europe/Zurich')
    dt_end = dt_event + pd.Timedelta(minutes=60)
    
    # Query prix
    query_prices = """
    SELECT close
    FROM prices_1m
    WHERE datetime >= ?
        AND datetime < ?
    """
    
    df_prices = conn.execute(query_prices, [
        dt_event,
        dt_end
    ]).fetchdf()
    
    if len(df_prices) < 10:
        print(f"⚠️  {event_date} {event_hour} : données insuffisantes ({len(df_prices)} minutes)")
        continue
    
    # Calculer impact réel (high-low dans fenêtre 60min)
    impact_reel_pips = (df_prices['close'].max() - df_prices['close'].min()) * 10000
    
    # Prédictions
    predit_or = row_or['impact_predit']
    predit_jobless = row_jobless['impact_predit']
    
    # Erreurs absolues
    erreur_or = abs(predit_or - impact_reel_pips)
    erreur_jobless = abs(predit_jobless - impact_reel_pips)
    
    # Sauvegarder
    results.append({
        'event_date': event_date,
        'event_hour': event_hour,
        'impact_reel': impact_reel_pips,
        'predit_OR': predit_or,
        'predit_OR_JOBLESS': predit_jobless,
        'erreur_OR': erreur_or,
        'erreur_OR_JOBLESS': erreur_jobless,
        'events_OR': row_or['num_events_dedup'],
        'events_OR_JOBLESS': row_jobless['num_events_dedup'],
        'meilleur_mode': 'OR' if erreur_or < erreur_jobless else 'OR_JOBLESS'
    })
    
    # Afficher
    marker_or = "✅" if erreur_or < erreur_jobless else "  "
    marker_jobless = "✅" if erreur_jobless < erreur_or else "  "
    
    print(f"{event_date} {event_hour} | Réel: {impact_reel_pips:5.1f} pips")
    print(f"{marker_or}  OR         : {predit_or:5.1f} ({row_or['num_events_dedup']} ev) → err {erreur_or:5.1f}")
    print(f"{marker_jobless}  OR_JOBLESS : {predit_jobless:5.1f} ({row_jobless['num_events_dedup']} ev) → err {erreur_jobless:5.1f}")
    print()

conn.close()

# ============================================================================
# CALCUL MÉTRIQUES GLOBALES
# ============================================================================

df_results = pd.DataFrame(results)

if len(df_results) == 0:
    print("❌ Aucun résultat valide !")
    sys.exit(1)

print()
print("=" * 80)
print("RÉSULTATS GLOBAUX SUR", len(df_results), "CLUSTERS")
print("=" * 80)
print()

# MAE et RMSE
mae_or = df_results['erreur_OR'].mean()
mae_jobless = df_results['erreur_OR_JOBLESS'].mean()

rmse_or = np.sqrt((df_results['erreur_OR'] ** 2).mean())
rmse_jobless = np.sqrt((df_results['erreur_OR_JOBLESS'] ** 2).mean())

# Corrélation
corr_or = df_results['predit_OR'].corr(df_results['impact_reel'])
corr_jobless = df_results['predit_OR_JOBLESS'].corr(df_results['impact_reel'])

# Victoires cas par cas
victoires_or = (df_results['meilleur_mode'] == 'OR').sum()
victoires_jobless = (df_results['meilleur_mode'] == 'OR_JOBLESS').sum()

# Affichage
print(f"{'Métrique':<25} {'OR (sans jobless)':>20} {'OR_JOBLESS (avec)':>20} {'Meilleur':>15}")
print("-" * 85)

meilleur_mae = "OR ✅" if mae_or < mae_jobless else "OR_JOBLESS ✅"
print(f"{'MAE (pips)':<25} {mae_or:>20.2f} {mae_jobless:>20.2f} {meilleur_mae:>15}")

meilleur_rmse = "OR ✅" if rmse_or < rmse_jobless else "OR_JOBLESS ✅"
print(f"{'RMSE (pips)':<25} {rmse_or:>20.2f} {rmse_jobless:>20.2f} {meilleur_rmse:>15}")

meilleur_corr = "OR ✅" if corr_or > corr_jobless else "OR_JOBLESS ✅"
print(f"{'Corrélation':<25} {corr_or:>20.3f} {corr_jobless:>20.3f} {meilleur_corr:>15}")

print()
print(f"{'Victoires (cas par cas)':<25} {victoires_or:>20} {victoires_jobless:>20}")
print()

# ============================================================================
# SAUVEGARDER
# ============================================================================

output_path = data_dir / "step2_comparaison_modes.csv"
df_results.to_csv(output_path, index=False)

print("=" * 80)
print(f"✅ Résultats détaillés sauvegardés : {output_path.name}")
print("=" * 80)
print()

# ============================================================================
# CONCLUSION FINALE
# ============================================================================

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()

if mae_or < mae_jobless and rmse_or < rmse_jobless:
    print("🎯 GAGNANT CLAIR : MODE OR (sans jobless claims faibles)")
    print()
    print("EXPLICATION :")
    print("  Les jobless claims (empirical_score = 26.8) DILUENT le score moyen")
    print("  et causent une SOUS-ESTIMATION systématique de l'impact réel.")
    print()
    print("RECOMMANDATION FINALE :")
    print("  ✅ Utiliser filtre : (importance_n = 1) OR (empirical_score > 40)")
    print("  ❌ Ne PAS inclure d'exception pour jobless claims")
    print()
    print("  Le seuil empirical_score > 40 est validé !")
    
elif mae_jobless < mae_or and rmse_jobless < rmse_or:
    print("🎯 GAGNANT CLAIR : MODE OR_JOBLESS (avec jobless claims)")
    print()
    print("EXPLICATION :")
    print("  Inclure les jobless claims AMÉLIORE significativement")
    print("  la précision des prédictions sur l'ensemble des cas.")
    print()
    print("RECOMMANDATION FINALE :")
    print("  ✅ Utiliser filtre avec exception jobless :")
    print("     (importance_n = 1) OR (score > 40) OR (jobless > 25)")
    
else:
    print("⚖️  RÉSULTATS MIXTES")
    print()
    print("Les deux modes ont des forces et faiblesses selon les cas.")
    print("Analyser step2_comparaison_modes.csv pour comprendre les patterns.")
    print()
    print(f"Tendance MAE  : {'OR' if mae_or < mae_jobless else 'OR_JOBLESS'} meilleur")
    print(f"Tendance RMSE : {'OR' if rmse_or < rmse_jobless else 'OR_JOBLESS'} meilleur")
    print(f"Victoires     : OR={victoires_or}, OR_JOBLESS={victoires_jobless}")
