#!/usr/bin/env python3
"""
Nettoyage complet des doublons Michigan
Objectif: Garder UNE SEULE version avec données
Format final: Nom simple sans préfixe (ex: 'michigan consumer sentiment')
"""

import duckdb
from datetime import datetime

def cleanup_michigan_events():
    """Nettoie tous les doublons Michigan"""
    
    conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
    
    print("🧹 NETTOYAGE MICHIGAN DUPLICATES")
    print("=" * 80)
    
    # Étape 1: Voir l'état actuel
    print("\n📊 ÉTAT AVANT NETTOYAGE:")
    before = conn.execute("""
        SELECT 
            event_key,
            previous,
            estimate,
            CASE 
                WHEN event_key LIKE '||%' THEN 'Préfixe ||'
                WHEN event_key LIKE '_%' THEN 'Préfixe _'
                ELSE 'Sans préfixe'
            END as type
        FROM events
        WHERE DATE(ts_utc) = '2025-10-10'
          AND LOWER(event_key) LIKE '%michigan%'
        ORDER BY event_key
    """).fetchdf()
    print(before)
    print(f"\nTotal: {len(before)} événements")
    
    # Étape 2: Supprimer événements SANS données (previous ET estimate NULL)
    print("\n🗑️  SUPPRESSION ÉVÉNEMENTS VIDES...")
    deleted_empty = conn.execute("""
        DELETE FROM events
        WHERE DATE(ts_utc) = '2025-10-10'
          AND LOWER(event_key) LIKE '%michigan%'
          AND previous IS NULL
          AND estimate IS NULL
    """).fetchone()[0]
    print(f"✅ {deleted_empty} événements vides supprimés")
    
    # Étape 3: Supprimer les anciennes versions avec préfixe ||
    print("\n🗑️  SUPPRESSION PRÉFIXE || (ancienne version)...")
    deleted_pipe = conn.execute("""
        DELETE FROM events
        WHERE DATE(ts_utc) = '2025-10-10'
          AND event_key LIKE '||michigan%'
    """).fetchone()[0]
    print(f"✅ {deleted_pipe} événements || supprimés")
    
    # Étape 4: Renommer les _ en version sans préfixe
    print("\n✏️  RENOMMAGE _ → sans préfixe...")
    
    # Récupérer les event_key avec _
    to_rename = conn.execute("""
        SELECT DISTINCT event_key
        FROM events
        WHERE DATE(ts_utc) = '2025-10-10'
          AND event_key LIKE '_%michigan%'
    """).fetchall()
    
    renamed_count = 0
    for (old_key,) in to_rename:
        # Enlever le _ du début
        new_key = old_key[1:] if old_key.startswith('_') else old_key
        
        # Mettre à jour
        conn.execute("""
            UPDATE events
            SET event_key = ?
            WHERE event_key = ?
              AND DATE(ts_utc) = '2025-10-10'
        """, [new_key, old_key])
        
        renamed_count += 1
        print(f"   {old_key} → {new_key}")
    
    print(f"✅ {renamed_count} événements renommés")
    
    # Étape 5: Vérifier résultat final
    print("\n📊 ÉTAT APRÈS NETTOYAGE:")
    after = conn.execute("""
        SELECT 
            event_key,
            previous,
            estimate,
            actual
        FROM events
        WHERE DATE(ts_utc) = '2025-10-10'
          AND LOWER(event_key) LIKE '%michigan%'
        ORDER BY event_key
    """).fetchdf()
    print(after)
    print(f"\nTotal: {len(after)} événements")
    
    # Étape 6: Validation
    print("\n✅ VALIDATION:")
    no_prefix = len(after[~after['event_key'].str.startswith(('_', '||'))])
    with_data = len(after[after['previous'].notna() | after['estimate'].notna()])
    
    print(f"   - Événements sans préfixe: {no_prefix}/{len(after)}")
    print(f"   - Événements avec données: {with_data}/{len(after)}")
    
    if no_prefix == len(after) and with_data == len(after):
        print("\n🎉 PARFAIT ! Tous les événements sont propres")
    else:
        print("\n⚠️  Attention : Il reste des problèmes")
    
    conn.close()
    return after

def verify_planificateur_mapping():
    """Vérifie que les mappings utilisent les bons event_key"""
    
    conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)
    
    print("\n" + "=" * 80)
    print("🔍 VÉRIFICATION MAPPINGS event_families")
    print("=" * 80)
    
    # Voir les mappings Michigan
    mappings = conn.execute("""
        SELECT 
            event_key,
            family,
            empirical_score
        FROM event_families
        WHERE LOWER(event_key) LIKE '%michigan%'
        ORDER BY event_key
    """).fetchdf()
    
    if len(mappings) > 0:
        print("\n📋 Mappings Michigan:")
        print(mappings)
        
        # Vérifier si ces event_key existent dans events
        print("\n🔍 Correspondance avec events:")
        for _, row in mappings.iterrows():
            exists = conn.execute("""
                SELECT COUNT(*) as cnt
                FROM events
                WHERE event_key = ?
                  AND DATE(ts_utc) = '2025-10-10'
            """, [row['event_key']]).fetchone()[0]
            
            status = "✅" if exists > 0 else "❌"
            print(f"   {status} {row['event_key']}: {exists} événement(s)")
    else:
        print("⚠️  Aucun mapping Michigan trouvé")
    
    conn.close()

if __name__ == "__main__":
    print("🔧 NETTOYAGE COMPLET MICHIGAN DUPLICATES")
    print("=" * 80)
    print("Date: 2025-10-10")
    print("Objectif: 1 seule version, nom simple, avec données")
    print("=" * 80)
    
    # Nettoyage
    result = cleanup_michigan_events()
    
    # Vérification mappings
    verify_planificateur_mapping()
    
    print("\n" + "=" * 80)
    print("✅ NETTOYAGE TERMINÉ")
    print("\n🎯 PROCHAINES ÉTAPES:")
    print("   1. Relancer Streamlit")
    print("   2. Aller dans Planificateur Multi-Événements")
    print("   3. Charger 10 octobre 2025")
    print("   4. Vérifier que Michigan a Previous/Estimate")
    print("=" * 80)
