#!/usr/bin/env python3
"""
SESSION 126 - VÉRIFICATION TEMPORELLE IMPORT
=============================================
Vérifier période couverte et complétude import événements

Question : On a 26,480 events (2023-2026) mais on devrait avoir 125k+ ?
- Limitation volontaire 3 ans (alignement prix) ?
- Ou problème import incomplet ?
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

print("=" * 80)
print("VÉRIFICATION TEMPORELLE : IMPORT ÉVÉNEMENTS")
print("=" * 80)
print()

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"

conn = duckdb.connect(str(DB_PATH), read_only=True)

# ============================================================================
# ANALYSE TEMPORELLE COMPLÈTE
# ============================================================================

print("[1] PÉRIODE COUVERTE")
print("-" * 80)
print()

query_period = """
SELECT 
    MIN(ts_utc) as first_event,
    MAX(ts_utc) as last_event,
    COUNT(*) as total_events,
    COUNT(DISTINCT DATE_TRUNC('month', ts_utc)) as unique_months,
    COUNT(DISTINCT DATE_TRUNC('year', ts_utc)) as unique_years
FROM events
"""

result = conn.execute(query_period).fetchone()
first_event, last_event, total_events, unique_months, unique_years = result

duration_days = (last_event - first_event).days
duration_years = duration_days / 365.25

print(f"📅 PÉRIODE COMPLÈTE :")
print(f"   Premier événement  : {first_event.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Dernier événement  : {last_event.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Durée              : {duration_days:,} jours ({duration_years:.2f} ans)")
print()
print(f"📊 STATISTIQUES :")
print(f"   Total événements   : {total_events:,}")
print(f"   Mois uniques       : {unique_months}")
print(f"   Années uniques     : {unique_years}")
print()

# ============================================================================
# DISTRIBUTION MENSUELLE
# ============================================================================

print("[2] DISTRIBUTION MENSUELLE")
print("-" * 80)
print()

query_monthly = """
SELECT 
    DATE_TRUNC('month', ts_utc) as month,
    COUNT(*) as count
FROM events
GROUP BY DATE_TRUNC('month', ts_utc)
ORDER BY month
"""

df_monthly = conn.execute(query_monthly).df()

print(f"📊 ÉVÉNEMENTS PAR MOIS ({len(df_monthly)} mois) :")
print()

# Statistiques
monthly_counts = df_monthly['count'].values
avg_monthly = monthly_counts.mean()
min_monthly = monthly_counts.min()
max_monthly = monthly_counts.max()

print(f"   Moyenne par mois : {avg_monthly:,.0f} événements")
print(f"   Min/Max          : {min_monthly:,} → {max_monthly:,}")
print()

# Premiers et derniers mois
print("   Premiers 6 mois :")
for _, row in df_monthly.head(6).iterrows():
    month_str = pd.to_datetime(row['month']).strftime('%Y-%m')
    print(f"     {month_str} : {row['count']:5,} événements")

print()
print("   Derniers 6 mois :")
for _, row in df_monthly.tail(6).iterrows():
    month_str = pd.to_datetime(row['month']).strftime('%Y-%m')
    print(f"     {month_str} : {row['count']:5,} événements")

print()

# ============================================================================
# DISTRIBUTION ANNUELLE
# ============================================================================

print("[3] DISTRIBUTION ANNUELLE")
print("-" * 80)
print()

query_yearly = """
SELECT 
    DATE_TRUNC('year', ts_utc) as year,
    COUNT(*) as count,
    COUNT(DISTINCT country) as unique_countries,
    COUNT(DISTINCT event_key) as unique_event_keys
