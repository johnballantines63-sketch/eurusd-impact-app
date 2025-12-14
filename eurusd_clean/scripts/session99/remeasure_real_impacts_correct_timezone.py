"""
RE-MESURE IMPACTS RÉELS - CORRECTION TIMEZONE
==============================================

Session 99 - Correction critique

PROBLÈME IDENTIFIÉ :
    Session 99 utilisait des impacts réels FAUX (14.3 pips au lieu de 56.2 pips)
    Cause probable : Bug timezone dans mesure d'impact

SOLUTION :
    Re-mesurer les 30 impacts avec la RÈGLE TIMEZONE VALIDÉE (Session 86)
    
RÈGLE SESSION 86 :
    Table events   : ts_utc contient +02:00 (Bern time)
    Table prices_1m: datetime contient +02:00 (Bern time)
    → MÊME TIMEZONE, PAS de conversion nécessaire
    → Event 14:30+02:00 → Chercher prix 14:30+02:00

MÉTHODOLOGIE MT5 :
    Impact = (High_peak - Price_event) OU (Price_event - Low_trough)
    Fenêtre : 120 minutes après événement
    Validation : Cas 11 sept 2025 = 56.2 pips confirmé

Date : 29 octobre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta

# Ajouter chemins
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))

print("="*80)
print("🔧 RE-MESURE IMPACTS RÉELS - CORRECTION TIMEZONE")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = project_root / "fx_impact_app" / "data" / "warehouse.duckdb"

# Charger les 30 dates Session 99
dates_file = Path(__file__).parent / "dates_validation_30plus.csv"
df_dates = pd.read_csv(dates_file)

print(f"\n📅 Dates à traiter : {len(df_dates)}")
print(f"📂 Base de données : {DB_PATH}")

# Validation référence connue
REFERENCE_DATE = "2025-09-11"
REFERENCE_IMPACT_MT5 = 56.2

# ============================================================================
# FONCTIONS
# ============================================================================

def get_db_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

def get_event_timestamp(date_str: str, conn) -> tuple:
    """
    Récupère le timestamp EXACT du premier événement HIGH
    RÈGLE SESSION 86 : ts_utc est en +02:00 (Bern time)
    """
    query = """
    SELECT 
        e.ts_utc,
        e.event_title
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 35
    ORDER BY e.ts_utc
    LIMIT 1
    """
    
    result = conn.execute(query, [date_str]).df()
    
    if result.empty:
        return None, None
    
    ts_utc = pd.to_datetime(result.iloc[0]['ts_utc'])
    event_title = result.iloc[0]['event_title']
    
    return ts_utc, event_title

def measure_real_impact_correct_timezone(event_timestamp, conn, window_minutes=120) -> dict:
    """
    Mesure l'impact réel avec TIMEZONE CORRECTE (Session 86)
    
    RÈGLE CRITIQUE :
    - events.ts_utc : +02:00 (Bern time)
    - prices_1m.datetime : +02:00 (Bern time)
    - PAS de conversion nécessaire !
    
    Args:
        event_timestamp: Timestamp événement (déjà en Bern time)
        conn: Connexion DB
        window_minutes: Fenêtre d'observation (défaut 120 min)
    
    Returns:
        dict avec impact_pips, direction, price_event, price_peak
    """
    if event_timestamp is None:
        return None
    
    # Fenêtre d'observation : event_timestamp à event_timestamp + window_minutes
    # RÈGLE SESSION 86 : Pas de conversion timezone !
    start_time = event_timestamp
    end_time = event_timestamp + timedelta(minutes=window_minutes)
    
    # Query prix - ATTENTION : datetime est aussi en +02:00 (Bern time)
    query_prices = """
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM prices_1m
    WHERE datetime >= ?
        AND datetime <= ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query_prices, [
        start_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time.strftime('%Y-%m-%d %H:%M:%S')
    ]).df()
    
    if df_prices.empty:
        return {
            'impact_pips': 0,
            'direction': 'NO_DATA',
            'price_event': None,
            'price_peak': None,
            'num_candles': 0,
            'error': 'NO_PRICE_DATA'
        }
    
    # Prix événement (première bougie)
    price_event = df_prices.iloc[0]['open']
    
    # Trouver peak (high max) et trough (low min)
    high_peak = df_prices['high'].max()
    low_trough = df_prices['low'].min()
    
    # Impact = plus grand mouvement
    impact_up = (high_peak - price_event) * 10000  # pips
    impact_down = (price_event - low_trough) * 10000  # pips
    
    if abs(impact_up) > abs(impact_down):
        impact_pips = impact_up
        direction = 'UP'
        price_peak = high_peak
    else:
        impact_pips = impact_down
        direction = 'DOWN'
        price_peak = low_trough
    
    return {
        'impact_pips': abs(impact_pips),
        'direction': direction,
        'price_event': price_event,
        'price_peak': price_peak,
        'num_candles': len(df_prices),
        'window_start': start_time,
        'window_end': end_time
    }

