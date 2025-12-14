#!/usr/bin/env python3
"""
SCANNER MENSUEL 2023-2025 - SESSION 130
========================================

Scan progressif mois par mois pour permettre validation intermédiaire.

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import duckdb
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Réutiliser MovementScanner
import sys
sys.path.insert(0, str(Path(__file__).parent))
from scan_movements_2023_2025 import MovementScanner, DB_PATH, TZ_BERN

OUTPUT_DIR = Path(__file__).parent
PROGRESS_FILE = OUTPUT_DIR / "scan_progress.json"
FINAL_OUTPUT = OUTPUT_DIR / "movements_2023_2025_complete.json"


def scan_by_month():
    """Scan mois par mois avec sauvegarde progressive"""
    
    print("=" * 80)
    print("SCANNER MENSUEL 2023-2025")
    print("=" * 80)
    
    scanner = MovementScanner(DB_PATH)
    scanner.connect()
    
    # Période complète
    start_date = datetime(2023, 1, 1, tzinfo=TZ_BERN)
    end_date = datetime(2025, 11, 7, tzinfo=TZ_BERN)
    
    # Générer liste mois
    months = []
    current = start_date
    while current <= end_date:
        # Dernier jour du mois
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1, day=1)
        else:
            next_month = current.replace(month=current.month + 1, day=1)
        
        month_end = next_month - timedelta(days=1)
        if month_end > end_date:
            month_end = end_date
        
        months.append((current, month_end))
        current = next_month
    
    print(f"\n📅 {len(months)} mois à scanner")
    print(f"Période : {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
    print("-" * 80)
    
    all_movements = []
    month_stats = []
    
    for i, (month_start, month_end) in enumerate(months, 1):
        month_str = month_start.strftime("%Y-%m")
        print(f"\n[{i:2d}/{len(months)}] {month_str}...", end=" ", flush=True)
        
        # Scan mois
        month_movements = []
        current_day = month_start
        
        while current_day <= month_end:
            movement = scanner.scan_date(current_day)
            if movement:
                month_movements.append(movement)
                all_movements.append(movement)
            
            current_day += timedelta(days=1)
        
        # Stats mois
        n_detected = len(month_movements)
        patterns = {}
        for m in month_movements:
            p = m["pattern"]
            patterns[p] = patterns.get(p, 0) + 1
        
        month_stats.append({
            "month": month_str,
            "detected": n_detected,
            "patterns": patterns
        })
        
        print(f"{n_detected:2d} mouvements", end="")
        if patterns:
            top_pattern = max(patterns.items(), key=lambda x: x[1])
            print(f" | {top_pattern[0]}: {top_pattern[1]}")
        else:
            print()
        
        # Sauvegarde progressive tous les 3 mois
        if i % 3 == 0:
            progress = {
                "last_month": month_str,
                "total_detected": len(all_movements),
                "month_stats": month_stats
            }
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(progress, f, indent=2)
    
    scanner.disconnect()
    
    # Résultats finaux
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS FINAUX")
    print("=" * 80)
    
    print(f"\nTotal mouvements détectés : {len(all_movements)}")
    
    # Distribution patterns
    pattern_counts = {}
    pattern_impacts = {}
    
    for m in all_movements:
        p = m["pattern"]
        pattern_counts[p] = pattern_counts.get(p, 0) + 1
        
        if p not in pattern_impacts:
            pattern_impacts[p] = []
        pattern_impacts[p].append(m["impact_pips"])
    
    print(f"\n📈 Distribution patterns :")
    for pattern in sorted(pattern_counts.keys(), key=lambda x: -pattern_counts[x]):
        count = pattern_counts[pattern]
        avg = sum(pattern_impacts[pattern]) / len(pattern_impacts[pattern])
        pct = 100.0 * count / len(all_movements)
        print(f"   {pattern:25s} : {count:3d} ({pct:5.1f}%) | Avg: {avg:6.1f} pips")
    
    # Sauvegarder résultat final
    output = {
        "metadata": {
            "scan_date": datetime.now().isoformat(),
            "period_start": "2023-01-01",
            "period_end": "2025-11-07",
            "threshold_pips": 35.0,
            "total_movements": len(all_movements)
        },
        "statistics": {
            "pattern_counts": pattern_counts,
            "pattern_avg_impact": {p: sum(impacts) / len(impacts) 
                                  for p, impacts in pattern_impacts.items()}
        },
        "month_stats": month_stats,
        "movements": all_movements
    }
    
    with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Résultats sauvegardés : {FINAL_OUTPUT}")
    print(f"   Taille : {FINAL_OUTPUT.stat().st_size / 1024:.1f} KB")
    
    # Validation cas connus
    print(f"\n" + "=" * 80)
    print("VALIDATION CAS CONNUS")
    print("=" * 80)
    
    known_dates = {
        "2025-09-11": ("DoubleWave", 56),
        "2025-08-01": ("SingleWave", 174),
        "2025-09-05": ("ZigZag", 72)
    }
    
    for date_str, (expected_pattern, expected_impact) in known_dates.items():
        found = next((m for m in all_movements if m["date"] == date_str), None)
        if found:
            print(f"\n✅ {date_str} détecté")
            print(f"   Pattern : {found['pattern']} (attendu: {expected_pattern})")
            print(f"   Impact : {found['impact_pips']:.1f} pips (référence: ~{expected_impact} pips)")
            
            # Vérifier match pattern
            if expected_pattern in found['pattern']:
                print(f"   ✅ Pattern correct !")
            else:
                print(f"   ⚠️  Pattern différent (peut varier selon seuils)")
        else:
            print(f"\n❌ {date_str} NON détecté")
    
    print("\n" + "=" * 80)
    print("✅ SCAN TERMINÉ AVEC SUCCÈS")
    print("=" * 80)
    
    return len(all_movements)


if __name__ == "__main__":
    try:
        n_movements = scan_by_month()
        print(f"\n🎉 {n_movements} mouvements détectés et sauvegardés !")
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
