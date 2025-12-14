"""
Chercher le 11 septembre dans les résultats du scan complet
Session 117 - Debug

Auteur: André Valentin avec Claude
Date: 06 novembre 2025
"""

import json
from pathlib import Path
from datetime import datetime

def find_sept11():
    """Chercher le 11 septembre dans patterns_detected.json"""
    
    json_path = Path(__file__).parent / "patterns_detected.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    print("=" * 70)
    print("🔍 RECHERCHE 11 SEPTEMBRE 2025")
    print(f"   Total patterns : {len(patterns)}")
    print("=" * 70)
    
    # Chercher tous les patterns du 11 septembre
    sept11_patterns = []
    for p in patterns:
        peak_time = datetime.fromisoformat(p['peak1_time'])
        if peak_time.date() == datetime(2025, 9, 11).date():
            sept11_patterns.append(p)
    
    if not sept11_patterns:
        print("\n❌ AUCUN PATTERN DU 11 SEPTEMBRE TROUVÉ !")
        print("   Ceci est ANORMAL - le test septembre l'avait détecté")
        return
    
    print(f"\n✅ {len(sept11_patterns)} pattern(s) du 11 septembre trouvé(s)\n")
    
    for i, p in enumerate(sept11_patterns, 1):
        print(f"{'='*70}")
        print(f"PATTERN #{i} - 11 SEPTEMBRE 2025")
        print(f"{'='*70}")
        
        peak_time = datetime.fromisoformat(p['peak1_time'])
        
        print(f"\n📅 TIMING :")
        print(f"   Peak1 : {peak_time.strftime('%H:%M:%S')}")
        print(f"   Baseline : {p['baseline_time']}")
        
        print(f"\n🎯 CLASSIFICATION :")
        print(f"   Pattern : {p['pattern'].upper()}")
        print(f"   Direction : {p['direction']}")
        
        print(f"\n📈 MÉTRIQUES :")
        print(f"   Peak1 (Wave 1) : {p['spike_pips']:.2f} pips")
        print(f"   Pullback : {p['pullback_pips']:.2f} pips ({p['pullback_ratio']*100:.1f}%)")
        print(f"   Impact total : {p['total_impact_pips']:.2f} pips")
        
        if p['pattern'] == 'double_wave':
            print(f"   Wave2 : {p['wave2_from_baseline_pips']:.2f} pips")
            print(f"   Extension factor : {p['extension_factor']:.2f}x")
        
        print(f"\n💡 COMPARAISON RÉFÉRENCE S115 :")
        print(f"   Impact attendu MT5 : 56.2 pips")
        print(f"   Impact détecté : {p['total_impact_pips']:.2f} pips")
        print(f"   Écart : {abs(p['total_impact_pips'] - 56.2):.2f} pips")
        
        if p['pattern'] == 'double_wave':
            print(f"\n   Extension S115 : 1.51x")
            print(f"   Extension détectée : {p['extension_factor']:.2f}x")
            print(f"   Écart : {abs(p['extension_factor'] - 1.51):.2f}x")
        else:
            print(f"\n   ⚠️  CLASSÉ COMME {p['pattern'].upper()} AU LIEU DE DOUBLE_WAVE")
            print(f"   Raison probable :")
            if p['pullback_ratio'] < 0.5:
                print(f"      - Pullback {p['pullback_ratio']*100:.1f}% < 50% (seuil Double Wave)")
            else:
                print(f"      - Extension factor < 1.0 ou Wave2 non détectée")


if __name__ == "__main__":
    find_sept11()