# ============================================================================
# PHASE 1 : RE-MESURE DES 30 IMPACTS
# ============================================================================

print(f"\n{'='*80}")
print(f"📊 PHASE 1 : Re-mesure des 30 impacts (timezone correcte)")
print(f"{'='*80}\n")

conn = get_db_connection()

results = []
errors = []

for idx, row in df_dates.iterrows():
    date_str = row['date']
    
    print(f"\n[{idx+1}/30] {date_str}")
    
    # 1. Récupérer timestamp événement
    event_ts, event_title = get_event_timestamp(date_str, conn)
    
    if event_ts is None:
        print(f"   ❌ Aucun événement trouvé")
        errors.append({
            'date': date_str,
            'error': 'NO_EVENT'
        })
        continue
    
    print(f"   ✅ Event: {event_title}")
    print(f"   📅 Timestamp: {event_ts.strftime('%Y-%m-%d %H:%M:%S%z')}")
    
    # 2. Mesurer impact CORRECT
    impact_result = measure_real_impact_correct_timezone(event_ts, conn, window_minutes=120)
    
    if impact_result is None or impact_result.get('error'):
        print(f"   ❌ Erreur mesure: {impact_result.get('error', 'UNKNOWN')}")
        errors.append({
            'date': date_str,
            'error': impact_result.get('error', 'UNKNOWN') if impact_result else 'MEASURE_FAILED'
        })
        continue
    
    impact_correct = impact_result['impact_pips']
    direction = impact_result['direction']
    num_candles = impact_result['num_candles']
    
    print(f"   📈 Impact CORRECT: {impact_correct:.1f} pips ({direction})")
    print(f"   📊 Bougie event: {impact_result['price_event']:.5f}")
    print(f"   🎯 Peak: {impact_result['price_peak']:.5f}")
    print(f"   📉 Bougies: {num_candles}")
    
    # 3. Validation référence
    if date_str == REFERENCE_DATE:
        diff_ref = abs(impact_correct - REFERENCE_IMPACT_MT5)
        print(f"   🔍 VALIDATION RÉFÉRENCE:")
        print(f"      Impact mesuré  : {impact_correct:.1f} pips")
        print(f"      Impact MT5     : {REFERENCE_IMPACT_MT5} pips")
        print(f"      Différence     : {diff_ref:.1f} pips")
        
        if diff_ref < 2:
            print(f"      ✅ VALIDÉ (écart < 2 pips)")
        else:
            print(f"      ⚠️  ATTENTION : Écart {diff_ref:.1f} pips")
    
    results.append({
        'date': date_str,
        'event_timestamp': event_ts.strftime('%Y-%m-%d %H:%M:%S%z'),
        'event_title': event_title,
        'impact_correct_pips': impact_correct,
        'direction': direction,
        'price_event': impact_result['price_event'],
        'price_peak': impact_result['price_peak'],
        'num_candles': num_candles,
        'window_minutes': 120
    })

conn.close()

# ============================================================================
# PHASE 2 : COMPARAISON AVEC SESSION 99
# ============================================================================

print(f"\n{'='*80}")
print(f"📊 PHASE 2 : Comparaison avec impacts Session 99 (faux)")
print(f"{'='*80}\n")

# Charger anciens résultats Session 99
s99_file = Path(__file__).parent / "test_amp_fixe_1.0_results.csv"
df_s99 = pd.read_csv(s99_file)

df_results = pd.DataFrame(results)

