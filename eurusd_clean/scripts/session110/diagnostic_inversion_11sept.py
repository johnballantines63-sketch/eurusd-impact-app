"""
SESSION 110 - DIAGNOSTIC DÉTECTION INVERSION
=============================================

Compare détection inversion mon script vs Session 107-108
Cas test : 11.09.2025

Date : 3 novembre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import duckdb

# Setup
session110_dir = Path(__file__).parent
scripts_dir = session110_dir.parent
project_root = scripts_dir.parent
sys.path.insert(0, str(project_root / "app"))
sys.path.insert(0, str(session110_dir))

from dynamic_amplification import detect_trend_by_inversion, load_prices_from_db
from config import Config

print("="*80)
print("DIAGNOSTIC DÉTECTION INVERSION - 11.09.2025")
print("="*80)

# Configuration
config = Config()
db_path = Path(config.get_db_path())

# Date test : 11.09.2025 CPI 14:30 Bern
event_time = pd.to_datetime("2025-09-11 14:30:00")
event_time = event_time.tz_localize('Europe/Zurich')

print(f"\n📅 Date test : 11.09.2025")
print(f"   Event time : {event_time}")

# Charger résultat attendu Session 107
phase1_file = scripts_dir / "session109" / "phase1_all_metrics_17dates.csv"
df = pd.read_csv(phase1_file)
row_11sept = df[df['date'] == '2025-09-11'].iloc[0]

print(f"\n✅ RÉSULTAT ATTENDU (SESSION 107) :")
print(f"   Duration : {row_11sept['duration_hours']:.2f}h")
print(f"   Type : {row_11sept['reversal_type']}")
print(f"   R² : {row_11sept['r2_linear']:.4f}")

# Calculer datetime inversion attendue
inversion_expected = event_time - timedelta(hours=row_11sept['duration_hours'])
print(f"   Datetime inversion : {inversion_expected}")

# Charger prix
print(f"\n📊 Chargement prix...")
prices_df = load_prices_from_db(db_path, event_time)
print(f"   {len(prices_df)} points chargés")

# Tester mon algorithme
print(f"\n🔍 TEST MON ALGORITHME :")
inversion_detected = detect_trend_by_inversion(prices_df, event_time)

if inversion_detected:
    print(f"   ✅ Inversion détectée !")
    print(f"   Type : {inversion_detected['inversion_type']}")
    print(f"   Datetime : {inversion_detected['inversion_time']}")
    print(f"   Duration : {inversion_detected['hours_before_event']:.2f}h")
    print(f"   R² avant : {inversion_detected['r2_before']:.4f}")
    print(f"   R² après : {inversion_detected['r2_after']:.4f}")
    
    # Calculer différence
    diff_hours = abs(inversion_detected['hours_before_event'] - row_11sept['duration_hours'])
    diff_time = abs((inversion_detected['inversion_time'] - inversion_expected).total_seconds() / 3600)
    
    print(f"\n📊 COMPARAISON :")
    print(f"   Différence duration : {diff_hours:.2f}h")
    print(f"   Différence temps : {diff_time:.2f}h")
    
    if diff_hours < 1:
        print(f"   ✅ EXCELLENT : < 1h de différence")
    elif diff_hours < 5:
        print(f"   ⚠️ ACCEPTABLE : < 5h de différence")
    else:
        print(f"   ❌ PROBLÈME : > 5h de différence")
        
    # Charger prix depuis inversion détectée vs attendue
    print(f"\n📊 ANALYSE DONNÉES PRIX :")
    
    # Mon inversion
    mask_mine = (prices_df['datetime'] >= inversion_detected['inversion_time']) & \
                (prices_df['datetime'] <= event_time)
    df_mine = prices_df[mask_mine].copy()
    
    # Inversion attendue
    mask_expected = (prices_df['datetime'] >= inversion_expected) & \
                    (prices_df['datetime'] <= event_time)
    df_expected = prices_df[mask_expected].copy()
    
    print(f"   Mon inversion : {len(df_mine)} points")
    print(f"   Attendue : {len(df_expected)} points")
    
else:
    print(f"   ❌ AUCUNE inversion détectée !")
    print(f"\n🚨 PROBLÈME CRITIQUE : Mon algorithme ne trouve rien")
    
# Testons aussi avec paramètres différents
print(f"\n" + "="*80)
print("TEST AVEC PARAMÈTRES AJUSTÉS")
print("="*80)

# Test 1 : Segments plus courts
from dynamic_amplification import (
    SEGMENT_HOURS, MIN_R2_FOR_TREND, 
    LOOKBACK_DAYS, MIN_HOURS_BEFORE_EVENT
)

print(f"\nParamètres actuels :")
print(f"   SEGMENT_HOURS : {SEGMENT_HOURS}h")
print(f"   MIN_R2_FOR_TREND : {MIN_R2_FOR_TREND}")
print(f"   LOOKBACK_DAYS : {LOOKBACK_DAYS}")
print(f"   MIN_HOURS_BEFORE_EVENT : {MIN_HOURS_BEFORE_EVENT}h")

# Regardons le script Session 107 pour voir leurs paramètres
session107_script = scripts_dir / "session107" / "phase2e_cluster3_inversion_trend.py"
print(f"\n📄 Lire paramètres Session 107...")

try:
    with open(session107_script, 'r') as f:
        content = f.read()
        
    # Chercher paramètres
    if 'segment_duration' in content:
        print("   ✅ Fichier Session 107 trouvé")
        # Extraire lignes pertinentes
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'segment_duration' in line or 'min_r2' in line.lower() or 'lookback' in line.lower():
                print(f"   {line.strip()}")
    else:
        print("   ⚠️ Paramètres non trouvés directement")
        
except Exception as e:
    print(f"   ❌ Erreur lecture : {e}")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLET")
print("="*80)

if inversion_detected:
    diff_hours = abs(inversion_detected['hours_before_event'] - row_11sept['duration_hours'])
    if diff_hours < 5:
        print("\n✅ MON ALGORITHME FONCTIONNE")
        print(f"   Différence acceptable : {diff_hours:.2f}h")
        print("\n💡 PROBLÈME : Calcul amplification avec ces inversions")
    else:
        print("\n❌ MON ALGORITHME DÉTECTE DIFFÉREMMENT")
        print(f"   Différence : {diff_hours:.2f}h")
        print("\n💡 ACTION : Ajuster paramètres détection")
else:
    print("\n❌ MON ALGORITHME NE DÉTECTE RIEN")
    print("\n💡 ACTION URGENTE : Déboguer détection")

print("\n" + "="*80)
