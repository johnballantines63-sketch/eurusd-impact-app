#!/usr/bin/env python3
"""
SESSION 125 - ÉTAPE 4 : CALCULER FACTEUR IDÉAL 11 SEPTEMBRE (CORRIGÉ TIMEZONE)
===============================================================================
Trouve le facteur d'amplification qui prédit exactement 56.2 pips

CORRECTION : Utiliser heures UTC (12:30) pas Bern (14:30)
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
import json

print("="*80)
print("SESSION 125 - CALCUL FACTEUR IDÉAL 11 SEPTEMBRE")
print("="*80)
print()

# Configuration
DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
OUTPUT_DIR = Path(__file__).parent / "results_11sept"
OUTPUT_DIR.mkdir(exist_ok=True)

TARGET_IMPACT = 56.2  # Impact réel MT5 (pips)
TARGET_DATE = '2025-09-11'

# CORRECTION : Utiliser heures UTC (DB stocke en UTC)
TARGET_TIME_START_UTC = '2025-09-11 12:25:00'  # 14:25 Bern = 12:25 UTC
TARGET_TIME_END_UTC = '2025-09-11 12:35:00'    # 14:35 Bern = 12:35 UTC

print(f"🎯 Cas référence : {TARGET_DATE}")
print(f"📊 Impact réel MT5 : {TARGET_IMPACT} pips")
print(f"⏰ Fenêtre cluster UTC : 12:25-12:35 (= 14:25-14:35 Bern)")
print()

# ============================================================================
# ÉTAPE 1 : CHARGER ÉVÉNEMENTS 11 SEPTEMBRE
# ============================================================================

print("="*80)
print("ÉTAPE 1 : CHARGEMENT ÉVÉNEMENTS 11 SEPTEMBRE")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Charger événements HIGH autour 14:30 Bern = 12:30 UTC
df_events = conn.execute("""
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE datetime_utc >= ?
      AND datetime_utc <= ?
      AND importance = 'HIGH'
    ORDER BY datetime_utc
