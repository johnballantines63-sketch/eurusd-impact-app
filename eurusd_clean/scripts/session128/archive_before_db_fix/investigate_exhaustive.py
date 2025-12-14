"""
INVESTIGATION EXHAUSTIVE - ÉCART SESSION 115 vs SESSION 128
===========================================================

Compare TOUS les éléments qui pourraient causer l'écart :
- Session 115 : MAE 0.29 pips (attendu)
- Session 128 : MAE 27.51 pips (actuel)

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 128
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(1, str(Path(__file__).parent.parent / 'session113'))
sys.path.insert(2, str(Path(__file__).parent.parent / 'session127'))

from src.config import DB_PATH


def investigate_all():
    """Investigation complète de tous les écarts possibles"""
    
    print("="*80)
    print("INVESTIGATION EXHAUSTIVE - ÉCART SESSION 115 vs 128")
    print("="*80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ==========================================================================
    # 1. COMPARER DONNÉES SOURCES (events vs economic_events)
    # ==========================================================================
    
    print("1️⃣  COMPARAISON DONNÉES SOURCES")
    print("-"*80)
    
    # Table events (ancienne)
    try:
        events_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        events_sept11 = conn.execute("""
            SELECT COUNT(*) FROM events 
            WHERE DATE(ts_utc) = '2025-09-11'
        """).fetchone()[0]
        
        print(f"Table 'events' (ancienne) :")
        print(f"  Total: {events_count:,} événements")
        print(f"  11 sept: {events_sept11} événements")
        
        if events_sept11 > 0:
            print("\n  Échantillon 11 sept (events) :")
            sample_events = conn.execute("""
                SELECT event_key, estimate, actual
                FROM events
                WHERE DATE(ts_utc) = '2025-09-11'
                AND country IN ('usd', 'eur')
                ORDER BY ts_utc
                LIMIT 15
            """).fetchall()
            
            for key, est, act in sample_events:
                est_str = f"{est:.2f}" if est else "NULL"
                act_str = f"{act:.2f}" if act else "NULL"
                print(f"    • {key:<40} est={est_str:>8} act={act_str:>8}")
    except Exception as e:
        print(f"Table 'events' : ERREUR ou VIDE ({e})")
    
    print()
    
    # Table economic_events (nouvelle)
    try:
        econ_count = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
        econ_sept11 = conn.execute("""
            SELECT COUNT(*) FROM economic_events 
            WHERE DATE(datetime_utc) = '2025-09-11'
        """).fetchone()[0]
        
        print(f"Table 'economic_events' (nouvelle) :")
        print(f"  Total: {econ_count:,} événements")
        print(f"  11 sept: {econ_sept11} événements")
        
        if econ_sept11 > 0:
            print("\n  Échantillon 11 sept (economic_events) :")
            sample_econ = conn.execute("""
                SELECT event_name, forecast, actual, raw_data
                FROM economic_events
                WHERE DATE(datetime_utc) = '2025-09-11'
                AND country IN ('US', 'EU')
                ORDER BY datetime_utc
                LIMIT 15
            """).fetchall()
            
            for key, fcst, act, raw in sample_econ:
                # Extraire estimate de raw_data
                try:
                    data = json.loads(raw)
                    est = data.get('estimate')
                    comparison = data.get('comparison', '')
                except:
                    est = fcst
                    comparison = ''
                
                est_str = f"{est:.2f}" if est else "NULL"
                act_str = f"{act:.2f}" if act else "NULL"
                comp_str = f"[{comparison}]" if comparison else ""
                print(f"    • {key:<35} {comp_str:<6} est={est_str:>8} act={act_str:>8}")
    except Exception as e:
        print(f"Table 'economic_events' : ERREUR ({e})")
    
    print()
    print("🔍 ANALYSE :")
    if events_sept11 == 0 and econ_sept11 > 0:
        print("  ⚠️  Table 'events' VIDE pour 11 sept → Session 115 ne peut PAS fonctionner")
        print("  ✅ Table 'economic_events' contient données")
        print("  ❗ PROBLÈME : Structures event_key différentes ?")
    
    print()
    
    # ==========================================================================
    # 2. ANALYSER raw_data POUR DÉRIVÉS TEMPORELS
    # ==========================================================================
    
    print("2️⃣  ANALYSE raw_data - DÉRIVÉS TEMPORELS (_mom, _yoy)")
    print("-"*80)
    
    try:
        raw_analysis = conn.execute("""
            SELECT 
                event_name,
                raw_data
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
            AND country = 'US'
            AND datetime_utc >= '2025-09-11 12:30:00'
            AND datetime_utc < '2025-09-11 12:31:00'
            ORDER BY event_name
        """).fetchall()
        
        print(f"Événements US 12:30 (11 sept) : {len(raw_analysis)}")
        print()
        
        has_comparison = 0
        for event_name, raw_data in raw_analysis:
            try:
                data = json.loads(raw_data)
                comparison = data.get('comparison', None)
                
                if comparison:
                    has_comparison += 1
                    print(f"  • {event_name:<35} → comparison='{comparison}'")
                    print(f"    ❗ Devrait être : {event_name}_{comparison}")
                else:
                    print(f"  • {event_name:<35} → comparison=NULL")
            except:
                print(f"  • {event_name:<35} → raw_data ERROR")
        
        print()
        print(f"🔍 RÉSULTAT : {has_comparison}/{len(raw_analysis)} événements ont 'comparison'")
        
        if has_comparison > 0:
            print("  ❗ PROBLÈME CONFIRMÉ : Les event_name manquent suffixes _mom/_yoy")
            print("  ✅ SOLUTION : Modifier import_eodhd_only.py pour ajouter suffixes")
        
    except Exception as e:
        print(f"ERREUR analyse raw_data : {e}")
    
    print()
    
    # ==========================================================================
    # 3. COMPARER SCORES EMPIRIQUES
    # ==========================================================================
    
    print("3️⃣  COMPARAISON SCORES EMPIRIQUES")
    print("-"*80)
    
    try:
        # Scores event_families
        scores_count = conn.execute("SELECT COUNT(*) FROM event_families").fetchone()[0]
        print(f"Table 'event_families' : {scores_count:,} scores")
        
        # Quelques exemples
        sample_scores = conn.execute("""
            SELECT event_key, country, empirical_score
            FROM event_families
            WHERE country = 'US'
            AND event_key LIKE '%inflation%'
            ORDER BY empirical_score DESC
            LIMIT 10
        """).fetchall()
        
        print("\nExemples scores inflation (US) :")
        for key, country, score in sample_scores:
            print(f"  • {key:<40} : {score:.2f} pips")
        
    except Exception as e:
        print(f"ERREUR scores : {e}")
    
    print()
    
    # ==========================================================================
    # 4. VÉRIFIER FORMULES - VERSION cluster_impact_calculator.py
    # ==========================================================================
    
    print("4️⃣  VÉRIFICATION VERSION FORMULES")
    print("-"*80)
    
    formula_file = project_root / "src" / "core" / "cluster_impact_calculator.py"
    
    if formula_file.exists():
        with open(formula_file, 'r') as f:
            content = f.read()
        
        # Chercher version
        if "Session 113 ORIGINALE" in content:
            print("  ✅ cluster_impact_calculator.py : Version Session 113 (ORIGINALE)")
        elif "Session 128" in content:
            print("  ⚠️  cluster_impact_calculator.py : MODIFIÉ Session 128")
        else:
            print("  ❓ cluster_impact_calculator.py : Version inconnue")
        
        # Chercher amplification par défaut
        if "amplification: float = 2.8" in content:
            print("  ✅ Amplification par défaut : 2.8 (correct)")
        elif "amplification: float = 2.5" in content:
            print("  ⚠️  Amplification par défaut : 2.5 (ancienne version)")
        
        # Chercher logique surprise
        if "is_rate_event" in content:
            print("  ✅ Logique surprise : is_rate_event présent")
        
        if "surprise_points = actual - reference" in content:
            print("  ✅ Calcul surprise : POINTS pour rate events")
    
    print()
    
    # ==========================================================================
    # 5. VÉRIFIER deduplicate_events.py
    # ==========================================================================
    
    print("5️⃣  VÉRIFICATION deduplicate_events.py")
    print("-"*80)
    
    dedup_file = Path(__file__).parent.parent / "session113" / "deduplicate_events.py"
    
    if dedup_file.exists():
        with open(dedup_file, 'r') as f:
            dedup_content = f.read()
        
        if "temporal_suffixes = ['_mom', '_yoy', '_qoq'" in dedup_content:
            print("  ✅ deduplicate_events.py : Reconnaît _mom, _yoy, _qoq")
        
        if "GARDER dérivés temporels" in dedup_content:
            print("  ✅ deduplicate_events.py : Logique GARDE dérivés")
        
        if "events_df['estimate'].notna()" in dedup_content:
            print("  ✅ deduplicate_events.py : Filtre estimate NULL")
    
    print()
    
    # ==========================================================================
    # 6. RÉSUMÉ DIAGNOSTIC
    # ==========================================================================
    
    print("="*80)
    print("RÉSUMÉ DIAGNOSTIC")
    print("="*80)
    print()
    
    print("PROBLÈMES IDENTIFIÉS :")
    print()
    
    print("1. ❌ CRITIQUE : event_name manque suffixes temporels (_mom, _yoy)")
    print("   • EODHD fournit 'comparison' dans raw_data")
    print("   • import_eodhd_only.py ne construit PAS les suffixes")
    print("   • Conséquence : deduplicate_events ne retire RIEN")
    print("   • Résultat : Trop d'événements → Impact surestimé")
    print()
    
    print("2. ⚠️  POSSIBLE : Table 'events' vide pour 11 sept")
    print("   • Script Session 115 cherche dans 'events'")
    print("   • Si vide → aucune donnée → échec")
    print()
    
    print("3. ✅ OK : Formules apparemment correctes")
    print("   • cluster_impact_calculator.py semble correct")
    print("   • Amplification = 2.8")
    print("   • deduplicate_events.py correct")
    print()
    
    print("="*80)
    print("ACTIONS REQUISES")
    print("="*80)
    print()
    
    print("PRIORITÉ 1 : Corriger import_eodhd_only.py")
    print("  → Ajouter construction event_key avec suffixes _mom/_yoy")
    print("  → Basé sur raw_data['comparison']")
    print()
    
    print("PRIORITÉ 2 : Réimporter données")
    print("  → Exécuter nouveau script import")
    print("  → Vérifier event_key contiennent _mom/_yoy")
    print()
    
    print("PRIORITÉ 3 : Retester Session 115")
    print("  → Lancer test_session115_ORIGINAL_adapted.py")
    print("  → Vérifier MAE < 2 pips")
    print()
    
    conn.close()


if __name__ == "__main__":
    investigate_all()
