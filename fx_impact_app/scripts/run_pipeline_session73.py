#!/usr/bin/env python3
"""
Master Script - Session 73
Exécute pipeline complète : Scanner → Dataset → Analyse ML

Author: Claude
Date: 24 octobre 2025
"""

import sys
from pathlib import Path

# Ajouter fx_impact_app au path
fx_impact_app_path = Path(__file__).parent.parent
sys.path.insert(0, str(fx_impact_app_path))

from scripts.scanner_movements_session73 import main as scanner_main
from scripts.create_dataset_session73 import main as dataset_main
from scripts.analyze_correlations_session73 import main as analyze_main


def main():
    """
    Exécuter pipeline complète Session 73
    """
    
    print("\n" + "="*70)
    print("SESSION 73 - PIPELINE COMPLÈTE")
    print("Méthodologie Inversée Data-Driven")
    print("="*70 + "\n")
    
    print("📋 Pipeline en 3 étapes :")
    print("   1️⃣  Scanner mouvements forts (prices_1m)")
    print("   2️⃣  Créer dataset (croiser avec events)")
    print("   3️⃣  Analyse ML (régression + clustering)")
    print()
    
    input("Appuyer sur ENTRÉE pour démarrer...")
    
    try:
        # Étape 1 : Scanner
        print("\n" + "🔍" * 35)
        print("ÉTAPE 1/3 : SCANNER MOUVEMENTS FORTS")
        print("🔍" * 35 + "\n")
        
        df_movements = scanner_main()
        
        if df_movements is None or len(df_movements) == 0:
            print("\n❌ Échec : Aucun mouvement détecté")
            return
        
        print("\n✅ Étape 1 complétée !")
        input("\nAppuyer sur ENTRÉE pour continuer vers étape 2...")
        
        # Étape 2 : Dataset
        print("\n" + "📊" * 35)
        print("ÉTAPE 2/3 : CRÉATION DATASET")
        print("📊" * 35 + "\n")
        
        df_dataset = dataset_main()
        
        if df_dataset is None or len(df_dataset) == 0:
            print("\n❌ Échec : Dataset vide")
            return
        
        print("\n✅ Étape 2 complétée !")
        input("\nAppuyer sur ENTRÉE pour continuer vers étape 3...")
        
        # Étape 3 : Analyse ML
        print("\n" + "🤖" * 35)
        print("ÉTAPE 3/3 : ANALYSE ML")
        print("🤖" * 35 + "\n")
        
        analyze_main()
        
        print("\n✅ Étape 3 complétée !")
        
        # Résumé final
        print("\n" + "="*70)
        print("🎉 PIPELINE COMPLÉTÉE AVEC SUCCÈS !")
        print("="*70 + "\n")
        
        print("📁 Fichiers générés :")
        data_dir = fx_impact_app_path / "data"
        print(f"   1. {data_dir / 'movements_strong_session73.csv'}")
        print(f"   2. {data_dir / 'dataset_complete_session73.csv'}")
        print(f"   3. {data_dir / 'regression_results_session73.txt'}")
        print(f"   4. {data_dir / 'clustering_results_session73.txt'}")
        print(f"   5. {data_dir / 'dataset_clustered_session73.csv'}")
        
        print(f"\n🎯 Prochaines étapes :")
        print(f"   - Examiner résultats ML (fichiers .txt)")
        print(f"   - Créer formulas_validated_v2.py")
        print(f"   - Intégrer au Planificateur V2.5")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrompue par utilisateur")
        return
    
    except Exception as e:
        print(f"\n\n❌ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
