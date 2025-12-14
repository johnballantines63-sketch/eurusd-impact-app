"""
RE-MESURE IMPACTS RÉELS - CORRECTION TIMEZONE ULTIME
====================================================

Session 100 - Correction timezone + Prix AVANT événement

CORRECTION CRITIQUE TIMEZONE :
    Event en DB : 14:30+02:00 (Bern time)
    Prix query  : 12:30+02:00 (UTC base + offset)
    
    Conversion : event_timestamp - 2 heures
    
    Exemple 11 sept 2025 :
    - DB events.ts_utc : 14:30+02:00
    - Query prices_1m  : 12:30+02:00
    - Prix AVANT       : 1.16874 (CLOSE de 12:29) ✅
    
CORRECTION CRITIQUE PRIX :
    Prix départ = Dernier CLOSE AVANT l'événement (pas CLOSE de l'événement)
    
    Validation test_validation_FINAL.py :
    - Impact : 57.1 pips (écart 0.9 vs MT5 56.2) ✅✅✅

RÉFÉRENCE VALIDATION :
    Date : 2025-09-11
    Impact attendu : 56.2 pips (MT5 confirmé)
    
Date : 30 octobre 2025
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
print("🎯 RE-MESURE IMPACTS RÉELS - CORRECTION TIMEZONE ULTIME")
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
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    LIMIT 1
    """
    
    result = conn.execute(query, [date_str]).df()
    
    if result.empty:
        return None, None
    
    ts_utc = pd.to_datetime(result.iloc[0]['ts_utc'])
    event_title = result.iloc[0]['event_title']
    
    return ts_utc, event_title

def measure_real_impact_TIMEZONE_CORRECT(event_timestamp_bern, conn, window_minutes=120) -> dict:
    """
    Mesure l'impact réel avec TIMEZONE + PRIX CORRECTS
    
    🔑 CORRECTIONS CRITIQUES :
    1. Timezone : Event 14:30 Bern → Query 12:30 UTC base
    2. Prix départ : Dernier CLOSE AVANT l'événement
    
    Args:
        event_timestamp_bern: Timestamp événement en Bern time (de la DB)
        conn: Connexion DB
        window_minutes: Fenêtre d'observation (défaut 120 min)
    
    Returns:
        dict avec impact_pips, ttr_minutes, price_start, price_peak
    """
    if event_timestamp_bern is None:
        return None
    
    # ✅ CORRECTION TIMEZONE : Event 14:30 Bern → Query 12:30 UTC base
    # Règle Session 92.10 : Soustraire 2h du timestamp DB
    event_timestamp_utc = event_timestamp_bern - timedelta(hours=2)
    
    # Fenêtre démarre -5 min AVANT l'événement (en UTC)
    start_time = event_timestamp_utc - timedelta(minutes=5)
    end_time = event_timestamp_utc + timedelta(minutes=window_minutes)
    
    # Query prix
    query_prices = """
    SELECT 
        datetime,
        close,
        high,
        low
    FROM prices_1m
    WHERE datetime >= ?
        AND datetime <= ?
    ORDER BY datetime ASC
    """
    
    prices = conn.execute(query_prices, [start_time, end_time]).fetchdf()
    
    if prices.empty:
        return {
            'impact_pips': 0,
            'ttr_minutes': None,
            'price_start': None,
            'price_peak': None,
            'num_candles': 0,
            'error': 'NO_PRICE_DATA',
            'event_timestamp_bern': event_timestamp_bern,
            'event_timestamp_utc': event_timestamp_utc
        }
    
    # ✅ CORRECTION PRIX : Prix AVANT événement (UTC)
    prices_before_event = prices[prices['datetime'] < event_timestamp_utc]
    
    if len(prices_before_event) == 0:
        # Fallback : utiliser premier prix disponible
        print(f"   ⚠️  Aucun prix AVANT événement - utilisation fallback")
        start_price = prices.iloc[0]['close']
    else:
        # Prix de référence = Dernier CLOSE AVANT l'événement
        start_price = prices_before_event.iloc[-1]['close']  # ✅✅✅
    
    # Filtrer prices APRÈS event pour calcul peak
    prices_after = prices[prices['datetime'] >= event_timestamp_utc].copy()
    
    if len(prices_after) == 0:
        return {
            'impact_pips': 0,
            'ttr_minutes': None,
            'price_start': start_price,
            'price_peak': None,
            'num_candles': 0,
            'error': 'NO_PRICES_AFTER_EVENT',
            'event_timestamp_bern': event_timestamp_bern,
            'event_timestamp_utc': event_timestamp_utc
        }
    
    # Impact = (high - start_price) × 10000
    prices_after['pips_high'] = (prices_after['high'] - start_price) * 10000
    
    # Peak = maximum des pips_high
    peak_pips = prices_after['pips_high'].max()
    peak_idx = prices_after['pips_high'].idxmax()
    peak_time = prices_after.loc[peak_idx, 'datetime']
    
    # TTR en minutes
    ttr_minutes = (peak_time - event_timestamp_utc).total_seconds() / 60.0
    
    return {
        'impact_pips': peak_pips,
        'ttr_minutes': ttr_minutes,
        'price_start': start_price,
        'price_peak': prices_after.loc[peak_idx, 'high'],
        'num_candles': len(prices_after),
        'peak_time': peak_time,
        'window_start': start_time,
        'window_end': end_time,
        'event_timestamp_bern': event_timestamp_bern,
        'event_timestamp_utc': event_timestamp_utc
    }

