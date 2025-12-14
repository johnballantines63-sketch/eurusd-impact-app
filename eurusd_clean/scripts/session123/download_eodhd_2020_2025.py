"""
Téléchargement EODHD 2020-2025 - Source 2

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Double source
"""

import requests
import json
import time
from pathlib import Path

# API KEY EODHD FUNDAMENTALS
API_KEY = "690fe4a00ab490.09631772"

def download_eodhd_2020_2025():
    """Télécharger EODHD 2020-2025 avec limit=1000"""
    
    print("=" * 80)
    print("TÉLÉCHARGEMENT EODHD 2020-2025")
    print("=" * 80)
    print()
    
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'eodhd_2020_2025'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    url = "https://eodhd.com/api/economic-events"
    
    years = list(range(2020, 2026))
    all_events = []
    stats = {'success': [], 'failed': []}
    
    print(f"Années à télécharger : {len(years)}")
    print(f"Output : {output_dir}")
    print()
    
    for year in years:
        print(f"📅 ANNÉE {year}")
        print("-" * 70)
        
        # Pagination si > 1000 événements
        offset = 0
        year_events = []
        
        while True:
            params = {
                'api_token': API_KEY,
                'from': f'{year}-01-01',
                'to': f'{year}-12-31',
                'limit': 1000,
                'offset': offset,
                'fmt': 'json'
            }
            
            try:
                response = requests.get(url, params=params, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list):
                        events = data
                    elif isinstance(data, dict):
                        events = data.get('events', data.get('data', []))
                    else:
                        events = []
                    
                    if len(events) == 0:
                        break  # Fin pagination
                    
                    year_events.extend(events)
                    
                    if len(events) < 1000:
                        break  # Dernière page
                    
                    offset += 1000
                    print(f"   Pagination offset={offset}...")
                
                else:
                    print(f"   ❌ Erreur {response.status_code}")
                    break
            
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                break
        
        if len(year_events) > 0:
            print(f"   ✅ {len(year_events)} événements")
            
            # Sauvegarder année
            year_file = output_dir / f'events_{year}.json'
            with open(year_file, 'w') as f:
                json.dump(year_events, f, indent=2)
            
            all_events.extend(year_events)
            stats['success'].append(year)
        else:
            stats['failed'].append(year)
        
        time.sleep(1)  # Rate limiting
        print()
    
    # Sauvegarder tout
    all_file = output_dir / 'eodhd_all_2020_2025.json'
    with open(all_file, 'w') as f:
        json.dump(all_events, f, indent=2)
    
    # Rapport
    print("=" * 80)
    print("RAPPORT EODHD")
    print("=" * 80)
    print()
    print(f"✅ Années téléchargées : {len(stats['success'])}/{len(years)}")
    print(f"📊 Total événements    : {len(all_events)}")
    print(f"💾 Fichier complet     : {all_file.name}")
    print()
    
    return all_events, stats

if __name__ == '__main__':
    events, stats = download_eodhd_2020_2025()
    
    if len(stats['success']) == 6:
        print("✅ EODHD COMPLET")
    else:
        print(f"⚠️  Années manquantes: {stats['failed']}")
