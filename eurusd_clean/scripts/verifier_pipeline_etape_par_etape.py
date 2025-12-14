#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VÉRIFICATION PIPELINE ÉTAPE PAR ÉTAPE - 1ER AOÛT 2025
======================================================

Vérifie que toutes les étapes du pipeline sont appliquées correctement
pour le 1er août 2025.

Date: 2025-01-XX
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def verifier_pipeline_etape_par_etape():
    """Vérifie chaque étape du pipeline"""
    
    date_str = '2025-08-01'
    
    print("\n" + "=" * 80)
    print(f"  VÉRIFICATION PIPELINE ÉTAPE PAR ÉTAPE - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=True)
    
    try:
        # Exécuter le pipeline avec logs détaillés
        result = executor.execute_complete_pipeline(
            date_str=date_str,
            window_minutes=30,
            support_threshold=0.8,
            jaccard_threshold=0.60,
            years_lookback=5
        )
        
        if not result['success']:
            print(f"❌ Erreur pipeline : {result.get('error', 'Erreur inconnue')}")
            return
        
        results = result.get('results', {})
        final_prediction = result['final_prediction']
        
        print()
        print("=" * 80)
        print("  VÉRIFICATION DÉTAILLÉE DE CHAQUE ÉTAPE")
        print("=" * 80)
        print()
        
        # ========================================================================
        # ÉTAPE 1 : Charger événements
        # ========================================================================
        
        print("1️⃣ ÉTAPE 1 : CHARGER ÉVÉNEMENTS")
        print("-" * 80)
        
        if 'etape1_events' in results:
            events_df = results['etape1_events']
            print(f"   ✅ Événements chargés : {len(events_df)} événements")
            
            if not events_df.empty:
                print(f"   Premier événement : {events_df.iloc[0].get('event_name', 'N/A')}")
                print(f"   Dernier événement : {events_df.iloc[-1].get('event_name', 'N/A')}")
                print(f"   Période : {events_df['ts_utc'].min()} → {events_df['ts_utc'].max()}")
        else:
            print(f"   ⚠️ Résultats étape 1 non trouvés")
        
        print()
        
        # ========================================================================
        # ÉTAPE 2 : Détecter clusters
        # ========================================================================
        
        print("2️⃣ ÉTAPE 2 : DÉTECTER CLUSTERS")
        print("-" * 80)
        
        if 'etape2_clusters' in results:
            clusters = results['etape2_clusters']
            print(f"   ✅ Clusters détectés : {len(clusters)} cluster(s)")
            
            for i, cluster in enumerate(clusters, 1):
                num_events = len(cluster.get('events', []))
                anchor_time = cluster.get('anchor_time', 'N/A')
                print(f"   Cluster {i}: {num_events} événements, anchor: {anchor_time}")
        else:
            print(f"   ⚠️ Résultats étape 2 non trouvés")
        
        print()
        
        # ========================================================================
        # ÉTAPE 3 : Définir noyau dur
        # ========================================================================
        
        print("3️⃣ ÉTAPE 3 : DÉFINIR NOYAU DUR")
        print("-" * 80)
        
        if 'etape3_core' in results:
            core = results['etape3_core']
            print(f"   ✅ Noyau dur défini")
            print(f"   Événements noyau dur : {len(core.get('core_events', []))}")
            print(f"   Support : {core.get('support', 0):.2%}")
        else:
            print(f"   ⚠️ Résultats étape 3 non trouvés")
        
        print()
        
        # ========================================================================
        # ÉTAPE 4 : Rechercher clusters identiques
        # ========================================================================
        
        print("4️⃣ ÉTAPE 4 : RECHERCHER CLUSTERS IDENTIQUES")
        print("-" * 80)
        
        if 'etape4_identical_clusters' in results:
            identical = results['etape4_identical_clusters']
            print(f"   ✅ Clusters identiques trouvés : {len(identical)} cluster(s)")
            
            if identical:
                for i, cluster in enumerate(identical[:5], 1):  # Afficher les 5 premiers
                    cluster_date = cluster.get('cluster_date', 'N/A')
                    jaccard = cluster.get('jaccard_similarity', 0.0)
                    print(f"   Cluster {i}: {cluster_date}, Jaccard: {jaccard:.3f}")
        else:
            print(f"   ⚠️ Résultats étape 4 non trouvés")
        
        print()
        
        # ========================================================================
        # ÉTAPE 5 : Calculer tendances
        # ========================================================================
        
        print("5️⃣ ÉTAPE 5 : CALCULER TENDANCES")
        print("-" * 80)
        
        if 'etape5_tendances' in results:
            tendances_df = results['etape5_tendances']
            
            if not tendances_df.empty:
                print(f"   ✅ Tendances calculées : {len(tendances_df)} tendance(s)")
                
                for idx, row in tendances_df.iterrows():
                    r2 = row.get('r2', 0.0)
                    direction = row.get('direction', 'UNKNOWN')
                    amplitude = row.get('amplitude_pips', 0.0)
                    trend_exists = row.get('trend_exists', False)
                    
                    print(f"   Cluster {idx+1}:")
                    print(f"      Tendance détectée : {trend_exists}")
                    print(f"      R² : {r2:.3f}")
                    print(f"      Direction : {direction}")
                    print(f"      Amplitude : {amplitude:.1f} pips")
            else:
                print(f"   ⚠️ Aucune tendance calculée (DataFrame vide)")
        else:
            print(f"   ⚠️ Résultats étape 5 non trouvés")
        
        print()
        
        # ========================================================================
        # ÉTAPE 6 : Calculer impacts base et amplifications
        # ========================================================================
        
        print("6️⃣ ÉTAPE 6 : CALCULER IMPACTS BASE ET AMPLIFICATIONS")
        print("-" * 80)
        
        if 'etape6_impacts' in results:
            impacts_df = results['etape6_impacts']
            
            if not impacts_df.empty:
                print(f"   ✅ Impacts calculés : {len(impacts_df)} impact(s)")
                
                for idx, row in impacts_df.iterrows():
                    impact_base = row.get('impact_base', 0.0)
                    impact_reel = row.get('impact_reel', 0.0)
                    amplification_parfaite = row.get('amplification_parfaite', 1.0)
                    direction = row.get('direction', 0)
                    
                    print(f"   Cluster {idx+1}:")
                    print(f"      Impact de base : {impact_base:.2f} pips")
                    print(f"      Impact réel : {impact_reel:.2f} pips")
                    print(f"      Amplification parfaite : {amplification_parfaite:.3f}x")
                    print(f"      Direction : {direction}")
            else:
                print(f"   ⚠️ Aucun impact calculé (DataFrame vide)")
        else:
            print(f"   ⚠️ Résultats étape 6 non trouvés")
        
        print()
        
        # ========================================================================
        # ÉTAPE 7 : Analyser relation tendance → amplification
        # ========================================================================
        
        print("7️⃣ ÉTAPE 7 : ANALYSER RELATION TENDANCE → AMPLIFICATION")
        print("-" * 80)
        
        if 'etape7_analysis' in results:
            etape7 = results['etape7_analysis']
            
            print(f"   ✅ Analyse réalisée")
            
            # Vérifier ce qui a été retourné
            amplification_predite = etape7.get('amplification_predite', 1.0)
            method_used = etape7.get('method_used', 'unknown')
            correlations = etape7.get('correlations', {})
            results_df = etape7.get('results_df', pd.DataFrame())
            
            print(f"   Amplification prédite : {amplification_predite:.3f}x")
            print(f"   Méthode utilisée : {method_used}")
            
            if correlations:
                print(f"   Corrélations :")
                for key, value in correlations.items():
                    print(f"      {key} : {value:.3f}")
            
            if not results_df.empty:
                print(f"   DataFrame résultats : {len(results_df)} lignes")
                
                # Vérifier colonnes disponibles
                print(f"   Colonnes disponibles : {', '.join(results_df.columns.tolist())}")
                
                # Vérifier si Random Forest aurait pu être utilisé
                if 'amplification_parfaite' in results_df.columns and 'r2' in results_df.columns:
                    num_clusters = len(results_df)
                    print(f"   Nombre de clusters pour RF : {num_clusters}")
                    if num_clusters >= 5:
                        print(f"   ✅ Suffisamment de clusters pour Random Forest (≥5)")
                    else:
                        print(f"   ⚠️ Pas assez de clusters pour Random Forest (<5)")
            else:
                print(f"   ⚠️ DataFrame résultats vide")
        else:
            print(f"   ⚠️ Résultats étape 7 non trouvés")
        
        print()
        
        # ========================================================================
        # ÉTAPE 8 : Appliquer cluster cible
        # ========================================================================
        
        print("8️⃣ ÉTAPE 8 : APPLIQUER CLUSTER CIBLE")
        print("-" * 80)
        
        print(f"   ✅ Prédiction finale calculée")
        
        impact_base = final_prediction.get('impact_base', 0.0)
        amplification_predite = final_prediction.get('amplification_predite', 1.0)
        adjustment_factor = final_prediction.get('adjustment_factor', 1.0)
        prediction_finale = final_prediction.get('prediction_finale', 0.0)
        pattern_type = final_prediction.get('pattern_type', 'NONE')
        
        print(f"   Impact de base : {impact_base:.2f} pips")
        print(f"   Amplification prédite : {amplification_predite:.3f}x")
        print(f"   Facteur d'ajustement : {adjustment_factor:.3f}x")
        print(f"   Pattern type : {pattern_type}")
        print(f"   Prédiction finale : {prediction_finale:.2f} pips")
        print()
        
        # Vérifier le calcul
        impact_formules_attendu = impact_base * amplification_predite * adjustment_factor
        print(f"   Calcul attendu : {impact_base:.2f} × {amplification_predite:.3f} × {adjustment_factor:.3f}")
        print(f"   = {impact_formules_attendu:.2f} pips")
        print()
        
        if abs(prediction_finale - impact_formules_attendu) > 0.01:
            print(f"   ⚠️ INCOHÉRENCE : Prédiction finale ({prediction_finale:.2f}) ≠ Calcul attendu ({impact_formules_attendu:.2f})")
            print(f"      → L'amplification n'est peut-être pas appliquée correctement")
        else:
            print(f"   ✅ Calcul cohérent")
        
        print()
        
        # ========================================================================
        # RÉSUMÉ ET DIAGNOSTIC
        # ========================================================================
        
        print("=" * 80)
        print("  RÉSUMÉ ET DIAGNOSTIC")
        print("=" * 80)
        print()
        
        # Vérifier chaque étape
        etapes_ok = []
        etapes_manquantes = []
        
        if 'etape1_events' in results:
            etapes_ok.append("Étape 1")
        else:
            etapes_manquantes.append("Étape 1")
        
        if 'etape2_clusters' in results:
            etapes_ok.append("Étape 2")
        else:
            etapes_manquantes.append("Étape 2")
        
        if 'etape3_core' in results:
            etapes_ok.append("Étape 3")
        else:
            etapes_manquantes.append("Étape 3")
        
        if 'etape4_identical_clusters' in results:
            etapes_ok.append("Étape 4")
        else:
            etapes_manquantes.append("Étape 4")
        
        if 'etape5_tendances' in results:
            etapes_ok.append("Étape 5")
        else:
            etapes_manquantes.append("Étape 5")
        
        if 'etape6_impacts' in results:
            etapes_ok.append("Étape 6")
        else:
            etapes_manquantes.append("Étape 6")
        
        if 'etape7_analysis' in results:
            etapes_ok.append("Étape 7")
        else:
            etapes_manquantes.append("Étape 7")
        
        print(f"✅ Étapes exécutées correctement : {', '.join(etapes_ok)}")
        if etapes_manquantes:
            print(f"⚠️ Étapes manquantes : {', '.join(etapes_manquantes)}")
        
        print()
        
        # Diagnostic final
        print("🔍 DIAGNOSTIC FINAL :")
        print("-" * 80)
        print()
        
        mesure_reelle = 188.3
        ecart = abs(prediction_finale - mesure_reelle)
        ecart_pct = (ecart / mesure_reelle) * 100
        
        print(f"   Mesure réelle : {mesure_reelle:.1f} pips")
        print(f"   Prédiction finale : {prediction_finale:.2f} pips")
        print(f"   Écart : {ecart:.1f} pips ({ecart_pct:.1f}%)")
        print()
        
        # Identifier les problèmes
        if impact_base > mesure_reelle:
            surestimation_base = impact_base - mesure_reelle
            print(f"   ⚠️ PROBLÈME 1 : Impact de base surestimé")
            print(f"      Impact base ({impact_base:.2f}) > Mesure réelle ({mesure_reelle:.1f})")
            print(f"      Surestimation : {surestimation_base:.1f} pips")
            print()
        
        if amplification_predite == 1.0:
            print(f"   ⚠️ PROBLÈME 2 : Amplification non optimisée (1.0x par défaut)")
        elif amplification_predite < 0.5:
            print(f"   ⚠️ PROBLÈME 3 : Amplification très faible ({amplification_predite:.3f}x)")
            print(f"      → Suggère que l'impact de base est très surestimé")
        
        if method_used == 'unknown' or 'random_forest' not in method_used.lower():
            print(f"   ⚠️ PROBLÈME 4 : Random Forest non utilisé")
            print(f"      Méthode : {method_used}")
        
        print()
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verifier_pipeline_etape_par_etape()




