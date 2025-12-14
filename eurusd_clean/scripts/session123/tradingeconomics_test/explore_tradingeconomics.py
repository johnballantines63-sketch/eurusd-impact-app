"""
Exploration Trading Economics API - Session 123

Test de l'API Trading Economics pour vérifier si elle peut remplacer JBlanked
comme source de données pour le calendrier économique.

Objectifs :
1. Tester connexion API avec developer key
2. Vérifier structure données (Actual/Forecast/Previous)
3. Tester cas août 2025 (27 événements attendus)
4. Comparer avec JBlanked
5. Identifier timezone

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import requests
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class TradingEconomicsExplorer:
    """Explorateur API Trading Economics"""
    
    def __init__(self, api_key: str):
        """
        Initialiser explorateur
        
        Args:
            api_key: Clé API Trading Economics
        """
        self.api_key = api_key
        self.base_url = "https://api.tradingeconomics.com"
        self.headers = {
            'Accept': 'application/json'
        }
        
        # Créer dossier output
        self.output_dir = Path(__file__).parent
        self.output_dir.mkdir(exist_ok=True)
    
    def test_connection(self) -> bool:
        """
        Tester connexion API
        
        Returns:
            bool: True si connexion réussie
        """
        print("🔌 TEST CONNEXION TRADING ECONOMICS API")
        print("=" * 70)
        
        # Endpoint test (souvent /markets ou /calendar)
        test_endpoints = [
            "/calendar",
            "/indicators",
            "/markets"
        ]
        
        for endpoint in test_endpoints:
            url = f"{self.base_url}{endpoint}"
            
            print(f"\nTest endpoint: {endpoint}")
            
            try:
                # Essayer avec API key en paramètre
                response = requests.get(
                    url,
                    params={'key': self.api_key, 'format': 'json'},
                    headers=self.headers,
                    timeout=10
                )
                
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  ✅ SUCCÈS - Endpoint fonctionnel")
                    
                    # Afficher structure
                    try:
                        data = response.json()
                        print(f"  Type réponse: {type(data)}")
                        
                        if isinstance(data, list) and len(data) > 0:
                            print(f"  Nombre éléments: {len(data)}")
                            print(f"  Premier élément keys: {list(data[0].keys())}")
                        elif isinstance(data, dict):
                            print(f"  Keys: {list(data.keys())}")
                        
                        return True
                    except:
                        print(f"  Réponse non-JSON")
                
                elif response.status_code == 401:
                    print(f"  ❌ ERREUR 401 - API Key invalide ou endpoint nécessite auth différente")
                elif response.status_code == 404:
                    print(f"  ⚠️  404 - Endpoint n'existe pas")
                else:
                    print(f"  ⚠️  Erreur {response.status_code}")
                    print(f"  Message: {response.text[:200]}")
                
            except requests.exceptions.RequestException as e:
                print(f"  ❌ ERREUR connexion: {e}")
        
        print("\n" + "=" * 70)
        return False
    
    def get_calendar_events(
        self,
        start_date: str,
        end_date: str,
        country: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Récupérer événements calendrier économique
        
        Args:
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            country: Code pays optionnel (US, EU, GB, etc.)
        
        Returns:
            Liste événements ou None si erreur
        """
        print(f"\n📅 RÉCUPÉRATION ÉVÉNEMENTS CALENDRIER")
        print(f"   Période: {start_date} → {end_date}")
        if country:
            print(f"   Pays: {country}")
        print("-" * 70)
        
        # Construire URL
        # Format typique Trading Economics : /calendar/country/{country}/{start_date}/{end_date}
        # Ou : /calendar?c={country}&d1={start_date}&d2={end_date}
        
        # Essayer format 1
        if country:
            url = f"{self.base_url}/calendar/country/{country}/{start_date}/{end_date}"
        else:
            url = f"{self.base_url}/calendar"
        
        params = {
            'key': self.api_key,
            'format': 'json'
        }
        
        if not country:
            params['d1'] = start_date
            params['d2'] = end_date
        
        print(f"   URL: {url}")
        print(f"   Params: {params}")
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    print(f"   ✅ SUCCÈS - {len(data)} événements récupérés")
                    return data
                else:
                    print(f"   ⚠️  Réponse non-liste: {type(data)}")
                    return None
            
            elif response.status_code == 401:
                print(f"   ❌ ERREUR 401 - Vérifier API Key")
                print(f"   Message: {response.text[:500]}")
                return None
            
            else:
                print(f"   ❌ ERREUR {response.status_code}")
                print(f"   Message: {response.text[:500]}")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"   ❌ ERREUR requête: {e}")
            return None
    
    def analyze_event_structure(self, events: List[Dict]) -> None:
        """
        Analyser structure événements
        
        Args:
            events: Liste événements
        """
        if not events:
            print("⚠️  Aucun événement à analyser")
            return
        
        print(f"\n🔍 ANALYSE STRUCTURE ÉVÉNEMENTS")
        print("=" * 70)
        
        # Premier événement
        first_event = events[0]
        
        print(f"\n📋 Premier événement (exemple):")
        print(json.dumps(first_event, indent=2))
        
        # Colonnes disponibles
        print(f"\n📊 Colonnes disponibles ({len(first_event)} colonnes):")
        for key in sorted(first_event.keys()):
            value = first_event[key]
            value_str = str(value)[:50]
            print(f"   - {key:<20} : {type(value).__name__:<10} = {value_str}")
        
        # Vérifier colonnes critiques
        print(f"\n✅ VÉRIFICATION COLONNES CRITIQUES:")
        
        critical_columns = {
            'Actual': ['Actual', 'actual', 'ActualValue', 'Value'],
            'Forecast': ['Forecast', 'forecast', 'ForecastValue', 'Consensus'],
            'Previous': ['Previous', 'previous', 'PreviousValue', 'Prior'],
            'Date': ['Date', 'date', 'DateTime', 'Timestamp'],
            'Country': ['Country', 'country', 'CountryCode'],
            'Event': ['Event', 'event', 'EventName', 'Name', 'Indicator']
        }
        
        found_columns = {}
        
        for critical, alternatives in critical_columns.items():
            found = None
            for alt in alternatives:
                if alt in first_event:
                    found = alt
                    break
            
            if found:
                print(f"   ✅ {critical:<15} → '{found}'")
                found_columns[critical] = found
            else:
                print(f"   ❌ {critical:<15} → NON TROUVÉ")
                found_columns[critical] = None
        
        # Statistiques
        print(f"\n📈 STATISTIQUES:")
        print(f"   Total événements: {len(events)}")
        
        # Compter événements avec Actual
        if found_columns['Actual']:
            actual_col = found_columns['Actual']
            events_with_actual = sum(1 for e in events if e.get(actual_col) not in [None, '', 'N/A'])
            print(f"   Avec Actual: {events_with_actual} ({events_with_actual/len(events)*100:.1f}%)")
        
        # Compter par pays
        if found_columns['Country']:
            country_col = found_columns['Country']
            df = pd.DataFrame(events)
            country_counts = df[country_col].value_counts()
            print(f"\n   Répartition par pays (top 5):")
            for country, count in country_counts.head(5).items():
                print(f"      {country}: {count}")
        
        print("=" * 70)
        
        return found_columns
    
    def test_august_2025(self) -> bool:
        """
        Tester cas août 2025 (cas problématique EODHD)
        
        Returns:
            bool: True si test réussi
        """
        print(f"\n🧪 TEST CAS AOÛT 2025")
        print("=" * 70)
        print("Cas problématique : EODHD n'avait que 1 événement")
        print("Attendu : 27+ événements (NFP, CPI, ISM, etc.)")
        print()
        
        # Récupérer août 2025
        events = self.get_calendar_events('2025-08-01', '2025-08-31')
        
        if not events:
            print("❌ ÉCHEC - Aucun événement récupéré")
            return False
        
        # Sauvegarder
        output_file = self.output_dir / 'tradingeconomics_august_2025.json'
        with open(output_file, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"\n💾 Données sauvegardées: {output_file}")
        
        # Analyser structure
        found_columns = self.analyze_event_structure(events)
        
        # Chercher NFP spécifiquement
        print(f"\n🔍 RECHERCHE NFP (Non-Farm Employment) 1er août:")
        
        if found_columns and found_columns['Event']:
            event_col = found_columns['Event']
            date_col = found_columns['Date']
            
            nfp_events = [
                e for e in events
                if 'nonfarm' in str(e.get(event_col, '')).lower() or
                   'non-farm' in str(e.get(event_col, '')).lower() or
                   'employment change' in str(e.get(event_col, '')).lower()
            ]
            
            if nfp_events:
                print(f"   ✅ {len(nfp_events)} événement(s) NFP trouvé(s)")
                for nfp in nfp_events[:3]:
                    print(f"\n   Événement:")
                    print(f"      Name: {nfp.get(event_col)}")
                    print(f"      Date: {nfp.get(date_col)}")
                    if found_columns['Actual']:
                        print(f"      Actual: {nfp.get(found_columns['Actual'])}")
                    if found_columns['Forecast']:
                        print(f"      Forecast: {nfp.get(found_columns['Forecast'])}")
            else:
                print(f"   ⚠️  Aucun NFP trouvé")
        
        # Résultat
        print(f"\n📊 RÉSULTAT TEST:")
        print(f"   Événements récupérés: {len(events)}")
        print(f"   Attendu minimum: 20")
        
        if len(events) >= 20:
            print(f"   ✅ TEST RÉUSSI - {len(events)} >= 20")
            return True
        else:
            print(f"   ⚠️  TEST PARTIEL - Moins de 20 événements")
            return False


