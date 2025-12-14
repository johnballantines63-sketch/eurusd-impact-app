#!/usr/bin/env python3
"""
OPTION 2 : Réimport depuis EODHD
- Sauvegarde DB actuelle
- Supprime événements du 10 octobre 2025
- Réimporte depuis EODHD (propre)
- Vérifie résultat
"""

import duckdb
import sys
from pathlib import Path
from datetime import date, datetime, timedelta

sys.path.insert(0, 'fx_impact_app/src')
from config import get_db_path
from eodhd_client import fetch_calendar_json, calendar_to_events_df, upsert_events

def create_backup():
    """Créer backup de la DB"""
    db_path = Path(get_db_path())
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = db_path.parent / f"warehouse_backup_reimport_{timestamp}.duckdb"
    
    print(f"📦 Création backup : {backup_path.name}")
    
    import shutil
    shutil.copy2(db_path, backup_path)
    
    print(f"✅ Backup créé : {backup_path}")
    return backup_path

def count_existing_events(conn, target_date):
    """Compter événements existants pour la date"""
    query = f"""
        SELECT COUNT(*)
        FROM events
        WHERE DATE(ts_utc) = '{target_date}'
    """
    
    count = conn.execute(query).fetchone()[0]
    return count

def delete_existing_events(conn, target_date, dry_run=True):
    """Supprimer événements existants pour la date"""
    
    count = count_existing_events(conn, target_date)
    
    if count == 0:
        print(f"   ℹ️  Aucun événement existant pour {target_date}")
        return 0
    
    if dry_run:
        print(f"   📋 Serait supprimé : {count} événements")
    else:
        query = f"DELETE FROM events WHERE DATE(ts_utc) = '{target_date}'"
        conn.execute(query)
        conn.commit()
        print(f"   🗑️  Supprimé : {count} événements")
    
    return count

def fetch_from_eodhd(target_date):
    """Récupérer événements depuis EODHD"""
    print(f"\n📡 Récupération depuis EODHD API...")
    
    # Fenêtre de 24h autour de la date
    d1 = target_date
    d2 = target_date + timedelta(days=1)
    
    try:
        items = fetch_calendar_json(
            d1=d1,
            d2=d2,
            countries=['US', 'EU', 'GB', 'JP', 'CH', 'CN', 'CA', 'AU'],
            importance=None
        )
        
        if not items:
            print("   ⚠️  Aucun événement retourné par EODHD")
            return None
        
        print(f"   ✅ {len(items)} événements récupérés")
        
        # Normaliser en DataFrame
        df = calendar_to_events_df(items)
        
        if df.empty:
            print("   ⚠️  Aucun événement valide après normalisation")
            return None
        
        print(f"   ✅ {len(df)} événements normalisés")
        
        return df
        
    except Exception as e:
        print(f"   ❌ Erreur EODHD : {e}")
        return None

def insert_events(conn, df, dry_run=True):
    """Insérer événements dans la DB"""
    
    if df is None or df.empty:
        print("   ⚠️  Aucun événement à insérer")
        return 0
    
    if dry_run:
        print(f"   📋 Serait inséré : {len(df)} événements")
        # Afficher échantillon
        print("\n   📊 Échantillon :")
        for idx, row in df.head(5).iterrows():
            print(f"      {row['ts_utc']} - {row['event_key']} ({row['country']})")
        return len(df)
    else:
        try:
            updated = upsert_events(conn, df)
            print(f"   ✅ Inséré/mis à jour : {updated} événements")
            return updated
        except Exception as e:
            print(f"   ❌ Erreur insertion : {e}")
            return 0

