#!/usr/bin/env python3
"""
EXPLORATION API MYFXBOOK - Session 122
======================================

Objectif : Explorer API MyFXBook et comparer avec EODHD

Tests :
1. Structure endpoint et paramètres
2. Téléchargement août 2025 (cas problématique EODHD)
3. Analyse structure JSON
4. Comparaison quantitative EODHD vs MyFXBook

Date : 08 novembre 2025
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Configuration
SESSION_ID = "4F%2Fd97ubtQcqjUEEXyD3uKoK8FkqpH4Blse95HYixvQl58PZ6Z%2FTdDQnEeQKVs8GQuHSgPbGSKjG7tRYOosIVA%3D%3D"
API_BASE_URL = "https://www.myfxbook.com/api"

# Dossier output
OUTPUT_DIR = Path(__file__).parent / "myfxbook_exploration"
OUTPUT_DIR.mkdir(exist_ok=True)


def test_endpoint_structure():
    """
    Test 1 : Explorer structure endpoint calendrier économique
    """
    print("=" * 80)
    print("TEST 1 : STRUCTURE ENDPOINT")
    print("=" * 80)
    
    # Endpoint attendu
    endpoint = f"{API_BASE_URL}/get-economic-calendar.json"
    
    print(f"\n📡 Endpoint : {endpoint}")
    print(f"🔑 Session ID : {SESSION_ID[:50]}...")
    
    # Test simple sans dates
    print("\n⏳ Test requête simple (sans paramètres dates)...")
    
    params = {
        "session": SESSION_ID
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        
        print(f"✅ Status code : {response.status_code}")
        print(f"📦 Content-Type : {response.headers.get('Content-Type', 'N/A')}")
        print(f"📏 Response size : {len(response.content)} bytes")
        
        if response.status_code == 200:
            data = response.json()
            
            # Sauvegarder réponse brute
            output_file = OUTPUT_DIR / "test_simple_response.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Réponse sauvegardée : {output_file}")
            
            # Analyser structure
            print("\n📊 STRUCTURE RÉPONSE :")
            print(f"   Type : {type(data)}")
            
            if isinstance(data, dict):
                print(f"   Clés principales : {list(data.keys())}")
                
                # Si erreur
                if 'error' in data:
                    print(f"   ⚠️ Error flag : {data.get('error')}")
                    print(f"   ⚠️ Message : {data.get('message', 'N/A')}")
                
                # Si données calendrier
                if 'economicCalendar' in data:
                    events = data['economicCalendar']
                    print(f"   📅 Events retournés : {len(events)}")
                    
                    if len(events) > 0:
                        print("\n   📋 Exemple premier event :")
                        first_event = events[0]
                        for key, value in first_event.items():
                            print(f"      {key}: {value}")
            
            return data
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
            print(f"   Réponse : {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return None


def test_august_2025_download():
    """
    Test 2 : Télécharger août 2025 (cas problématique EODHD)
    """
    print("\n" + "=" * 80)
    print("TEST 2 : TÉLÉCHARGEMENT AOÛT 2025")
    print("=" * 80)
    
    endpoint = f"{API_BASE_URL}/get-economic-calendar.json"
    
    # Dates août 2025
    start_date = "08-01-2025"  # Format MM-DD-YYYY (à tester)
    end_date = "08-31-2025"
    
    print(f"\n📅 Période : {start_date} → {end_date}")
    print(f"🎯 Objectif : Vérifier présence NFP 1er août 2025")
    
    params = {
        "session": SESSION_ID,
        "start": start_date,
        "end": end_date
    }
    
    print(f"\n⏳ Téléchargement...")
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Sauvegarder
            output_file = OUTPUT_DIR / "august_2025_events.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Téléchargement réussi")
            print(f"💾 Sauvegardé : {output_file}")
            
            # Analyser
            if 'error' in data and data['error']:
                print(f"\n⚠️ ERREUR API :")
                print(f"   Message : {data.get('message', 'N/A')}")
                return None
            
            events = data.get('economicCalendar', [])
            print(f"\n📊 RÉSULTATS :")
            print(f"   Total events août 2025 : {len(events)}")
            
            if len(events) > 0:
                # Analyser par date
                events_by_date = {}
                for event in events:
                    date = event.get('date', 'N/A')
                    if date not in events_by_date:
                        events_by_date[date] = []
                    events_by_date[date].append(event)
                
                print(f"   Dates uniques : {len(events_by_date)}")
                
                # Focus sur 1er août
                august_first_keys = [k for k in events_by_date.keys() if '08-01-2025' in k or '2025-08-01' in k]
                
                if august_first_keys:
                    print(f"\n   🎯 ÉVÉNEMENTS 1er AOÛT 2025 :")
                    for date_key in august_first_keys:
                        events_aug1 = events_by_date[date_key]
                        print(f"      Date key : {date_key}")
                        print(f"      Nombre events : {len(events_aug1)}")
                        
                        # Chercher NFP
                        nfp_events = [e for e in events_aug1 if 'nfp' in e.get('title', '').lower() or 'payroll' in e.get('title', '').lower()]
                        
                        if nfp_events:
                            print(f"      ✅ NFP trouvés : {len(nfp_events)}")
                            for nfp in nfp_events:
                                print(f"         - {nfp.get('title', 'N/A')} ({nfp.get('country', 'N/A')}) - Impact: {nfp.get('impact', 'N/A')}")
                        else:
                            print(f"      ⚠️ Aucun NFP trouvé")
                        
                        # Lister tous events HIGH
                        high_events = [e for e in events_aug1 if e.get('impact', '').lower() == 'high']
                        print(f"      Events HIGH : {len(high_events)}")
                        for he in high_events[:10]:  # Limiter affichage
                            print(f"         - {he.get('title', 'N/A')} ({he.get('country', 'N/A')})")
                else:
                    print(f"\n   ⚠️ Aucun événement trouvé pour le 1er août 2025")
                
                # Statistiques globales
                print(f"\n   📈 STATISTIQUES AOÛT 2025 :")
                
                # Par impact
                impacts = {}
                for event in events:
                    impact = event.get('impact', 'Unknown')
                    impacts[impact] = impacts.get(impact, 0) + 1
                
                for impact, count in sorted(impacts.items(), key=lambda x: x[1], reverse=True):
                    print(f"      {impact}: {count} events")
                
                # Par pays
                countries = {}
                for event in events:
                    country = event.get('country', 'Unknown')
                    countries[country] = countries.get(country, 0) + 1
                
                print(f"\n      Top 5 pays :")
                for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"         {country}: {count} events")
            
            return data
            
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
            print(f"   Réponse : {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_data_structure(data):
    """
    Test 3 : Analyser structure détaillée des données
    """
    print("\n" + "=" * 80)
    print("TEST 3 : ANALYSE STRUCTURE DONNÉES")
    print("=" * 80)
    
    if not data or 'economicCalendar' not in data:
        print("⚠️ Pas de données à analyser")
        return
    
    events = data['economicCalendar']
    
    if len(events) == 0:
        print("⚠️ Aucun événement dans les données")
        return
    
    print(f"\n📊 Analyse de {len(events)} événements...")
    
    # Convertir en DataFrame pour analyse
    df = pd.DataFrame(events)
    
    print(f"\n📋 COLONNES DISPONIBLES :")
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"   {col}: {non_null}/{len(df)} non-null")
    
    print(f"\n📝 EXEMPLE ÉVÉNEMENT COMPLET :")
    if len(events) > 0:
        example = events[0]
        for key, value in example.items():
            print(f"   {key:20s} : {value}")
    
    # Mapping vers structure DB
    print(f"\n🗺️ MAPPING VERS STRUCTURE DB events :")
    print(f"   MyFXBook             →  DB events")
    print(f"   {'─' * 50}")
    
    mappings = {
        'title': 'event_key',
        'country': 'country',
        'impact': 'importance_n (High=3, Medium=2, Low=1)',
        'date/time': 'ts_utc (conversion timezone)',
        'actual': 'actual',
        'forecast': 'estimate',
        'previous': 'previous'
    }
    
    for myfx_field, db_field in mappings.items():
        # Vérifier présence
        if myfx_field.split('/')[0] in df.columns or myfx_field in df.columns:
            status = "✅"
        else:
            status = "❌"
        print(f"   {status} {myfx_field:20s} → {db_field}")
    
    # Sauvegarder CSV pour inspection
    output_csv = OUTPUT_DIR / "august_2025_events.csv"
    df.to_csv(output_csv, index=False)
    print(f"\n💾 Export CSV : {output_csv}")
    
    return df


def compare_with_eodhd():
    """
    Test 4 : Comparer quantitativement avec EODHD
    """
    print("\n" + "=" * 80)
    print("TEST 4 : COMPARAISON AVEC EODHD")
    print("=" * 80)
    
    print("\n📊 EODHD (données actuelles DB) :")
    print("   Août 2025 : 1 événement (INCOMPLET ❌)")
    print("   Problème : NFP 1er août manquants")
    
    # Charger résultats MyFXBook
    json_file = OUTPUT_DIR / "august_2025_events.json"
    
    if not json_file.exists():
        print("⚠️ Données MyFXBook non disponibles")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    events = data.get('economicCalendar', [])
    
    print(f"\n📊 MYFXBOOK (nouvelles données) :")
    print(f"   Août 2025 : {len(events)} événements")
    
    # Compter HIGH importance
    high_events = [e for e in events if e.get('impact', '').lower() == 'high']
    print(f"   Events HIGH : {len(high_events)}")
    
    # Chercher NFP 1er août
    august_first_events = [e for e in events if '08-01-2025' in str(e.get('date', '')) or '2025-08-01' in str(e.get('date', ''))]
    nfp_events = [e for e in august_first_events if 'nfp' in e.get('title', '').lower() or 'payroll' in e.get('title', '').lower()]
    
    print(f"\n🎯 1ER AOÛT 2025 :")
    print(f"   EODHD     : 1 event total")
    print(f"   MyFXBook  : {len(august_first_events)} events")
    print(f"   NFP trouvés : {len(nfp_events)}")
    
    if nfp_events:
        print(f"\n   ✅ NFP DÉTECTÉS :")
        for nfp in nfp_events:
            print(f"      - {nfp.get('title', 'N/A')}")
            print(f"        Time: {nfp.get('time', 'N/A')}")
            print(f"        Actual: {nfp.get('actual', 'N/A')}")
            print(f"        Forecast: {nfp.get('forecast', 'N/A')}")
    
    print(f"\n📈 CONCLUSION :")
    if len(events) > 1:
        print(f"   ✅ MyFXBook est PLUS COMPLET que EODHD")
        print(f"   ✅ Facteur amélioration : {len(events)}x")
    else:
        print(f"   ⚠️ Résultats similaires ou problème")
    
    # Recommandation
    print(f"\n💡 RECOMMANDATION :")
    if len(nfp_events) > 0:
        print(f"   ✅ ADOPTER MyFXBook comme source principale")
        print(f"   ✅ Procéder au remplacement complet DB")
    else:
        print(f"   ⚠️ Investiguer davantage avant remplacement")


def main():
    """
    Orchestration des tests
    """
    print("\n" + "=" * 80)
    print("EXPLORATION API MYFXBOOK - SESSION 122")
    print("=" * 80)
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output : {OUTPUT_DIR}")
    
    # Test 1 : Structure endpoint
    print("\n🔍 Démarrage Test 1...")
    test_data = test_endpoint_structure()
    
    # Test 2 : Août 2025
    print("\n🔍 Démarrage Test 2...")
    august_data = test_august_2025_download()
    
    # Test 3 : Analyse structure
    if august_data:
        print("\n🔍 Démarrage Test 3...")
        df = analyze_data_structure(august_data)
    
    # Test 4 : Comparaison
    print("\n🔍 Démarrage Test 4...")
    compare_with_eodhd()
    
    print("\n" + "=" * 80)
    print("✅ EXPLORATION TERMINÉE")
    print("=" * 80)
    print(f"\n📂 Résultats sauvegardés : {OUTPUT_DIR}")
    print(f"   - test_simple_response.json")
    print(f"   - august_2025_events.json")
    print(f"   - august_2025_events.csv")
    
    print(f"\n👉 PROCHAINE ÉTAPE :")
    print(f"   - Analyser résultats")
    print(f"   - Décider adoption MyFXBook")
    print(f"   - Si OK → Créer script import complet")


if __name__ == "__main__":
    main()
