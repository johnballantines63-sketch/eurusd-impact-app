"""
Vérification événements 1er août 2025 - Fichier EODHD corrigé

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import json
from pathlib import Path
from collections import defaultdict

def verify_august_1():
    """Vérifier événements 1er août 2025 dans EODHD corrigé"""
    
    print("=" * 80)
    print("VÉRIFICATION 1ER AOÛT 2025 - EODHD CORRIGÉ")
    print("=" * 80)
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # Fichier EODHD corrigé
    eodhd_file = data_dir / 'eodhd_2020_2025_fixed' / 'eodhd_all_2020_2025_fixed.json'
    
    if not eodhd_file.exists():
        print(f"❌ Fichier non trouvé: {eodhd_file}")
        return
    
    print(f"📂 Fichier: {eodhd_file.name}")
    print()
    
    with open(eodhd_file, 'r') as f:
        events = json.load(f)
    
    print(f"📊 Total EODHD: {len(events):,} événements")
    print()
    
    # Filtrer 1er août 2025
    aug1_events = [e for e in events if e.get('date', '').startswith('2025-08-01')]
    
    print("=" * 80)
    print("1ER AOÛT 2025 - EODHD")
    print("=" * 80)
    print()
    
    print(f"📅 Total événements: {len(aug1_events)}")
    print()
    
    # Par pays
    by_country = defaultdict(int)
    for e in aug1_events:
        country = e.get('country', 'XX')
        by_country[country] += 1
    
    print("Par pays:")
    for country in sorted(by_country.keys(), key=lambda x: by_country[x], reverse=True):
        count = by_country[country]
        print(f"   {country:3s}: {count:3d} événements")
    
    print()
    
    # Événements US spécifiquement
    aug1_us = [e for e in aug1_events if e.get('country') == 'US']
    
    print("=" * 80)
    print("ÉVÉNEMENTS US 1ER AOÛT 2025")
    print("=" * 80)
    print()
    
    print(f"📊 Total US: {len(aug1_us)} événements")
    print()
    
    if len(aug1_us) > 0:
        print("Détail:")
        for e in sorted(aug1_us, key=lambda x: x.get('date', '')):
            date = e.get('date', '')
            event_type = e.get('type', 'Unknown')
            actual = e.get('actual', '')
            forecast = e.get('forecast', '')
            previous = e.get('previous', '')
            
            print(f"   {date} | {event_type:40s} | A:{actual} F:{forecast} P:{previous}")
    
    print()
    
    # Comparer avec JBlanked
    print("=" * 80)
    print("COMPARAISON AVEC JBLANKED")
    print("=" * 80)
    print()
    
    jblanked_file = data_dir / 'jblanked_2020_2025' / 'jblanked_all_2020_2025.json'
    
    if jblanked_file.exists():
        with open(jblanked_file, 'r') as f:
            jb_events = json.load(f)
        
        jb_aug1 = [e for e in jb_events if e.get('Date', '').startswith('2025.08.01')]
        jb_aug1_usd = [e for e in jb_aug1 if e.get('Currency') == 'USD']
        
        print(f"JBlanked 1er août:")
        print(f"   Total: {len(jb_aug1)} événements")
        print(f"   USD: {len(jb_aug1_usd)} événements")
        print()
        
        print(f"EODHD 1er août:")
        print(f"   Total: {len(aug1_events)} événements")
        print(f"   US: {len(aug1_us)} événements")
        print()
        
        print(f"APRÈS MERGE (estimation):")
        print(f"   Total unique: {len(aug1_events) + len(jb_aug1)} événements (avant dédoublonnage)")
        print(f"   USD/US: ~{len(jb_aug1_usd) + len(aug1_us)} événements USD")
    
    print()
    
    # Conclusion
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    
    if len(aug1_us) > 10:
        print(f"✅ 1ER AOÛT BIEN COUVERT PAR EODHD")
        print()
        print(f"   • {len(aug1_us)} événements US dans EODHD")
        print(f"   • Couverture complète attendue après merge")
    elif len(aug1_us) > 0:
        print(f"⚠️  1ER AOÛT PARTIELLEMENT COUVERT")
        print()
        print(f"   • {len(aug1_us)} événements US dans EODHD")
        print(f"   • JBlanked complètera les données")
    else:
        print(f"❌ 1ER AOÛT NON COUVERT PAR EODHD")
        print()
        print(f"   • 0 événements US dans EODHD")
        print(f"   • JBlanked source unique pour 1er août")
    
    print()

if __name__ == '__main__':
    verify_august_1()
