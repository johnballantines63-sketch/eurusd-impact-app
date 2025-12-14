#!/usr/bin/env python3
"""
ÉTAPE 2 : MESURER IMPACTS RÉELS
================================

Pour chaque date dans step1_impacts_predits_NEW.csv :
1. Charger prix depuis prices_1m
2. Prix départ : 12:29 UTC (1 min avant événement à 12:30 UTC)
3. Fenêtre : 120 minutes après événement
4. Impact réel : peak_close - price_start (en pips)

ENTRÉE : step1_impacts_predits_NEW.csv
SORTIE : step2_impacts_reels_NEW.csv
"""

import sys
from pathlib import Path
import duckdb
from datetime import datetime, timedelta
import pandas as pd

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 80)
print("ÉTAPE 2 : MESURER IMPACTS RÉELS")
print("=" * 80)
print()

# ============================================================================
# CHARGER RÉSULTATS STEP1
# ============================================================================

data_dir = Path(__file__).parent / "data"
step1_path = data_dir / "step1_impacts_predits_NEW.csv"

if not step1_path.exists():
    print(f"❌ Fichier manquant : {step1_path.name}")
    print(f"   → Exécuter d'abord : python3 step1_calculer_impacts_NEW.py")
    sys.exit(1)

df_step1 = pd.read_csv(step1_path)
df_step1['event_date'] = pd.to_datetime(df_step1['event_date'])

print(f"✅ {len(df_step1)} dates à traiter")
print()

# Connexion DB
db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# MESURER IMPACT RÉEL POUR CHAQUE DATE
# ============================================================================

results = []

for idx, row in df_step1.iterrows():
    event_date = row['event_date']
    
    # Événements US CPI à 14:30 Berne = 12:30 UTC
    event_time_utc = event_date.replace(hour=12, minute=30, second=0)
    
    # Prix départ : 1 minute avant
    time_start = event_time_utc - timedelta(minutes=1)
    
    # Essayer d'obtenir prix à 12:29 exactement
    query_start = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime = ?
    LIMIT 1
    """
    
    df_start = conn.execute(query_start, [time_start]).fetchdf()
    
    # Fallback : dernier prix avant événement
    if len(df_start) == 0:
        query_start = """
        SELECT datetime, close
        FROM prices_1m
        WHERE datetime < ?
        ORDER BY datetime DESC
        LIMIT 1
        """
        df_start = conn.execute(query_start, [event_time_utc]).fetchdf()
    
    if len(df_start) == 0:
        print(f"⚠️  {event_date.strftime('%Y-%m-%d')} : Pas de prix départ")
        continue
    
    price_start = df_start.iloc[0]['close']
    time_start_actual = df_start.iloc[0]['datetime']
    
    # Fenêtre 120 minutes après événement
    time_end = event_time_utc + timedelta(minutes=120)
    
    query_window = """
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime > ?
      AND datetime <= ?
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_window, [event_time_utc, time_end]).fetchdf()
    
    if len(df_prices) == 0:
        print(f"⚠️  {event_date.strftime('%Y-%m-%d')} : Pas de prix dans fenêtre")
        continue
    
    # Trouver peak et trough
    max_close = df_prices['close'].max()
    min_close = df_prices['close'].min()
    
    # Calculer mouvements UP et DOWN
    movement_up = (max_close - price_start) * 10000
    movement_down = (price_start - min_close) * 10000
    
    # Impact = plus grand mouvement absolu
    if movement_up > movement_down:
        impact_real = movement_up
        peak_used = max_close
        direction = "UP"
    else:
        impact_real = movement_down
        peak_used = min_close
        direction = "DOWN"
    
    results.append({
        'event_date': event_date.strftime('%Y-%m-%d'),
        'price_start': price_start,
        'time_start': time_start_actual,
        'peak_close': peak_used,
        'impact_real': impact_real,
        'direction': direction,
        'num_prices': len(df_prices)
    })
    
    print(f"✅ {event_date.strftime('%Y-%m-%d')} : "
          f"start={price_start:.5f}, peak={peak_used:.5f}, "
          f"impact={impact_real:.1f} pips ({direction})")

conn.close()

# ============================================================================
# SAUVEGARDER
# ============================================================================

df_results = pd.DataFrame(results)
output_path = data_dir / "step2_impacts_reels_NEW.csv"
df_results.to_csv(output_path, index=False)

print()
print("=" * 80)
print(f"✅ ÉTAPE 2 TERMINÉE : {len(results)} cas traités")
print(f"✅ Sauvegardé : {output_path.name}")
print("=" * 80)
print()
print("📊 STATISTIQUES :")
print(f"   Impact réel moyen : {df_results['impact_real'].mean():.1f} pips")
print(f"   Impact réel min   : {df_results['impact_real'].min():.1f} pips")
print(f"   Impact réel max   : {df_results['impact_real'].max():.1f} pips")
print()
print("➡️  PROCHAINE ÉTAPE : python3 step3_amplifications_parfaites_NEW.py")
