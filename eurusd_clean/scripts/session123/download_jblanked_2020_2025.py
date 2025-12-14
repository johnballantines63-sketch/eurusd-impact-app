"""
Téléchargement JBlanked 2020-2025 - Source 1

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Double source
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

# CLÉ API VIP
API_KEY = "dDHtBWTu.4pZsVUuSaGY51HHDq2gHVbI9HOECbSPy"

def download_jblanked_2020_2025():
    """Télécharger JBlanked 2020-2025"""
    
    print("=" * 80)
    print("TÉLÉCHARGEMENT JBLANKED 2020-2025")
    print("=" * 80)
    print()
    
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'jblanked_2020_2025'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    url = "https://www.jblanked.com/news/api/forex-factory/calendar/range/"
    headers = {
        'Authorization': f'Api-Key {API_KEY}',
        'Accept': 'application/json'
    }
    
    years = list(range(2020, 2026))  # 2020-2025
    all_events = []
    stats = {'success': [], 'failed': []}
    
    print(f"Années à télécharger : {len(years)}")
    print(f"Output : {output_dir}")
    print()
    
    for year in years:
        print(f"📅 ANNÉE {year}")
        print("-" * 70)
        
        params = {
            'from': f'{year}-01-01',
            'to': f'{year}-12-31'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    print(f"   ✅ {len(data)} événements")
                    
                    # Sauvegarder année
                    year_file = output_dir / f'events_{year}.json'
                    with open(year_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    all_events.extend(data)
                    stats['success'].append(year)
                else:
                    print(f"   ❌ Format inattendu")
                    stats['failed'].append(year)
            else:
                print(f"   ❌ Erreur {response.status_code}")
                stats['failed'].append(year)
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            stats['failed'].append(year)
        
        # Rate limiting
        if year < years[-1]:
            time.sleep(2)
        
        print()
    
    # Sauvegarder tout
    all_file = output_dir / 'jblanked_all_2020_2025.json'
    with open(all_file, 'w') as f:
        json.dump(all_events, f, indent=2)
    
    # Rapport
    print("=" * 80)
    print("RAPPORT JBLANKED")
    print("=" * 80)
    print()
    print(f"✅ Années téléchargées : {len(stats['success'])}/{len(years)}")
    print(f"📊 Total événements    : {len(all_events)}")
    print(f"💾 Fichier complet     : {all_file.name}")
    print()
    
    return all_events, stats

if __name__ == '__main__':
    events, stats = download_jblanked_2020_2025()
    
    if len(stats['success']) == 6:
        print("✅ JBLANKED COMPLET")
    else:
        print(f"⚠️  Années manquantes: {stats['failed']}")
