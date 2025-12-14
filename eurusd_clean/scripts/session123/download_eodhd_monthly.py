"""
Téléchargement EODHD 2020-2025 - Requêtes MENSUELLES
Contournement limitation 2000 événements/an

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Double source optimisé
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime
from calendar import monthrange

# API KEY EODHD FUNDAMENTALS
API_KEY = "690fe4a00ab490.09631772"

def download_eodhd_monthly():
    """Télécharger EODHD 2020-2025 mois par mois"""
    
    print("=" * 80)
    print("TÉLÉCHARGEMENT EODHD 2020-2025 - MENSUEL")
    print("=" * 80)
    print()
    print("🎯 STRATÉGIE: Contournement limitation 2000 événements/an")
    print("   Requêtes mensuelles → Max 1000 événements/mois")
    print()
    
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'eodhd_2020_2025_monthly'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    url = "https://eodhd.com/api/economic-events"
    
    years = list(range(2020, 2026))  # 2020-2025
    all_events = []
    stats = {
        'success': [],
        'failed': [],
        'total_requests': 0,
        'total_events': 0
    }
    
    total_months = len(years) * 12
    current_month = 0
    
    print(f"📅 Période: 2020-2025")
    print(f"   Années: {len(years)}")
    print(f"   Mois total: {total_months}")
    print()
    print("⏱️  Durée estimée: 12-15 minutes")
    print()
    
    start_time = time.time()
    
    for year in years:
        print(f"📅 ANNÉE {year}")
        print("=" * 70)
        
        year_events = []
        year_success = 0
        year_failed = 0
        
        for month in range(1, 13):
            current_month += 1
            
            # Calculer dernier jour du mois
            last_day = monthrange(year, month)[1]
            
            month_name = datetime(year, month, 1).strftime('%B')
            
            print(f"   [{current_month:2d}/{total_months}] {month_name} {year} ", end='', flush=True)
            
            params = {
                'api_token': API_KEY,
                'from': f'{year}-{month:02d}-01',
                'to': f'{year}-{month:02d}-{last_day}',
                'limit': 1000,
                'fmt': 'json'
            }
            
            try:
                response = requests.get(url, params=params, timeout=60)
                stats['total_requests'] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list):
                        events = data
                    elif isinstance(data, dict):
                        events = data.get('events', data.get('data', []))
                    else:
                        events = []
                    
                    year_events.extend(events)
                    stats['total_events'] += len(events)
                    year_success += 1
                    
                    print(f"✅ {len(events):4d} événements")
                    
                else:
                    year_failed += 1
                    print(f"❌ Erreur {response.status_code}")
            
            except Exception as e:
                year_failed += 1
                print(f"❌ Erreur: {str(e)[:50]}")
            
            # Rate limiting léger
            time.sleep(0.5)
        
        # Sauvegarder année
        if len(year_events) > 0:
            year_file = output_dir / f'events_{year}.json'
            with open(year_file, 'w') as f:
                json.dump(year_events, f, indent=2)
            
            all_events.extend(year_events)
            stats['success'].append(year)
            
            print()
            print(f"   📊 {year}: {len(year_events)} événements ({year_success} mois OK, {year_failed} échecs)")
        else:
            stats['failed'].append(year)
            print(f"   ⚠️  {year}: 0 événements")
        
        print()
    
    # Sauvegarder tout
    all_file = output_dir / 'eodhd_all_2020_2025_monthly.json'
    with open(all_file, 'w') as f:
        json.dump(all_events, f, indent=2)
    
    elapsed = time.time() - start_time
    
    # Rapport final
    print("=" * 80)
    print("RAPPORT EODHD MENSUEL")
    print("=" * 80)
    print()
    print(f"✅ Années téléchargées : {len(stats['success'])}/{len(years)}")
    print(f"📊 Total événements    : {len(all_events)}")
    print(f"🔄 Requêtes effectuées : {stats['total_requests']}")
    print(f"💾 Fichier complet     : {all_file.name}")
    print(f"⏱️  Durée              : {elapsed/60:.1f} minutes")
    print()
    
    # Comparaison avec téléchargement annuel
    previous_total = 12000  # Téléchargement annuel précédent
    improvement = len(all_events) - previous_total
    
    print("COMPARAISON:")
    print(f"   Téléchargement annuel (précédent): {previous_total}")
    print(f"   Téléchargement mensuel (nouveau) : {len(all_events)}")
    print(f"   Amélioration                     : +{improvement} événements ({improvement/previous_total*100:.1f}%)")
    print()
    
    # Statistiques par année
    print("ÉVÉNEMENTS PAR ANNÉE:")
    for year in years:
        year_events_count = sum(1 for e in all_events 
                               if e.get('date', '').startswith(str(year)))
        print(f"   {year}: {year_events_count} événements")
    print()
    
    return all_events, stats

if __name__ == '__main__':
    print("🚀 DÉMARRAGE TÉLÉCHARGEMENT MENSUEL EODHD")
    print()
    print("⚠️  ATTENTION: 72 requêtes à effectuer")
    print("   Durée estimée: 12-15 minutes")
    print()
    
    input("Appuyez sur ENTRÉE pour démarrer...")
    print()
    
    events, stats = download_eodhd_monthly()
    
    if len(stats['success']) == 6:
        print("=" * 80)
        print("✅ EODHD MENSUEL COMPLET")
        print("=" * 80)
        print()
        print(f"🎉 {len(events)} événements téléchargés")
        print()
        print("Prochaines étapes:")
        print("   1. Remplacer fichier EODHD dans data/eodhd_2020_2025/")
        print("   2. Re-lancer merge_sources.py")
        print("   3. Import DB")
    else:
        print(f"⚠️  Années manquantes: {stats['failed']}")
