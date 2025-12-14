#!/usr/bin/env python3
"""
RECALCUL event_impacts_v2 avec forecast corrigé
Session 27 - Utilisation des vraies surprises
"""

import duckdb
import pandas as pd
from datetime import datetime

def main():
    print("=" * 80)
    print("🔄 RECALCUL event_impacts_v2 AVEC FORECAST CORRIGÉ")
    print("=" * 80)
    
    con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
    
    # Backup de l'ancienne version
    print("\n📦 Backup event_impacts_v2 ancienne version...")
    try:
        con.execute("DROP TABLE IF EXISTS event_impacts_v2_OLD")
        con.execute("CREATE TABLE event_impacts_v2_OLD AS SELECT * FROM event_impacts_v2")
        print("  ✅ Backup créé : event_impacts_v2_OLD")
    except Exception as e:
        print(f"  ⚠️  Pas de table existante : {e}")
    
    # Supprimer ancienne version
    print("\n🗑️  Suppression ancienne event_impacts_v2...")
    con.execute("DROP TABLE IF EXISTS event_impacts_v2")
    
    # Créer nouvelle version avec forecast corrigé
    print("\n📊 Calcul des impacts avec forecast corrigé...")
    
    # ✅ CORRECTION: Retirer ef.importance qui n'existe pas
    create_query = """
    CREATE TABLE event_impacts_v2 AS
    SELECT 
        e.ts_utc,
        e.event_key,
        e.event_title,
        e.country,
        e.actual,
        e.forecast,
        e.previous,
        CASE 
            WHEN e.forecast IS NOT NULL AND e.forecast != 0 
            THEN ABS((e.actual - e.forecast) / e.forecast) * 100
            ELSE NULL
        END as surprise_pct,
        e.importance_n as importance,
        NULL::DOUBLE as phase1_pips,
        NULL::INTEGER as ttr_minutes,
        NULL::VARCHAR as direction,
        NULL::DOUBLE as start_price,
        NULL::DOUBLE as ttr_price,
        'forecast_corrected_session27' as source,
        CURRENT_TIMESTAMP as created_at
    FROM events e
    WHERE e.actual IS NOT NULL
    AND e.forecast IS NOT NULL
    AND e.forecast != 0
    AND ABS((e.actual - e.forecast) / e.forecast) * 100 > 30
    """
    
    con.execute(create_query)
    
    # Statistiques
    stats = con.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(surprise_pct) as avg_surprise,
            MIN(surprise_pct) as min_surprise,
            MAX(surprise_pct) as max_surprise
        FROM event_impacts_v2
    """).fetchone()
    
    print(f"\n  ✅ event_impacts_v2 recréée")
    print(f"     Total événements: {stats[0]:,}")
    print(f"     Surprise moyenne: {stats[1]:.1f}%")
    print(f"     Surprise min: {stats[2]:.1f}%")
    print(f"     Surprise max: {stats[3]:.1f}%")
    
    # Vérifier 11 septembre
    print("\n\n📊 VÉRIFICATION: 11 septembre 2025")
    print("-" * 80)
    
    sept11 = con.execute("""
        SELECT 
            event_key,
            country,
            surprise_pct,
            actual,
            forecast
        FROM event_impacts_v2
        WHERE DATE(ts_utc) = '2025-09-11'
        AND EXTRACT(HOUR FROM ts_utc) BETWEEN 12 AND 15
        ORDER BY surprise_pct DESC
    """).df()
    
    print(f"\n  ✅ {len(sept11)} événements trouvés le 11 septembre")
    
    if len(sept11) > 0:
        print("\n  Top événements:")
        for _, row in sept11.head(10).iterrows():
            print(f"    {row['event_key']:40s} ({row['country']}) : {row['surprise_pct']:.1f}% (A:{row['actual']:.2f} F:{row['forecast']:.2f})")
    else:
        print("\n  ⚠️  Aucun événement > 30% surprise le 11 septembre")
        print("      Vérifions tous les événements US ce jour-là:")
        
        all_sept11 = con.execute("""
            SELECT 
                e.event_key,
                e.country,
                e.actual,
                e.forecast,
                CASE 
                    WHEN e.forecast IS NOT NULL AND e.forecast != 0 
                    THEN ABS((e.actual - e.forecast) / e.forecast) * 100
                    ELSE NULL
                END as surprise_pct
            FROM events e
            WHERE DATE(e.ts_utc) = '2025-09-11'
            AND e.country = 'US'
            AND e.actual IS NOT NULL
            AND e.forecast IS NOT NULL
            ORDER BY surprise_pct DESC NULLS LAST
            LIMIT 10
        """).df()
        
        print("\n  Top 10 surprises US le 11 septembre:")
        for _, row in all_sept11.iterrows():
            surprise = f"{row['surprise_pct']:.1f}%" if pd.notna(row['surprise_pct']) else 'NULL'
            print(f"    {row['event_key']:40s} : {surprise} (A:{row['actual']:.2f} F:{row['forecast']:.2f})")
    
    # Comparer avec ancienne version
    print("\n\n📊 COMPARAISON ANCIENNE vs NOUVELLE")
    print("-" * 80)
    
    try:
        comparison = con.execute("""
            SELECT 
                'Ancienne (v2_OLD)' as version,
                COUNT(*) as total
            FROM event_impacts_v2_OLD
            UNION ALL
            SELECT 
                'Nouvelle (v2)' as version,
                COUNT(*) as total
            FROM event_impacts_v2
        """).df()
        
        print("\n", comparison.to_string(index=False))
        
        if len(comparison) == 2:
            old_count = comparison.iloc[0]['total']
            new_count = comparison.iloc[1]['total']
            diff = new_count - old_count
            pct_change = (diff / old_count * 100) if old_count > 0 else 0
            
            print(f"\n  Différence: {diff:+,} événements ({pct_change:+.1f}%)")
    except:
        print("\n  ⚠️  Pas de comparaison possible (pas d'ancienne version)")
    
    con.close()
    
    print("\n" + "=" * 80)
    print("✅ RECALCUL TERMINÉ")
    print("=" * 80)
    print("\n📋 NOTES:")
    print("   - Phase 1, TTR, direction seront calculés plus tard")
    print("   - Cette table contient les événements surprise > 30% basés sur FORECAST corrigé")
    print("\n📋 PROCHAINE ÉTAPE:")
    print("   Calculer Phase 1 depuis prices_1m pour ces événements")

if __name__ == "__main__":
    main()
