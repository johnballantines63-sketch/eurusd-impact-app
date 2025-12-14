#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFFICHAGE DÉTAILLÉ DES PICS ET PULLBACKS DÉTECTÉS
==================================================

Affiche en détail les pics et pullbacks détectés dans les prix réels
et les compare avec les valeurs prédites.

Date: 2025-01-XX
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz
import duckdb

# Ajouter le chemin parent pour les imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'session120'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor
from double_wave_detector_rev12 import detect_for_date_duckdb_rev12
from core.price_loader_finnhub import get_finnhub_prices_at_event_time

TZ_BERN = pytz.timezone('Europe/Zurich')

def afficher_detection_reelle(pattern_real_result, event_time):
    """Affiche les détails de la détection réelle dans les prix"""
    if not pattern_real_result:
        print("⚠️ Aucune détection réelle disponible")
        return
    
    print("\n" + "=" * 80)
    print("  DÉTECTION RÉELLE DANS LES PRIX (REV12)")
    print("=" * 80)
    print()
    
    double_wave = pattern_real_result.get('double_wave', False)
    confidence = pattern_real_result.get('confidence', 0.0)
    
    print(f"📊 Pattern : {'DOUBLE WAVE' if double_wave else 'SINGLE WAVE'}")
    print(f"   Confiance : {confidence:.1f}%")
    print()
    
    baseline_price = pattern_real_result.get('baseline_price')
    if baseline_price:
        baseline_time = pattern_real_result.get('baseline_time')
        print(f"💰 BASELINE (Prix de référence) :")
        print(f"   Prix : {baseline_price:.5f}")
        print(f"   Heure : {format_timestamp(baseline_time)}")
        print()
    
    # Wave 1
    wave1_pips = pattern_real_result.get('wave1_pips', 0.0)
    peak1_time = pattern_real_result.get('peak1_time')
    peak1_price = pattern_real_result.get('peak1_price')
    
    if wave1_pips > 0 and peak1_time:
        print(f"📈 WAVE 1 (Premier pic) :")
        print(f"   Impact : {wave1_pips:.1f} pips")
        print(f"   Heure : {format_timestamp(peak1_time)}")
        if peak1_price:
            print(f"   Prix : {peak1_price:.5f}")
        print()
    
    # Pullback 1
    pullback1_pips = pattern_real_result.get('pullback1_pips', 0.0)
    pullback1_time = pattern_real_result.get('pullback1_time')
    pullback1_price = pattern_real_result.get('pullback1_price')
    pullback1_ratio = pattern_real_result.get('pullback1_ratio', 0.0)
    
    if pullback1_time:
        print(f"📉 PULLBACK 1 (Creux) :")
        print(f"   Retracement : {pullback1_pips:.1f} pips")
        print(f"   Heure : {format_timestamp(pullback1_time)}")
        if pullback1_price:
            print(f"   Prix : {pullback1_price:.5f}")
        if pullback1_ratio > 0:
            print(f"   Ratio : {pullback1_ratio * 100:.1f}% de Wave 1")
        print()
    
    # Wave 2 (si Double Wave)
    if double_wave:
        wave2_pips = pattern_real_result.get('wave2_pips', 0.0)
        peak2_time = pattern_real_result.get('peak2_time')
        peak2_price = pattern_real_result.get('peak2_price')
        
        if wave2_pips > 0 and peak2_time:
            print(f"📈 WAVE 2 (Pic absolu) :")
            print(f"   Impact total : {wave2_pips:.1f} pips")
            print(f"   Heure : {format_timestamp(peak2_time)}")
            if peak2_price:
                print(f"   Prix : {peak2_price:.5f}")
            print()

def format_timestamp(ts):
    """Formate un timestamp pour affichage"""
    if ts is None:
        return "N/A"
    if isinstance(ts, pd.Timestamp):
        return ts.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(ts, datetime):
        return ts.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(ts, str):
        try:
            dt = pd.to_datetime(ts)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return ts
    return str(ts)

def charger_prix_autour_event(event_time, lookback_minutes=60, lookahead_minutes=120):
    """Charge les prix autour d'un événement pour visualisation"""
    df_prices = get_finnhub_prices_at_event_time(
        db_path=DB_PATH,
        event_timestamp_bern=event_time,
        lookback_minutes=lookback_minutes,
        lookahead_minutes=lookahead_minutes
    )
    
    if df_prices.empty:
        return None
    
    # Convertir datetime si nécessaire
    if 'datetime' in df_prices.columns:
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    return df_prices

