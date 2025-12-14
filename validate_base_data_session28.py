#!/usr/bin/env python3
"""
SESSION 28 - VALIDATION DONNÉES DE BASE
Vérifie que les données prices_1m et events sont correctes
avant de recalculer quoi que ce soit.
"""

import duckdb
import pandas as pd
from datetime import datetime

print("=" * 80)
print("SESSION 28 - VALIDATION DONNÉES DE BASE")
print("=" * 80)

# Connexion DB
con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# ============================================================================
# 1. VÉRIFIER TABLES DISPONIBLES
# ============================================================================
print("\n1. TABLES DISPONIBLES")
print("-" * 80)
tables = con.execute("SHOW TABLES").fetchdf()
print(tables)

# ============================================================================
# 2. VÉRIFIER FORECAST DANS EVENTS
# ============================================================================
print("\n2. ÉTAT FORECAST/ESTIMATE DANS EVENTS")
print("-" * 80)
forecast_stats = con.execute("""
    SELECT 
        COUNT(*) as total_events,
        COUNT(actual) as with_actual,
        COUNT(forecast) as with_forecast,
        COUNT(estimate) as with_estimate,
        COUNT(previous) as with_previous,
        ROUND(100.0 * COUNT(forecast) / COUNT(*), 1) as pct_forecast,
        ROUND(100.0 * COUNT(estimate) / COUNT(*), 1) as pct_estimate
    FROM events
""").fetchdf()
print(forecast_stats)

if forecast_stats['pct_forecast'].iloc[0] < 40:
    print("\n⚠️  WARNING: Moins de 40% des événements ont forecast !")
    print("Session 27 devrait avoir corrigé cela.")
else:
    print(f"\n✅ OK: {forecast_stats['pct_forecast'].iloc[0]}% événements ont forecast")

# ============================================================================
# 3. CAS RÉFÉRENCE 11 SEPTEMBRE 2025
# ============================================================================
print("\n3. CAS RÉFÉRENCE 11 SEPTEMBRE 2025")
print("-" * 80)

# 3a. Événement dans events
print("\n3a. Événement Inflation Rate MoM (US)")
sept11_event = con.execute("""
    SELECT 
        ts_utc,
        event_key,
        event_title,
        country,
        actual,
        forecast,
        previous,
        CASE 
            WHEN forecast IS NOT NULL AND forecast != 0 
            THEN ROUND(ABS((actual - forecast) / forecast) * 100, 2)
            ELSE NULL
        END as surprise_pct
    FROM events
    WHERE ts_utc::DATE = '2025-09-11'
    AND country = 'US'
    AND event_title LIKE '%Inflation Rate%'
    AND event_title LIKE '%MoM%'
""").fetchdf()

if len(sept11_event) > 0:
    print(sept11_event)
    surprise = sept11_event['surprise_pct'].iloc[0]
    if surprise is not None and surprise > 30:
        print(f"\n✅ Surprise = {surprise}% (> 30%, OK)")
    else:
        print(f"\n⚠️  Surprise = {surprise}% (< 30%, PROBLÈME)")
else:
    print("❌ ERREUR: Événement 11 septembre introuvable !")

# 3b. Prix dans prices_1m
print("\n3b. Prix 11 septembre 12:25-12:35 UTC")
sept11_prices = con.execute("""
    SELECT 
        datetime,
        open,
        high,
        low,
        close,
        ROUND((high - low) * 10000, 2) as range_pips
    FROM prices_1m
    WHERE datetime >= '2025-09-11 12:25:00'
    AND datetime <= '2025-09-11 12:35:00'
    ORDER BY datetime
""").fetchdf()

