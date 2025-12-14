"""
Scanner 2024-2025 avec DoubleWaveDetectorRev12
==============================================
SESSION 124 - Validation Multi-Dates

OBJECTIF:
Détecter tous Double Wave 2024-2025 avec détecteur validé Rev12

ALGORITHME:
1. Scanner chaque jour 2024-2025
2. Détecter patterns avec Rev12 (MAE 4.5 pips validé)
3. Filtrer patterns valides (confidence > 50%)
4. Sauvegarder JSON pour validation formule S115

CRITÈRE SUCCÈS:
- 10-20 Double Wave détectés (comme Session 117)
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime, timedelta

# Ajouter scripts/session120 au path
current_dir = Path(__file__).parent  # scripts/session124/
scripts_dir = current_dir.parent      # scripts/
session120_dir = scripts_dir / 'session120'

if str(session120_dir) not in sys.path:
    sys.path.insert(0, str(session120_dir))

# Importer Rev12
from double_wave_detector_rev12 import detect_for_date_duckdb_rev12


# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb')
TABLE = 'prices_bern'
TZ = 'Europe/Zurich'


# ============================================================================
# SCANNER
# ============================================================================

def scan_period(start_date: str, end_date: str, debug: bool = False):
    """
    Scanner période avec Rev12
    
    Args:
        start_date: Date début (YYYY-MM-DD)
        end_date: Date fin (YYYY-MM-DD)
        debug: Mode debug détaillé
    
    Returns:
        Liste patterns détectés
    """
    patterns = []
    
    # Convertir dates
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Scanner chaque jour
    current = start
    total_days = (end - start).days + 1
    processed = 0
    detected = 0
    
    print(f"\n{'='*80}")
    print(f"SCAN PÉRIODE: {start_date} → {end_date}")
    print(f"{'='*80}")
    print(f"Total jours: {total_days}")
    print(f"DB: {DB_PATH}")
    print(f"Table: {TABLE}")
    print(f"Timezone: {TZ}")
    print()
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        # Scanner jour
        try:
            result = detect_for_date_duckdb_rev12(
                db_path=DB_PATH,
                table=TABLE,
                date=current,
                tz=TZ,
                baseline_mode='prev_close_14_29',  # ✅ Validé Session 118
                minutes_after_hint=120,
                trading_window=True,
                debug=debug
            )
            
            if result is not None:
                # Filtrer patterns valides (confidence > 50%)
                if result.get('confidence', 0) > 50:
                    patterns.append(result)
                    detected += 1
                    
                    w1 = result['wave1_amp_pips']
                    w2 = result['wave2_amp_pips']
                    conf = result['confidence']
                    
                    print(f"✅ {date_str}: Double Wave détecté")
                    print(f"   Wave1={w1:.1f} pips, Wave2={w2:.1f} pips, Conf={conf:.1f}%")
            
            processed += 1
            
            # Progress tous les 30 jours
            if processed % 30 == 0:
                pct = (processed / total_days) * 100
                print(f"\n📊 Progression: {processed}/{total_days} jours ({pct:.1f}%)")
                print(f"   Patterns détectés: {detected}\n")
        
        except Exception as e:
            if debug:
                print(f"⚠️  {date_str}: Erreur - {str(e)}")
        
        # Jour suivant
        current += timedelta(days=1)
    
    print(f"\n{'='*80}")
    print(f"SCAN TERMINÉ")
    print(f"{'='*80}")
    print(f"Jours traités: {processed}/{total_days}")
    print(f"Double Wave détectés: {detected}")
    print(f"{'='*80}\n")
    
    return patterns


def scan_2024_2025(debug: bool = False):
    """Scanner complet 2024-2025"""
    
    all_patterns = []
    
    # Scanner 2024
    print("\n🗓️  ANNÉE 2024")
    patterns_2024 = scan_period('2024-01-01', '2024-12-31', debug=debug)
    all_patterns.extend(patterns_2024)
    
    # Scanner 2025 (jusqu'à octobre)
    print("\n🗓️  ANNÉE 2025")
    patterns_2025 = scan_period('2025-01-01', '2025-10-31', debug=debug)
    all_patterns.extend(patterns_2025)
    
    return all_patterns


def save_results(patterns: list, output_dir: Path):
    """Sauvegarder résultats"""
    
    # JSON complet
    json_file = output_dir / 'double_waves_rev12.json'
    with open(json_file, 'w') as f:
        json.dump(patterns, f, indent=2)
    
    print(f"💾 Sauvegardé: {json_file}")
    print(f"   {len(patterns)} patterns")
    
    # CSV résumé
    if patterns:
        df = pd.DataFrame([{
            'date': p['date'],
            'wave1_pips': p['wave1_amp_pips'],
            'wave2_pips': p['wave2_amp_pips'],
            'total_pips': p['wave1_amp_pips'] + p['wave2_amp_pips'],
            'pullback1_ratio': p['pullback1_ratio'],
            'pullback2_ratio': p['pullback2_ratio'],
            'confidence': p['confidence'],
            'direction': p['direction']
        } for p in patterns])
        
        csv_file = output_dir / 'double_waves_summary.csv'
        df.to_csv(csv_file, index=False)
        print(f"💾 Sauvegardé: {csv_file}")
        
        # Statistiques
        print(f"\n📊 STATISTIQUES:")
        print(f"   Moyenne Wave1: {df['wave1_pips'].mean():.1f} pips")
        print(f"   Moyenne Wave2: {df['wave2_pips'].mean():.1f} pips")
        print(f"   Moyenne Total: {df['total_pips'].mean():.1f} pips")
        print(f"   Direction bullish: {(df['direction'] == 'bullish').sum()}")
        print(f"   Direction bearish: {(df['direction'] == 'bearish').sum()}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scanner Double Wave 2024-2025')
    parser.add_argument('--debug', action='store_true', help='Mode debug détaillé')
    parser.add_argument('--period', type=str, help='Période spécifique (YYYY-MM-DD:YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    output_dir = Path(__file__).parent
    
    print(f"\n{'='*80}")
    print(f"SCANNER DOUBLE WAVE REV12")
    print(f"SESSION 124 - Validation Multi-Dates")
    print(f"{'='*80}")
    
    if args.period:
        # Scanner période spécifique
        start, end = args.period.split(':')
        patterns = scan_period(start, end, debug=args.debug)
    else:
        # Scanner 2024-2025 complet
        patterns = scan_2024_2025(debug=args.debug)
    
    # Sauvegarder
    save_results(patterns, output_dir)
    
    print(f"\n✅ SCAN TERMINÉ")
    print(f"   {len(patterns)} Double Wave détectés")
    print(f"   Prêt pour validation formule S115 (Étape 2)")
