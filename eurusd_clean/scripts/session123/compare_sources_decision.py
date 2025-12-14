"""
Analyse comparative EODHD vs JBlanked - Décision source unique

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import json
from pathlib import Path
from collections import defaultdict

def compare_sources_critical_dates():
    """Comparer EODHD vs JBlanked sur dates critiques"""
    
    print("=" * 80)
    print("ANALYSE COMPARATIVE - EODHD vs JBLANKED")
    print("=" * 80)
    print()
    print("🎯 OBJECTIF: Déterminer si EODHD seul suffit")
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # Charger fichiers
    eodhd_file = data_dir / 'eodhd_2020_2025_fixed' / 'eodhd_all_2020_2025_fixed.json'
    jblanked_file = data_dir / 'jblanked_2020_2025' / 'jblanked_all_2020_2025.json'
    
    with open(eodhd_file, 'r') as f:
        eodhd_events = json.load(f)
    
    with open(jblanked_file, 'r') as f:
        jblanked_events = json.load(f)
    
    print(f"📊 EODHD    : {len(eodhd_events):,} événements")
    print(f"📊 JBlanked : {len(jblanked_events):,} événements")
    print()
    
    # Dates critiques
    critical_dates = [
        ('2025-08-01', '2025.08.01', '1er août 2025'),
        ('2025-09-11', '2025.09.11', '11 septembre 2025'),
    ]
    
    # ====================================================================
    # ANALYSE PAR DATE CRITIQUE
    # ====================================================================
    
    for eodhd_date, jb_date, label in critical_dates:
        print("=" * 80)
        print(f"{label.upper()}")
        print("=" * 80)
        print()
        
        # EODHD
        eodhd_day = [e for e in eodhd_events if e.get('date', '').startswith(eodhd_date)]
        eodhd_us = [e for e in eodhd_day if e.get('country') == 'US']
        
        print(f"EODHD:")
        print(f"   Total: {len(eodhd_day)} événements")
        print(f"   US: {len(eodhd_us)} événements")
        print()
        
        if len(eodhd_us) > 0:
            print("   Événements US (5 premiers):")
            for e in eodhd_us[:5]:
                event_type = e.get('type', 'Unknown')
                actual = e.get('actual', '-')
                forecast = e.get('forecast', '-')
                previous = e.get('previous', '-')
                print(f"      {e.get('date')} | {event_type:35s} | A:{actual} F:{forecast} P:{previous}")
            if len(eodhd_us) > 5:
                print(f"      ... et {len(eodhd_us)-5} autres")
        
        print()
        
        # JBlanked
        jb_day = [e for e in jblanked_events if e.get('Date', '').startswith(jb_date)]
        jb_usd = [e for e in jb_day if e.get('Currency') == 'USD']
        
        print(f"JBlanked:")
        print(f"   Total: {len(jb_day)} événements")
        print(f"   USD: {len(jb_usd)} événements")
        print()
        
        if len(jb_usd) > 0:
            print("   Événements USD (5 premiers):")
            for e in jb_usd[:5]:
                name = e.get('Name', 'Unknown')
                actual = e.get('Actual', '-')
                forecast = e.get('Forecast', '-')
                previous = e.get('Previous', '-')
                print(f"      {e.get('Date')} | {name:35s} | A:{actual} F:{forecast} P:{previous}")
            if len(jb_usd) > 5:
                print(f"      ... et {len(jb_usd)-5} autres")
        
        print()
        
        # Comparaison
        print("COMPARAISON:")
        if len(eodhd_us) > len(jb_usd):
            print(f"   ✅ EODHD plus complet ({len(eodhd_us)} vs {len(jb_usd)})")
        elif len(eodhd_us) == len(jb_usd):
            print(f"   ⚖️  Équivalent ({len(eodhd_us)} événements)")
        else:
            print(f"   ⚠️  JBlanked plus complet ({len(jb_usd)} vs {len(eodhd_us)})")
        
        print()
    
    # ====================================================================
    # ANALYSE QUALITÉ DONNÉES
    # ====================================================================
    
    print("=" * 80)
    print("ANALYSE QUALITÉ DONNÉES")
    print("=" * 80)
    print()
    
    # Vérifier présence Actual/Forecast/Previous
    eodhd_with_values = sum(1 for e in eodhd_events 
                            if e.get('actual') or e.get('forecast') or e.get('previous'))
    
    jb_with_values = sum(1 for e in jblanked_events 
                         if e.get('Actual') or e.get('Forecast') or e.get('Previous'))
    
    print(f"Événements avec valeurs Actual/Forecast/Previous:")
    print(f"   EODHD    : {eodhd_with_values:,} / {len(eodhd_events):,} ({eodhd_with_values/len(eodhd_events)*100:.1f}%)")
    print(f"   JBlanked : {jb_with_values:,} / {len(jblanked_events):,} ({jb_with_values/len(jblanked_events)*100:.1f}%)")
    print()
    
    # ====================================================================
    # ANALYSE PAYS COUVERTS
    # ====================================================================
    
    print("=" * 80)
    print("ANALYSE PAYS COUVERTS")
    print("=" * 80)
    print()
    
    eodhd_countries = set(e.get('country', 'XX') for e in eodhd_events)
    jb_countries = set(e.get('Currency', 'XX') for e in jblanked_events)
    
    print(f"Pays EODHD    : {len(eodhd_countries)} pays")
    print(f"Pays JBlanked : {len(jb_countries)} pays")
    print()
    
    only_jb = jb_countries - eodhd_countries
    if len(only_jb) > 0:
        print(f"⚠️  Pays UNIQUEMENT dans JBlanked: {sorted(only_jb)}")
        print()
    
    # ====================================================================
    # RECOMMANDATION
    # ====================================================================
    
    print("=" * 80)
    print("RECOMMANDATION SCIENTIFIQUE")
    print("=" * 80)
    print()
    
    eodhd_better = True
    
    for eodhd_date, jb_date, label in critical_dates:
        eodhd_count = len([e for e in eodhd_events 
                          if e.get('date', '').startswith(eodhd_date) 
                          and e.get('country') == 'US'])
        jb_count = len([e for e in jblanked_events 
                       if e.get('Date', '').startswith(jb_date) 
                       and e.get('Currency') == 'USD'])
        
        if jb_count > eodhd_count:
            eodhd_better = False
            break
    
    if eodhd_better and eodhd_with_values > jb_with_values * 0.8:
        print("✅ RECOMMANDATION: UTILISER EODHD SEUL")
        print()
        print("JUSTIFICATION:")
        print(f"   • {len(eodhd_events):,} événements (vs {len(jblanked_events):,} JBlanked)")
        print(f"   • Dates critiques mieux couvertes")
        print(f"   • {eodhd_with_values/len(eodhd_events)*100:.1f}% événements avec valeurs")
        print()
        print("AVANTAGES:")
        print("   • Pas de merge nécessaire")
        print("   • Pas de conflits à gérer")
        print("   • Pipeline simplifié")
        print("   • 1 seule source = plus maintenable")
        print()
        print("PROCHAINES ÉTAPES:")
        print("   1. Importer EODHD seul dans DB")
        print("   2. Valider dates critiques")
        print("   3. Tester système complet")
    else:
        print("⚠️  RECOMMANDATION: GARDER DOUBLE SOURCE")
        print()
        print("JUSTIFICATION:")
        print("   • JBlanked apporte événements manquants")
        print("   • Ou qualité données supérieure")
        print()
        print("PROCHAINES ÉTAPES:")
        print("   1. Merger EODHD + JBlanked")
        print("   2. Gérer doublons")
        print("   3. Importer DB")
    
    print()

if __name__ == '__main__':
    compare_sources_critical_dates()