if len(sept11_prices) > 0:
    print(sept11_prices)
    
    # Calcul Phase 1 manuel (5 premières minutes après 12:30)
    phase1_prices = sept11_prices[sept11_prices['datetime'] >= '2025-09-11 12:30:00'].head(5)
    if len(phase1_prices) > 0:
        start_price = phase1_prices.iloc[0]['open']
        max_price = phase1_prices['high'].max()
        min_price = phase1_prices['low'].min()
        phase1_pips = (max_price - min_price) * 10000
        
        print(f"\n📊 CALCUL PHASE 1 MANUEL (5 min après 12:30 UTC)")
        print(f"Prix départ: {start_price:.5f}")
        print(f"Max: {max_price:.5f}")
        print(f"Min: {min_price:.5f}")
        print(f"Phase 1: {phase1_pips:.2f} pips")
        
        # Validation
        expected = 33.7
        tolerance = 5
        if abs(phase1_pips - expected) <= tolerance:
            print(f"✅ EXCELLENT: Écart {abs(phase1_pips - expected):.2f} pips (< {tolerance})")
        else:
            print(f"⚠️  ÉCART: {abs(phase1_pips - expected):.2f} pips (attendu ~{expected})")
else:
    print("❌ ERREUR: Prix 11 septembre introuvables !")

# ============================================================================
# 4. VÉRIFIER EVENT_IMPACTS_V2
# ============================================================================
print("\n4. ÉTAT EVENT_IMPACTS_V2 (Session 27)")
print("-" * 80)

impacts_check = con.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(surprise_pct) as with_surprise,
        COUNT(phase1_pips) as with_phase1,
        MIN(surprise_pct) as min_surprise,
        MAX(surprise_pct) as max_surprise,
        ROUND(AVG(surprise_pct), 1) as avg_surprise
    FROM event_impacts_v2
""").fetchdf()

print(impacts_check)

if impacts_check['total'].iloc[0] == 8344:
    print(f"\n✅ event_impacts_v2 contient {impacts_check['total'].iloc[0]} événements (Session 27)")
else:
    print(f"\n⚠️  event_impacts_v2 contient {impacts_check['total'].iloc[0]} événements (attendu 8,344)")

# Vérifier si Phase 1 est calculée
if impacts_check['with_phase1'].iloc[0] == 0:
    print("⚠️  Phase 1 NON calculée dans event_impacts_v2")
    print("   → À calculer dans cette session")
else:
    print(f"✅ Phase 1 calculée pour {impacts_check['with_phase1'].iloc[0]} événements")

# ============================================================================
# 5. VÉRIFIER EVENT_FAMILIES ET SCORES
# ============================================================================
print("\n5. EVENT_FAMILIES ET SCORES")
print("-" * 80)

families_count = con.execute("SELECT COUNT(*) FROM event_families").fetchone()[0]
scores_count = con.execute("SELECT COUNT(*) FROM scores").fetchone()[0]

print(f"event_families: {families_count} lignes")
print(f"scores: {scores_count} lignes")

if families_count == 747:
    print("✅ event_families OK (747 familles)")
else:
    print(f"⚠️  event_families: {families_count} (attendu 747)")

# ============================================================================
# RÉSUMÉ VALIDATION
# ============================================================================
print("\n" + "=" * 80)
print("RÉSUMÉ VALIDATION")
print("=" * 80)

checks = {
    "forecast disponible (> 40%)": forecast_stats['pct_forecast'].iloc[0] >= 40,
    "11 sept event trouvé": len(sept11_event) > 0 if 'sept11_event' in locals() else False,
    "11 sept surprise > 30%": sept11_event['surprise_pct'].iloc[0] > 30 if len(sept11_event) > 0 and sept11_event['surprise_pct'].iloc[0] is not None else False,
    "11 sept prix trouvés": len(sept11_prices) > 0 if 'sept11_prices' in locals() else False,
    "Phase 1 calculée ≈ 33.7": abs(phase1_pips - 33.7) <= 5 if 'phase1_pips' in locals() else False,
    "event_impacts_v2 existe": impacts_check['total'].iloc[0] > 0,
    "event_families OK": families_count == 747,
}

all_ok = all(checks.values())

for check, status in checks.items():
    symbol = "✅" if status else "❌"
    print(f"{symbol} {check}")

print("\n" + "=" * 80)
if all_ok:
    print("✅ VALIDATION COMPLÈTE RÉUSSIE")
    print("Les données de base sont correctes et validées.")
    print("On peut maintenant recalculer les scores empiriques.")
else:
    print("❌ VALIDATION ÉCHOUÉE")
    print("Certaines données de base sont incorrectes.")
    print("Il faut corriger avant de continuer.")

con.close()
print("\n✅ Validation terminée")
