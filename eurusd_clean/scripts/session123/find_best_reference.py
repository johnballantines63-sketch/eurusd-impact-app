"""
Chercher date avec 10+ événements simultanés - Alternative au 11 septembre

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import json
from pathlib import Path
from collections import defaultdict

def find_best_reference_date():
    """Trouver la meilleure date de référence avec événements multiples"""
    
    print("=" * 80)
    print("RECHERCHE DATE RÉFÉRENCE AVEC 10+ ÉVÉNEMENTS SIMULTANÉS")
    print("=" * 80)
    print()
    
    # Charger septembre
    data_file = Path(__file__).parent / 'jblanked_september_2025.json'
    
    if not data_file.exists():
        print("❌ Fichier septembre non trouvé")
        return
    
    with open(data_file, 'r') as f:
        sept_events = json.load(f)
    
    # Grouper par date + heure
    by_datetime = defaultdict(list)
    
    for event in sept_events:
        if event.get('Currency') == 'USD':
            datetime_str = event.get('Date', '')
            if datetime_str:
                # Extraire date et heure
                parts = datetime_str.split()
                if len(parts) >= 2:
                    date = parts[0]
                    time = parts[1]
                    key = f"{date} {time}"
                    by_datetime[key].append(event)
    
    # Trier par nombre d'événements
    sorted_datetimes = sorted(by_datetime.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"📊 Analysé: {len(sept_events)} événements septembre")
    print(f"📊 Trouvé: {len(by_datetime)} moments différents avec événements USD")
    print()
    
    print("=" * 80)
    print("TOP 10 MOMENTS AVEC LE PLUS D'ÉVÉNEMENTS USD")
    print("=" * 80)
    print()
    
    for i, (datetime_key, events) in enumerate(sorted_datetimes[:10], 1):
        print(f"[{i:2d}] {datetime_key} - {len(events)} événements USD")
        
        for event in events:
            print(f"     • {event['Name']}")
        
        print()
    
    # Chercher moment avec 10+ événements
    print("=" * 80)
    print("MOMENTS AVEC 10+ ÉVÉNEMENTS")
    print("=" * 80)
    print()
    
    found_10plus = False
    
    for datetime_key, events in sorted_datetimes:
        if len(events) >= 10:
            found_10plus = True
            print(f"✅ {datetime_key} - {len(events)} événements")
            
            for event in events:
                print(f"   • {event['Name']}")
                print(f"     Actual: {event.get('Actual')}, Forecast: {event.get('Forecast')}, Previous: {event.get('Previous')}")
            
            print()
    
    if not found_10plus:
        print("⚠️  AUCUN moment avec 10+ événements simultanés en septembre")
        print()
        print("Maximum trouvé:")
        if sorted_datetimes:
            best_datetime, best_events = sorted_datetimes[0]
            print(f"   {best_datetime}: {len(best_events)} événements")
    
    print()
    print("=" * 80)
    print("RECOMMANDATION")
    print("=" * 80)
    print()
    
    if sorted_datetimes:
        best_datetime, best_events = sorted_datetimes[0]
        best_count = len(best_events)
        
        if best_count >= 10:
            print(f"✅ Utiliser {best_datetime} comme cas de référence")
            print(f"   {best_count} événements simultanés")
        elif best_count >= 5:
            print(f"⚠️  Maximum {best_count} événements le {best_datetime}")
            print()
            print("Options:")
            print("  1. Utiliser ce moment comme référence (moins d'événements)")
            print("  2. Télécharger autre mois (août, octobre)")
            print("  3. Accepter que cas 11 événements n'existe pas dans JBlanked")
        else:
            print(f"❌ Septembre insuffisant (max {best_count} événements)")
    
    print()

if __name__ == '__main__':
    find_best_reference_date()