""", [TARGET_TIME_START_UTC, TARGET_TIME_END_UTC]).df()

conn.close()

print(f"✅ {len(df_events)} événements HIGH détectés (12:25-12:35 UTC)")
print()

if len(df_events) == 0:
    print("❌ AUCUN événement trouvé dans cette fenêtre !")
    print("   → Élargir fenêtre à 12:00-13:00 UTC")
    
    # Réessayer avec fenêtre plus large
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    df_events = conn.execute("""
        SELECT 
            datetime_utc,
            event_name,
            country,
            importance,
            actual,
            forecast,
            previous
        FROM economic_events
        WHERE datetime_utc >= '2025-09-11 12:00:00'
          AND datetime_utc <= '2025-09-11 13:00:00'
          AND importance = 'HIGH'
        ORDER BY datetime_utc
    """).df()
    conn.close()
    
    print(f"   ✅ {len(df_events)} événements HIGH (12:00-13:00 UTC)")
    print()

if len(df_events) == 0:
    print("❌ Toujours aucun événement !")
    sys.exit(1)

# Afficher événements
print("📋 Événements du cluster :")
for _, e in df_events.iterrows():
    dt_utc = pd.to_datetime(e['datetime_utc'], utc=True)
    dt_bern = dt_utc.tz_convert('Europe/Zurich')
    print(f"   UTC {e['datetime_utc']} (Bern {dt_bern.strftime('%H:%M')}) - {e['event_name']:40s} ({e['country']})")
print()

# ============================================================================
# ÉTAPE 2 : MAPPER SCORES EMPIRIQUES
# ============================================================================

print("="*80)
print("ÉTAPE 2 : MAPPING SCORES EMPIRIQUES")
print("="*80)
print()

df_scores = pd.read_csv(SCORES_PATH)

df_events = df_events.merge(
    df_scores[['event_name', 'country', 'empirical_score', 'sample_size', 'avg_movement_pips']],
    on=['event_name', 'country'],
    how='left'
)

# Filtrer mesurables
df_measurable = df_events[
    df_events['sample_size'].notna() & (df_events['sample_size'] > 0)
].copy()

print(f"✅ {len(df_measurable)}/{len(df_events)} événements avec score empirique")
print()

if len(df_measurable) == 0:
    print("❌ AUCUN événement mesurable trouvé !")
    print("\nÉvénements sans score :")
    for _, e in df_events[df_events['sample_size'].isna()].iterrows():
        print(f"   {e['event_name']:40s} - {e['country']}")
    sys.exit(1)

# Afficher scores
print("📊 Scores empiriques :")
total_score = 0
for _, e in df_measurable.iterrows():
    print(f"   {e['event_name']:40s} - Score: {e['empirical_score']:.2f} pips")
    total_score += e['empirical_score']
print()
print(f"📊 Score total brut : {total_score:.2f} pips")
print()

# ============================================================================
# ÉTAPE 3 : CALCUL SURPRISES
# ============================================================================

print("="*80)
print("ÉTAPE 3 : CALCUL SURPRISES")
print("="*80)
print()

# Note : actual/forecast = NaN dans DB EODHD
print("⚠️  Données actual/forecast = NaN (DB EODHD incomplet)")
print("   → Utilisation scores bruts (pas d'ajustement surprise)")
print()

surprise_factor = 1.0
n_events = len(df_measurable)

# ============================================================================
# ÉTAPE 4 : CALCULER FACTEUR IDÉAL
# ============================================================================

print("="*80)
print("ÉTAPE 4 : CALCUL FACTEUR AMPLIFICATION IDÉAL")
print("="*80)
print()

print("📐 Formule calculate_impact_d (Session 51) :")
print("   impact = score × amplification × sqrt(n_events) × surprise_factor")
print()
print("📐 Résolution pour amplification :")
print("   amplification = impact / (score × sqrt(n_events) × surprise_factor)")
print()

# Calculer facteur idéal
denominator = total_score * np.sqrt(n_events) * surprise_factor

if denominator == 0:
    print("❌ ERREUR : Dénominateur = 0")
    sys.exit(1)

amplification_ideal = TARGET_IMPACT / denominator

print(f"📊 Paramètres :")
print(f"   Impact cible       : {TARGET_IMPACT:.2f} pips")
print(f"   Score total        : {total_score:.2f}")
print(f"   Nombre événements  : {n_events}")
print(f"   Facteur surprise   : {surprise_factor:.4f}")
print(f"   sqrt(n_events)     : {np.sqrt(n_events):.4f}")
print()

print(f"🎯 FACTEUR IDÉAL = {amplification_ideal:.4f}")
print()

# Vérification
impact_calculated = total_score * amplification_ideal * np.sqrt(n_events) * surprise_factor
error = abs(impact_calculated - TARGET_IMPACT)

print(f"✅ Vérification :")
print(f"   Impact calculé : {impact_calculated:.2f} pips")
print(f"   Impact réel    : {TARGET_IMPACT:.2f} pips")
print(f"   Erreur         : {error:.4f} pips")
print()

if error < 0.01:
    print(f"   ✅✅✅ PARFAIT (erreur < 0.01 pips)")
else:
    print(f"   ⚠️ Erreur {error:.4f} pips")
print()

# ============================================================================
# ÉTAPE 5 : SAUVEGARDER CAS RÉFÉRENCE
# ============================================================================

print("="*80)
print("ÉTAPE 5 : SAUVEGARDE CAS RÉFÉRENCE")
print("="*80)
print()

cas_reference = {
    'date': TARGET_DATE,
    'pattern': 'Double Wave overlapping',
    'cluster': {
        'time_utc': TARGET_TIME_START_UTC + ' - ' + TARGET_TIME_END_UTC,
        'time_bern': '14:25-14:35',
        'events': df_measurable[['event_name', 'country', 'empirical_score']].to_dict('records'),
        'num_events': int(n_events),
        'total_score': float(total_score)
    },
    'impact': {
        'target_pips': float(TARGET_IMPACT),
        'calculated_pips': float(impact_calculated),
        'error_pips': float(error)
    },
    'amplification': {
        'ideal_factor': float(amplification_ideal),
        'surprise_factor': float(surprise_factor),
        'sqrt_n_events': float(np.sqrt(n_events))
    },
    'tendance_pre_cluster': {
        'r2': 0.6376,  # Session 107
        'duration_hours': 54.58,
        'inversion_time': '2025-09-09 08:00:00',
        'type': 'PEAK'
    }
}

# Sauvegarder JSON
output_json = OUTPUT_DIR / "cas_reference_11sept.json"
with open(output_json, 'w') as f:
    json.dump(cas_reference, f, indent=2)

print(f"💾 Cas référence sauvegardé : {output_json.name}")
print()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("="*80)
print("RÉSUMÉ - CAS RÉFÉRENCE 11 SEPTEMBRE 2025")
print("="*80)
print()

print(f"📅 Date              : {TARGET_DATE}")
print(f"🕐 Cluster UTC       : 12:30 ({n_events} événements)")
print(f"🕐 Cluster Bern      : 14:30")
print(f"📊 Score total       : {total_score:.2f} pips")
print(f"🎯 Impact réel       : {TARGET_IMPACT:.2f} pips")
print()

print(f"🔧 FACTEUR IDÉAL     : {amplification_ideal:.4f}")
print()

print(f"📈 Tendance pré-cluster :")
print(f"   R² inversion     : 0.6376")
print(f"   Durée            : 54.58 heures")
print(f"   Type             : PEAK → DOWN")
print()

print("="*80)
print("ÉTAPE 4 TERMINÉE ✅")
print("="*80)
print()

print("🎯 PROCHAINES ÉTAPES :")
print("   5. Établir cas référence (documentation)")
print("   6. Chercher clusters identiques dans historique")
print("   7. Calculer tendances pré-cluster pour chaque cas")
print("   8. Tester corrélation R² ↔ facteur amplification")
