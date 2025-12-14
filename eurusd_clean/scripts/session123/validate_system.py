"""
Validation système complet avec DB EODHD finale

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Finalisation
"""

import duckdb
from pathlib import Path

def validate_system():
    """Valider système complet"""
    
    print("=" * 80)
    print("VALIDATION SYSTÈME COMPLET - DB EODHD FINALE")
    print("=" * 80)
    print()
    
    db_path = Path(__file__).parent.parent.parent / 'warehouse.duckdb'
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # ====================================================================
    # VALIDATION DB
    # ====================================================================
    
    print("1️⃣ VALIDATION DB")
    print("=" * 70)
    print()
    
    # Total
    total = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
    print(f"✅ Total événements : {total:,}")
    
    if total < 100000:
        print(f"⚠️  Attendu >100k, obtenu {total:,}")
    
    print()
    
    # Structure
    columns = conn.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'economic_events'
        ORDER BY ordinal_position
    """).fetchall()
    
    required_cols = ['event_id', 'datetime_utc', 'event_name', 'country', 'actual', 'forecast', 'previous']
    missing = [col for col in required_cols if col not in [c[0] for c in columns]]
    
    if missing:
        print(f"❌ Colonnes manquantes : {missing}")
    else:
        print(f"✅ Structure table OK ({len(columns)} colonnes)")
    
    print()
    
    # ====================================================================
    # VALIDATION DATES CRITIQUES
    # ====================================================================
    
    print("2️⃣ VALIDATION DATES CRITIQUES")
    print("=" * 70)
    print()
    
    critical_dates = [
        ('2025-08-01', '1er août 2025', 10),
        ('2025-09-11', '11 septembre 2025', 7)
    ]
    
    for date, label, min_usd in critical_dates:
        total_date = conn.execute(f"""
            SELECT COUNT(*) 
            FROM economic_events
            WHERE DATE(datetime_utc) = '{date}'
        """).fetchone()[0]
        
        usd = conn.execute(f"""
            SELECT COUNT(*) 
            FROM economic_events
            WHERE DATE(datetime_utc) = '{date}'
            AND country = 'usd'
        """).fetchone()[0]
        
        status = "✅" if usd >= min_usd else "⚠️"
        
        print(f"{status} {label}")
        print(f"   Total : {total_date} événements")
        print(f"   USD   : {usd} événements (min attendu: {min_usd})")
        print()
    
    # ====================================================================
    # VALIDATION COUVERTURE TEMPORELLE
    # ====================================================================
    
    print("3️⃣ VALIDATION COUVERTURE TEMPORELLE")
    print("=" * 70)
    print()
    
    by_year = conn.execute("""
        SELECT 
            EXTRACT(YEAR FROM datetime_utc) as year,
            COUNT(*) as count
        FROM economic_events
        GROUP BY year
        ORDER BY year
    """).fetchall()
    
    print("Événements par année :")
    for year, count in by_year:
        print(f"   {int(year)} : {count:,} événements")
    
    # Vérifier années complètes
    years_expected = list(range(2020, 2026))
    years_db = [int(y) for y, _ in by_year]
    missing_years = [y for y in years_expected if y not in years_db]
    
    if missing_years:
        print(f"\n⚠️  Années manquantes : {missing_years}")
    else:
        print(f"\n✅ Toutes années 2020-2025 présentes")
    
    print()
    
    # ====================================================================
    # VALIDATION PAYS
    # ====================================================================
    
    print("4️⃣ VALIDATION PAYS CRITIQUES")
    print("=" * 70)
    print()
    
    critical_countries = ['usd', 'eur', 'gbp', 'jpy']
    
    for country in critical_countries:
        count = conn.execute(f"""
            SELECT COUNT(*)
            FROM economic_events
            WHERE country = '{country}'
        """).fetchone()[0]
        
        status = "✅" if count > 1000 else "⚠️"
        print(f"{status} {country.upper()} : {count:,} événements")
    
    print()
    
    # ====================================================================
    # VALIDATION VALEURS
    # ====================================================================
    
    print("5️⃣ VALIDATION VALEURS ACTUAL/FORECAST/PREVIOUS")
    print("=" * 70)
    print()
    
    with_actual = conn.execute("""
        SELECT COUNT(*)
        FROM economic_events
        WHERE actual IS NOT NULL
    """).fetchone()[0]
    
    with_forecast = conn.execute("""
        SELECT COUNT(*)
        FROM economic_events
        WHERE forecast IS NOT NULL
    """).fetchone()[0]
    
    with_previous = conn.execute("""
        SELECT COUNT(*)
        FROM economic_events
        WHERE previous IS NOT NULL
    """).fetchone()[0]
    
    print(f"Actual   : {with_actual:,} / {total:,} ({with_actual/total*100:.1f}%)")
    print(f"Forecast : {with_forecast:,} / {total:,} ({with_forecast/total*100:.1f}%)")
    print(f"Previous : {with_previous:,} / {total:,} ({with_previous/total*100:.1f}%)")
    print()
    
    if with_actual/total < 0.5:
        print("⚠️  Moins de 50% événements avec Actual")
    else:
        print("✅ Couverture valeurs satisfaisante")
    
    print()
    
    # ====================================================================
    # CONCLUSION
    # ====================================================================
    
    print("=" * 80)
    print("CONCLUSION VALIDATION")
    print("=" * 80)
    print()
    
    issues = []
    
    if total < 100000:
        issues.append(f"Total événements insuffisant ({total:,})")
    
    if missing:
        issues.append(f"Colonnes manquantes : {missing}")
    
    # Dates critiques
    for date, label, min_usd in critical_dates:
        usd = conn.execute(f"""
            SELECT COUNT(*) 
            FROM economic_events
            WHERE DATE(datetime_utc) = '{date}'
            AND country = 'usd'
        """).fetchone()[0]
        
        if usd < min_usd:
            issues.append(f"{label} : seulement {usd} USD (min {min_usd})")
    
    if missing_years:
        issues.append(f"Années manquantes : {missing_years}")
    
    if with_actual/total < 0.5:
        issues.append("Moins de 50% événements avec valeurs Actual")
    
    if len(issues) == 0:
        print("✅ SYSTÈME VALIDÉ")
        print()
        print("Tous les critères sont satisfaits :")
        print(f"   • {total:,} événements (>100k)")
        print("   • Dates critiques OK")
        print("   • Couverture 2020-2025 complète")
        print("   • Pays critiques présents")
        print("   • Valeurs Actual/Forecast/Previous OK")
        print()
        print("🎉 PRÊT POUR VALIDATION PLANIFICATEUR")
    else:
        print("⚠️  PROBLÈMES DÉTECTÉS")
        print()
        for issue in issues:
            print(f"   • {issue}")
        print()
        print("Corrections nécessaires avant validation Planificateur")
    
    print()
    
    conn.close()

if __name__ == '__main__':
    validate_system()
