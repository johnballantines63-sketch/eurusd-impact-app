#!/usr/bin/env python3
"""
Diagnostic événements 11 septembre 2025
========================================

Objectif :
- Répondre aux questions : Combien d'événements totaux à 14:30 ?
- Pourquoi seulement 4 event_key ?
- Y a-t-il d'autres composantes CPI manquantes ?

Contexte :
- Test cluster_impact_calculator prédit 15.8 pips au lieu de 37.4 pips
- Seulement 4 event_key extraits au lieu de ~14 attendus
- Besoin de comprendre structure réelle de la DB
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

def main():
    """Diagnostic complet des événements du 11 septembre 2025."""
    
    # Chemins
    base_path = Path(__file__).parent.parent.parent
    db_path = base_path / "app" / "data" / "warehouse.duckdb"
    
    print("=" * 80)
    print("DIAGNOSTIC ÉVÉNEMENTS 11 SEPTEMBRE 2025 - 14:30 BERN")
    print("=" * 80)
    print(f"\nDatabase: {db_path}")
    
    if not db_path.exists():
        print(f"❌ ERREUR: Database introuvable à {db_path}")
        return
    
    # Connexion DB
    con = duckdb.connect(str(db_path), read_only=True)
    
    try:
        # =====================================================================
        # 1. TOUS LES ÉVÉNEMENTS 14:30 (SANS AUCUN FILTRE)
        # =====================================================================
        print("\n" + "=" * 80)
        print("1. TOUS LES ÉVÉNEMENTS À 14:30 (SANS FILTRE)")
        print("=" * 80)
        
        query_all = """
        SELECT 
            e.event_key,
            e.event_title,
            e.actual,
            e.estimate,
            e.previous,
            e.importance_n,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef ON e.event_key = ef.event_key
        WHERE e.ts_utc = '2025-09-11 14:30:00+02:00'
        ORDER BY ef.empirical_score DESC NULLS LAST
        """
        
        df_all = con.execute(query_all).df()
        
        print(f"\n📊 Total événements trouvés : {len(df_all)}")
        
        if len(df_all) == 0:
            print("❌ AUCUN événement trouvé à cette date/heure !")
            print("\nVérification des timestamps disponibles dans la DB...")
            
            query_ts = """
            SELECT DISTINCT ts_utc, COUNT(*) as num_events
            FROM events
            WHERE DATE(ts_utc) = '2025-09-11'
            GROUP BY ts_utc
            ORDER BY ts_utc
            """
            df_ts = con.execute(query_ts).df()
            print("\nTimestamps disponibles le 11 sept 2025 :")
            print(df_ts.to_string())
            
            con.close()
            return
        
        # Afficher tous les événements
        print("\n" + "-" * 80)
        print("LISTE COMPLÈTE DES ÉVÉNEMENTS")
        print("-" * 80)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        print(df_all.to_string(index=False))
        
        # =====================================================================
        # 2. ÉVÉNEMENTS AVEC ESTIMATE (SURPRENABLES)
        # =====================================================================
        print("\n" + "=" * 80)
        print("2. ÉVÉNEMENTS AVEC ESTIMATE (SURPRENABLES)")
        print("=" * 80)
        
        df_with_estimate = df_all[df_all['estimate'].notna()]
        print(f"\n📊 Événements avec estimate : {len(df_with_estimate)}")
        
        if len(df_with_estimate) > 0:
            print("\n" + "-" * 80)
            print("LISTE ÉVÉNEMENTS SURPRENABLES")
            print("-" * 80)
            print(df_with_estimate.to_string(index=False))
        
        # =====================================================================
        # 3. ANALYSE EVENT_KEY UNIQUES
        # =====================================================================
        print("\n" + "=" * 80)
        print("3. ANALYSE EVENT_KEY UNIQUES")
        print("=" * 80)
        
        unique_keys = df_all['event_key'].unique()
        print(f"\n📊 Nombre d'event_key uniques : {len(unique_keys)}")
        print("\nListe des event_key :")
        for i, key in enumerate(unique_keys, 1):
            count = len(df_all[df_all['event_key'] == key])
            print(f"  {i}. {key} (apparaît {count}x)")
        
        # =====================================================================
        # 4. ANALYSE SCORES EMPIRIQUES
        # =====================================================================
        print("\n" + "=" * 80)
        print("4. ANALYSE SCORES EMPIRIQUES")
        print("=" * 80)
        
        df_with_scores = df_all[df_all['empirical_score'].notna()]
        print(f"\n📊 Événements avec score empirique : {len(df_with_scores)}")
        
        if len(df_with_scores) > 0:
            print(f"\nScore moyen : {df_with_scores['empirical_score'].mean():.2f}")
            print(f"Score min : {df_with_scores['empirical_score'].min():.2f}")
            print(f"Score max : {df_with_scores['empirical_score'].max():.2f}")
            
            print("\n" + "-" * 80)
            print("ÉVÉNEMENTS AVEC SCORES")
            print("-" * 80)
            print(df_with_scores[['event_key', 'event_title', 'empirical_score']].to_string(index=False))
        
        # =====================================================================
        # 5. RECHERCHE COMPOSANTES CPI
        # =====================================================================
        print("\n" + "=" * 80)
        print("5. RECHERCHE COMPOSANTES CPI")
        print("=" * 80)
        
        # Chercher tous les événements contenant "CPI" ou "Inflation"
        query_cpi = """
        SELECT 
            e.event_key,
            e.event_title,
            e.actual,
            e.estimate,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef ON e.event_key = ef.event_key
        WHERE e.ts_utc = '2025-09-11 14:30:00+02:00'
          AND (
              LOWER(e.event_title) LIKE '%cpi%' 
              OR LOWER(e.event_title) LIKE '%inflation%'
          )
        ORDER BY ef.empirical_score DESC NULLS LAST
        """
        
        df_cpi = con.execute(query_cpi).df()
        print(f"\n📊 Événements CPI/Inflation trouvés : {len(df_cpi)}")
        
        if len(df_cpi) > 0:
            print("\n" + "-" * 80)
            print("COMPOSANTES CPI/INFLATION")
            print("-" * 80)
            print(df_cpi.to_string(index=False))
        
        # =====================================================================
        # 6. COMPARAISON AVEC ATTENTES
        # =====================================================================
        print("\n" + "=" * 80)
        print("6. COMPARAISON AVEC DOCUMENTATION")
        print("=" * 80)
        
        print("\n📋 SELON REFERENCE_CASE_11_SEPT_2025.md :")
        print("   - ~14 événements attendus (multiples composantes CPI)")
        print("   - Impact attendu Phase 1 Peak 1 : 37.4 pips")
        print("   - Cluster avec CPI + Jobless Claims")
        
        print(f"\n📊 RÉALITÉ DATABASE :")
        print(f"   - {len(df_all)} événements trouvés au total")
        print(f"   - {len(df_with_estimate)} événements avec estimate (surprenables)")
        print(f"   - {len(unique_keys)} event_key uniques")
        print(f"   - {len(df_with_scores)} événements avec score empirique")
        
        # Calcul impact si on a les scores
        if len(df_with_scores) > 0:
            avg_score = df_with_scores['empirical_score'].mean()
            num_events = len(df_with_scores)
            
            # Formule D simplifiée (sans amplification)
            # impact = (score * sqrt(num_events)) / 10
            import math
            impact_base = (avg_score * math.sqrt(num_events)) / 10
            impact_amplified = impact_base * 2.5  # amplification par défaut
            
            print(f"\n📐 CALCUL IMPACT THÉORIQUE :")
            print(f"   - Score moyen : {avg_score:.2f}")
            print(f"   - Nombre événements : {num_events}")
            print(f"   - Impact base (formule D) : {impact_base:.2f} pips")
            print(f"   - Impact amplifié (x2.5) : {impact_amplified:.2f} pips")
            print(f"   - Impact attendu : 37.4 pips")
            print(f"   - Écart : {abs(impact_amplified - 37.4):.2f} pips ({((impact_amplified - 37.4) / 37.4 * 100):.1f}%)")
        
        # =====================================================================
        # 7. DIAGNOSTIC FINAL
        # =====================================================================
        print("\n" + "=" * 80)
        print("7. DIAGNOSTIC & RECOMMANDATIONS")
        print("=" * 80)
        
        if len(df_all) < 10:
            print("\n⚠️  BASE DE DONNÉES INCOMPLÈTE")
            print(f"   - Trouvé : {len(df_all)} événements")
            print(f"   - Attendu : ~14 événements")
            print(f"   - Manque : ~{14 - len(df_all)} événements")
            print("\n💡 SOLUTIONS POSSIBLES :")
            print("   A. Accepter limitation et ajuster validation (tolérance ±5 pips)")
            print("   B. Utiliser amplification compensatoire pour petits clusters")
            print("   C. Enrichir la DB avec événements CPI manquants")
            
        elif len(df_with_estimate) < len(df_all):
            print("\n⚠️  CERTAINS ÉVÉNEMENTS SANS ESTIMATE")
            print(f"   - Total : {len(df_all)} événements")
            print(f"   - Avec estimate : {len(df_with_estimate)} événements")
            print(f"   - Sans estimate : {len(df_all) - len(df_with_estimate)} événements")
            print("\n💡 Les événements sans estimate ne génèrent pas de surprise")
            
        else:
            print("\n✅ STRUCTURE DB CORRECTE")
            print(f"   - {len(df_all)} événements avec données complètes")
            print("\n💡 Si impact encore incorrect, problème dans :")
            print("   - Formule D (inadaptée aux petits clusters ?)")
            print("   - Amplification (2.5 trop faible ?)")
            print("   - Calcul surprise (valeurs aberrantes ?)")
    
    except Exception as e:
        print(f"\n❌ ERREUR lors du diagnostic : {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        con.close()
        print("\n" + "=" * 80)
        print("FIN DU DIAGNOSTIC")
        print("=" * 80)

if __name__ == "__main__":
    main()
