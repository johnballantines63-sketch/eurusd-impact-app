#!/usr/bin/env python3
"""
SESSION 126 - INVENTAIRE COMPLET BASE DE DONNÉES
=================================================
Analyse EXHAUSTIVE de TOUS les événements dans la DB

Objectifs:
1. Inventorier TOUT ce qui existe dans events (tous pays, tous event_keys)
2. Comparer avec scores CSV disponibles
3. Identifier données manquantes (pour réimport si nécessaire)
4. Vérifier complétude import JBlanked API

Perspective: Développement futur sur toutes devises (EUR, GBP, JPY, etc.)
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd
from collections import defaultdict

print("=" * 80)
print("INVENTAIRE COMPLET : BASE DE DONNÉES EVENTS")
print("=" * 80)
print()

# Configuration
DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
SCORES_PATH = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
OUTPUT_PATH = Path(__file__).parent / "db_inventory_complete.txt"

print(f"📁 Database : {DB_PATH}")
print(f"📊 Scores   : {SCORES_PATH}")
print(f"📄 Output   : {OUTPUT_PATH}")
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# ============================================================================
# PARTIE 1 : INVENTAIRE COMPLET DB
# ============================================================================

print("=" * 80)
print("PARTIE 1 : INVENTAIRE COMPLET BASE DE DONNÉES")
print("=" * 80)
print()

# Statistiques globales DB
query_global = """
SELECT 
    COUNT(*) as total_events,
    COUNT(DISTINCT country) as unique_countries,
    COUNT(DISTINCT event_key) as unique_event_keys,
    MIN(ts_utc) as first_date,
    MAX(ts_utc) as last_date
FROM events
"""

stats_global = conn.execute(query_global).fetchone()
total_events, unique_countries, unique_event_keys, first_date, last_date = stats_global

print(f"📊 STATISTIQUES GLOBALES DB :")
print(f"   Total événements     : {total_events:,}")
print(f"   Pays uniques         : {unique_countries}")
print(f"   Event keys uniques   : {unique_event_keys:,}")
print(f"   Période couverte     : {first_date.strftime('%Y-%m-%d')} → {last_date.strftime('%Y-%m-%d')}")
print()

# Liste pays
query_countries = """
SELECT 
    country,
    COUNT(*) as count,
    COUNT(DISTINCT event_key) as unique_events
