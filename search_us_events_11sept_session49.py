"""
Script Session 49 : Chercher événements US du 11 septembre 2025

Objectif : Trouver CPI, Jobless Claims, etc. pour les tests
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import duckdb

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path


def search_us_events_sept11():
    """Cherche les événements US majeurs du 11 septembre"""
    
    conn = duckdb.connect(get_db_path(), read_only=True)
    
    print("=" * 80)
    print("🔍 RECHERCHE ÉVÉNEMENTS US - 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    # Chercher tous les événements US du 11 septembre (toute la journée)
    query = """
    SELECT 
        ts_utc,
        country,
        event_title,
        event_key,
        importance_n,
        actual,
        previous,
        estimate,
        forecast,
        unit
    FROM events
    WHERE strftime(ts_utc, '%Y-%m-%d') = '2025-09-11'
      AND country IN ('US', 'USA', 'United States')
    ORDER BY ts_utc
    """
    
    result = conn.execute(query).fetchall()
    
    if not result:
        print("\n❌ AUCUN ÉVÉNEMENT US TROUVÉ LE 11/09/2025")
        
        # Essayer de chercher autour de cette date
        print("\n🔍 Recherche élargie (10-12 septembre)...")
        
        extended_query = """
        SELECT 
            ts_utc,
            country,
            event_title,
            event_key,
            importance_n
        FROM events
        WHERE strftime(ts_utc, '%Y-%m-%d') BETWEEN '2025-09-10' AND '2025-09-12'
          AND country IN ('US', 'USA', 'United States')
          AND importance_n >= 2
        ORDER BY ts_utc
        """
        
        extended_result = conn.execute(extended_query).fetchall()
        
        if extended_result:
            print(f"\n✅ {len(extended_result)} événements US trouvés (10-12 sept):")
            for row in extended_result:
                print(f"  • {row[0]} - {row[2]} ({row[3]})")
        else:
            print("❌ Aucun événement US trouvé dans cette période")
        
        conn.close()
        return
    
    print(f"\n✅ {len(result)} événement(s) US trouvé(s)\n")
    
    # Chercher spécifiquement CPI et Jobless Claims
    cpi_found = False
    jobless_found = False
    
    for i, row in enumerate(result, 1):
        ts_utc, country, event_title, event_key, importance, actual, previous, estimate, forecast, unit = row
        
        print(f"Événement #{i}")
        print(f"  Timestamp      : {ts_utc}")
        print(f"  Event Title    : {event_title}")
        print(f"  Event Key      : {event_key}")
        print(f"  Country        : {country}")
        print(f"  Importance     : {importance}")
        print(f"  Actual         : {actual}")
        print(f"  Previous       : {previous}")
        print(f"  Estimate       : {estimate}")
        print(f"  Forecast       : {forecast}")
        print(f"  Unit           : {unit}")
        
        # Vérifier mapping vers family
        family_query = f"""
        SELECT family, empirical_score, mfe_p80, latency_median, ttr_median
        FROM event_families
        WHERE event_key = '{event_key}' AND country = '{country}'
        """
        
        try:
            family_result = conn.execute(family_query).fetchone()
            if family_result:
                family, score, mfe, latency, ttr = family_result
                print(f"  Family         : {family} ⭐")
                print(f"  Empirical Score: {score}")
                print(f"  MFE P80        : {mfe}")
                print(f"  Latency Median : {latency}")
                print(f"  TTR Median     : {ttr}")
                
                # Marquer si c'est un événement attendu
                if 'cpi' in event_key.lower() or 'consumer price' in str(event_title).lower():
                    print("  🎯 CPI DÉTECTÉ !")
                    cpi_found = True
                
                if 'jobless' in event_key.lower() or 'claims' in event_key.lower():
                    print("  🎯 JOBLESS CLAIMS DÉTECTÉ !")
                    jobless_found = True
            else:
                print("  ⚠️  Pas de mapping family trouvé")
        except Exception as e:
            print(f"  ⚠️  Erreur recherche family : {e}")
        
        print()
    
    # Résumé
    print("=" * 80)
    print("📋 ÉVÉNEMENTS ATTENDUS POUR TEST")
    print("=" * 80)
    
    if cpi_found:
        print("✅ CPI trouvé")
    else:
        print("❌ CPI manquant")
    
    if jobless_found:
        print("✅ Jobless Claims trouvé")
    else:
        print("❌ Jobless Claims manquant")
    
    print("\n❓ Current Account (DE) - À chercher séparément (pays = DE)")
    
    # Chercher Current Account DE
    print("\n" + "=" * 80)
    print("🔍 RECHERCHE CURRENT ACCOUNT (DE)")
    print("=" * 80)
    
    de_query = """
    SELECT 
        ts_utc,
        country,
        event_title,
        event_key,
        actual,
        previous,
        forecast
    FROM events
    WHERE strftime(ts_utc, '%Y-%m-%d') = '2025-09-11'
      AND country IN ('DE', 'Germany', 'GER')
      AND (event_key LIKE '%current%' OR event_key LIKE '%account%')
    ORDER BY ts_utc
    """
    
    de_result = conn.execute(de_query).fetchall()
    
    if de_result:
        print(f"\n✅ {len(de_result)} événement(s) Current Account (DE) trouvé(s)")
        for row in de_result:
            print(f"  • {row[0]} - {row[2]} ({row[3]})")
            print(f"    Actual: {row[4]}, Previous: {row[5]}, Forecast: {row[6]}")
    else:
        print("❌ Aucun Current Account (DE) trouvé")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("💡 CONCLUSION")
    print("=" * 80)
    
    if not result or (not cpi_found and not jobless_found):
        print("""
⚠️  LES ÉVÉNEMENTS DU 11 SEPTEMBRE NE SONT PAS (ENCORE) DANS LA DB

DEUX OPTIONS :

OPTION A : Utiliser une autre date de test
  → Chercher une date avec CPI + NFP dans la DB
  → Valider les formules sur des données existantes
  
OPTION B : Insérer les événements du 11 septembre
  → Créer script d'insertion avec forecast/actual
  → Enrichir la DB pour tests futurs

OPTION C : Tester avec données hard-codées (comme actuellement)
  → Garder test_validation_11sept.py tel quel
  → Mais reconnaître que c'est pour validation méthodologique uniquement
        """)
    else:
        print("""
✅ ÉVÉNEMENTS TROUVÉS !

PROCHAINES ÉTAPES :
1. Vérifier que forecast/actual/surprise sont présents
2. Modifier test_validation_11sept.py pour lire depuis DB
3. Lancer test de validation
4. Analyser métriques MAE/RMSE
        """)


if __name__ == "__main__":
    search_us_events_sept11()
