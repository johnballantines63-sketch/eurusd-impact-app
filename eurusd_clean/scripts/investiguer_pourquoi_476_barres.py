#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGATION : POURQUOI SEULEMENT 476 BARRES ?
===============================================

Analyse pourquoi on n'a que 476 barres au lieu des 672 barres théoriques
(14 jours * 48 barres/jour = 672 barres).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import pytz
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

def investiguer_pourquoi_476_barres():
    """Investigation détaillée du nombre de barres"""
    
    date_str = '2025-08-01'
    anchor_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  INVESTIGATION : POURQUOI SEULEMENT 476 BARRES ?")
    print("=" * 80)
    print()
    
    print(f"📅 Date : {date_str}")
    print(f"⏰ Anchor time : {anchor_time}")
    print()
    
    # Connexion DB
    conn = duckdb.connect(str(DB_PATH))
    
    # 1. Vérifier les prix disponibles dans la base
    print("=" * 80)
    print("  1. PRIX DISPONIBLES DANS LA BASE")
    print("=" * 80)
    print()
    
    # Période large : 30 jours avant et après
    start_large = anchor_time - timedelta(days=30)
    end_large = anchor_time + timedelta(days=30)
    
    query_large = f"""
    SELECT COUNT(*) as count, 
           MIN(datetime) as min_dt, 
           MAX(datetime) as max_dt
    FROM prices_finnhub_m30
    WHERE datetime >= '{start_large.isoformat()}' AND datetime <= '{end_large.isoformat()}'
    """
    
    result_large = conn.execute(query_large).df()
    
    if not result_large.empty:
        count_large = result_large.iloc[0]['count']
        min_dt = result_large.iloc[0]['min_dt']
        max_dt = result_large.iloc[0]['max_dt']
        
        print(f"📊 Prix disponibles (30 jours avant/après) :")
        print(f"   Nombre total : {count_large} barres")
        print(f"   Première barre : {min_dt}")
        print(f"   Dernière barre : {max_dt}")
        print()
    
    # 2. Période chargée dans l'étape 8
    print("=" * 80)
    print("  2. PÉRIODE CHARGÉE DANS L'ÉTAPE 8")
    print("=" * 80)
    print()
    
    lookback_days = 14
    start_dt_etape8 = anchor_time - timedelta(days=lookback_days)
    end_dt_etape8 = anchor_time + timedelta(days=6)  # Besoin de données après pour mesurer tendance
    
    print(f"📊 Période chargée dans l'étape 8 :")
    print(f"   De : {start_dt_etape8}")
    print(f"   À : {end_dt_etape8}")
    print(f"   Durée : {(end_dt_etape8 - start_dt_etape8).days} jours")
    print()
    
    query_etape8 = f"""
    SELECT COUNT(*) as count
    FROM prices_finnhub_m30
    WHERE datetime >= '{start_dt_etape8.isoformat()}' AND datetime <= '{end_dt_etape8.isoformat()}'
    """
    
    result_etape8 = conn.execute(query_etape8).df()
    
    if not result_etape8.empty:
        count_etape8 = result_etape8.iloc[0]['count']
        print(f"   Nombre de barres chargées : {count_etape8}")
        print(f"   Barres théoriques (20 jours * 48) : {20 * 48} = 960 barres")
        print()
    
    # 3. Période utilisée dans detect_trend_by_inversion_s107
    print("=" * 80)
    print("  3. PÉRIODE UTILISÉE DANS detect_trend_by_inversion_s107")
    print("=" * 80)
    print()
    
    # Simuler la logique de detect_trend_by_inversion_s107
    event_datetime = anchor_time
    query_dt = event_datetime - timedelta(hours=2)  # Event - 2h
    start_dt_s107 = query_dt - timedelta(days=lookback_days)
    
    # Pour M30 : end_dt_for_window = query_dt (pas de données après)
    end_dt_s107 = query_dt
    
    print(f"📊 Période utilisée dans detect_trend_by_inversion_s107 :")
    print(f"   Event datetime : {event_datetime}")
    print(f"   Query dt (event - 2h) : {query_dt}")
    print(f"   Start dt (query - 14 jours) : {start_dt_s107}")
    print(f"   End dt (query_dt, pas de données après) : {end_dt_s107}")
    print(f"   Durée : {(end_dt_s107 - start_dt_s107).days} jours + {((end_dt_s107 - start_dt_s107).seconds / 3600):.1f} heures")
    print()
    
    query_s107 = f"""
    SELECT COUNT(*) as count,
           MIN(datetime) as min_dt,
           MAX(datetime) as max_dt
    FROM prices_finnhub_m30
    WHERE datetime >= '{start_dt_s107.isoformat()}' AND datetime < '{end_dt_s107.isoformat()}'
    """
    
    result_s107 = conn.execute(query_s107).df()
    
    if not result_s107.empty:
        count_s107 = result_s107.iloc[0]['count']
        min_dt_s107 = result_s107.iloc[0]['min_dt']
        max_dt_s107 = result_s107.iloc[0]['max_dt']
        
        print(f"   Nombre de barres disponibles : {count_s107}")
        print(f"   Première barre : {min_dt_s107}")
        print(f"   Dernière barre : {max_dt_s107}")
        print()
        
        # Calculer barres théoriques
        hours_diff = (end_dt_s107 - start_dt_s107).total_seconds() / 3600
        bars_theoretical = int(hours_diff / 0.5)  # M30 = 0.5h par barre
        
        print(f"   Barres théoriques : {hours_diff:.1f} heures / 0.5h = {bars_theoretical} barres")
        print(f"   Barres réelles : {count_s107} barres")
        print(f"   Différence : {bars_theoretical - count_s107} barres manquantes")
        print()
    
    # 4. Vérifier les heures de trading
    print("=" * 80)
    print("  4. VÉRIFICATION HEURES DE TRADING")
    print("=" * 80)
    print()
    
    # Compter barres par jour
    query_by_day = f"""
    SELECT DATE(datetime) as date, COUNT(*) as count
    FROM prices_finnhub_m30
    WHERE datetime >= '{start_dt_s107.isoformat()}' AND datetime < '{end_dt_s107.isoformat()}'
    GROUP BY DATE(datetime)
    ORDER BY date ASC
    """
    
    result_by_day = conn.execute(query_by_day).df()
    
    if not result_by_day.empty:
        print(f"📊 Barres par jour :")
        print()
        for _, row in result_by_day.iterrows():
            date = row['date']
            count = row['count']
            print(f"   {date} : {count} barres")
        
        print()
        print(f"   Moyenne : {result_by_day['count'].mean():.1f} barres/jour")
        print(f"   Min : {result_by_day['count'].min()} barres")
        print(f"   Max : {result_by_day['count'].max()} barres")
        print()
        
        # Vérifier si certains jours ont moins de 48 barres (jours de trading incomplets)
        incomplete_days = result_by_day[result_by_day['count'] < 48]
        if not incomplete_days.empty:
            print(f"   ⚠️ Jours avec moins de 48 barres :")
            for _, row in incomplete_days.iterrows():
                print(f"      {row['date']} : {row['count']} barres")
            print()
    
    # 5. Vérifier les gaps dans les données
    print("=" * 80)
    print("  5. VÉRIFICATION GAPS DANS LES DONNÉES")
    print("=" * 80)
    print()
    
    query_gaps = f"""
    SELECT datetime
    FROM prices_finnhub_m30
    WHERE datetime >= '{start_dt_s107.isoformat()}' AND datetime < '{end_dt_s107.isoformat()}'
    ORDER BY datetime ASC
    """
    
    df_gaps = conn.execute(query_gaps).df()
    
    if not df_gaps.empty:
        df_gaps['datetime'] = pd.to_datetime(df_gaps['datetime'])
        df_gaps = df_gaps.set_index('datetime')
        
        # Calculer intervalles entre barres
        df_gaps['time_diff'] = df_gaps.index.to_series().diff()
        
        # Trouver gaps > 1h (normalement M30 = 30 min)
        gaps_large = df_gaps[df_gaps['time_diff'] > pd.Timedelta(hours=1)]
        
        if not gaps_large.empty:
            print(f"⚠️ Gaps détectés (> 1h) : {len(gaps_large)} gaps")
            print()
            print("   Premiers gaps :")
            for idx, (dt, row) in enumerate(gaps_large.head(10).iterrows()):
                gap_hours = row['time_diff'].total_seconds() / 3600
                print(f"      {dt} : gap de {gap_hours:.1f} heures")
            print()
        else:
            print("✅ Aucun gap significatif détecté")
            print()
    
    conn.close()
    
    print("=" * 80)
    print()

if __name__ == "__main__":
    investiguer_pourquoi_476_barres()