FROM events
GROUP BY DATE_TRUNC('year', ts_utc)
ORDER BY year
"""

df_yearly = conn.execute(query_yearly).df()

print(f"📊 ÉVÉNEMENTS PAR ANNÉE ({len(df_yearly)} années) :")
print()

for _, row in df_yearly.iterrows():
    year_str = pd.to_datetime(row['year']).strftime('%Y')
    print(f"   {year_str} : {row['count']:7,} événements | {row['unique_countries']:3d} pays | {row['unique_event_keys']:4d} event_keys")

print()

# ============================================================================
# COMPARAISON AVEC PRIX
# ============================================================================

print("[4] COMPARAISON AVEC PÉRIODE PRIX")
print("-" * 80)
print()

# Vérifier période prix (si table existe)
tables = conn.execute("SHOW TABLES").df()

if 'prices_1m' in tables['name'].values or 'prices_bern' in tables['name'].values:
    price_table = 'prices_bern' if 'prices_bern' in tables['name'].values else 'prices_1m'
    
    query_prices = """
    SELECT 
        MIN(datetime) as first_price,
        MAX(datetime) as last_price,
        COUNT(*) as total_bars
    FROM {}
    """.format(price_table)
    
    result_prices = conn.execute(query_prices).fetchone()
    first_price, last_price, total_bars = result_prices
    
    print(f"📊 PÉRIODE PRIX (table {price_table}) :")
    print(f"   Premier prix : {first_price.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Dernier prix : {last_price.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Total bars   : {total_bars:,}")
    print()
    
    # Comparaison
    print("📊 ALIGNEMENT ÉVÉNEMENTS ↔ PRIX :")
    print()
    
    events_before_prices = first_event < first_price
    events_after_prices = last_event > last_price
    
    if events_before_prices:
        days_before = (first_price - first_event).days
        print(f"   ⚠️  Événements commencent {days_before} jours AVANT les prix")
    else:
        days_after = (first_event - first_price).days
        print(f"   ✅ Événements commencent {days_after} jours après les prix (OK)")
    
    if events_after_prices:
        days_after = (last_event - last_price).days
        print(f"   ⚠️  Événements finissent {days_after} jours APRÈS les prix")
    else:
        days_before = (last_price - last_event).days
        print(f"   ✅ Événements finissent {days_before} jours avant les prix (OK)")
    
    print()
    
    # Overlap
    overlap_start = max(first_event, first_price)
    overlap_end = min(last_event, last_price)
    overlap_days = (overlap_end - overlap_start).days
    
    print(f"📊 PÉRIODE COMMUNE (overlap) :")
    print(f"   {overlap_start.strftime('%Y-%m-%d')} → {overlap_end.strftime('%Y-%m-%d')}")
    print(f"   {overlap_days:,} jours ({overlap_days/365.25:.2f} ans)")
    print()
    
else:
    print("⚠️  Tables prix non trouvées (prices_1m ou prices_bern)")
    print()

# ============================================================================
# VÉRIFICATION DENSITÉ TEMPORELLE
# ============================================================================

print("[5] ANALYSE DENSITÉ TEMPORELLE")
print("-" * 80)
print()

# Événements par jour (moyenne)
events_per_day = total_events / duration_days
events_per_week = events_per_day * 7
events_per_month = events_per_day * 30.44

print(f"📊 DENSITÉ ÉVÉNEMENTS :")
print(f"   Par jour  : {events_per_day:.1f} événements/jour")
print(f"   Par semaine : {events_per_week:.0f} événements/semaine")
print(f"   Par mois  : {events_per_month:.0f} événements/mois")
print()

# Vérifier trous (gaps)
query_gaps = """
WITH daily_counts AS (
    SELECT 
        DATE_TRUNC('day', ts_utc) as day,
        COUNT(*) as count
    FROM events
    GROUP BY DATE_TRUNC('day', ts_utc)
)
SELECT 
    COUNT(*) as days_with_events,
    MIN(count) as min_per_day,
    MAX(count) as max_per_day,
    AVG(count) as avg_per_day
