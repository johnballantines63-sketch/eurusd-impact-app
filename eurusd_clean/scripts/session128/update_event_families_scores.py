"""
MISE À JOUR event_families - SCORES SESSION 123
================================================

Remplace scores event_families (DB) par scores CSV Session 123 (source vérité).

IMPORTANT :
- CSV Session 123 = scores empiriques validés (11-23 dates)
- event_families (DB) = anciennes valeurs, obsolètes
- Normalisation nécessaire : underscores→espaces, usd→US

Actions :
1. Backup event_families actuelle
2. Charger CSV Session 123
3. Normaliser formats (underscores→espaces, usd→US)
4. Mettre à jour event_families avec nouveaux scores
5. Valider : comparer avant/après

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 128 Phase 2
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import DB_PATH


def backup_event_families():
    """
    Backup table event_families avant mise à jour
    """
    print("="*80)
    print("BACKUP event_families")
    print("="*80)
    print()
    
    conn = duckdb.connect(str(DB_PATH))
    
    # Compter lignes
    count = conn.execute("SELECT COUNT(*) FROM event_families").fetchone()[0]
    
    if count == 0:
        print("⚠️ Table vide, pas de backup nécessaire")
        conn.close()
        return None
    
    # Créer backup
    backup_name = f"event_families_backup_s128_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"🔄 Création backup : {backup_name}")
    print(f"   Lignes : {count:,}")
    
    conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM event_families")
    
    # Vérifier
    backup_count = conn.execute(f"SELECT COUNT(*) FROM {backup_name}").fetchone()[0]
    
    if backup_count == count:
        print(f"   ✅ Backup créé : {backup_count:,} lignes")
        conn.close()
        return backup_name
    else:
        print(f"   ❌ Backup incomplet - ABANDON")
        conn.close()
        return False


def normalize_csv_to_db_format(df_csv):
    """
    Normalise format CSV vers format DB
    
    CSV :  event_name avec underscores, country minuscule
    DB  :  event_key avec espaces, country majuscule
    """
    print("="*80)
    print("NORMALISATION CSV → DB")
    print("="*80)
    print()
    
    df = df_csv.copy()
    
    # Renommer colonne
    df = df.rename(columns={'event_name': 'event_key'})
    
    # Normaliser event_key : underscores → espaces
    # SAUF avant suffixes _mom/_yoy/_qoq
    def normalize_event_key(key):
        # Garder suffixes avec underscore
        for suffix in ['_mom', '_yoy', '_qoq', '_mtd', '_ytd']:
            if key.endswith(suffix):
                base = key[:-len(suffix)]
                base_normalized = base.replace('_', ' ')
                return base_normalized + suffix
        
        # Pas de suffixe : remplacer tous underscores
        return key.replace('_', ' ')
    
    df['event_key'] = df['event_key'].apply(normalize_event_key)
    
    # Normaliser country : minuscule → majuscule
    country_map = {
        'usd': 'US', 'eur': 'EU', 'gbp': 'GB', 'jpy': 'JP',
        'cad': 'CA', 'aud': 'AU', 'nzd': 'NZ', 'chf': 'CH'
    }
    
    df['country'] = df['country'].map(country_map).fillna(df['country'].str.upper())
    
    print(f"✅ Normalisation effectuée : {len(df)} lignes")
    print()
    
    # Afficher exemples
    print("Exemples normalisés :")
    for idx, row in df.head(5).iterrows():
        print(f"   '{row['event_key']}' ({row['country']}) → {row['empirical_score']:.2f}")
    
    print()
    
    return df


def update_event_families(df_normalized):
    """
    Met à jour event_families avec nouveaux scores
    + Crée variantes _mom/_yoy/_qoq avec même score
    """
    print("="*80)
    print("MISE À JOUR event_families")
    print("="*80)
    print()
    
    conn = duckdb.connect(str(DB_PATH))
    
    # Supprimer anciennes données
    print("🗑️ Suppression anciennes données...")
    conn.execute("DELETE FROM event_families")
    print("   ✅ Table vidée")
    print()
    
    # Insérer nouvelles données + variantes
    print("💾 Insertion nouveaux scores + variantes...")
    
    rows = []
    
    for _, row in df_normalized.iterrows():
        event_key = row['event_key']
        country = row['country']
        score = row['empirical_score']
        avg_pips = row.get('avg_movement_pips')
        sample_size = row.get('sample_size')
        
        # Insérer événement de base
        rows.append((
            event_key, country, None, score, avg_pips, sample_size,
            None, None, None, None, None, None, None, None
        ))
        
        # Créer variantes SEULEMENT si pas déjà un dérivé
        if not any(event_key.endswith(suffix) for suffix in ['_mom', '_yoy', '_qoq', '_mtd', '_ytd']):
            # Créer variantes avec même score
            for suffix in ['_mom', '_yoy', '_qoq']:
                variant_key = event_key + suffix
                rows.append((
                    variant_key, country, None, score, avg_pips, sample_size,
                    None, None, None, None, None, None, None, None
                ))
    
    # Structure event_families : event_key, country, family, empirical_score, 
    #                            avg_movement_pips, sample_size, latency_median, ...
    
    conn.executemany("""
        INSERT INTO event_families 
        (event_key, country, family, empirical_score, avg_movement_pips, 
         sample_size, latency_median, latency_p20, latency_p80, 
         ttr_median, ttr_p20, ttr_p80, mfe_p80, n_events_latency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    
    # Vérifier
    count = conn.execute("SELECT COUNT(*) FROM event_families").fetchone()[0]
    conn.close()
    
    print(f"   ✅ {count:,} lignes insérées (base + variantes)")
    print()
    
    return count


def validate_update():
    """
    Valide mise à jour en comparant quelques événements
    """
    print("="*80)
    print("VALIDATION MISE À JOUR")
    print("="*80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Tester quelques événements critiques
    test_cases = [
        ('inflation rate_mom', 'US'),
        ('core inflation rate_mom', 'US'),
        ('initial jobless claims', 'US'),
    ]
    
    print("Vérification scores critiques :")
    print()
    
    all_ok = True
    
    for event_key, country in test_cases:
        result = conn.execute("""
            SELECT empirical_score
            FROM event_families
            WHERE event_key = ? AND country = ?
        """, [event_key, country]).fetchone()
        
        if result:
            score = result[0]
            print(f"✅ '{event_key}' ({country}) : {score:.2f} pips")
        else:
            print(f"❌ '{event_key}' ({country}) : NON TROUVÉ")
            all_ok = False
    
    conn.close()
    
    print()
    
    if all_ok:
        print("✅ Validation réussie")
        return True
    else:
        print("❌ Validation échouée")
        return False


def main():
    """
    Script principal
    """
    print("="*80)
    print("MISE À JOUR event_families - SCORES SESSION 123")
    print("="*80)
    print()
    print("Remplace scores obsolètes par scores validés Session 123")
    print()
    
    # Backup
    backup_name = backup_event_families()
    
    if backup_name is False:
        print("\n❌ Backup échoué - ABANDON")
        return False
    
    print()
    
    # Charger CSV
    print("="*80)
    print("CHARGEMENT CSV SESSION 123")
    print("="*80)
    print()
    
    csv_path = project_root / "scripts" / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
    
    if not csv_path.exists():
        print(f"❌ Fichier introuvable : {csv_path}")
        return False
    
    df_csv = pd.read_csv(csv_path)
    print(f"✅ CSV chargé : {len(df_csv)} lignes")
    print()
    
    # Normaliser
    df_normalized = normalize_csv_to_db_format(df_csv)
    
    # Mettre à jour
    count = update_event_families(df_normalized)
    
    # Valider
    success = validate_update()
    
    # Résumé
    print("="*80)
    print("RÉSUMÉ")
    print("="*80)
    print()
    
    if success:
        print("🎉 MISE À JOUR RÉUSSIE ✅")
        print(f"   {count:,} scores mis à jour")
        if backup_name:
            print(f"   Backup : {backup_name}")
        print()
        print("🎯 PROCHAINE ÉTAPE :")
        print("   Retester validation mapping Session 127")
        print("   → python validate_mapping_s127.py")
        print()
        print("   ATTENDU : Scores identiques LEFT JOIN = Mapping")
    else:
        print("❌ MISE À JOUR ÉCHOUÉE")
        print("   Restaurer backup si nécessaire")
    
    print()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
