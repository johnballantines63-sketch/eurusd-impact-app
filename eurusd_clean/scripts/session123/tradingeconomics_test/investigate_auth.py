"""
Investigation approfondie Trading Economics API - Session 123

Test de différentes méthodes d'authentification et endpoints
pour identifier le problème d'accès calendar.

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import requests
import json
from pathlib import Path


API_KEY = "8b145686977a48b:r3l0g33rz588g77"
BASE_URL = "https://api.tradingeconomics.com"


def test_auth_methods():
    """Tester différentes méthodes d'authentification"""
    
    print("=" * 70)
    print("TEST MÉTHODES AUTHENTIFICATION")
    print("=" * 70)
    
    # Endpoint test : calendar
    endpoint = "/calendar"
    
    # Méthode 1 : Query parameter 'key'
    print("\n1️⃣ MÉTHODE 1 : Query parameter 'key'")
    print("-" * 70)
    
    url = f"{BASE_URL}{endpoint}"
    params = {'key': API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   URL: {response.url}")
        print(f"   Status: {response.status_code}")
        print(f"   Response length: {len(response.text)} chars")
        print(f"   First 200 chars: {response.text[:200]}")
        
        if response.status_code == 200:
            print("   ✅ SUCCÈS")
            return True
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # Méthode 2 : Header 'Authorization: Client'
    print("\n2️⃣ MÉTHODE 2 : Header 'Authorization: Client {KEY}'")
    print("-" * 70)
    
    headers = {'Authorization': f'Client {API_KEY}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   First 200 chars: {response.text[:200]}")
        
        if response.status_code == 200:
            print("   ✅ SUCCÈS")
            return True
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # Méthode 3 : Header 'Authorization: Bearer'
    print("\n3️⃣ MÉTHODE 3 : Header 'Authorization: Bearer {KEY}'")
    print("-" * 70)
    
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   First 200 chars: {response.text[:200]}")
        
        if response.status_code == 200:
            print("   ✅ SUCCÈS")
            return True
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
    
    # Méthode 4 : Séparé client:secret
    print("\n4️⃣ MÉTHODE 4 : Query 'client' + 'secret'")
    print("-" * 70)
    
    # API Key format "client:secret" ?
    if ':' in API_KEY:
        client, secret = API_KEY.split(':', 1)
        params = {'client': client, 'secret': secret}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"   URL: {response.url}")
            print(f"   Status: {response.status_code}")
            print(f"   First 200 chars: {response.text[:200]}")
            
            if response.status_code == 200:
                print("   ✅ SUCCÈS")
                return True
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
    else:
        print("   ⏭️  SKIP - API Key ne contient pas ':'")
    
    return False


def test_alternative_endpoints():
    """Tester endpoints alternatifs calendar"""
    
    print("\n" + "=" * 70)
    print("TEST ENDPOINTS ALTERNATIFS")
    print("=" * 70)
    
    endpoints = [
        "/calendar",
        "/calendar/country/all",
        "/events",
        "/calendar/indicator/united states/non farm payrolls",
        "/historical/country/united states/indicator/non farm payrolls",
    ]
    
    for endpoint in endpoints:
        print(f"\n📍 Test: {endpoint}")
        print("-" * 70)
        
        url = f"{BASE_URL}{endpoint}"
        params = {'key': API_KEY}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Length: {len(response.text)} chars")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCÈS")
                print(f"   First 300 chars: {response.text[:300]}")
                
                # Essayer parser JSON
                try:
                    data = response.json()
                    print(f"   Type: {type(data)}")
                    if isinstance(data, list):
                        print(f"   Count: {len(data)} items")
                        if len(data) > 0:
                            print(f"   First item keys: {list(data[0].keys())}")
                except:
                    print(f"   ⚠️  Non-JSON")
            
            elif response.status_code == 401:
                print(f"   ❌ 401 Unauthorized")
            elif response.status_code == 404:
                print(f"   ⚠️  404 Not Found")
            else:
                print(f"   ⚠️  {response.status_code}")
                print(f"   Message: {response.text[:200]}")
        
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")


def check_account_info():
    """Vérifier infos compte et limites"""
    
    print("\n" + "=" * 70)
    print("VÉRIFICATION COMPTE")
    print("=" * 70)
    
    # Endpoint account info (si existe)
    endpoints_info = [
        "/account",
        "/user",
        "/subscription",
        "/info"
    ]
    
    for endpoint in endpoints_info:
        url = f"{BASE_URL}{endpoint}"
        params = {'key': API_KEY}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                print(f"\n✅ {endpoint} - SUCCÈS")
                print(f"   {response.text[:500]}")
        except:
            pass


def test_documentation_examples():
    """Tester exemples de la documentation officielle"""
    
    print("\n" + "=" * 70)
    print("TEST EXEMPLES DOCUMENTATION")
    print("=" * 70)
    print()
    print("Basé sur : https://docs.tradingeconomics.com/")
    print()
    
    # Format typique doc TE
    examples = [
        {
            'name': 'Calendar country/date',
            'url': f'{BASE_URL}/calendar/country/united states/2025-08-01/2025-08-31',
            'params': {'key': API_KEY}
        },
        {
            'name': 'Calendar indicator',
            'url': f'{BASE_URL}/calendar/indicator/non farm payrolls',
            'params': {'key': API_KEY}
        },
        {
            'name': 'Historical indicator',
            'url': f'{BASE_URL}/historical/country/united states/indicator/gdp',
            'params': {'key': API_KEY}
        }
    ]
    
    for example in examples:
        print(f"\n📚 {example['name']}")
        print("-" * 70)
        print(f"   URL: {example['url']}")
        
        try:
            response = requests.get(
                example['url'],
                params=example['params'],
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCÈS")
                try:
                    data = response.json()
                    print(f"   Type: {type(data)}")
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   Count: {len(data)}")
                        print(f"   First keys: {list(data[0].keys())}")
                except:
                    print(f"   Response: {response.text[:200]}")
            else:
                print(f"   ❌ {response.status_code}")
                print(f"   Message: {response.text[:300]}")
        
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")


def main():
    print("=" * 70)
    print("INVESTIGATION TRADING ECONOMICS API - SESSION 123")
    print("=" * 70)
    print()
    print(f"API Key: {API_KEY[:20]}...")
    print()
    
    # Test 1 : Méthodes auth
    success = test_auth_methods()
    
    if success:
        print("\n🎉 MÉTHODE AUTH TROUVÉE !")
        return
    
    # Test 2 : Endpoints alternatifs
    test_alternative_endpoints()
    
    # Test 3 : Info compte
    check_account_info()
    
    # Test 4 : Exemples doc
    test_documentation_examples()
    
    # Conclusion
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()
    print("Si tous les tests échouent avec 401 sur /calendar :")
    print()
    print("➡️  Votre plan Trading Economics ne semble PAS inclure Calendar API")
    print()
    print("Options :")
    print("  1. Contacter support TE pour upgrade plan")
    print("  2. Vérifier dashboard TE pour voir APIs disponibles")
    print("  3. OU continuer avec JBlanked (déjà validé)")
    print()


if __name__ == '__main__':
    main()
