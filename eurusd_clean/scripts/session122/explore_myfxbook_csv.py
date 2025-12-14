#!/usr/bin/env python3
"""
EXPLORATION CALENDRIER MYFXBOOK CSV - Session 122
===================================================

Objectif : Tester endpoint CSV calendrier économique MyFXBook

Découverte : L'API MyFXBook n'a PAS d'endpoint JSON pour calendrier
Solution  : Utiliser calendar_statement.csv directement (pas d'auth requise)

URL Format:
https://www.myfxbook.com/calendar_statement.csv?
  filter=0-1-2-3_USD-EUR-GBP-JPY-etc
  &start=YYYY-MM-DD HH:MM:SS
  &end=YYYY-MM-DD HH:MM:SS
  &calPeriod=10
  &tabType=0

Date : 08 novembre 2025
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from io import StringIO

# Configuration
BASE_URL = "https://www.myfxbook.com/calendar_statement.csv"
OUTPUT_DIR = Path(__file__).parent / "myfxbook_exploration"
OUTPUT_DIR.mkdir(exist_ok=True)


def test_august_2025_csv():
    """
    Test : Télécharger août 2025 en CSV (cas problématique EODHD)
    """
    print("=" * 80)
    print("TEST CALENDRIER MYFXBOOK CSV - AOÛT 2025")
    print("=" * 80)
    
    # Paramètres août 2025
    params = {
        'start': '2025-08-01 00:00:00',
        'end': '2025-08-31 23:59:59',
        'filter': '0-1-2-3_USD-EUR-GBP-JPY-CHF-CAD-AUD-NZD',  # Impact 0-3 (Low-High), principales devises
        'calPeriod': '10',  # Période affichage
        'tabType': '0'      # Type onglet
    }
    
    print(f"\n📅 Période : {params['start']} → {params['end']}")
    print(f"🎯 Objectif : Vérifier présence NFP 1er août 2025")
    print(f"📡 URL : {BASE_URL}")
    print(f"📋 Paramètres : {params}")
    
    print(f"\n⏳ Téléchargement...")
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        
        print(f"✅ Status code : {response.status_code}")
        print(f"📏 Response size : {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Sauvegarder réponse brute
            output_file = OUTPUT_DIR / "august_2025_calendar.csv"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            print(f"💾 CSV sauvegardé : {output_file}")
            
            # Parser CSV
            print(f"\n📊 ANALYSE CSV...")
            
            # Lire CSV
            csv_content = response.content.decode('utf-8')
            
            # Afficher premières lignes pour inspection
            print(f"\n📝 PREMIÈRES LIGNES CSV :")
            print("─" * 80)
            lines = csv_content.split('\n')[:10]
            for i, line in enumerate(lines, 1):
                print(f"{i:2d}. {line}")
            print("─" * 80)
            
            # Parser avec pandas
            try:
                df = pd.read_csv(StringIO(csv_content))
                
                print(f"\n✅ CSV parsé avec succès")
                print(f"   Total lignes : {len(df)}")
                print(f"   Colonnes : {list(df.columns)}")
                
                # Afficher structure
                print(f"\n📋 STRUCTURE DONNÉES :")
                print(df.info())
                
                # Afficher premiers événements
                print(f"\n📅 PREMIERS ÉVÉNEMENTS :")
                print(df.head(10).to_string())
                
                # Chercher NFP 1er août
                print(f"\n🎯 RECHERCHE NFP 1ER AOÛT 2025 :")
                
                # Si colonne date existe
                if 'Date' in df.columns or 'date' in df.columns:
                    date_col = 'Date' if 'Date' in df.columns else 'date'
                    august_first = df[df[date_col].str.contains('2025-08-01', na=False) | 
                                     df[date_col].str.contains('08-01-2025', na=False) |
                                     df[date_col].str.contains('01.08.2025', na=False)]
                    
                    print(f"   Événements 1er août : {len(august_first)}")
                    
                    if len(august_first) > 0:
                        print(f"\n   📋 DÉTAILS :")
                        print(august_first.to_string())
                        
                        # Chercher NFP/Payrolls
                        title_col = [col for col in df.columns if 'title' in col.lower() or 'event' in col.lower()]
                        if title_col:
                            title_col = title_col[0]
                            nfp_events = august_first[
                                august_first[title_col].str.contains('NFP|Payroll|payroll', case=False, na=False)
                            ]
                            
                            if len(nfp_events) > 0:
                                print(f"\n   ✅ NFP TROUVÉS : {len(nfp_events)}")
                                print(nfp_events.to_string())
                            else:
                                print(f"\n   ⚠️ Aucun NFP trouvé dans événements 1er août")
                    else:
                        print(f"   ⚠️ Aucun événement 1er août trouvé")
                
                # Statistiques globales
                print(f"\n📈 STATISTIQUES AOÛT 2025 :")
                
                # Par impact si colonne existe
                impact_col = [col for col in df.columns if 'impact' in col.lower()]
                if impact_col:
                    impact_col = impact_col[0]
                    print(f"\n   Par impact :")
                    print(df[impact_col].value_counts().to_string())
                
                # Par pays si colonne existe
                country_col = [col for col in df.columns if 'country' in col.lower() or 'currency' in col.lower()]
                if country_col:
                    country_col = country_col[0]
                    print(f"\n   Top 5 pays/devises :")
                    print(df[country_col].value_counts().head(5).to_string())
                
                # Sauvegarder DataFrame
                output_excel = OUTPUT_DIR / "august_2025_calendar.xlsx"
                df.to_excel(output_excel, index=False)
                print(f"\n💾 Export Excel : {output_excel}")
                
                return df
                
            except Exception as e:
                print(f"\n⚠️ Erreur parsing CSV : {e}")
                print(f"   Contenu brut sauvegardé dans {output_file}")
                return None
        
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
            print(f"   Réponse : {response.text[:1000]}")
            return None
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return None


def test_single_day_nfp():
    """
    Test ciblé : 1er août 2025 uniquement (journée NFP)
    """
    print("\n" + "=" * 80)
    print("TEST CIBLÉ - 1ER AOÛT 2025 (NFP)")
    print("=" * 80)
    
    params = {
        'start': '2025-08-01 00:00:00',
        'end': '2025-08-01 23:59:59',
        'filter': '3_USD',  # HIGH impact seulement, USD uniquement
        'calPeriod': '10',
        'tabType': '0'
    }
    
    print(f"\n🎯 Test ultra-ciblé : 1er août, HIGH impact USD seulement")
    print(f"📡 Paramètres : {params}")
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            csv_content = response.content.decode('utf-8')
            
            print(f"\n✅ Réponse reçue ({len(response.content)} bytes)")
            print(f"\n📝 CONTENU COMPLET :")
            print("─" * 80)
            print(csv_content)
            print("─" * 80)
            
            # Sauvegarder
            output_file = OUTPUT_DIR / "august_01_2025_high_usd.csv"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            print(f"\n💾 Sauvegardé : {output_file}")
            
            # Parser si possible
            try:
                df = pd.read_csv(StringIO(csv_content))
                print(f"\n📊 Événements détectés : {len(df)}")
                if len(df) > 0:
                    print(df.to_string())
                return df
            except:
                print(f"⚠️ Parsing impossible, voir fichier brut")
                return None
        else:
            print(f"❌ Erreur : {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return None


def compare_with_eodhd(df):
    """
    Comparaison avec EODHD
    """
    if df is None or len(df) == 0:
        print("\n⚠️ Pas de données MyFXBook à comparer")
        return
    
    print("\n" + "=" * 80)
    print("COMPARAISON EODHD vs MYFXBOOK")
    print("=" * 80)
    
    print(f"\n📊 EODHD (données actuelles DB) :")
    print(f"   Août 2025 : 1 événement SEULEMENT (INCOMPLET ❌)")
    
    print(f"\n📊 MYFXBOOK (nouvelles données) :")
    print(f"   Août 2025 : {len(df)} événements")
    
    # Événements HIGH
    impact_col = [col for col in df.columns if 'impact' in col.lower()]
    if impact_col:
        high_events = df[df[impact_col[0]].str.contains('High|high|3', na=False)]
        print(f"   Events HIGH : {len(high_events)}")
    
    print(f"\n📈 CONCLUSION :")
    if len(df) > 1:
        ratio = len(df)
        print(f"   ✅ MyFXBook est {ratio}x PLUS COMPLET que EODHD")
        print(f"   ✅ RECOMMANDATION : Adopter MyFXBook comme source principale")
    else:
        print(f"   ⚠️ Résultats similaires, investigation nécessaire")


def main():
    """
    Orchestration des tests
    """
    print("\n" + "=" * 80)
    print("EXPLORATION CALENDRIER MYFXBOOK CSV - SESSION 122")
    print("=" * 80)
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output : {OUTPUT_DIR}")
    
    # Test 1 : Août 2025 complet
    print("\n🔍 Test 1 : Août 2025 complet...")
    df_august = test_august_2025_csv()
    
    # Test 2 : 1er août ciblé
    print("\n🔍 Test 2 : 1er août ciblé (HIGH USD)...")
    df_nfp = test_single_day_nfp()
    
    # Comparaison
    if df_august is not None:
        compare_with_eodhd(df_august)
    
    print("\n" + "=" * 80)
    print("✅ EXPLORATION TERMINÉE")
    print("=" * 80)
    print(f"\n📂 Résultats : {OUTPUT_DIR}")
    print(f"   - august_2025_calendar.csv")
    print(f"   - august_2025_calendar.xlsx")
    print(f"   - august_01_2025_high_usd.csv")
    
    print(f"\n👉 PROCHAINE ÉTAPE :")
    print(f"   - Analyser résultats CSV")
    print(f"   - Valider structure mapping DB")
    print(f"   - Créer script import complet si OK")


if __name__ == "__main__":
    main()