# Merger
df_compare = df_results.merge(
    df_s99[['date', 'impact_real']],
    on='date',
    how='left'
)
df_compare.rename(columns={'impact_real': 'impact_s99_faux'}, inplace=True)

# Calcul différences
df_compare['difference_pips'] = df_compare['impact_correct_pips'] - df_compare['impact_s99_faux']
df_compare['difference_pct'] = (df_compare['difference_pips'] / df_compare['impact_s99_faux']) * 100

print(f"{'Date':<12} {'Impact CORRECT':<15} {'Impact S99 (faux)':<18} {'Différence':<12} {'% Erreur'}")
print(f"{'-'*80}")

for idx, row in df_compare.iterrows():
    impact_correct = row['impact_correct_pips']
    impact_s99 = row.get('impact_s99_faux', 0)
    diff = row.get('difference_pips', 0)
    diff_pct = row.get('difference_pct', 0)
    
    print(f"{row['date']:<12} {impact_correct:>11.1f} pips   {impact_s99:>11.1f} pips     {diff:>7.1f} pips   {diff_pct:>6.1f}%")

# Statistiques globales
mean_correct = df_compare['impact_correct_pips'].mean()
mean_s99 = df_compare['impact_s99_faux'].mean()
mean_diff = df_compare['difference_pips'].mean()
mean_diff_pct = (mean_diff / mean_s99) * 100

print(f"\n{'='*80}")
print(f"📊 STATISTIQUES GLOBALES")
print(f"{'='*80}\n")

print(f"Moyenne impacts CORRECTS  : {mean_correct:.1f} pips")
print(f"Moyenne impacts S99 (faux): {mean_s99:.1f} pips")
print(f"Différence moyenne        : {mean_diff:+.1f} pips ({mean_diff_pct:+.1f}%)")

if mean_diff > 10:
    print(f"\n🚨 CONFIRMATION : Session 99 SOUS-ESTIMAIT massivement les impacts !")
    print(f"   → Amplification 1.0 semblait meilleure car comparée à impacts FAUX")
    print(f"   → Avec impacts CORRECTS, amp=2.5 sera probablement meilleure")

# ============================================================================
# PHASE 3 : SAUVEGARDE
# ============================================================================

print(f"\n{'='*80}")
print(f"💾 PHASE 3 : Sauvegarde résultats")
print(f"{'='*80}\n")

# Sauvegarder impacts corrects
output_file = Path(__file__).parent / "real_impacts_corrected_timezone.csv"
df_compare.to_csv(output_file, index=False)

print(f"✅ Impacts corrects sauvegardés : {output_file}")

# Sauvegarder erreurs
if errors:
    errors_file = Path(__file__).parent / "measurement_errors.csv"
    pd.DataFrame(errors).to_csv(errors_file, index=False)
    print(f"⚠️  Erreurs sauvegardées : {errors_file} ({len(errors)} dates)")

# ============================================================================
# VALIDATION FINALE
# ============================================================================

print(f"\n{'='*80}")
print(f"✅ VALIDATION FINALE")
print(f"{'='*80}\n")

# Vérifier référence
ref_row = df_compare[df_compare['date'] == REFERENCE_DATE]
if not ref_row.empty:
    ref_impact = ref_row.iloc[0]['impact_correct_pips']
    ref_diff = abs(ref_impact - REFERENCE_IMPACT_MT5)
    
    print(f"📊 Date référence {REFERENCE_DATE} :")
    print(f"   Impact mesuré : {ref_impact:.1f} pips")
    print(f"   Impact MT5    : {REFERENCE_IMPACT_MT5} pips")
    print(f"   Écart         : {ref_diff:.1f} pips")
    
    if ref_diff < 2:
        print(f"   ✅ VALIDÉ : Méthodologie timezone correcte !")
    else:
        print(f"   ⚠️  ATTENTION : Écart {ref_diff:.1f} pips - vérifier méthodologie")

print(f"\n🎯 PROCHAINE ÉTAPE :")
print(f"   Utiliser {output_file}")
print(f"   pour RE-CALIBRER l'amplification avec les VRAIS impacts")

print("\n" + "="*80)
print("✅ RE-MESURE IMPACTS TERMINÉE")
print("="*80)
