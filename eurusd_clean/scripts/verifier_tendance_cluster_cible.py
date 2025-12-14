#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VÉRIFICATION TENDANCE CLUSTER CIBLE - 1ER AOÛT 2025
====================================================

Vérifie pourquoi la tendance n'est pas détectée pour le cluster cible
du 1er août 2025.

Date: 2025-01-XX
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def verifier_tendance_cluster_cible():
    """Vérifie la détection de tendance pour le cluster cible"""
    
    date_str = '2025-08-01'
    
    print("\n" + "=" * 80)
    print(f"  VÉRIFICATION TENDANCE CLUSTER CIBLE - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=True)
    
    try:
        # Exécuter le pipeline
        result = executor.execute_complete_pipeline(
            date_str=date_str,
            window_minutes=30,
            support_threshold=0.8,
            jaccard_threshold=0.60,
            years_lookback=5
        )
        
        if not result['success']:
            print(f"❌ Erreur : {result.get('error', 'Erreur inconnue')}")
            return
        
        final_prediction = result['final_prediction']
        
        print()
        print("=" * 80)
        print("  ANALYSE DÉTECTION TENDANCE POUR CLUSTER CIBLE")
        print("=" * 80)
        print()
        
        # Vérifier les résultats de tendance dans la prédiction finale
        trend_exists = final_prediction.get('trend_exists', False)
        trend_r2 = final_prediction.get('trend_r2', 0.0)
        trend_direction = final_prediction.get('trend_direction', 'UNKNOWN')
        trend_amplitude_pips = final_prediction.get('trend_amplitude_pips', 0.0)
        
        print("📊 RÉSULTATS TENDANCE POUR CLUSTER CIBLE :")
        print("-" * 80)
        print()
        print(f"   Tendance détectée : {trend_exists}")
        print(f"   R² : {trend_r2:.3f}")
        print(f"   Direction : {trend_direction}")
        print(f"   Amplitude : {trend_amplitude_pips:.1f} pips")
        print()
        
        if not trend_exists:
            print("⚠️ PROBLÈME : Aucune tendance détectée pour le cluster cible")
            print()
            print("🔍 RECHERCHE DES CAUSES :")
            print("-" * 80)
            print()
            
            # Analyser pourquoi la tendance n'est pas détectée
            print("1️⃣ Vérification des paramètres de détection :")
            print()
            print("   Timeframe utilisé : M30 (par défaut selon documentation)")
            print("   Lookback days : 14 jours")
            print("   Segment hours : 12 heures")
            print("   Min R² : 0.15 (critère assoupli)")
            print("   Min hours before event : 12 heures (assoupli)")
            print()
            
            # Vérifier les prix disponibles
            print("2️⃣ Vérification des prix disponibles :")
            print()
            
            anchor_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
            lookback_days = 14
            start_dt = anchor_time - timedelta(days=lookback_days)
            end_dt = anchor_time + timedelta(days=6)
            
            print(f"   Période requise :")
            print(f"      De : {start_dt}")
            print(f"      À : {end_dt}")
            print()
            
            # Vérifier les prix
            conn = executor._get_connection()
            
            try:
                start_dt_iso = start_dt.isoformat()
                end_dt_iso = end_dt.isoformat()
                
                query = f"""
                SELECT COUNT(*) as count, 
                       MIN(datetime) as min_dt, 
                       MAX(datetime) as max_dt
                FROM prices_finnhub_m30
                WHERE datetime >= '{start_dt_iso}' AND datetime <= '{end_dt_iso}'
                """
                
                result_check = conn.execute(query).df()
                
                if not result_check.empty:
                    count = result_check.iloc[0]['count']
                    min_dt = result_check.iloc[0]['min_dt']
                    max_dt = result_check.iloc[0]['max_dt']
                    
                    print(f"   Prix M30 disponibles :")
                    print(f"      Nombre de barres : {count}")
                    print(f"      Première barre : {min_dt}")
                    print(f"      Dernière barre : {max_dt}")
                    
                    if count < 100:
                        print(f"      ⚠️ INSUFFISANT : Moins de 100 barres requises")
                    else:
                        print(f"      ✅ SUFFISANT : {count} barres disponibles")
                else:
                    print(f"   ❌ Aucun prix trouvé dans la période")
                
            except Exception as e:
                print(f"   ❌ Erreur vérification prix : {e}")
            
            print()
            
            # Vérifier la fonction de détection
            print("3️⃣ Test direct de la fonction de détection :")
            print()
            
            try:
                from src.core.trend_detection import detect_trend_by_inversion_s107
                
                # Charger les prix
                query = f"""
                SELECT datetime, open, high, low, close
                FROM prices_finnhub_m30
                WHERE datetime >= '{start_dt_iso}' AND datetime <= '{end_dt_iso}'
                ORDER BY datetime ASC
                """
                
                df_prices = conn.execute(query).df()
                
                if not df_prices.empty and len(df_prices) >= 100:
                    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
                    df_prices = df_prices.set_index('datetime')
                    prices_series = df_prices['close']
                    
                    # Trouver index événement
                    event_time_idx = None
                    for idx, dt in enumerate(prices_series.index):
                        if dt >= anchor_time:
                            event_time_idx = idx
                            break
                    
                    if event_time_idx is not None and event_time_idx > 0:
                        print(f"   Index événement dans série : {event_time_idx}")
                        print(f"   Nombre total de barres : {len(prices_series)}")
                        print()
                        
                        # Tester détection avec paramètres assouplis
                        print("   Test avec paramètres assouplis :")
                        print("      - segment_hours: 12")
                        print("      - min_r2_for_trend: 0.15")
                        print("      - min_hours_before_event: 12")
                        print()
                        
                        trend_result = detect_trend_by_inversion_s107(
                            prices=prices_series,
                            event_time_idx=event_time_idx,
                            lookback_days=lookback_days,
                            segment_hours=12,
                            min_r2_for_trend=0.15,
                            min_hours_before_event=12,
                            timeframe='M30'
                        )
                        
                        if trend_result:
                            print("   ✅ Résultat de détection :")
                            print(f"      Tendance détectée : {trend_result.get('trend_exists', False)}")
                            print(f"      R² : {trend_result.get('r2', 0.0):.3f}")
                            print(f"      Direction : {trend_result.get('direction', 'UNKNOWN')}")
                            print(f"      Amplitude : {trend_result.get('amplitude_pips', 0.0):.1f} pips")
                            
                            if not trend_result.get('trend_exists', False):
                                print()
                                print("   ⚠️ Pourquoi pas de tendance ?")
                                print(f"      R² calculé : {trend_result.get('r2', 0.0):.3f}")
                                print(f"      Seuil requis : 0.15")
                                
                                if trend_result.get('r2', 0.0) < 0.15:
                                    print(f"      → R² trop faible ({trend_result.get('r2', 0.0):.3f} < 0.15)")
                                
                                # Vérifier autres critères
                                if 'inversion_found' in trend_result:
                                    print(f"      Inversion trouvée : {trend_result.get('inversion_found', False)}")
                                
                                if 'reason' in trend_result:
                                    print(f"      Raison : {trend_result.get('reason', 'N/A')}")
                        else:
                            print("   ❌ Aucun résultat retourné par detect_trend_by_inversion_s107")
                            
                            # Tester avec paramètres encore plus assouplis
                            print()
                            print("   Test avec paramètres encore plus assouplis :")
                            print("      - min_r2_for_trend: 0.10")
                            print("      - min_hours_before_event: 6")
                            print()
                            
                            trend_result_relaxed = detect_trend_by_inversion_s107(
                                prices=prices_series,
                                event_time_idx=event_time_idx,
                                lookback_days=lookback_days,
                                segment_hours=12,
                                min_r2_for_trend=0.10,  # Encore plus assoupli
                                min_hours_before_event=6,  # Encore plus assoupli
                                timeframe='M30'
                            )
                            
                            if trend_result_relaxed:
                                print("   Résultat avec paramètres assouplis :")
                                print(f"      Tendance détectée : {trend_result_relaxed.get('trend_exists', False)}")
                                print(f"      R² : {trend_result_relaxed.get('r2', 0.0):.3f}")
                    else:
                        print(f"   ⚠️ Index événement non trouvé ou invalide")
                else:
                    print(f"   ❌ Pas assez de prix disponibles ({len(df_prices) if not df_prices.empty else 0} barres)")
                    
            except Exception as e:
                print(f"   ❌ Erreur test détection : {e}")
                import traceback
                traceback.print_exc()
            
        else:
            print("✅ Tendance détectée !")
            print()
            print(f"   R² : {trend_r2:.3f}")
            print(f"   Direction : {trend_direction}")
            print(f"   Amplitude : {trend_amplitude_pips:.1f} pips")
        
        print()
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verifier_tendance_cluster_cible()




