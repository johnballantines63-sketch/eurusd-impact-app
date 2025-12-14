"""
Vérification Timezone JBlanked API - Session 123

Ce script vérifie quelle timezone utilise JBlanked en comparant
des événements connus avec leurs heures UTC de publication réelles.

Objectif : Identifier si JBlanked utilise UTC, GMT, CEST, ou autre timezone.

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import json
from pathlib import Path
from datetime import datetime
import pytz
from typing import Dict, List, Tuple


# Événements de référence avec heures UTC CONNUES
# Source : ForexFactory, Investing.com, calendriers officiels
REFERENCE_EVENTS = [
    {
        'name': 'Non-Farm Employment Change',
        'country': 'USD',
        'date': '2025-08-01',
        'time_utc': '12:30:00',  # NFP TOUJOURS 12:30 UTC
        'description': 'US NFP (1er vendredi du mois, 8:30 ET = 12:30 UTC)'
    },
    {
        'name': 'Unemployment Rate',
        'country': 'USD',
        'date': '2025-08-01',
        'time_utc': '12:30:00',  # Publié avec NFP
        'description': 'US Unemployment (avec NFP, 8:30 ET = 12:30 UTC)'
    },
    {
        'name': 'Average Hourly Earnings',
        'country': 'USD',
        'date': '2025-08-01',
        'time_utc': '12:30:00',  # Publié avec NFP
        'description': 'US Average Hourly Earnings (avec NFP, 8:30 ET = 12:30 UTC)'
    },
    {
        'name': 'ISM Manufacturing PMI',
        'country': 'USD',
        'date': '2025-08-01',
        'time_utc': '14:00:00',  # ISM généralement 10:00 ET = 14:00 UTC
        'description': 'US ISM Manufacturing (10:00 ET = 14:00 UTC)'
    },
    {
        'name': 'Construction Spending',
        'country': 'USD',
        'date': '2025-08-01',
        'time_utc': '14:00:00',  # Construction Spending 10:00 ET = 14:00 UTC
        'description': 'US Construction Spending (10:00 ET = 14:00 UTC)'
    }
]


def load_jblanked_august_data() -> List[Dict]:
    """Charger données JBlanked août 2025 (téléchargées Session 122)"""
    data_path = Path(__file__).parent.parent / 'session122' / 'jblanked_test' / 'jblanked_august_2025.json'
    
    if not data_path.exists():
        raise FileNotFoundError(f"Fichier données août 2025 introuvable : {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    print(f"✅ Chargé {len(data)} événements août 2025")
    return data


def find_event_in_jblanked(events_jblanked: List[Dict], event_ref: Dict) -> Dict:
    """
    Trouver événement de référence dans données JBlanked
    
    Args:
        events_jblanked: Liste événements JBlanked
        event_ref: Événement référence à chercher
    
    Returns:
        Événement JBlanked trouvé ou None
    """
    # Normaliser nom pour recherche flexible
    name_search = event_ref['name'].lower()
    date_search = event_ref['date']
    country_search = event_ref['country']
    
    for event in events_jblanked:
        # Vérifier correspondance
        if (country_search in event.get('Currency', '') and
            date_search in event.get('Date', '') and
            name_search in event.get('Name', '').lower()):
            return event
    
    return None


def parse_jblanked_timestamp(date_str: str) -> datetime:
    """
    Parser timestamp JBlanked (format "YYYY.MM.DD HH:MM:SS")
    
    ATTENTION : Retourne datetime NAIVE (sans timezone)
    Car on ne connaît PAS encore la timezone JBlanked !
    """
    return datetime.strptime(date_str, "%Y.%m.%d %H:%M:%S")


def calculate_offset_minutes(jblanked_time: str, utc_time: str) -> int:
    """
    Calculer décalage en minutes entre timestamp JBlanked et UTC attendu
    
    Args:
        jblanked_time: "HH:MM:SS" (JBlanked)
        utc_time: "HH:MM:SS" (UTC réel)
    
    Returns:
        Décalage en minutes (positif = JBlanked en avance sur UTC)
    """
    # Parser heures
    jb_h, jb_m, jb_s = map(int, jblanked_time.split(':'))
    utc_h, utc_m, utc_s = map(int, utc_time.split(':'))
    
    # Convertir en minutes totales
    jb_minutes = jb_h * 60 + jb_m
    utc_minutes = utc_h * 60 + utc_m
    
    # Décalage
    offset = jb_minutes - utc_minutes
    
    return offset


def identify_timezone_from_offset(offset_minutes: int) -> str:
    """
    Identifier timezone probable selon décalage UTC
    
    Args:
        offset_minutes: Décalage en minutes
    
    Returns:
        Timezone probable (ex: "UTC+2", "CEST", etc.)
    """
    offset_hours = offset_minutes / 60.0
    
    # Timezones connues
    timezones = {
        0: 'UTC / GMT',
        60: 'CET (UTC+1) - Central European Time',
        120: 'CEST (UTC+2) - Central European Summer Time',
        180: 'GMT+3 (Moscou)',
        -240: 'EDT (UTC-4) - Eastern Daylight Time',
        -300: 'EST (UTC-5) - Eastern Standard Time',
        -360: 'CST (UTC-6) - Central Standard Time'
    }
    
    return timezones.get(offset_minutes, f'UTC{offset_hours:+.1f}')


def verify_timezone():
    """Fonction principale : vérifier timezone JBlanked"""
    
    print("=" * 80)
    print("VÉRIFICATION TIMEZONE JBLANKED API")
    print("=" * 80)
    print()
    
    # 1. Charger données août 2025
    print("📂 ÉTAPE 1 : Chargement données août 2025")
    print("-" * 80)
    events_jblanked = load_jblanked_august_data()
    print()
    
    # 2. Tester chaque événement référence
    print("🔍 ÉTAPE 2 : Comparaison événements référence")
    print("-" * 80)
    
    results = []
    
    for i, event_ref in enumerate(REFERENCE_EVENTS, 1):
        print(f"\n[{i}/{len(REFERENCE_EVENTS)}] {event_ref['name']}")
        print(f"    Date attendue : {event_ref['date']} {event_ref['time_utc']} UTC")
        print(f"    Description   : {event_ref['description']}")
        
        # Chercher dans JBlanked
        event_jb = find_event_in_jblanked(events_jblanked, event_ref)
        
        if not event_jb:
            print(f"    ❌ NON TROUVÉ dans données JBlanked")
            continue
        
        # Extraire timestamp JBlanked
        jb_timestamp_str = event_jb['Date']
        jb_datetime = parse_jblanked_timestamp(jb_timestamp_str)
        
        # Extraire heure seulement
        jb_time_str = jb_datetime.strftime("%H:%M:%S")
        
        print(f"    ✅ TROUVÉ : {event_jb['Name']}")
        print(f"    Timestamp JBlanked : {jb_timestamp_str}")
        print(f"    Heure JBlanked     : {jb_time_str}")
        
        # Calculer décalage
        offset = calculate_offset_minutes(jb_time_str, event_ref['time_utc'])
        offset_hours = offset / 60.0
        
        print(f"    Décalage           : {offset:+d} minutes ({offset_hours:+.1f}h)")
        
        # Identifier timezone
        tz_probable = identify_timezone_from_offset(offset)
        print(f"    Timezone probable  : {tz_probable}")
        
        # Sauvegarder résultat
        results.append({
            'event_name': event_ref['name'],
            'jblanked_time': jb_time_str,
            'utc_time': event_ref['time_utc'],
            'offset_minutes': offset,
            'offset_hours': offset_hours,
            'timezone_probable': tz_probable
        })
    
    # 3. Analyser résultats
    print("\n" + "=" * 80)
    print("📊 ÉTAPE 3 : ANALYSE RÉSULTATS")
    print("=" * 80)
    
    if not results:
        print("❌ ERREUR : Aucun événement trouvé pour validation !")
        return
    
    # Calculer décalage moyen
    offsets = [r['offset_minutes'] for r in results]
    offset_mean = sum(offsets) / len(offsets)
    offset_std = (sum((o - offset_mean)**2 for o in offsets) / len(offsets))**0.5
    
    print(f"\nNombre événements testés : {len(results)}")
    print(f"Décalage moyen           : {offset_mean:+.1f} minutes ({offset_mean/60:+.2f}h)")
    print(f"Écart-type               : {offset_std:.1f} minutes")
    
    # Tous identiques ?
    if offset_std < 1.0:  # Écart-type < 1 minute = identiques
        print(f"\n✅ DÉCALAGE CONSTANT : Tous événements ont même décalage")
        
        # Identifier timezone
        tz_final = identify_timezone_from_offset(int(offset_mean))
        
        print(f"\n🎯 CONCLUSION :")
        print(f"   JBlanked utilise : {tz_final}")
        print(f"   Décalage UTC     : {offset_mean/60:+.2f} heures")
        
        # Recommandation conversion
        print(f"\n💡 CONVERSION NÉCESSAIRE :")
        if abs(offset_mean) < 1:
            print(f"   ✅ JBlanked = UTC → Pas de conversion nécessaire")
            print(f"   Stocker directement dans DB (ts_utc)")
        else:
            print(f"   ⚠️  JBlanked ≠ UTC → Conversion obligatoire")
            print(f"   Soustraire {offset_mean/60:.1f}h des timestamps JBlanked")
            print(f"   Exemple : {results[0]['jblanked_time']} → {results[0]['utc_time']}")
        
    else:
        print(f"\n⚠️  DÉCALAGES VARIABLES : Différents selon événements")
        print(f"   Écart-type trop grand : {offset_std:.1f} minutes")
        print(f"   Investigation manuelle nécessaire")
    
    # 4. Détails par événement
    print("\n" + "-" * 80)
    print("DÉTAILS PAR ÉVÉNEMENT :")
    print("-" * 80)
    print(f"{'Événement':<40} {'JBlanked':<10} {'UTC':<10} {'Offset':<10}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['event_name']:<40} {r['jblanked_time']:<10} {r['utc_time']:<10} {r['offset_hours']:+.1f}h")
    
    print("\n" + "=" * 80)
    
    # Sauvegarder résultats JSON
    output_path = Path(__file__).parent / 'timezone_verification_results.json'
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp_verification': datetime.now().isoformat(),
            'offset_mean_minutes': offset_mean,
            'offset_std_minutes': offset_std,
            'timezone_identified': identify_timezone_from_offset(int(offset_mean)),
            'events_tested': results
        }, f, indent=2)
    
    print(f"✅ Résultats sauvegardés : {output_path}")
    print()


if __name__ == '__main__':
    verify_timezone()