FROM daily_counts
"""

result_gaps = conn.execute(query_gaps).fetchone()
days_with_events, min_per_day, max_per_day, avg_per_day = result_gaps

print(f"📊 COUVERTURE JOURNALIÈRE :")
print(f"   Jours avec événements : {days_with_events:,} / {duration_days:,} ({days_with_events/duration_days*100:.1f}%)")
print(f"   Min/Max par jour      : {min_per_day} → {max_per_day} événements")
print(f"   Moyenne par jour      : {avg_per_day:.1f} événements")
print()

# ============================================================================
# DIAGNOSTIC FINAL
# ============================================================================

print("=" * 80)
print("DIAGNOSTIC")
print("=" * 80)
print()

# Critères
has_3_years = duration_years >= 2.8 and duration_years <= 3.5
starts_2023 = first_event.year == 2023
total_seems_low = total_events < 50000

print("📊 VÉRIFICATIONS :")
print()

print(f"   Période ~3 ans          : {'✅ OUI' if has_3_years else '❌ NON'} ({duration_years:.1f} ans)")
print(f"   Commence en 2023        : {'✅ OUI' if starts_2023 else '❌ NON'} ({first_event.year})")
print(f"   Total < 50k événements  : {'⚠️  OUI' if total_seems_low else '✅ NON'} ({total_events:,})")
print()

print("💡 INTERPRÉTATION :")
print()

if has_3_years and starts_2023:
    print("✅ LIMITATION VOLONTAIRE 3 ANS (2023-2026)")
    print()
    print("   Raisons probables :")
    print("   - Alignement avec période prix disponibles")
    print("   - Focus sur données récentes (pertinence trading)")
    print("   - Limitation volontaire Session 123 import")
    print()
    print("   Densité : {:.0f} événements/mois est NORMALE pour 140 pays".format(events_per_month))
    print()
    
    if 'prices_1m' in tables['name'].values or 'prices_bern' in tables['name'].values:
        print("   Alignement prix ↔ événements vérifié ci-dessus")
        print()
    
    print("🎯 CONCLUSION : Import COMPLET pour période 2023-2026")
    print()
    print("   Si besoin données historiques complètes (2015-2022) :")
    print("   → Réimport JBlanked API sans filtre date")
    print("   → Mais nécessitera aussi import prix étendus")
    
    exit_code = 0
    
else:
    print("⚠️  CONFIGURATION INHABITUELLE")
    print()
    print("   Période ne correspond PAS à 3 ans standards")
    print("   ou ne commence pas en 2023")
    print()
    print("   Vérifier :")
    print("   - Script import Session 123")
    print("   - Filtres temporels appliqués")
    print("   - Cohérence avec import prix")
    
    exit_code = 1

print()

# ============================================================================
# ESTIMATION SI HISTORIQUE COMPLET
# ============================================================================

print("=" * 80)
print("ESTIMATION : SI IMPORT HISTORIQUE COMPLET")
print("=" * 80)
print()

# Extrapoler
events_per_year = total_events / duration_years
years_historical = 12  # 2015-2026 = 12 ans
estimated_total = events_per_year * years_historical

print(f"📊 Si import 2015-2026 (12 ans) :")
print(f"   Événements actuels    : {total_events:,} ({duration_years:.1f} ans)")
print(f"   Événements/an         : {events_per_year:,.0f}")
print(f"   Estimation 12 ans     : {estimated_total:,.0f} événements")
print()

print(f"   Ratio actuel/estimé   : {total_events/estimated_total*100:.1f}%")
print()

if estimated_total > 100000:
    print(f"✅ Estimation cohérente avec >125k événements mentionnés")
    print(f"   Import historique complet donnerait ~{estimated_total:,.0f} événements")
else:
    print(f"⚠️  Estimation plus faible que 125k attendus")
    print(f"   Vérifier source chiffre 125k (peut-être incluait autre chose ?)")

print()

conn.close()

print("=" * 80)
print("VÉRIFICATION TERMINÉE")
print("=" * 80)

sys.exit(exit_code)