def main():
    """Fonction principale"""
    
    print("=" * 70)
    print("EXPLORATION TRADING ECONOMICS API - SESSION 123")
    print("=" * 70)
    print()
    
    # Demander API Key
    print("📌 Entrez votre API Key Trading Economics:")
    print("   (ou éditez le script avec votre clé)")
    print()
    
    # OPTION 1 : Éditer ici directement
    api_key = ""  # ← METTRE VOTRE CLÉ ICI
    
    # OPTION 2 : Ou demander interactivement
    if not api_key:
        api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ ERREUR : API Key requise")
        return
    
    # Créer explorateur
    explorer = TradingEconomicsExplorer(api_key)
    
    # Test 1 : Connexion
    print("\n" + "="*70)
    print("TEST 1 : CONNEXION API")
    print("="*70)
    
    if not explorer.test_connection():
        print("\n❌ IMPOSSIBLE DE SE CONNECTER À L'API")
        print("\nVérifiez:")
        print("  - API Key correcte")
        print("  - Accès actif (pas expiré)")
        print("  - Documentation API Trading Economics")
        return
    
    # Test 2 : Cas août 2025
    print("\n" + "="*70)
    print("TEST 2 : CAS AOÛT 2025")
    print("="*70)
    
    success = explorer.test_august_2025()
    
    # Conclusion
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    
    if success:
        print("✅ Trading Economics semble être une bonne alternative à JBlanked")
        print()
        print("Prochaines étapes:")
        print("  1. Vérifier timezone (comme Étape 1 pour JBlanked)")
        print("  2. Tester historique 2015-2025")
        print("  3. Comparer coût vs JBlanked")
        print("  4. Décider quelle source utiliser")
    else:
        print("⚠️  Problèmes détectés - Investigation nécessaire")
        print()
        print("Actions:")
        print("  1. Vérifier documentation API")
        print("  2. Contacter support Trading Economics")
        print("  3. Ou continuer avec JBlanked")
    
    print()


if __name__ == '__main__':
    main()
