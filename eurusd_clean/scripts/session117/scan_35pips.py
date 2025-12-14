"""
Scanner avec seuil ajusté à 35 pips (au lieu de 40)
Pour mieux détecter les Double Wave comme le 11 septembre

Auteur: André Valentin avec Claude
Date: 06 novembre 2025
"""

import sys
from pathlib import Path

# Ajouter le chemin parent pour import
sys.path.insert(0, str(Path(__file__).parent))

from scan_price_patterns import PricePatternScanner

def main():
    print("=" * 60)
    print("🚀 SCANNER PRICE PATTERNS - SEUIL AJUSTÉ 35 PIPS")
    print("   (Au lieu de 40 pips pour mieux détecter Double Wave)")
    print("=" * 60)
    
    # Initialiser scanner
    scanner = PricePatternScanner(
        db_path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
    )
    
    try:
        # Connexion
        scanner.connect()
        
        # Scanner période complète avec SEUIL 35 PIPS
        patterns = scanner.scan_period(
            start_date="2024-01-01",
            end_date="2025-11-06",
            min_spike_pips=35.0,  # ✅ RÉDUIT à 35 pips
            trading_hours_only=True
        )
        
        # Exporter résultats
        scanner.export_results(patterns, "patterns_detected_35pips.json")
        
        # Vérifier 11 septembre
        from datetime import datetime
        sept11_patterns = [
            p for p in patterns 
            if datetime.fromisoformat(p['peak1_time']).date() == datetime(2025, 9, 11).date()
        ]
        
        if sept11_patterns:
            p = sept11_patterns[0]
            print(f"\n🎯 11 SEPTEMBRE DÉTECTÉ :")
            print(f"   Pattern : {p['pattern'].upper()}")
            print(f"   Peak1 : {p['peak1_time']}")
            print(f"   Impact : {p['total_impact_pips']:.1f} pips")
            if p['pattern'] == 'double_wave':
                print(f"   Extension : {p['extension_factor']:.2f}x")
                print(f"   Pullback : {p['pullback_ratio']*100:.1f}%")
                print(f"   ✅ CORRECTEMENT CLASSÉ DOUBLE_WAVE !")
            else:
                print(f"   ⚠️  Classé {p['pattern']} au lieu de double_wave")
        else:
            print(f"\n⚠️  11 septembre non détecté")
        
    finally:
        # Fermer connexion
        scanner.disconnect()
    
    print("\n✅ SCAN TERMINÉ")


if __name__ == "__main__":
    main()
