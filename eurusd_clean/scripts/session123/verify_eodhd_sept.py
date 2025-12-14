"""
Vérification fichier EODHD septembre - Recherche 11 septembre

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import json
from pathlib import Path
from collections import defaultdict

def verify_eodhd_september():
    """Vérifier contenu exact EODHD septembre"""
    
    print("=" * 80)
    print("VÉRIFICATION EODHD SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    # Fichier septembre spécifique
    sept_file = data_dir / 'eodhd_2020_2025_monthly' / 'events_2025.json'
    
    if not sept_file.exists():
        print(f"❌ Fichier septembre non trouvé: {sept_file}")
        return
    
    print(f"📂 Fichier: {sept_file}")
    print()
    
    with open(sept_file, 'r') as f:
        events_2025 = json.load(f)
    
    print(f"📊 Total événements 2025: {len(events_2025)}")
    print()
    
    # Compter par mois
    by_month = defaultdict(int)
    for e in events_2025:
        date = e.get('date', '')
        if date:
            month = date[:7]  # YYYY-MM
            by_month[month] += 1
    
    print("Événements par mois 2025:")
    for month in sorted(by_month.keys()):
        count = by_month[month]
        print(f"   {month}: {count} événements")
    
    print()
    
    # Chercher spécifiquement 11 septembre
    print("=" * 80)
    print("RECHERCHE 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    sept_11 = [e for e in events_2025 if e.get('date', '').startswith('2025-09-11')]
    
    print(f"📅 Événements 11 septembre: {len(sept_11)}")
    print()
    
    if len(sept_11) > 0:
        print("ÉVÉNEMENTS TROUVÉS:")
        for e in sept_11:
            country = e.get('country', 'XX')
            event_type = e.get('type', 'Unknown')
            date = e.get('date', '')
            actual = e.get('actual', '')
            print(f"   {date} | {country:3s} | {event_type} | Actual: {actual}")
    else:
        print("❌ AUCUN ÉVÉNEMENT 11 SEPTEMBRE DANS FICHIER")
        print()
        print("Vérification dates voisines:")
        
        # Chercher 10, 11, 12 septembre
        for day in [10, 11, 12]:
            date_str = f'2025-09-{day:02d}'
            events_day = [e for e in events_2025 if e.get('date', '').startswith(date_str)]
            print(f"   {date_str}: {len(events_day)} événements")
            
            if len(events_day) > 0 and day != 11:
                print("      Exemples:")
                for e in events_day[:3]:
                    print(f"         {e.get('date')} - {e.get('type')}")
    
    print()
    
    # Vérifier septembre complet
    print("=" * 80)
    print("VÉRIFICATION SEPTEMBRE COMPLET")
    print("=" * 80)
    print()
    
    sept_events = [e for e in events_2025 if e.get('date', '').startswith('2025-09')]
    
    print(f"📊 Total événements septembre: {len(sept_events)}")
    print()
    
    # Compter par jour
    by_day = defaultdict(int)
    for e in sept_events:
        date = e.get('date', '')
        if date:
            day = date[:10]  # YYYY-MM-DD
            by_day[day] += 1
    
    print("Événements par jour septembre (premiers 15 jours):")
    for day in sorted(by_day.keys())[:15]:
        count = by_day[day]
        marker = " ← 11 SEPTEMBRE" if day == '2025-09-11' else ""
        print(f"   {day}: {count:3d} événements{marker}")
    
    print()
    
    # Vérifier requête téléchargement
    print("=" * 80)
    print("ANALYSE REQUÊTE TÉLÉCHARGEMENT")
    print("=" * 80)
    print()
    
    print("Requête effectuée (théorique):")
    print("   from: 2025-09-01")
    print("   to: 2025-09-30")
    print("   limit: 1000")
    print()
    
    if len(sept_events) < 1000:
        print(f"✅ Pas de troncature (< 1000 événements)")
    else:
        print(f"⚠️  Limite 1000 atteinte - possible troncature")
    
    print()
    
    # Conclusion
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    
    if len(sept_11) == 0:
        print("❌ 11 SEPTEMBRE ABSENT DU FICHIER EODHD")
        print()
        print("EXPLICATION PROBABLE:")
        print("   • EODHD n'a PAS publié événements 11 septembre 2025")
        print("   • OU événements supprimés depuis ancien téléchargement")
        print("   • OU problème date côté EODHD")
        print()
        print("IMPLICATION:")
        print("   • DB originale avait ancien téléchargement EODHD avec 11 sept")
        print("   • Nouveau téléchargement EODHD n'a plus ces événements")
        print("   • EODHD source instable pour 11 septembre")
        print()
        print("SOLUTION:")
        print("   • Utiliser JBlanked comme source principale")
        print("   • 11 septembre: 7 événements USD JBlanked disponibles")
    else:
        print("✅ 11 SEPTEMBRE PRÉSENT")
        print()
        print("Événements doivent être dans pipeline")

if __name__ == '__main__':
    verify_eodhd_september()
