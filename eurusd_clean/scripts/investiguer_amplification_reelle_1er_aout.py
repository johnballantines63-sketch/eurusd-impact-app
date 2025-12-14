#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGATION AMPLIFICATION RÉELLE - 1ER AOÛT 2025
==================================================

Vérifie pourquoi l'amplification calculée (0.246x) est si faible
alors que l'impact réel (188.3 pips) est proche de l'impact de base (250.82 pips).
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
from core.price_loader_finnhub import measure_impact_from_finnhub

TZ_BERN = pytz.timezone('Europe/Zurich')

def investiguer_amplification_reelle():
    """Investigation détaillée de l'amplification réelle"""
    
    date_str = '2025-08-01'
    anchor_time = TZ_BERN.localize(datetime.strptime(f"{date_str} 14:30:00", "%Y-%m-%d %H:%M:%S"))
    
    print("\n" + "=" * 80)
    print(f"  INVESTIGATION AMPLIFICATION RÉELLE - 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=False)
    
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
        results = result['results']
        
        print()
        print("=" * 80)
        print("  ANALYSE AMPLIFICATION RÉELLE")
        print("=" * 80)
        print()
        
        # 1. Impact réel mesuré
        print("1️⃣ IMPACT RÉEL MESURÉ :")
        print("-" * 80)
        print()
        
        impact_reel_mesure = measure_impact_from_finnhub(
            db_path=DB_PATH,
            event_timestamp=anchor_time,
            lookback_minutes=5,
            lookahead_minutes=120,
            debug=False
        )
        
        if impact_reel_mesure:
            impact_reel_pips = impact_reel_mesure.get('impact_pips', 0.0)
            print(f"   Impact réel mesuré : {impact_reel_pips:.1f} pips")
            print(f"   Direction : {impact_reel_mesure.get('direction', 'UNKNOWN')}")
            print(f"   Peak time : {impact_reel_mesure.get('peak_time', 'N/A')}")
            print()
        else:
            print("   ⚠️ Impossible de mesurer l'impact réel")
            impact_reel_pips = 188.3  # Valeur connue d'après analyses précédentes
            print(f"   Utilisation valeur connue : {impact_reel_pips:.1f} pips")
            print()
        
        # 2. Impact de base calculé
        print("2️⃣ IMPACT DE BASE CALCULÉ :")
        print("-" * 80)
        print()
        
        impact_base = final_prediction.get('impact_base', 0.0)
        print(f"   Impact de base : {impact_base:.2f} pips")
        print()
        
        # 3. Amplification réelle
        print("3️⃣ AMPLIFICATION RÉELLE (IMPACT RÉEL / IMPACT DE BASE) :")
        print("-" * 80)
        print()
        
        if impact_base > 0:
            amplification_reelle = impact_reel_pips / impact_base
            print(f"   Impact réel : {impact_reel_pips:.1f} pips")
            print(f"   Impact de base : {impact_base:.2f} pips")
            print(f"   Amplification réelle : {impact_reel_pips:.1f} / {impact_base:.2f} = {amplification_reelle:.3f}x")
            print()
        
        # 4. Amplification calculée par le pipeline
        print("4️⃣ AMPLIFICATION CALCULÉE PAR LE PIPELINE :")
        print("-" * 80)
        print()
        
        amplification_predite = final_prediction.get('amplification_predite', 1.0)
        print(f"   Amplification prédite : {amplification_predite:.3f}x")
        print()
        
        # 5. Comparaison
        print("5️⃣ COMPARAISON :")
        print("-" * 80)
        print()
        
        if impact_base > 0:
            print(f"   Amplification réelle : {amplification_reelle:.3f}x")
            print(f"   Amplification prédite : {amplification_predite:.3f}x")
            print(f"   Différence : {abs(amplification_reelle - amplification_predite):.3f}x")
            print()
            
            if abs(amplification_reelle - amplification_predite) > 0.2:
                print(f"   ⚠️ DIFFÉRENCE IMPORTANTE : L'amplification prédite est très différente de l'amplification réelle")
                print()
        
        # 6. Analyse des amplifications parfaites historiques
        print("6️⃣ ANALYSE DES AMPLIFICATIONS PARFAITES HISTORIQUES :")
        print("-" * 80)
        print()
        
        etape7_analysis = results.get('etape7_analysis', {})
        results_df = etape7_analysis.get('results_df')
        
        if results_df is not None and not results_df.empty:
            if 'amplification_parfaite' in results_df.columns:
                amp_parfaite = results_df['amplification_parfaite']
                
                print(f"   Nombre de clusters : {len(results_df)}")
                print(f"   Amplification moyenne : {amp_parfaite.mean():.3f}x")
                print(f"   Amplification médiane : {amp_parfaite.median():.3f}x")
                print(f"   Amplification min : {amp_parfaite.min():.3f}x")
                print(f"   Amplification max : {amp_parfaite.max():.3f}x")
                print(f"   Écart-type : {amp_parfaite.std():.3f}x")
                print()
                
                # Afficher quelques exemples
                print("   Exemples d'amplifications parfaites :")
                for idx, row in results_df.head(10).iterrows():
                    amp = row.get('amplification_parfaite', 0.0)
                    impact_base_hist = row.get('impact_base', 0.0)
                    impact_reel_hist = row.get('impact_reel', 0.0)
                    print(f"      Cluster {idx+1}: base={impact_base_hist:.1f}, réel={impact_reel_hist:.1f}, amp={amp:.3f}x")
                print()
                
                # Vérifier si l'amplification réelle du 1er août est dans la distribution
                if impact_base > 0:
                    print(f"   Amplification réelle 1er août : {amplification_reelle:.3f}x")
                    print(f"   Amplification moyenne historique : {amp_parfaite.mean():.3f}x")
                    
                    if amplification_reelle > amp_parfaite.max():
                        print(f"   ⚠️ Amplification réelle ({amplification_reelle:.3f}x) > Amplification max historique ({amp_parfaite.max():.3f}x)")
                    elif amplification_reelle < amp_parfaite.min():
                        print(f"   ⚠️ Amplification réelle ({amplification_reelle:.3f}x) < Amplification min historique ({amp_parfaite.min():.3f}x)")
                    else:
                        print(f"   ✅ Amplification réelle dans la distribution historique")
                    print()
        else:
            print("   ⚠️ Aucun résultat de l'étape 7 disponible")
            print()
        
        # 7. Prédiction finale vs Réalité
        print("7️⃣ PRÉDICTION FINALE VS RÉALITÉ :")
        print("-" * 80)
        print()
        
        prediction_finale = final_prediction.get('prediction_finale', 0.0)
        
        print(f"   Impact réel mesuré : {impact_reel_pips:.1f} pips")
        print(f"   Prédiction finale : {prediction_finale:.2f} pips")
        print()
        
        erreur_absolue = abs(prediction_finale - impact_reel_pips)
        erreur_pourcentage = (erreur_absolue / impact_reel_pips * 100) if impact_reel_pips > 0 else 0
        
        print(f"   Erreur absolue : {erreur_absolue:.1f} pips")
        print(f"   Erreur relative : {erreur_pourcentage:.1f}%")
        print()
        
        if erreur_pourcentage > 50:
            print(f"   ❌ ERREUR TRÈS IMPORTANTE : {erreur_pourcentage:.1f}% d'erreur")
        elif erreur_pourcentage > 20:
            print(f"   ⚠️ ERREUR IMPORTANTE : {erreur_pourcentage:.1f}% d'erreur")
        else:
            print(f"   ✅ Erreur acceptable : {erreur_pourcentage:.1f}%")
        print()
        
        # 8. Conclusion
        print("=" * 80)
        print("  CONCLUSION")
        print("=" * 80)
        print()
        
        print(f"📊 Résumé :")
        print(f"   Impact réel : {impact_reel_pips:.1f} pips")
        print(f"   Impact de base : {impact_base:.2f} pips")
        print(f"   Amplification réelle : {amplification_reelle:.3f}x")
        print(f"   Amplification prédite : {amplification_predite:.3f}x")
        print(f"   Prédiction finale : {prediction_finale:.2f} pips")
        print(f"   Erreur : {erreur_pourcentage:.1f}%")
        print()
        
        if amplification_reelle > 0.5 and amplification_predite < 0.3:
            print("⚠️ PROBLÈME IDENTIFIÉ :")
            print(f"   L'amplification réelle ({amplification_reelle:.3f}x) est beaucoup plus élevée que")
            print(f"   l'amplification prédite ({amplification_predite:.3f}x).")
            print()
            print("   Cela suggère que :")
            print("   1. L'amplification parfaite moyenne historique (0.246x) est trop faible")
            print("   2. Ou que l'impact de base est surestimé")
            print("   3. Ou que le calcul de l'amplification parfaite dans l'étape 6 est incorrect")
        
        print()
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investiguer_amplification_reelle()




