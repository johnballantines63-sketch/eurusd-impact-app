"""
Merge intelligent JBlanked + EODHD → Table Master

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Double source
"""

import json
from pathlib import Path
from normalize import normalize_jblanked_event, normalize_eodhd_event

def merge_sources():
    """Merger JBlanked + EODHD avec déduplication"""
    
    print("=" * 80)
    print("MERGE JBLANKED + EODHD → MASTER")
    print("=" * 80)
    print()
    
    # Charger données
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    jblanked_file = data_dir / 'jblanked_2020_2025' / 'jblanked_all_2020_2025.json'
    eodhd_file = data_dir / 'eodhd_2020_2025' / 'eodhd_all_2020_2025.json'
    
    print("📂 Chargement données...")
    
    with open(jblanked_file, 'r') as f:
        jblanked_events = json.load(f)
    print(f"   ✅ JBlanked: {len(jblanked_events)} événements")
    
    with open(eodhd_file, 'r') as f:
        eodhd_events = json.load(f)
    print(f"   ✅ EODHD: {len(eodhd_events)} événements")
    print()
    
    # Normaliser et merger
    print("🔄 Normalisation et merge...")
    print()
    
    master = {}  # event_key → event
    
    # Étape 1 : Ajouter JBlanked
    print("ÉTAPE 1 : Ajout JBlanked (source prioritaire)")
    jblanked_added = 0
    jblanked_errors = 0
    
    for event in jblanked_events:
        try:
            normalized = normalize_jblanked_event(event)
            event_key = normalized['event_key']
            
            if event_key not in master:
                master[event_key] = normalized
                jblanked_added += 1
        except Exception as e:
            jblanked_errors += 1
            if jblanked_errors <= 5:
                print(f"   ⚠️ Erreur normalisation JBlanked: {e}")
    
    print(f"   ✅ {jblanked_added} événements JBlanked ajoutés")
    if jblanked_errors > 0:
        print(f"   ⚠️ {jblanked_errors} erreurs normalisation")
    print()
    
    # Étape 2 : Ajouter EODHD (uniquement nouveaux)
    print("ÉTAPE 2 : Ajout EODHD (complément)")
    eodhd_added = 0
    eodhd_duplicates = 0
    eodhd_conflicts = 0
    eodhd_errors = 0
    
    for event in eodhd_events:
        try:
            normalized = normalize_eodhd_event(event)
            event_key = normalized['event_key']
            
            if event_key in master:
                # Doublon détecté
                eodhd_duplicates += 1
                
                existing = master[event_key]
                
                # Vérifier si valeurs identiques
                if (existing['actual'] == normalized['actual'] and
                    existing['forecast'] == normalized['forecast'] and
                    existing['previous'] == normalized['previous']):
                    # Valeurs identiques → marquer BOTH
                    existing['source'] = 'BOTH'
                    existing['validated'] = True
                else:
                    # Valeurs différentes → conflit
                    eodhd_conflicts += 1
                    existing['source'] = 'BOTH_CONFLICT'
                    existing['jblanked_actual'] = existing['actual']
                    existing['eodhd_actual'] = normalized['actual']
                    # Garder valeur JBlanked (prioritaire)
            else:
                # Nouvel événement
                master[event_key] = normalized
                eodhd_added += 1
        
        except Exception as e:
            eodhd_errors += 1
            if eodhd_errors <= 5:
                print(f"   ⚠️ Erreur normalisation EODHD: {e}")
    
    print(f"   ✅ {eodhd_added} événements EODHD ajoutés (nouveaux)")
    print(f"   🔄 {eodhd_duplicates} doublons détectés")
    if eodhd_conflicts > 0:
        print(f"   ⚠️ {eodhd_conflicts} conflits valeurs (JBlanked prioritaire)")
    if eodhd_errors > 0:
        print(f"   ⚠️ {eodhd_errors} erreurs normalisation")
    print()
    
    # Statistiques finales
    print("=" * 80)
    print("STATISTIQUES MASTER")
    print("=" * 80)
    print()
    
    total = len(master)
    
    # Compter par source
    jblanked_only = sum(1 for e in master.values() if e['source'] == 'JBLANKED')
    eodhd_only = sum(1 for e in master.values() if e['source'] == 'EODHD')
    both = sum(1 for e in master.values() if e['source'] in ['BOTH', 'BOTH_CONFLICT'])
    
    print(f"📊 TOTAL MASTER        : {total} événements")
    print()
    print("Par source:")
    print(f"   JBlanked uniquement : {jblanked_only}")
    print(f"   EODHD uniquement    : {eodhd_only}")
    print(f"   Les deux (validés)  : {both}")
    print()
    
    # Compter par pays
    countries = {}
    for event in master.values():
        country = event['country']
        countries[country] = countries.get(country, 0) + 1
    
    print("Top 10 pays:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {country.upper()}: {count} événements")
    print()
    
    # Compter par année
    years = {}
    for event in master.values():
        year = event['datetime_utc'][:4]
        years[year] = years.get(year, 0) + 1
    
    print("Par année:")
    for year in sorted(years.keys()):
        print(f"   {year}: {years[year]} événements")
    print()
    
    # Sauvegarder master
    output_dir = data_dir / 'master'
    output_dir.mkdir(exist_ok=True)
    
    master_file = output_dir / 'events_master_2020_2025.json'
    
    # Convertir dict → list
    master_list = list(master.values())
    
    # Trier par date
    master_list.sort(key=lambda x: x['datetime_utc'])
    
    with open(master_file, 'w') as f:
        json.dump(master_list, f, indent=2)
    
    print(f"💾 Master sauvegardé: {master_file}")
    print(f"   Fichier: {master_file.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    # Validation dates critiques
    print("=" * 80)
    print("VALIDATION DATES CRITIQUES")
    print("=" * 80)
    print()
    
    # 1er août 2025
    august_1st = [e for e in master_list if e['datetime_utc'].startswith('2025-08-01')]
    august_1st_usd = [e for e in august_1st if e['country'] == 'usd']
    
    print("1er août 2025:")
    print(f"   Total: {len(august_1st)} événements")
    print(f"   USD: {len(august_1st_usd)} événements")
    
    if len(august_1st_usd) > 0:
        sources = {}
        for e in august_1st_usd:
            src = e['source']
            sources[src] = sources.get(src, 0) + 1
        print(f"   Sources: {sources}")
    print()
    
    # 11 septembre 2025
    sept_11 = [e for e in master_list if e['datetime_utc'].startswith('2025-09-11')]
    sept_11_usd = [e for e in sept_11 if e['country'] == 'usd']
    
    print("11 septembre 2025:")
    print(f"   Total: {len(sept_11)} événements")
    print(f"   USD: {len(sept_11_usd)} événements")
    
    if len(sept_11_usd) > 0:
        sources = {}
        for e in sept_11_usd:
            src = e['source']
            sources[src] = sources.get(src, 0) + 1
        print(f"   Sources: {sources}")
        print()
        print("   Événements USD 11 sept:")
        for e in sept_11_usd:
            print(f"      • {e['datetime_utc']} - {e['event_name']} ({e['source']})")
    else:
        print("   ⚠️ Aucun événement USD")
    print()
    
    print("=" * 80)
    print("✅ MERGE TERMINÉ")
    print("=" * 80)
    
    return master_list

if __name__ == '__main__':
    master = merge_sources()
    print(f"\n🎉 Master créé: {len(master)} événements")