def trouver_pics_manuels(df_prices, baseline_price, event_time):
    """Trouve manuellement les pics et pullbacks dans les prix"""
    if df_prices is None or df_prices.empty:
        return None
    
    # Filtrer prix après événement
    prices_after = df_prices[df_prices['datetime'] >= event_time].copy()
    
    if prices_after.empty:
        return None
    
    # Calculer pips depuis baseline
    prices_after['pips_high'] = (prices_after['high'] - baseline_price) * 10000
    prices_after['pips_low'] = (baseline_price - prices_after['low']) * 10000
    
    # Trouver pic maximum (Wave 1)
    peak1_idx = prices_after['pips_high'].idxmax()
    peak1_time = prices_after.loc[peak1_idx, 'datetime']
    peak1_price = prices_after.loc[peak1_idx, 'high']
    peak1_pips = prices_after.loc[peak1_idx, 'pips_high']
    
    # Chercher pullback après Wave 1
    prices_after_peak1 = prices_after[prices_after['datetime'] > peak1_time].copy()
    
    pullback1_time = None
    pullback1_price = None
    pullback1_pips = 0.0
    
    if not prices_after_peak1.empty:
        # Chercher le creux minimum dans les 30 min après peak1
        window_30min = prices_after_peak1[
            (prices_after_peak1['datetime'] - peak1_time).dt.total_seconds() / 60 <= 30
        ]
        
        if not window_30min.empty:
            pullback1_idx = window_30min['pips_low'].idxmax()  # Plus grand creux = retracement max
            pullback1_time = prices_after_peak1.loc[pullback1_idx, 'datetime']
            pullback1_price = prices_after_peak1.loc[pullback1_idx, 'low']
            pullback1_pips = (peak1_price - pullback1_price) * 10000
    
    # Chercher Wave 2 (pic absolu après pullback)
    peak2_time = None
    peak2_price = None
    peak2_pips = 0.0
    
    if pullback1_time:
        prices_after_pullback = prices_after[prices_after['datetime'] > pullback1_time].copy()
        
        if not prices_after_pullback.empty:
            # Chercher dans les 60 min après pullback
            window_60min = prices_after_pullback[
                (prices_after_pullback['datetime'] - pullback1_time).dt.total_seconds() / 60 <= 60
            ]
            
            if not window_60min.empty:
                peak2_idx = window_60min['pips_high'].idxmax()
                peak2_time = prices_after_pullback.loc[peak2_idx, 'datetime']
                peak2_price = prices_after_pullback.loc[peak2_idx, 'high']
                peak2_pips = (peak2_price - baseline_price) * 10000
    
    return {
        'baseline_price': baseline_price,
        'peak1_time': peak1_time,
        'peak1_price': peak1_price,
        'peak1_pips': peak1_pips,
        'pullback1_time': pullback1_time,
        'pullback1_price': pullback1_price,
        'pullback1_pips': pullback1_pips,
        'peak2_time': peak2_time,
        'peak2_price': peak2_price,
        'peak2_pips': peak2_pips
    }

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Affiche les pics et pullbacks détectés en détail')
    parser.add_argument('--date', type=str, default='2025-09-11', help='Date au format YYYY-MM-DD')
    parser.add_argument('--verbose', action='store_true', help='Mode verbose')
    
    args = parser.parse_args()
    
    date_str = args.date
    
    print()
    print("=" * 80)
    print(f"  ANALYSE DÉTAILLÉE DES PICS ET PULLBACKS - {date_str}")
    print("=" * 80)
    print()
    
    # Déterminer heure événement CPI US (14:30 Bern)
    event_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print(f"📅 Date : {date_str}")
    print(f"⏰ Événement : CPI US à 14:30 Bern")
    print(f"   Timestamp : {event_time}")
    print()
    
    # 1. Détection réelle dans les prix (REV12)
    print("=" * 80)
    print("  1. DÉTECTION RÉELLE DANS LES PRIX (REV12)")
    print("=" * 80)
    print()
    
    try:
        pattern_date = event_time.replace(tzinfo=None)  # Naive pour REV12
        pattern_real_result = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_finnhub_m1',
            date=pattern_date,
            tz='Europe/Zurich',
            baseline_mode='prev_close_14_29',
            minutes_after_hint=120,
            trading_window=True,
            debug=True  # Afficher détails
        )
        
        if pattern_real_result:
            afficher_detection_reelle(pattern_real_result, event_time)
        else:
            print("⚠️ Aucun pattern détecté par REV12")
            print()
    except Exception as e:
        print(f"❌ Erreur détection REV12 : {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # 2. Recherche manuelle des pics dans les prix
    print()
    print("=" * 80)
    print("  2. RECHERCHE MANUELLE DES PICS DANS LES PRIX")
    print("=" * 80)
    print()
    
    try:
        # Charger prix
        df_prices = charger_prix_autour_event(event_time, lookback_minutes=60, lookahead_minutes=120)
        
        if df_prices is not None and not df_prices.empty:
            # Trouver baseline (prix juste avant événement)
            prices_before = df_prices[df_prices['datetime'] < event_time]
            if not prices_before.empty:
                baseline_price = prices_before.iloc[-1]['close']
            else:
                baseline_price = df_prices.iloc[0]['open']
            
            print(f"💰 Prix baseline : {baseline_price:.5f}")
            print()
            
            # Trouver pics manuellement
            pics_manuels = trouver_pics_manuels(df_prices, baseline_price, event_time)
            
            if pics_manuels:
                print(f"📈 WAVE 1 (Premier pic) :")
                print(f"   Impact : {pics_manuels['peak1_pips']:.1f} pips")
                print(f"   Heure : {format_timestamp(pics_manuels['peak1_time'])}")
                print(f"   Prix : {format_price(pics_manuels['peak1_price'])}")
                print()
                
                if pics_manuels['pullback1_time']:
                    print(f"📉 PULLBACK 1 (Creux) :")
                    print(f"   Retracement : {pics_manuels['pullback1_pips']:.1f} pips")
                    print(f"   Heure : {format_timestamp(pics_manuels['pullback1_time'])}")
                    print(f"   Prix : {format_price(pics_manuels['pullback1_price'])}")
                    if pics_manuels['peak1_pips'] > 0:
                        ratio = (pics_manuels['pullback1_pips'] / pics_manuels['peak1_pips']) * 100
                        print(f"   Ratio : {ratio:.1f}% de Wave 1")
                    print()
                
                if pics_manuels['peak2_time']:
                    print(f"📈 WAVE 2 (Pic absolu) :")
                    print(f"   Impact total : {pics_manuels['peak2_pips']:.1f} pips")
                    print(f"   Heure : {format_timestamp(pics_manuels['peak2_time'])}")
                    print(f"   Prix : {format_price(pics_manuels['peak2_price'])}")
                    print()
        else:
            print("⚠️ Aucun prix trouvé")
            print()
            
    except Exception as e:
        print(f"❌ Erreur recherche manuelle : {e}")
        import traceback
        traceback.print_exc()
        print()
    
    # 3. Résultats du pipeline (prédictions)
    print()
    print("=" * 80)
    print("  3. PRÉDICTIONS DU PIPELINE")
    print("=" * 80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=False)
    
    try:
        result = executor.execute_complete_pipeline(
            date_str=date_str,
            window_minutes=30,
            support_threshold=0.8,
            jaccard_threshold=0.60,
            years_lookback=5
        )
        
        if result['success']:
            final_prediction = result['final_prediction']
            pattern_info = final_prediction.get('pattern_info', {})
            
            print(f"📊 Pattern prédit : {pattern_info.get('pattern_type', 'NONE')}")
            print()
            
            if pattern_info.get('pattern_type') != 'NONE':
                baseline_price = final_prediction.get('baseline_price')
                
                if baseline_price:
                    print(f"💰 Prix baseline : {baseline_price:.5f}")
                    print()
                
                wave1_pips = pattern_info.get('wave1_pips', 0.0)
                wave1_time = pattern_info.get('wave1_peak_time')
                
                if wave1_time:
                    print(f"📈 WAVE 1 (Prédit) :")
                    print(f"   Impact : {wave1_pips:.1f} pips")
                    print(f"   Heure : {format_timestamp(wave1_time)}")
                    if baseline_price and wave1_pips > 0:
                        wave1_price = baseline_price + (wave1_pips / 10000)
                        print(f"   Prix : {wave1_price:.5f}")
                    print()
                
                pullback_pips = pattern_info.get('pullback_pips', 0.0)
                pullback_time = pattern_info.get('pullback_low_time')
                
                if pullback_time:
                    print(f"📉 PULLBACK (Prédit) :")
                    print(f"   Retracement : {pullback_pips:.1f} pips")
                    print(f"   Heure : {format_timestamp(pullback_time)}")
                    if baseline_price and wave1_pips > 0:
                        pullback_price = baseline_price + ((wave1_pips - pullback_pips) / 10000)
                        print(f"   Prix : {pullback_price:.5f}")
                    print()
                
                wave2_pips = pattern_info.get('wave2_peak_pips_absolute', 0.0)
                wave2_time = pattern_info.get('wave2_peak_time')
                
                if wave2_time:
                    print(f"📈 WAVE 2 (Prédit - Pic Absolu) :")
                    print(f"   Impact total : {wave2_pips:.1f} pips")
                    print(f"   Heure : {format_timestamp(wave2_time)}")
                    if baseline_price and wave2_pips > 0:
                        wave2_price = baseline_price + (wave2_pips / 10000)
                        print(f"   Prix : {wave2_price:.5f}")
                    print()
        else:
            print(f"❌ Erreur pipeline : {result.get('error', 'Erreur inconnue')}")
            
    except Exception as e:
        print(f"❌ Erreur pipeline : {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("  FIN DE L'ANALYSE")
    print("=" * 80)
    print()

def format_price(price):
    """Formate un prix pour affichage"""
    if price is None:
        return "N/A"
    return f"{price:.5f}"

if __name__ == "__main__":
    main()




