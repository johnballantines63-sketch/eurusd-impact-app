"""
Extraire country_code propre depuis raw_data JSON

Crée colonne country_code (US, EU, GB, etc.) depuis raw_data.country

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Extraction country_code propre
"""

import duckdb
from pathlib import Path
import json
from tqdm import tqdm

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def extract_country_codes():
    """Extraire country_code depuis raw_data JSON"""
    
    print("=" * 80)
    print("EXTRACTION COUNTRY_CODE DEPUIS RAW_DATA")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # ========================================================================
    # 1. AJOUTER COLONNE country_code
    # ========================================================================
    
    print("1. AJOUT COLONNE country_code")
    print("-" * 80)
    print()
    
    try:
        conn.execute("ALTER TABLE economic_events ADD COLUMN country_code VARCHAR")
        print("✅ Colonne country_code créée")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✅ Colonne country_code existe déjà")
        else:
            print(f"❌ Erreur: {e}")
            conn.close()
            return
    
    print()
    
    # ========================================================================
    # 2. EXTRAIRE country DEPUIS raw_data
    # ========================================================================
    
    print("2. EXTRACTION country DEPUIS raw_data JSON")
    print("-" * 80)
    print()
    
    # Charger tous les événements avec raw_data
    query = """
    SELECT event_id, raw_data
    FROM economic_events
    WHERE raw_data IS NOT NULL
    """
    
    events = conn.execute(query).df()
    
    print(f"Total événements avec raw_data : {len(events):,}")
    print()
    
    # Extraire country_code
    updates = []
    
    for idx, row in tqdm(events.iterrows(), total=len(events), desc="Extraction"):
        event_id = row['event_id']
        
        try:
            raw = json.loads(row['raw_data'])
            country_code = raw.get('country', None)
            
            if country_code:
                updates.append((country_code, event_id))
        except:
            continue
    
    print()
    print(f"✅ {len(updates):,} country_code extraits")
    print()
    
    # ========================================================================
    # 3. UPDATE BASE DE DONNÉES
    # ========================================================================
    
    print("3. UPDATE DATABASE")
    print("-" * 80)
    print()
    
    # Batch update par 1000
    batch_size = 1000
    
    for i in tqdm(range(0, len(updates), batch_size), desc="Update"):
        batch = updates[i:i+batch_size]
        
        for country_code, event_id in batch:
            conn.execute("""
                UPDATE economic_events
                SET country_code = ?
                WHERE event_id = ?
            """, [country_code, event_id])
    
    print()
    print("✅ Updates terminés")
    print()
    
    # ========================================================================
    # 4. VÉRIFICATION
    # ========================================================================
    
    print("4. VÉRIFICATION")
    print("-" * 80)
    print()
    
    # Compter country_code remplis
    query_count = """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN country_code IS NOT NULL THEN 1 ELSE 0 END) as with_code,
        SUM(CASE WHEN country_code IS NULL THEN 1 ELSE 0 END) as without_code
    FROM economic_events
    """
    
    counts = conn.execute(query_count).df()
    
    print(f"Total événements     : {counts['total'].iloc[0]:,}")
    print(f"Avec country_code    : {counts['with_code'].iloc[0]:,}")
    print(f"Sans country_code    : {counts['without_code'].iloc[0]:,}")
    print()
    
    # Échantillon 11 septembre
    query_sept = """
    SELECT 
        datetime_utc,
        event_name,
        country as currency_code,
        country_code as country_iso,
        importance
    FROM economic_events
    WHERE DATE(datetime_utc) = '2025-09-11'
      AND importance = 'HIGH'
    ORDER BY datetime_utc
    LIMIT 10
    """
    
    sept = conn.execute(query_sept).df()
    
    print("Échantillon 11 septembre HIGH :")
    print()
    print(sept.to_string())
    print()
    
    # Values uniques country_code
    query_codes = """
    SELECT DISTINCT country_code
    FROM economic_events
    WHERE country_code IS NOT NULL
    ORDER BY country_code
    """
    
    codes = conn.execute(query_codes).df()
    
    print(f"Country codes uniques : {len(codes)}")
    print()
    print("Exemples :")
    for code in codes['country_code'].head(20).tolist():
        print(f"   {code}")
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ EXTRACTION TERMINÉE")
    print("=" * 80)
    print()
    print("Colonnes disponibles :")
    print("   - country      : devise (usd, eur) ou code pays (us, uk)")
    print("   - country_code : code pays ISO-2 (US, EU, GB) ← NOUVEAU")
    print()


if __name__ == '__main__':
    extract_country_codes()