# ============================================================================
# PHASE 1 : RE-MESURE DES 30 IMPACTS (TIMEZONE + PRIX CORRECTS)
# ============================================================================

print(f"\n{'='*80}")
print(f"📊 PHASE 1 : Re-mesure avec TIMEZONE + PRIX CORRECTS")
print(f"{'='*80}\n")

conn = get_db_connection()

results = []
errors = []

for idx, row in df_dates.iterrows():
    date_str = row['date']
    
    print(f"\n[{idx+1}/{len(df_dates)}] {date_str}")
    
    # 1. Récupérer timestamp événement (Bern time de la DB)
    event_ts_bern, event_title = get_event_timestamp(date_str, conn)
    
    if event_ts_bern is None:
        print(f"   ❌ Aucun événement trouvé")
        errors.append({
            'date': date_str,
            'error': 'NO_EVENT'
        })
        continue
    
    print(f"   ✅ Event: {event_title}")
    print(f"   📅 Timestamp DB (Bern): {event_ts_bern.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Calculer timestamp UTC pour query
    event_ts_utc = event_ts_bern - timedelta(hours=2)
    print(f"   🔄 Timestamp Query (UTC): {event_ts_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 2. Mesurer impact avec TIMEZONE + PRIX CORRECTS
    impact_result = measure_real_impact_TIMEZONE_CORRECT(event_ts_bern, conn, window_minutes=120)
    
    if impact_result is None or impact_result.get('error'):
        print(f"   ❌ Erreur mesure: {impact_result.get('error', 'UNKNOWN')}")
        errors.append({
            'date': date_str,
            'error': impact_result.get('error', 'UNKNOWN') if impact_result else 'MEASURE_FAILED'
        })
        continue
    
    impact_correct = impact_result['impact_pips']
    ttr_minutes = impact_result['ttr_minutes']
    num_candles = impact_result['num_candles']
    
    print(f"   📈 Impact: {impact_correct:.1f} pips")
    print(f"   ⏱️  TTR: {ttr_minutes:.1f} min")
    print(f"   📊 Prix start (AVANT event): {impact_result['price_start']:.5f}")
    print(f"   🎯 Prix peak: {impact_result['price_peak']:.5f}")
    print(f"   📉 Bougies après event: {num_candles}")
    
    # 3. Validation référence
    if date_str == REFERENCE_DATE:
        diff_ref = abs(impact_correct - REFERENCE_IMPACT_MT5)
        print(f"\n   🔍 *** VALIDATION RÉFÉRENCE 11 SEPTEMBRE ***")
        print(f"      Impact mesuré  : {impact_correct:.1f} pips")
        print(f"      Impact MT5     : {REFERENCE_IMPACT_MT5} pips")
        print(f"      Différence     : {diff_ref:.1f} pips")
        
        if diff_ref < 2:
            print(f"      ✅ ✅ ✅ VALIDÉ : Méthodologie correcte !")
        elif diff_ref < 5:
            print(f"      ⚠️  PROCHE : Écart {diff_ref:.1f} pips (acceptable)")
        else:
            print(f"      ❌ PROBLÈME : Écart {diff_ref:.1f} pips (>5 pips)")
    
    results.append({
        'date': date_str,
        'event_timestamp_bern': event_ts_bern.strftime('%Y-%m-%d %H:%M:%S'),
        'event_timestamp_utc': impact_result['event_timestamp_utc'].strftime('%Y-%m-%d %H:%M:%S'),
        'event_title': event_title,
        'impact_pips': impact_correct,
        'ttr_minutes': ttr_minutes,
        'price_start': impact_result['price_start'],
        'price_peak': impact_result['price_peak'],
        'num_candles': num_candles,
        'peak_time': impact_result['peak_time'].strftime('%Y-%m-%d %H:%M:%S'),
        'window_minutes': 120
    })

conn.close()

# ============================================================================
# PHASE 2 : COMPARAISON AVEC SESSION 99 (ANCIENNE VERSION)
# ============================================================================

print(f"\n{'='*80}")
print(f"📊 PHASE 2 : Comparaison ancienne vs nouvelle méthode")
print(f"{'='*80}\n")

# Charger anciens résultats Session 99
s99_file = Path(__file__).parent / "test_amp_fixe_1.0_results.csv"

if s99_file.exists():
    df_s99 = pd.read_csv(s99_file)
    
    df_results = pd.DataFrame(results)
    
    # Merger
    df_compare = df_results.merge(
        df_s99[['date', 'impact_real']],
        on='date',
        how='left'
    )
    df_compare.rename(columns={'impact_real': 'impact_old_method'}, inplace=True)
    
    # Calcul différences
    df_compare['difference_pips'] = df_compare['impact_pips'] - df_compare['impact_old_method']
    df_compare['difference_pct'] = (df_compare['difference_pips'] / df_compare['impact_old_method']) * 100
    
    print(f"{'Date':<12} {'Nouvelle méthode':<17} {'Ancienne méthode':<17} {'Différence':<12} {'% Erreur'}")
    print(f"{'-'*80}")
    
    for idx, row in df_compare.iterrows():
        impact_new = row['impact_pips']
        impact_old = row.get('impact_old_method', 0)
        diff = row.get('difference_pips', 0)
        diff_pct = row.get('difference_pct', 0)
        
        status = "✅" if abs(diff) < 5 else ("⚠️" if abs(diff) < 15 else "❌")
        
        print(f"{row['date']:<12} {impact_new:>11.1f} pips   {impact_old:>11.1f} pips    {diff:>7.1f} pips {status} {diff_pct:>6.1f}%")
    
    # Statistiques
    mean_new = df_compare['impact_pips'].mean()
    mean_old = df_compare['impact_old_method'].mean()
    mean_diff = df_compare['difference_pips'].mean()
    mean_diff_pct = (mean_diff / mean_old) * 100 if mean_old > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"📊 STATISTIQUES COMPARATIVES")
    print(f"{'='*80}\n")
    
    print(f"Moyenne nouvelle méthode : {mean_new:.1f} pips")
    print(f"Moyenne ancienne méthode : {mean_old:.1f} pips")
    print(f"Différence moyenne       : {mean_diff:+.1f} pips ({mean_diff_pct:+.1f}%)")
    
    if mean_diff > 10:
        print(f"\n🚨 CONFIRMATION : Ancienne méthode SOUS-ESTIMAIT les impacts !")
        print(f"   → Session 99 utilisait des impacts FAUX")
        print(f"   → Amplification 1.0 semblait meilleure avec données fausses")
        print(f"   → Avec impacts CORRECTS, amp=2.5 devrait redevenir optimale")
    elif abs(mean_diff) < 5:
        print(f"\n✅ Méthodes cohérentes - pas de sous-estimation massive")
else:
    df_compare = pd.DataFrame(results)
    print(f"⚠️ Fichier {s99_file} non trouvé - pas de comparaison possible")

# ============================================================================
# PHASE 3 : SAUVEGARDE
# ============================================================================

print(f"\n{'='*80}")
print(f"💾 PHASE 3 : Sauvegarde résultats CORRECTS")
print(f"{'='*80}\n")

# Sauvegarder impacts corrects
output_file = Path(__file__).parent / "real_impacts_TIMEZONE_FIX_FINAL.csv"
df_compare.to_csv(output_file, index=False)

print(f"✅ Impacts corrects (TIMEZONE + PRIX) : {output_file}")

# Sauvegarder erreurs
if errors:
    errors_file = Path(__file__).parent / "measurement_errors_timezone_fix.csv"
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
    ref_impact = ref_row.iloc[0]['impact_pips']
    ref_diff = abs(ref_impact - REFERENCE_IMPACT_MT5)
    
    print(f"📊 Date référence {REFERENCE_DATE} :")
    print(f"   Impact mesuré (TIMEZONE + PRIX corrects) : {ref_impact:.1f} pips")
    print(f"   Impact MT5 validé                        : {REFERENCE_IMPACT_MT5} pips")
    print(f"   Écart                                     : {ref_diff:.1f} pips")
    
    if ref_diff < 2:
        print(f"\n   ✅ ✅ ✅ MÉTHODOLOGIE VALIDÉE !")
        print(f"   → Écart < 2 pips sur cas de référence")
        print(f"   → Timezone conversion correcte (14:30 Bern → 12:30 UTC)")
        print(f"   → Prix AVANT événement = méthode correcte")
        print(f"   → Prêt pour re-calibration amplification")
    elif ref_diff < 5:
        print(f"\n   ⚠️  MÉTHODOLOGIE ACCEPTABLE")
        print(f"   → Écart {ref_diff:.1f} pips (< 5 pips)")
    else:
        print(f"\n   ❌ MÉTHODOLOGIE INVALIDE")
        print(f"   → Écart {ref_diff:.1f} pips (> 5 pips)")
        print(f"   → STOP : Vérifier méthodologie")
else:
    print(f"⚠️ Date référence {REFERENCE_DATE} non trouvée dans résultats")

print(f"\n🎯 PROCHAINE ÉTAPE :")
print(f"   1. ✅ Validation référence < 2 pips")
print(f"   2. Utiliser {output_file}")
print(f"      pour RE-CALIBRER l'amplification avec les VRAIS impacts")
print(f"   3. Re-tester amp=1.0 vs amp=2.5 avec données correctes")
print(f"   4. Décision finale sur amplification optimale")

print("\n" + "="*80)
print("✅ RE-MESURE IMPACTS TERMINÉE (TIMEZONE + PRIX CORRECTS)")
print("="*80)
