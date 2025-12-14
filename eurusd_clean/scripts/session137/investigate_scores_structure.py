"""
INVESTIGATION STRUCTURE SCORES EMPIRIQUES
Session 137 - Trouver où sont stockés les scores

Hypothèses:
1. Table event_families (JOIN avec events)
2. CSV externe event_mapping_rules_complete.csv (Session 127)
3. Autre table dans warehouse.duckdb

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path

# =============================================================================
# PARAMÈTRES
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
MAPPING_CSV = Path(__file__).parent.parent.parent / "scripts" / "session127" / "event_mapping_rules_complete.csv"

# =============================================================================
# 1. LISTER TOUTES TABLES DB
# =============================================================================

def list_all_tables():
    """Lister toutes tables dans warehouse.duckdb"""
    
    print("="*80)
    print("1. TABLES DISPONIBLES DANS warehouse.duckdb")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    tables = conn.execute("SHOW TABLES").df()
    print(f"\nNombre de tables : {len(tables)}")
    print("\nListe des tables:")
    for idx, row in tables.iterrows():
        print(f"   {idx+1}. {row['name']}")
    
    conn.close()
    
    return tables['name'].tolist()

# =============================================================================
# 2. STRUCTURE TABLE EVENT_FAMILIES
# =============================================================================

def check_event_families_structure():
    """Vérifier structure table event_families"""
    
    print("\n" + "="*80)
    print("2. STRUCTURE TABLE event_families")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Structure
    print("\nColonnes table event_families:")
    print("-" * 80)
    structure = conn.execute("DESCRIBE event_families").df()
    print(structure.to_string(index=False))
    
    # Aperçu données
    print("\n\nAperçu données (5 premières lignes):")
    print("-" * 80)
    sample = conn.execute("SELECT * FROM event_families LIMIT 5").df()
    print(sample.to_string())
    
    # Compter lignes
    count = conn.execute("SELECT COUNT(*) FROM event_families").fetchone()[0]
    print(f"\n\nNombre de lignes : {count}")
    
    conn.close()

# =============================================================================
# 3. VÉRIFIER CSV MAPPING SESSION 127
# =============================================================================

def check_mapping_csv():
    """Vérifier si CSV mapping Session 127 existe"""
    
    print("\n" + "="*80)
    print("3. CSV MAPPING SESSION 127")
    print("="*80)
    
    print(f"\nChemin attendu : {MAPPING_CSV}")
    
    if MAPPING_CSV.exists():
        print(f"✅ Fichier existe")
        
        df = pd.read_csv(MAPPING_CSV)
        print(f"\nNombre de mappings : {len(df)}")
        print(f"Colonnes : {list(df.columns)}")
        
        print(f"\nAperçu (5 premières lignes):")
        print("-" * 80)
        print(df.head().to_string(index=False))
        
    else:
        print(f"❌ Fichier N'EXISTE PAS")
        
        # Chercher dans dossier session127
        session127_dir = Path(__file__).parent.parent / "session127"
        if session127_dir.exists():
            print(f"\nFichiers dans session127:")
            for f in session127_dir.iterdir():
                if f.suffix == '.csv':
                    print(f"   - {f.name}")

# =============================================================================
# 4. TESTER JOIN events <-> event_families
# =============================================================================

def test_join_events_families():
    """Tester JOIN entre events et event_families pour récupérer scores"""
    
    print("\n" + "="*80)
    print("4. TEST JOIN events <-> event_families")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Identifier colonne de jointure
    print("\nColonnes table events (liées event_families):")
    print("-" * 80)
    events_cols = conn.execute("DESCRIBE events").df()
    key_cols = events_cols[events_cols['column_name'].str.contains('key|family|name', case=False)]
    print(key_cols[['column_name', 'column_type']].to_string(index=False))
    
    print("\nColonnes table event_families (liées events):")
    print("-" * 80)
    families_cols = conn.execute("DESCRIBE event_families").df()
    key_cols_fam = families_cols[families_cols['column_name'].str.contains('key|family|name', case=False)]
    print(key_cols_fam[['column_name', 'column_type']].to_string(index=False))
    
    # Tester JOIN
    print("\n\nTest JOIN sur 1 événement HIGH:")
    print("-" * 80)
    
    query = """
    SELECT 
        e.ts_utc,
        e.country,
        e.event_title,
        e.event_key,
        e.importance_n,
        f.*
    FROM events e
    LEFT JOIN event_families f ON e.event_key = f.event_key
    WHERE e.importance_n = 3
    LIMIT 1
    """
    
    result = conn.execute(query).df()
    
    if len(result) > 0:
        print("✅ JOIN réussi")
        print(f"\nColonnes disponibles après JOIN:")
        for col in result.columns:
            print(f"   - {col}")
        
        # Chercher colonne score
        score_cols = [col for col in result.columns if 'score' in col.lower()]
        if score_cols:
            print(f"\n✅ Colonnes score trouvées : {score_cols}")
            for col in score_cols:
                print(f"   {col} = {result[col].iloc[0]}")
        else:
            print(f"\n⚠️ Aucune colonne score dans event_families")
    else:
        print("❌ JOIN échoué ou aucun résultat")
    
    conn.close()

# =============================================================================
# 5. RECOMMANDATION
# =============================================================================

def provide_recommendation():
    """Fournir recommandation basée sur investigation"""
    
    print("\n" + "="*80)
    print("5. RECOMMANDATION")
    print("="*80)
    
    print("\nOPTIONS POSSIBLES:")
    print("-" * 80)
    print("\nOPTION A : Scores dans event_families")
    print("   → JOIN events <-> event_families pour récupérer scores")
    print("   → Modifier step2_match_clusters.py pour inclure JOIN")
    print("   → Avantage: Scores centralisés dans DB")
    
    print("\nOPTION B : Scores dans CSV externe (Session 127)")
    print("   → Charger event_mapping_rules_complete.csv")
    print("   → Lookup scores via mapping event_key")
    print("   → Avantage: Utilise travail Session 127")
    
    print("\nOPTION C : Pas de scores (total_score = 0.0)")
    print("   → Continuer ÉTAPE 2 sans scores")
    print("   → total_score = 0.0 pour tous")
    print("   → Avantage: Workflow continue, scores optionnels")
    print("   → Inconvénient: Perd information score_empirique")
    
    print("\nOPTION D : Créer colonne score_empirique dans events")
    print("   → Migration DB: ALTER TABLE events ADD COLUMN score_empirique")
    print("   → Remplir depuis event_families ou CSV")
    print("   → Avantage: Structure propre long terme")
    print("   → Inconvénient: Modification DB (temps)")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("INVESTIGATION STRUCTURE SCORES EMPIRIQUES")
    print("="*80 + "\n")
    
    # 1. Lister tables
    tables = list_all_tables()
    
    # 2. Structure event_families
    if 'event_families' in tables:
        check_event_families_structure()
    else:
        print("\n⚠️ Table event_families N'EXISTE PAS")
    
    # 3. CSV mapping
    check_mapping_csv()
    
    # 4. Test JOIN
    if 'event_families' in tables:
        test_join_events_families()
    
    # 5. Recommandation
    provide_recommendation()
    
    print("\n" + "="*80)
    print("✅ INVESTIGATION COMPLÉTÉE")
    print("="*80 + "\n")
