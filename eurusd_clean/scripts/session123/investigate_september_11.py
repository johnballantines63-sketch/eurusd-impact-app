"""
Investigation complète 11 septembre 2025 - Chercher événements manquants

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import json
from pathlib import Path

def investigate_september_11():
    """Analyser tous événements US du 11 septembre"""
    
    print("=" * 80)
    print("INVESTIGATION 11 SEPTEMBRE 2025 - ÉVÉNEMENTS MANQUANTS")
    print("=" * 80)
    print()
    
    # Charger septembre
    data_file = Path(__file__).parent / 'jblanked_september_2025.json'
    
    if not data_file.exists():
        print("❌ Fichier septembre non trouvé")
        return
    
    with open(data_file, 'r') as f:
        sept_events = json.load(f)
    
    # Extraire 11 septembre
    sept_11 = [e for e in sept_events if e.get('Date', '').startswith('2025.09.11')]
    
    print(f"📊 Total événements 11 septembre: {len(sept_11)}")
    print()
    
    # Filtrer USD uniquement
    sept_11_usd = [e for e in sept_11 if e.get('Currency') == 'USD']
    
    print(f"📊 Événements USD 11 septembre: {len(sept_11_usd)}")
    print()
    
    print("=" * 80)
    print("TOUS LES ÉVÉNEMENTS USD DU 11 SEPTEMBRE")
    print("=" * 80)
    print()
    
    for i, event in enumerate(sept_11_usd, 1):
        print(f"[{i:2d}] {event['Date']} | {event['Name']}")
        print(f"     Actual: {event.get('Actual'):>10}  Forecast: {event.get('Forecast'):>10}  Previous: {event.get('Previous'):>10}")
        print()
    
    print("=" * 80)
    print("ANALYSE")
    print("=" * 80)
    print()
    
    # Chercher événements critiques manquants
    critical_missing = {
        'Retail Sales': False,
        'PPI': False,
        'Core PPI': False,
    }
    
    for event in sept_11_usd:
        name = event['Name'].lower()
        if 'retail sales' in name:
            critical_missing['Retail Sales'] = True
        if 'ppi' in name and 'core' not in name:
            critical_missing['PPI'] = True
        if 'core ppi' in name:
            critical_missing['Core PPI'] = True
    
    print("ÉVÉNEMENTS CRITIQUES ATTENDUS:")
    print()
    for event_name, found in critical_missing.items():
        status = "✅" if found else "❌ MANQUANT"
        print(f"   {status} {event_name}")
    
    print()
    
    # Hypothèses
    print("=" * 80)
    print("HYPOTHÈSES ÉVÉNEMENTS MANQUANTS")
    print("=" * 80)
    print()
    
    print("🔍 Possibilités:")
    print()
    print("1. Retail Sales / PPI publiés à AUTRE DATE")
    print("   → Chercher autour du 11 septembre")
    print()
    print("2. Cas référence utilisait AUTRE SOURCE")
    print("   → Données agrégées de plusieurs sources")
    print()
    print("3. Cas référence était AUTRE DATE")
    print("   → Vérifier si c'était vraiment 11 septembre")
    print()
    
    # Chercher autour du 11 septembre
    print("=" * 80)
    print("ÉVÉNEMENTS USD AUTOUR DU 11 SEPTEMBRE")
    print("=" * 80)
    print()
    
    dates_around = ['2025.09.10', '2025.09.11', '2025.09.12']
    
    for date in dates_around:
        events_date = [e for e in sept_events if e.get('Date', '').startswith(date) and e.get('Currency') == 'USD']
        
        print(f"📅 {date}: {len(events_date)} événements USD")
        
        for event in events_date:
            if any(keyword in event['Name'].lower() for keyword in ['retail', 'ppi', 'sales']):
                print(f"   → {event['Date']} | {event['Name']}")
        
        print()
    
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    
    if len(sept_11_usd) < 10:
        print(f"⚠️  PROBLÈME: Seulement {len(sept_11_usd)} événements USD le 11 septembre")
        print()
        print("Actions recommandées:")
        print()
        print("1️⃣ Vérifier si cas référence était VRAIMENT 11 septembre")
        print("   → Chercher dans documentation Sessions précédentes")
        print("   → Peut-être que c'était une autre date")
        print()
        print("2️⃣ Accepter que JBlanked n'a que 4 événements ce jour")
        print("   → Utiliser autre date comme référence")
        print("   → Chercher date avec 10+ événements simultanés")
        print()
        print("3️⃣ Combiner plusieurs dates pour tests")
        print("   → 11 sept: CPI")
        print("   → Autre date: Retail Sales")
        print("   → Autre date: PPI")
    
    print()

if __name__ == '__main__':
    investigate_september_11()
