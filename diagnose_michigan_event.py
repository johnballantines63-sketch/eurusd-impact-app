#!/usr/bin/env python3
"""
Diagnostic événement Michigan Consumer Sentiment - 10 Oct 2025
Vérifie présence dans events et event_families
"""

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = "fx_impact_app/data/warehouse.duckdb"

def diagnose_michigan():
    """Diagnostic complet"""
    
    print("🔍 DIAGNOSTIC MICHIGAN CONSUMER SENTIMENT")
    print("=" * 70)
    
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # 1. Chercher dans events
    print("\n📊 Recherche dans table 'events' (10 oct 2025)...")
    
    query_events = """
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        estimate,
        previous
    FROM events
    WHERE DATE(ts_utc) = '2025-10-10'
      AND country = 'US'
      AND (event_key LIKE '%michigan%' OR event_key LIKE '%consumer%sentiment%')
    ORDER BY ts_utc
    """
    
    events_df = conn.execute(query_events).fetchdf()
    
    if len(events_df) > 0:
        print(f"✅ {len(events_df)} événement(s) trouvé(s):\n")
        for idx, row in events_df.iterrows():
            print(f"   ⏰ {row['ts_utc']}")
            print(f"   📌 event_key: {row['event_key']}")
            print(f"   🌍 country: {row['country']}")
            print(f"   🎯 importance_n: {row['importance_n']}")
            print(f"   📊 actual: {row['actual']}, estimate: {row['estimate']}, previous: {row['previous']}")
            print()
    else:
        print("❌ AUCUN événement Michigan trouvé pour le 10 oct 2025")
        
        # Chercher autres dates
        print("\n🔍 Recherche Michigan sur autres dates...")
        query_other = """
        SELECT 
            DATE(ts_utc) as date,
            COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND event_key LIKE '%michigan%'
        GROUP BY DATE(ts_utc)
        ORDER BY date DESC
        LIMIT 10
        """
        other_df = conn.execute(query_other).fetchdf()
        
        if len(other_df) > 0:
            print("\n📅 Michigan trouvé sur ces dates:")
            for idx, row in other_df.iterrows():
                print(f"   • {row['date']}: {row['count']} événement(s)")
        else:
            print("❌ Aucun événement Michigan dans toute la DB")
    
    # 2. Chercher dans event_families
    print("\n📋 Recherche dans table 'event_families'...")
    
    query_families = """
    SELECT 
        event_key,
        family,
        is_tradable,
        empirical_score,
        empirical_impact
    FROM event_families
    WHERE event_key LIKE '%michigan%'
    """
    
    families_df = conn.execute(query_families).fetchdf()
    
    if len(families_df) > 0:
        print(f"✅ {len(families_df)} mapping(s) trouvé(s):\n")
        for idx, row in families_df.iterrows():
            tradable = "✅ OUI" if row['is_tradable'] else "❌ NON"
            print(f"   📌 {row['event_key']}")
            print(f"      → famille: {row['family']}")
            print(f"      → tradable: {tradable}")
            print(f"      → score: {row['empirical_score']}, impact: {row['empirical_impact']}")
            print()
    else:
        print("❌ AUCUN mapping dans event_families")
        print("   → Michigan sera affiché comme 'événement sans famille'")
    
    # 3. Vérifier FAMILY_PATTERNS
    print("\n🔧 Vérification FAMILY_PATTERNS dans code...")
    
    try:
        import sys
        sys.path.insert(0, 'fx_impact_app/src')
        from event_families import FAMILY_PATTERNS
        
        michigan_patterns = [k for k, v in FAMILY_PATTERNS.items() if 'michigan' in v.lower()]
        
        if michigan_patterns:
            print(f"✅ Pattern(s) trouvé(s): {', '.join(michigan_patterns)}")
        else:
            print("❌ AUCUN pattern Michigan dans FAMILY_PATTERNS")
            print("   → Ajouter pattern pour auto-classification")
    except Exception as e:
        print(f"⚠️ Impossible de charger FAMILY_PATTERNS: {e}")
    
    # 4. Test requête du Planificateur
    print("\n🔬 Test requête Planificateur (comme dans le code)...")
    
    query_planner = """
    SELECT 
        e.ts_utc, e.event_key, e.country, e.importance_n,
        e.actual, e.forecast, e.previous,
        ef.empirical_score, ef.empirical_impact, ef.impact_level,
        ef.avg_movement_pips, ef.avg_latency_min, ef.reaction_rate
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= '2025-10-10 00:00'
      AND e.ts_utc <= '2025-10-10 23:59'
      AND e.country = 'US'
    ORDER BY e.ts_utc
    """
    
    planner_df = conn.execute(query_planner).fetchdf()
    
    print(f"\n📊 Résultat requête Planificateur: {len(planner_df)} événements US")
    
    michigan_rows = planner_df[planner_df['event_key'].str.contains('michigan', case=False, na=False)]
    
    if len(michigan_rows) > 0:
        print(f"✅ Michigan présent dans résultats: {len(michigan_rows)} ligne(s)")
        for idx, row in michigan_rows.iterrows():
            has_family = pd.notna(row['empirical_score'])
            status = "✅ Avec famille" if has_family else "⚠️ Sans famille"
            print(f"   {row['ts_utc'].strftime('%H:%M')} - {row['event_key']} [{status}]")
    else:
        print("❌ Michigan ABSENT des résultats")
        
        # Lister ce qui est trouvé
        if len(planner_df) > 0:
            print(f"\n📋 Événements US trouvés ce jour:")
            for idx, row in planner_df.iterrows():
                print(f"   • {row['ts_utc'].strftime('%H:%M')} - {row['event_key']}")
    
    # 5. Test avec identify_family
    print("\n🔍 Test fonction identify_family()...")
    
    if len(events_df) > 0:
        try:
            import sys
            import re
            sys.path.insert(0, 'fx_impact_app/src')
            from event_families import FAMILY_PATTERNS
            
            def identify_family(event_key):
                for family_name, pattern in FAMILY_PATTERNS.items():
                    clean_pattern = pattern.replace('(?i)', '')
                    if re.search(clean_pattern, event_key, re.IGNORECASE):
                        return family_name
                return None
            
            for idx, row in events_df.iterrows():
                family = identify_family(row['event_key'])
                status = "✅" if family else "❌"
                print(f"   {status} {row['event_key']} → {family if family else 'None'}")
        except Exception as e:
            print(f"   ⚠️ Erreur: {e}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ Diagnostic terminé")
    
    # === RECOMMANDATIONS ===
    print("\n💡 RECOMMANDATIONS:\n")
    
    # Cas 1: Michigan dans events mais pas dans résultats Planificateur
    if len(events_df) > 0 and len(michigan_rows) == 0:
        print("❌ PROBLÈME: Michigan dans DB mais pas dans Planificateur")
        print("   → Cause probable: Filtrage trop agressif (ligne après 397)")
        print("   → Il faut chercher le filtre dans get_future_events()")
    
    # Cas 2: Michigan pas dans events du tout
    elif len(events_df) == 0:
        print("❌ PROBLÈME: Michigan absent de la table 'events'")
        print("   → Cause: Données pas scrapées pour le 10 oct 2025")
        print("   → Solution: Vérifier scraper ou choisir autre date")
    
    # Cas 3: Michigan sans famille
    elif len(families_df) == 0:
        print("⚠️ ATTENTION: Michigan sans mapping dans 'event_families'")
        print("   → Impact: Sera affiché comme 'événement sans famille'")
        print("   → Pas de prédiction automatique possible")
        print("   → Solution optionnelle: Ajouter dans event_families.py")
    
    # Cas 4: Michigan OK
    else:
        print("✅ Michigan correctement configuré !")
        print("   → Présent dans events ✅")
        print("   → Mapping dans event_families ✅")
        print("   → Devrait être visible dans Planificateur")
    
    print("\n📄 Fichiers à vérifier:")
    print(f"   • DB: {DB_PATH}")
    print("   • Code: fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
    print("   • Patterns: fx_impact_app/src/event_families.py")

if __name__ == '__main__':
    try:
        diagnose_michigan()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