FROM events
GROUP BY country
ORDER BY count DESC
"""

df_countries = conn.execute(query_countries).df()

print(f"📋 PAYS DANS LA DB ({len(df_countries)}) :")
print()
for _, row in df_countries.iterrows():
    print(f"   {row['country']:4s} : {row['count']:7,} événements | {row['unique_events']:4d} event_keys uniques")
print()

# ============================================================================
# PARTIE 2 : DÉTAILS PAR PAYS
# ============================================================================

print("=" * 80)
print("PARTIE 2 : ANALYSE DÉTAILLÉE PAR PAYS")
print("=" * 80)
print()

# Mapping country code → currency
COUNTRY_TO_CURRENCY = {
    'US': 'usd',
    'GB': 'gbp',
    'JP': 'jpy',
    'CH': 'chf',
    'DE': 'eur',
    'FR': 'eur',
    'IT': 'eur',
    'ES': 'eur',
    'CA': 'cad',
    'AU': 'aud',
    'NZ': 'nzd'
}

country_details = {}

for _, country_row in df_countries.iterrows():
    country_code = country_row['country']
    
    print(f"[{country_code}] Analyse en cours...", end=' ')
    
    # Détails par importance
    query_importance = """
    SELECT 
        importance_n,
        COUNT(*) as count,
        COUNT(DISTINCT event_key) as unique_events
    FROM events
    WHERE country = ?
    GROUP BY importance_n
    ORDER BY importance_n DESC
    """
    
    df_imp = conn.execute(query_importance, [country_code]).df()
    
    # Top event_keys par importance
    query_top_events = """
    SELECT 
        event_key,
        importance_n,
        COUNT(*) as count,
        MIN(ts_utc) as first_date,
        MAX(ts_utc) as last_date
    FROM events
    WHERE country = ?
    GROUP BY event_key, importance_n
    ORDER BY importance_n DESC, count DESC
    """
    
    df_events = conn.execute(query_top_events, [country_code]).df()
    
    country_details[country_code] = {
        'total': country_row['count'],
        'unique_events': country_row['unique_events'],
        'by_importance': df_imp,
        'all_events': df_events
    }
    
    print(f"✅ ({len(df_events)} event_keys)")

print()

# ============================================================================
# PARTIE 3 : COMPARAISON AVEC SCORES CSV
# ============================================================================

print("=" * 80)
print("PARTIE 3 : COMPARAISON DB ↔ SCORES CSV")
print("=" * 80)
print()

df_scores = pd.read_csv(SCORES_PATH)

print(f"📊 Scores CSV : {len(df_scores)} scores")
print(f"   Pays : {', '.join(sorted(df_scores['country'].unique()))}")
print()

# Mapping inverse : currency → country
CURRENCY_TO_COUNTRY = {v: k for k, v in COUNTRY_TO_CURRENCY.items()}

# Pour chaque currency dans scores, vérifier disponibilité DB
scores_coverage = {}

for currency in df_scores['country'].unique():
    country_code = CURRENCY_TO_COUNTRY.get(currency, currency.upper())
    
    scores_currency = df_scores[df_scores['country'] == currency]
    
    if country_code in country_details:
        db_events = country_details[country_code]['unique_events']
        scores_count = len(scores_currency)
        
        scores_coverage[currency] = {
            'country_code': country_code,
            'db_events': db_events,
            'scores_count': scores_count,
            'coverage_pct': (scores_count / db_events * 100) if db_events > 0 else 0
        }
    else:
        scores_coverage[currency] = {
            'country_code': country_code,
            'db_events': 0,
            'scores_count': len(scores_currency),
            'coverage_pct': 0
        }

print("📊 COUVERTURE SCORES PAR PAYS :")
print()
print(f"{'Currency':<10} {'Country':<8} {'DB Events':<12} {'Scores CSV':<12} {'Coverage':<10}")
print("-" * 70)

for currency in sorted(scores_coverage.keys()):
    cov = scores_coverage[currency]
    print(f"{currency:<10} {cov['country_code']:<8} {cov['db_events']:>10,}  {cov['scores_count']:>10,}  {cov['coverage_pct']:>8.1f}%")

print()

# ============================================================================
# PARTIE 4 : ÉVÉNEMENTS DB SANS SCORES
# ============================================================================

print("=" * 80)
print("PARTIE 4 : ÉVÉNEMENTS DB SANS SCORES (Manquants)")
print("=" * 80)
print()

print("Analyse événements présents dans DB mais SANS score CSV...")
print()

missing_scores_summary = {}

for country_code, details in country_details.items():
    currency = COUNTRY_TO_CURRENCY.get(country_code, country_code.lower())
    
    # Event_keys dans DB
    db_event_keys = set(details['all_events']['event_key'].unique())
    
    # Event_names dans scores (convertir en event_keys)
    scores_currency = df_scores[df_scores['country'] == currency]
    scores_event_keys = set(scores_currency['event_name'].str.replace('_', ' '))
    
    # Manquants
    missing = db_event_keys - scores_event_keys
    
    if missing:
        missing_scores_summary[country_code] = {
            'currency': currency,
            'missing_count': len(missing),
            'missing_events': missing,
            'total_db_events': len(db_event_keys)
        }

print(f"📊 RÉSUMÉ ÉVÉNEMENTS SANS SCORES :")
print()

for country_code in sorted(missing_scores_summary.keys(), key=lambda x: missing_scores_summary[x]['missing_count'], reverse=True):
    miss = missing_scores_summary[country_code]
    print(f"   {country_code} ({miss['currency']}) : {miss['missing_count']:4d} événements sans scores ({miss['missing_count']/miss['total_db_events']*100:.1f}%)")

print()

# ============================================================================
# GÉNÉRATION RAPPORT COMPLET
# ============================================================================

print("=" * 80)
print("GÉNÉRATION RAPPORT DÉTAILLÉ")
print("=" * 80)
print()

report = []

report.append("=" * 80)
report.append("INVENTAIRE COMPLET : BASE DE DONNÉES EVENTS")
report.append("=" * 80)
report.append("")
report.append(f"Date : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append(f"Database : {DB_PATH.name}")
report.append("")

# PARTIE 1 : Statistiques globales
report.append("=" * 80)
report.append("PARTIE 1 : STATISTIQUES GLOBALES")
report.append("=" * 80)
report.append("")
report.append(f"Total événements     : {total_events:,}")
report.append(f"Pays uniques         : {unique_countries}")
report.append(f"Event keys uniques   : {unique_event_keys:,}")
report.append(f"Période              : {first_date.strftime('%Y-%m-%d')} → {last_date.strftime('%Y-%m-%d')}")
report.append("")

# PARTIE 2 : Détails par pays
report.append("=" * 80)
report.append("PARTIE 2 : ANALYSE PAR PAYS")
report.append("=" * 80)
report.append("")

for country_code in sorted(country_details.keys()):
    details = country_details[country_code]
    currency = COUNTRY_TO_CURRENCY.get(country_code, country_code.lower())
    
    report.append("-" * 80)
    report.append(f"PAYS : {country_code} (currency: {currency})")
    report.append("-" * 80)
    report.append("")
    report.append(f"Total événements  : {details['total']:,}")
    report.append(f"Event keys uniques: {details['unique_events']:,}")
    report.append("")
    
    # Par importance
    report.append("Distribution par importance :")
    for _, imp_row in details['by_importance'].iterrows():
        imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(imp_row['importance_n'], "?")
        report.append(f"  {imp_label:4s} ({imp_row['importance_n']}) : {imp_row['count']:6,} événements | {imp_row['unique_events']:4d} event_keys")
    report.append("")
    
    # Top 20 event_keys
    report.append("Top 20 event_keys (par importance) :")
    top_20 = details['all_events'].head(20)
    for idx, event_row in top_20.iterrows():
        imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(event_row['importance_n'], "?")
        report.append(f"  [{imp_label}] '{event_row['event_key']:<50s}' : {event_row['count']:4d} events | {event_row['first_date'].strftime('%Y-%m-%d')} → {event_row['last_date'].strftime('%Y-%m-%d')}")
    
    if len(details['all_events']) > 20:
        report.append(f"  ... et {len(details['all_events']) - 20} autres event_keys")
    
    report.append("")

# PARTIE 3 : Couverture scores
report.append("=" * 80)
report.append("PARTIE 3 : COUVERTURE SCORES CSV")
report.append("=" * 80)
report.append("")
report.append(f"{'Currency':<10} {'Country':<8} {'DB Events':<12} {'Scores CSV':<12} {'Coverage':<10}")
report.append("-" * 70)

for currency in sorted(scores_coverage.keys()):
    cov = scores_coverage[currency]
    report.append(f"{currency:<10} {cov['country_code']:<8} {cov['db_events']:>10,}  {cov['scores_count']:>10,}  {cov['coverage_pct']:>8.1f}%")

report.append("")

# PARTIE 4 : Événements sans scores
report.append("=" * 80)
report.append("PARTIE 4 : ÉVÉNEMENTS DB SANS SCORES")
report.append("=" * 80)
report.append("")

if missing_scores_summary:
    for country_code in sorted(missing_scores_summary.keys()):
        miss = missing_scores_summary[country_code]
        
        report.append("-" * 80)
        report.append(f"{country_code} ({miss['currency']}) : {miss['missing_count']} événements sans scores")
        report.append("-" * 80)
        report.append("")
        
        # Lister événements manquants (triés par fréquence)
        events_missing = details['all_events'][details['all_events']['event_key'].isin(miss['missing_events'])]
        events_missing_sorted = events_missing.sort_values('count', ascending=False)
        
        for idx, event_row in events_missing_sorted.iterrows():
            imp_label = {1: "LOW", 2: "MED", 3: "HIGH"}.get(event_row['importance_n'], "?")
            report.append(f"  [{imp_label}] '{event_row['event_key']:<50s}' : {event_row['count']:4d} events")
        
        report.append("")
else:
    report.append("✅ Tous les événements DB ont des scores correspondants")
    report.append("")

# PARTIE 5 : Recommandations
report.append("=" * 80)
report.append("PARTIE 5 : RECOMMANDATIONS")
report.append("=" * 80)
report.append("")

# Calcul complétude
total_db_events_all = sum([d['unique_events'] for d in country_details.values()])
total_scores_all = len(df_scores)
coverage_global = (total_scores_all / total_db_events_all * 100) if total_db_events_all > 0 else 0

report.append(f"Complétude globale : {coverage_global:.1f}% ({total_scores_all}/{total_db_events_all} événements)")
report.append("")

if coverage_global >= 80:
    report.append("✅ BONNE COUVERTURE (>80%)")
    report.append("")
    report.append("Actions :")
    report.append("  1. Utiliser scores existants pour pipeline")
    report.append("  2. Recalculer scores manquants si nécessaires pour développement futur")
elif coverage_global >= 50:
    report.append("⚠️  COUVERTURE PARTIELLE (50-80%)")
    report.append("")
    report.append("Actions :")
    report.append("  1. Priorité : Recalculer scores pour événements HIGH manquants")
    report.append("  2. Session 127 : Recalibration scores majeurs pays (USD, EUR)")
    report.append("  3. Développement futur : Compléter autres devises")
else:
    report.append("❌ COUVERTURE INSUFFISANTE (<50%)")
    report.append("")
    report.append("Actions URGENTES :")
    report.append("  1. Session dédiée : Recalcul COMPLET tous scores")
    report.append("  2. Vérifier intégrité import JBlanked API")
    report.append("  3. Validation méthodologie calcul empirique")

report.append("")

# Sauvegarde
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print(f"💾 Rapport sauvegardé : {OUTPUT_PATH.name}")
print()

# Affichage résumé
print("=" * 80)
print("RÉSUMÉ FINAL")
print("=" * 80)
print()
print(f"📊 Base de données : {total_events:,} événements | {unique_event_keys:,} event_keys | {unique_countries} pays")
print(f"📊 Scores CSV      : {len(df_scores)} scores")
print(f"📊 Complétude      : {coverage_global:.1f}%")
print()

if missing_scores_summary:
    total_missing = sum([m['missing_count'] for m in missing_scores_summary.values()])
    print(f"⚠️  {total_missing:,} événements DB sans scores")
    print()
    print("Top 5 pays avec scores manquants :")
    for country_code in sorted(missing_scores_summary.keys(), key=lambda x: missing_scores_summary[x]['missing_count'], reverse=True)[:5]:
        miss = missing_scores_summary[country_code]
        print(f"   {country_code} : {miss['missing_count']:4d} événements manquants")
else:
    print("✅ Aucun événement manquant - Couverture complète !")

print()
print(f"📄 Rapport détaillé : {OUTPUT_PATH}")
print()

conn.close()

print("=" * 80)
print("INVENTAIRE TERMINÉ")
print("=" * 80)

# Exit code
if coverage_global >= 80:
    sys.exit(0)
elif coverage_global >= 50:
    sys.exit(1)
else:
    sys.exit(2)
