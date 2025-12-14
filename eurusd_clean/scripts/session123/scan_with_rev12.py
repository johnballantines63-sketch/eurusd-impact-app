"""
Scanner 2024-2025 avec DoubleWaveDetectorRev12

Utilise détecteur validé Session 120 (MAE 4.5 pips)
pour scanner toutes dates 2024-2025 et détecter Double Wave

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 → 124
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import List, Dict

# Ajouter session120 au path
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
session120_dir = scripts_dir / 'session120'

if str(session120_dir) not in sys.path:
    sys.path.insert(0, str(session120_dir))

from double_wave_detector_rev12 import detect_for_date_duckdb_rev12

# DB unifiée
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'
OUTPUT_DIR.mkdir(exist_ok=True)


def scan_month(year: int, month: int, debug: bool = False) -> List[Dict]:
    """Scanner un mois complet"""
    
    patterns = []
    
    # Dates du mois
    start_date = datetime(year, month, 1)
    
    # Dernier jour du mois
    if month == 12:
        end_date = datetime(year, 12, 31)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    current_date = start_date
    
    while current_date <= end_date:
        # Scanner cette date
        result = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_bern',
            date=current_date,
            tz='Europe/Zurich',
            baseline_mode='prev_close_14_29',
            minutes_after_hint=120,
            trading_window=True,
            debug=debug
        )
        
        if result is not None:
            patterns.append(result)
            
            if not debug:  # Si pas debug, afficher résumé
                wave2 = result['wave2_amp_pips']
                peak2_time = result['peak2_time'].split()[1][:5]
                print(f"   ✅ {current_date.strftime('%Y-%m-%d')} : {wave2:.1f} pips à {peak2_time}")
        
        # Date suivante
        current_date += timedelta(days=1)
    
    return patterns


def scan_2024_2025(debug: bool = False) -> Dict:
    """Scanner 2024-2025 complet"""
    
    print("=" * 80)
    print("SCANNER 2024-2025 AVEC DOUBLEWAVE DETECTOR REV12")
    print("=" * 80)
    print()
    print(f"📊 DB : {DB_PATH.name}")
    print(f"🔍 Détecteur : Rev12 (validé S120, MAE 4.5 pips)")
    print(f"📅 Période : 2024-2025")
    print()
    
    all_patterns = []
    
    # ========================================================================
    # SCAN 2024
    # ========================================================================
    
    print("=" * 80)
    print("SCAN 2024")
    print("=" * 80)
    print()
    
    for month in range(1, 13):
        print(f"📅 2024-{month:02d}")
        patterns = scan_month(2024, month, debug=debug)
        all_patterns.extend(patterns)
        print(f"   → {len(patterns)} Double Wave détectés ce mois")
        print()
    
    patterns_2024 = len(all_patterns)
    print(f"✅ 2024 : {patterns_2024} Double Wave total")
    print()
    
    # ========================================================================
    # SCAN 2025
    # ========================================================================
    
    print("=" * 80)
    print("SCAN 2025")
    print("=" * 80)
    print()
    
    patterns_2025_start = len(all_patterns)
    
    for month in range(1, 11):  # Jusqu'à octobre 2025
        print(f"📅 2025-{month:02d}")
        patterns = scan_month(2025, month, debug=debug)
        all_patterns.extend(patterns)
        print(f"   → {len(patterns)} Double Wave détectés ce mois")
        print()
    
    patterns_2025 = len(all_patterns) - patterns_2025_start
    print(f"✅ 2025 : {patterns_2025} Double Wave total")
    print()
    
    # ========================================================================
    # STATISTIQUES
    # ========================================================================
    
    print("=" * 80)
    print("STATISTIQUES GLOBALES")
    print("=" * 80)
    print()
    
    total = len(all_patterns)
    print(f"📊 Total Double Wave : {total}")
    print()
    
    if total > 0:
        # Distribution amplitudes
        waves2 = [p['wave2_amp_pips'] for p in all_patterns]
        avg_wave2 = sum(waves2) / len(waves2)
        min_wave2 = min(waves2)
        max_wave2 = max(waves2)
        
        print(f"Wave2 amplitude :")
        print(f"   Moyenne : {avg_wave2:.1f} pips")
        print(f"   Min     : {min_wave2:.1f} pips")
        print(f"   Max     : {max_wave2:.1f} pips")
        print()
        
        # Distribution directions
        bullish = sum(1 for p in all_patterns if p['direction'] == 'bullish')
        bearish = total - bullish
        
        print(f"Direction :")
        print(f"   Bullish : {bullish} ({bullish/total*100:.1f}%)")
        print(f"   Bearish : {bearish} ({bearish/total*100:.1f}%)")
        print()
        
        # Confidence moyenne
        avg_conf = sum(p['confidence'] for p in all_patterns) / total
        print(f"Confidence moyenne : {avg_conf:.1f}%")
        print()
    
    # ========================================================================
    # SAUVEGARDER
    # ========================================================================
    
    output_file = OUTPUT_DIR / 'double_waves_rev12_2024_2025.json'
    
    with open(output_file, 'w') as f:
        json.dump(all_patterns, f, indent=2)
    
    print("=" * 80)
    print("SAUVEGARDE")
    print("=" * 80)
    print()
    print(f"💾 Fichier : {output_file}")
    print(f"📊 Patterns : {total}")
    print()
    
    # ========================================================================
    # COMPARAISON SESSION 117
    # ========================================================================
    
    print("=" * 80)
    print("COMPARAISON VS SESSION 117")
    print("=" * 80)
    print()
    
    print("Session 117 (Scanner Rev7) :")
    print("   Double Wave : 15")
    print()
    
    print("Session 123 (Scanner simple) :")
    print("   Double Wave : 0 (algorithme trop simpliste)")
    print()
    
    print(f"Session 124 (Rev12 validé) :")
    print(f"   Double Wave : {total}")
    print()
    
    if total >= 10:
        print("✅ EXCELLENT : 10+ patterns détectés")
    elif total >= 5:
        print("✅ BON : 5-10 patterns détectés")
    elif total > 0:
        print("⚠️ FAIBLE : < 5 patterns détectés")
    else:
        print("❌ AUCUN : Vérifier configuration Rev12")
    
    print()
    
    # ========================================================================
    # PROCHAINES ÉTAPES
    # ========================================================================
    
    print("=" * 80)
    print("PROCHAINES ÉTAPES")
    print("=" * 80)
    print()
    
    if total > 0:
        print("✅ ÉTAPE 1 COMPLÉTÉE : Scanner Rev12")
        print()
        print("→ ÉTAPE 2 : Validation formules S115")
        print("   1. Charger events causaux pour chaque pattern")
        print("   2. Calculer impacts prédits (formules S115)")
        print("   3. Comparer vs amplitudes réelles")
        print("   4. Calculer MAE moyen")
        print()
        print("Commande :")
        print("   python validate_formulas_rev12.py")
    else:
        print("⚠️ ÉTAPE 1 INCOMPLÈTE")
        print()
        print("Actions :")
        print("   1. Vérifier configuration Rev12")
        print("   2. Tester sur 11 septembre (doit détecter)")
        print("   3. Ajuster seuils si nécessaire")
    
    print()
    print("=" * 80)
    print()
    
    return {
        'total': total,
        'patterns_2024': patterns_2024,
        'patterns_2025': patterns_2025,
        'patterns': all_patterns,
        'output_file': str(output_file)
    }


def main():
    """Entrée principale"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Scanner 2024-2025 avec Rev12')
    parser.add_argument('--debug', action='store_true', help='Mode debug (logs détaillés)')
    
    args = parser.parse_args()
    
    result = scan_2024_2025(debug=args.debug)
    
    if result['total'] > 0:
        print("🎉 SESSION 124 - ÉTAPE 1 COMPLÉTÉE")
        print(f"   {result['total']} Double Wave détectés")
        print("   Prêt pour validation formules")
    else:
        print("⚠️ SESSION 124 - ÉTAPE 1 À REPRENDRE")
        print("   Aucun pattern détecté")
        print("   Vérifier configuration")


if __name__ == '__main__':
    main()