def verify_reimport(conn, target_date):
    """Vérifier le résultat du réimport"""
    print("\n🔍 VÉRIFICATION POST-RÉIMPORT\n")
    
    # Compter événements
    total = count_existing_events(conn, target_date)
    print(f"   📊 Total événements : {total}")
    
    # Vérifier event_key cassés
    corrupted_query = """
        SELECT COUNT(*)
        FROM events
        WHERE DATE(ts_utc) = ?
          AND (event_key LIKE '_%'
               OR event_key LIKE '||%'
               OR event_key LIKE '|%')
    """
    
    corrupted = conn.execute(corrupted_query, [str(target_date)]).fetchone()[0]
    
    if corrupted == 0:
        print(f"   ✅ Aucun event_key cassé")
    else:
        print(f"   ⚠️  {corrupted} event_key cassés détectés")
    
    # Vérifier doublons
    dup_query = """
        SELECT COUNT(*)
        FROM (
            SELECT ts_utc, event_key, COUNT(*) as n
            FROM events
            WHERE DATE(ts_utc) = ?
            GROUP BY ts_utc, event_key
            HAVING COUNT(*) > 1
        )
    """
    
    duplicates = conn.execute(dup_query, [str(target_date)]).fetchone()[0]
    
    if duplicates == 0:
        print(f"   ✅ Aucun doublon (ts_utc + event_key)")
    else:
        print(f"   ⚠️  {duplicates} doublons détectés")
    
    # Échantillon événements
    sample_query = """
        SELECT ts_utc, event_key, country, importance_n
        FROM events
        WHERE DATE(ts_utc) = ?
        ORDER BY ts_utc
        LIMIT 10
    """
    
    sample = conn.execute(sample_query, [str(target_date)]).fetchall()
    
    print(f"\n   📋 Échantillon (10 premiers) :")
    for row in sample:
        ts, key, country, imp = row
        print(f"      {ts.strftime('%H:%M')} - {key} ({country}) [Imp:{imp}]")
    
    return corrupted == 0 and duplicates == 0

def main():
    print("="*80)
    print("📥 RÉIMPORT DEPUIS EODHD - 10 octobre 2025")
    print("="*80)
    
    target_date = date(2025, 10, 10)
    
    # Créer backup
    backup_path = create_backup()
    
    # Ouvrir DB
    conn = duckdb.connect(get_db_path())
    
    # État actuel
    print(f"\n📊 ÉTAT ACTUEL")
    print("="*80)
    existing = count_existing_events(conn, target_date)
    print(f"   Événements existants : {existing}")
    
    # Récupérer depuis EODHD
    print(f"\n" + "="*80)
    print("📡 RÉCUPÉRATION EODHD")
    print("="*80)
    df = fetch_from_eodhd(target_date)
    
    if df is None:
        print("\n❌ Échec récupération EODHD - annulation")
        conn.close()
        return
    
    # Simulation
    print(f"\n" + "="*80)
    print("📋 SIMULATION")
    print("="*80)
    
    print("\n1️⃣ Suppression événements existants :")
    delete_existing_events(conn, target_date, dry_run=True)
    
    print("\n2️⃣ Insertion nouveaux événements :")
    insert_events(conn, df, dry_run=True)
    
    # Demander confirmation
    print("\n" + "="*80)
    response = input("⚠️  Confirmer le réimport ? (oui/non) : ")
    
    if response.lower() not in ['oui', 'yes', 'o', 'y']:
        print("\n❌ Annulé - aucune modification")
        conn.close()
        return
    
    # Réimport réel
    print("\n" + "="*80)
    print("🔄 RÉIMPORT RÉEL")
    print("="*80)
    
    print("\n1️⃣ Suppression événements existants :")
    deleted = delete_existing_events(conn, target_date, dry_run=False)
    
    print("\n2️⃣ Insertion nouveaux événements :")
    inserted = insert_events(conn, df, dry_run=False)
    
    # Vérification
    success = verify_reimport(conn, target_date)
    
    conn.close()
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ")
    print("="*80)
    print(f"\n   🗑️  Événements supprimés : {deleted}")
    print(f"   📥 Événements insérés : {inserted}")
    print(f"   📦 Backup : {backup_path.name}")
    
    if success:
        print(f"   ✅ Réimport réussi")
        print(f"\n💡 PROCHAINES ÉTAPES :")
        print(f"   1. Redémarrer Streamlit")
        print(f"   2. Vérifier événements du 10 octobre")
        print(f"   3. Si problème : restaurer avec backup")
    else:
        print(f"   ⚠️  Vérification partielle - contrôle manuel recommandé")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
