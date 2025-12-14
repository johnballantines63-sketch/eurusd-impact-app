#!/usr/bin/env python3
"""
Script de validation import Dukascopy - Session 25
Vérifie que l'import est terminé et valide le cas du 11 septembre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path

def get_db_path():
    """Retourne le chemin de la base de données"""
    return Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"

def main():
    print("=" * 80)
    print("🔍 VALIDATION IMPORT DUKASCOPY - SESSION 25")
    print("=" * 80)
    
    db_path = get_db_path()
    if not db_path.exists():
        print(f"❌ ERREUR: Base de données non trouvée: {db_path}")
        return
    
    con = duckdb.connect(str(db_path))
    
    # 1. Compter total de lignes
    print("\n📊 STATISTIQUES GÉNÉRALES")
    print("-" * 80)
    
    count_query = "SELECT COUNT(*) as count FROM prices_1m"
    total_rows = con.execute(count_query).fetchone()[0]
    print(f"Total lignes prices_1m: {total_rows:,}")
    
    # 2. Vérifier période couverte
    stats_query = """
        SELECT 
            MIN(datetime) as min_date,
            MAX(datetime) as max_date,
            COUNT(DISTINCT DATE(datetime)) as days
        FROM prices_1m
    """
    
    stats = con.execute(stats_query).df().iloc[0]
    print(f"\n📅 Période couverte:")
    print(f"   Début    : {stats['min_date']}")
    print(f"   Fin      : {stats['max_date']}")
    print(f"   Jours    : {stats['days']}")
    
    # Estimer si complet (3 ans × 365 jours × ~1440 min/jour = ~1.5M lignes)
    expected_rows = 3 * 365 * 1440 * 0.7  # 70% du temps (marchés fermés week-end)
    print(f"\n   Attendu  : ~{expected_rows:,.0f} lignes (3 ans de données)")
    print(f"   Actuel   : {total_rows:,} lignes")
    
    if total_rows > expected_rows * 0.8:
        print(f"   ✅ Import semble complet (>{expected_rows*0.8:,.0f} lignes)")
    else:
        print(f"   ⚠️  Import peut-être incomplet (<{expected_rows*0.8:,.0f} lignes)")
    
    # 3. VALIDATION CRITIQUE: 11 septembre 2025 à 12:30 UTC (14:30 Berne)
    print("\n" + "=" * 80)
    print("🔍 VALIDATION CRITIQUE - 11 SEPTEMBRE 2025")
    print("=" * 80)
    print("\nCas de référence validé par graphiques MT5 d'André:")
    print("   Date     : 11 septembre 2025")
    print("   Heure    : 12:30 UTC (14:30 Berne CEST)")
    print("   Phase 1  : ~617 pips (12:30 → 12:35 UTC)")
    print("   Attendu  : >= 400 pips (critère validation)")
    
    validation_query = """
        SELECT datetime, open, high, low, close
        FROM prices_1m
        WHERE datetime >= '2025-09-11 12:30:00'
          AND datetime < '2025-09-11 12:45:00'
        ORDER BY datetime
    """
    
    df = con.execute(validation_query).df()
    
    if df.empty:
        print("\n❌ ERREUR CRITIQUE: Aucune donnée pour 11 septembre 12:30 UTC")
        print("   → L'import Dukascopy n'est pas terminé ou a échoué")
        print("   → Vérifier logs import_dukascopy_session24.py")
        con.close()
        return
    
    print(f"\n📊 Données trouvées: {len(df)} lignes (12:30 → 12:45 UTC)")
    
    # Afficher quelques lignes pour debug
    print("\n📋 Aperçu données (premières 3 lignes):")
    print(df.head(3).to_string(index=False))
    
    # Calculer Phase 1 (mouvement sur 15 minutes)
    print("\n" + "-" * 80)
    print("📈 CALCUL PHASE 1")
    print("-" * 80)
    
    start_price = df.iloc[0]['close']
    high = df['high'].max()
    low = df['low'].min()
    
    move_up = (high - start_price) * 10000
    move_down = (start_price - low) * 10000
    phase1_pips = max(move_up, move_down)
    direction = "UP" if move_up > move_down else "DOWN"
    
    print(f"\nPrix départ (12:30:00) : {start_price:.5f}")
    print(f"High période (12:30-12:45) : {high:.5f}")
    print(f"Low période (12:30-12:45)  : {low:.5f}")
    print(f"\nMouvement UP   : {move_up:.2f} pips")
    print(f"Mouvement DOWN : {move_down:.2f} pips")
    print(f"\n{'='*80}")
    print(f"📊 PHASE 1 CALCULÉE: {phase1_pips:.2f} pips ({direction})")
    print(f"🎯 ATTENDU: ~600 pips (critère validation: >= 400 pips)")
    print(f"{'='*80}")
    
    # Validation
    if phase1_pips >= 400:
        print("\n✅ ✅ ✅ VALIDATION RÉUSSIE ✅ ✅ ✅")
        print("\nDukascopy capte correctement les mouvements!")
        print("→ On peut continuer avec:")
        print("   1. Recalcul des 944 cas extrêmes")
        print("   2. Création de la formule V4")
        print("   3. Implémentation dans le planificateur")
    elif phase1_pips >= 200:
        print("\n⚠️ VALIDATION PARTIELLE")
        print(f"\nPhase 1 = {phase1_pips:.2f} pips (attendu ~600 pips)")
        print("→ Dukascopy sous-estime mais capte une partie du mouvement")
        print("→ Meilleur que EODHD (36 pips) et HistData (1.8 pips)")
        print("→ Peut nécessiter facteur de correction")
    else:
        print("\n❌ VALIDATION ÉCHOUÉE")
        print(f"\nPhase 1 = {phase1_pips:.2f} pips (attendu >= 400 pips)")
        print("→ Mouvement trop faible, investigation nécessaire")
        print("→ Vérifier:")
        print("   - Décalage horaire (14:30 Berne = 12:30 UTC ?)")
        print("   - Qualité import Dukascopy")
        print("   - Scanner toute la journée du 11 septembre")
    
    # Détails supplémentaires pour analyse
    print("\n" + "=" * 80)
    print("📊 DÉTAILS MINUTE PAR MINUTE (12:30 → 12:35)")
    print("=" * 80)
    
    df_5min = df[df['datetime'] <= '2025-09-11 12:35:00']
    for idx, row in df_5min.iterrows():
        time = row['datetime'].strftime('%H:%M:%S')
        range_pips = (row['high'] - row['low']) * 10000
        close_move = (row['close'] - start_price) * 10000
        print(f"{time}: Close={row['close']:.5f} | Range={range_pips:.1f}p | Move={close_move:+.1f}p")
    
    con.close()
    
    print("\n" + "=" * 80)
    print("Fin validation")
    print("=" * 80)

if __name__ == "__main__":
    main()
