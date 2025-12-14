#!/usr/bin/env python3
"""
Diagnostic complet de la corruption DB
- Identifier les event_key cassés
- Trouver les doublons (même ts_utc + previous)
- Proposer stratégie de nettoyage
"""

import duckdb
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'fx_impact_app/src')
from config import get_db_path

def main():
    print("="*80)
    print("🔍 DIAGNOSTIC CORRUPTION BASE DE DONNÉES")
    print("="*80)
    
    conn = duckdb.connect(get_db_path(), read_only=True)
    
    # ============================================
    # 1. TOUS les événements du 10 octobre 2025
    # ============================================
    print("\n📊 TOUS les événements US du 10 octobre 2025 :\n")
    
    query = """
        SELECT 
            ts_utc,
            event_key,
            previous,
            estimate,
            actual,
            importance_n
        FROM events
        WHERE DATE(ts_utc) = '2025-10-10'
          AND country = 'US'
        ORDER BY ts_utc, event_key
    """
    
    events = conn.execute(query).fetchall()
    
    print(f"Total : {len(events)} événements US\n")
    
    # Grouper par timestamp
    from collections import defaultdict
    by_time = defaultdict(list)
    
    for evt in events:
        ts = evt[0]
        time_key = ts.strftime('%H:%M')
        by_time[time_key].append(evt)
    
    # ============================================
    # 2. IDENTIFIER LES DOUBLONS SUSPECTS
    # ============================================
    print("⚠️  DOUBLONS SUSPECTS (même heure + previous) :\n")
    
    duplicates = []
    
    for time_key, evts in sorted(by_time.items()):
        if len(evts) > 1:
            # Grouper par previous
            by_prev = defaultdict(list)
            for evt in evts:
                prev = evt[2]  # previous
                by_prev[prev].append(evt)
            
            # Si plusieurs événements avec même previous → doublons !
            for prev, dup_events in by_prev.items():
                if len(dup_events) > 1 and prev is not None:
                    print(f"🚨 {time_key} - Previous={prev} : {len(dup_events)} événements")
                    for evt in dup_events:
                        event_key = evt[1]
                        estimate = evt[3]
                        # Identifier les event_key cassés
                        if event_key.startswith('_') or '||' in event_key or event_key.startswith('|'):
                            status = "❌ CASSÉ"
                        else:
                            status = "✅ OK"
                        
                        print(f"   {status} '{event_key}' (Est: {estimate})")
                        
                        duplicates.append({
                            'time': time_key,
                            'event_key': event_key,
                            'previous': prev,
                            'is_corrupted': status == "❌ CASSÉ"
                        })
                    print()
    
    # ============================================
    # 3. PATTERNS D'EVENT_KEY CASSÉS
    # ============================================
    print("\n🔍 PATTERNS D'EVENT_KEY CASSÉS :\n")
    
    corrupted_patterns = [
        (r'^_', 'Commence par underscore'),
        (r'^\|\|', 'Commence par double pipe'),
        (r'^\|', 'Commence par pipe simple'),
        (r'  ', 'Double espace'),
        (r'^\s', 'Commence par espace'),
        (r'\s$', 'Finit par espace'),
    ]
    
    query_all = """
        SELECT DISTINCT event_key
        FROM events
        WHERE DATE(ts_utc) = '2025-10-10'
          AND country = 'US'
    """
    
    all_keys = [row[0] for row in conn.execute(query_all).fetchall()]
    
    corrupted_keys = []
    for key in all_keys:
        import re
        for pattern, desc in corrupted_patterns:
            if re.search(pattern, key):
                corrupted_keys.append((key, desc))
                print(f"   ❌ '{key}' → {desc}")
                break
    
    if not corrupted_keys:
        print("   ✅ Aucun pattern cassé détecté")
    
    # ============================================
    # 4. STATISTIQUES GLOBALES
    # ============================================
    print("\n📊 STATISTIQUES DB :\n")
    
    # Total événements
    total_query = "SELECT COUNT(*) FROM events WHERE DATE(ts_utc) = '2025-10-10'"
    total = conn.execute(total_query).fetchone()[0]
    print(f"   Total événements (tous pays) : {total}")
    
    # Événements avec famille
    with_family_query = """
        SELECT COUNT(*)
        FROM events e
        INNER JOIN event_families ef ON e.event_key = ef.event_key
        WHERE DATE(e.ts_utc) = '2025-10-10'
    """
    with_family = conn.execute(with_family_query).fetchone()[0]
    print(f"   Avec famille : {with_family}")
    
    # Événements sans famille
    without_family = total - with_family
    print(f"   Sans famille : {without_family}")
    
    # Date dernier import
    last_import_query = "SELECT MAX(ts_utc) FROM events"
    last_import = conn.execute(last_import_query).fetchone()[0]
    print(f"   Dernier événement : {last_import}")
    
    # ============================================
    # 5. RECOMMANDATIONS
    # ============================================
    print("\n" + "="*80)
    print("💡 RECOMMANDATIONS")
    print("="*80)
    
    if len(duplicates) > 0:
        n_corrupted = sum(1 for d in duplicates if d['is_corrupted'])
        print(f"\n⚠️  {len(duplicates)} doublons détectés dont {n_corrupted} cassés\n")
        
        print("OPTIONS :\n")
        
        print("📌 OPTION 1 : Nettoyage chirurgical (RECOMMANDÉ)")
        print("   - Supprimer uniquement les event_key cassés")
        print("   - Garder les données historiques")
        print("   - Script : clean_corrupted_events.py\n")
        
        print("📌 OPTION 2 : Réimport complet")
        print("   - Sauvegarder DB actuelle")
        print("   - Réimporter depuis EODHD (propre)")
        print("   - Vérifier résultat")
        print("   - Script : reimport_from_eodhd.py\n")
        
        print("📌 OPTION 3 : Déduplication intelligente")
        print("   - Garder le meilleur event_key par (ts_utc, previous)")
        print("   - Supprimer les doublons")
        print("   - Script : deduplicate_events.py\n")
        
        # Générer commandes de nettoyage
        print("🔧 COMMANDES SQL DE NETTOYAGE :\n")
        
        for dup in duplicates:
            if dup['is_corrupted']:
                event_key = dup['event_key'].replace("'", "''")  # Escape quotes
                print(f"DELETE FROM events WHERE event_key = '{event_key}' AND DATE(ts_utc) = '2025-10-10';")
        
    else:
        print("\n✅ Aucun doublon cassé détecté - DB semble propre")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ Diagnostic terminé")
    print("="*80)

if __name__ == "__main__":
    main()
