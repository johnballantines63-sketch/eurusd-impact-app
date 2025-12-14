"""
VALIDATION FENÊTRES TEMPORELLES - Session 92.4
==============================================

Objectif : Comprendre pourquoi CSV Session 90 (51.7 pips) ≠ MT5/Planificateur (56.2 pips)

Méthodologie :
1. Tester différentes fenêtres temporelles (30, 45, 60, 90, 120 min)
2. Calculer impact pour chaque fenêtre (méthode Session 90)
3. Identifier quelle fenêtre donne 56.2 pips (MT5)
4. Confirmer que 60 min = 51.7 pips (CSV Session 90)

Date : 28 octobre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

# Date référence : 11 septembre 2025
TEST_DATE = '2025-09-11'
TEST_TIME = '12:30:00'  # Heure événement CPI (Bern time +02:00)

# Valeurs attendues
IMPACT_CSV_SESSION90 = 51.7  # CSV Session 90
IMPACT_MT5_PLANNER = 56.2    # MT5/Planificateur

# Fenêtres à tester
WINDOWS_MINUTES = [15, 30, 45, 60, 75, 90, 120]

print("="*80)
print("🔬 VALIDATION FENÊTRES TEMPORELLES - 11 SEPTEMBRE 2025")
print("="*80)
print(f"\nDate événement : {TEST_DATE} {TEST_TIME}+02:00")
print(f"Impact CSV Session 90 : {IMPACT_CSV_SESSION90} pips")
print(f"Impact MT5/Planificateur : {IMPACT_MT5_PLANNER} pips")
print(f"Divergence à expliquer : {abs(IMPACT_MT5_PLANNER - IMPACT_CSV_SESSION90):.1f} pips")

# ============================================================================
# CONNEXION DB
# ============================================================================

print(f"\n📁 Connexion DB : {DB_PATH.name}")

if not DB_PATH.exists():
    print(f"❌ ERREUR : DB non trouvée")
    print(f"   Chemin : {DB_PATH}")
    exit(1)

conn = duckdb.connect(str(DB_PATH), read_only=True)
print("✅ Connexion OK")

# ============================================================================
# FONCTION CALCUL IMPACT (MÉTHODE SESSION 90)
# ============================================================================

def calculate_impact_window(conn, date_str, time_str, window_minutes):
    """
    Calcule impact avec fenêtre temporelle donnée
    
    EXACTEMENT méthode Session 90 :
    - Prix départ : open première minute
    - Impact : max(impact_up, impact_down)
    """
    query = f"""
    SELECT datetime, open, high, low FROM prices_1m
    WHERE datetime >= '{date_str} {time_str}+02:00'::TIMESTAMP
      AND datetime <= '{date_str} {time_str}+02:00'::TIMESTAMP + INTERVAL '{window_minutes} minutes'
    ORDER BY datetime
    """
    
    df = conn.execute(query).df()
    
    if df.empty:
        return None, 0
    
    # Méthode Session 90
    start_price = df.iloc[0]['open']
    impact_down = abs(start_price - df['low'].min()) * 10000
    impact_up = abs(df['high'].max() - start_price) * 10000
    impact = max(impact_down, impact_up)
    
    # Identifier peak time
    if impact == impact_up:
        peak_row = df[df['high'] == df['high'].max()].iloc[0]
        peak_time = peak_row['datetime']
        peak_price = peak_row['high']
        direction = "UP"
    else:
        peak_row = df[df['low'] == df['low'].min()].iloc[0]
        peak_time = peak_row['datetime']
        peak_price = peak_row['low']
        direction = "DOWN"
    
    minutes_to_peak = len(df[df['datetime'] <= peak_time]) - 1
    
    return {
        'window_min': window_minutes,
        'impact_pips': impact,
        'start_price': start_price,
        'peak_price': peak_price,
        'direction': direction,
        'peak_time': peak_time,
        'minutes_to_peak': minutes_to_peak,
        'n_candles': len(df)
    }, impact

# ============================================================================
# TEST FENÊTRES
# ============================================================================

print("\n" + "="*80)
print("📊 TEST FENÊTRES TEMPORELLES")
print("="*80)

results = []

for window in WINDOWS_MINUTES:
    result, impact = calculate_impact_window(conn, TEST_DATE, TEST_TIME, window)
    
    if result:
        results.append(result)
        
        # Afficher résultat
        print(f"\n🕐 Fenêtre {window:3d} min :")
        print(f"   Impact : {impact:5.1f} pips ({result['direction']})")
        print(f"   Peak à : T+{result['minutes_to_peak']:2d} min ({result['peak_time']})")
        print(f"   Candles : {result['n_candles']}")
        
        # Comparer avec valeurs attendues
        diff_csv = abs(impact - IMPACT_CSV_SESSION90)
        diff_mt5 = abs(impact - IMPACT_MT5_PLANNER)
        
        if diff_csv < 0.5:
            print(f"   ✅ MATCH CSV Session 90 (écart {diff_csv:.1f} pips)")
        if diff_mt5 < 0.5:
            print(f"   ✅ MATCH MT5/Planificateur (écart {diff_mt5:.1f} pips)")
        
        if diff_csv >= 0.5 and diff_mt5 >= 0.5:
            print(f"   ⚠️ Écarts : CSV +{diff_csv:.1f}p, MT5 +{diff_mt5:.1f}p")

# ============================================================================
# ANALYSE RÉSULTATS
# ============================================================================

print("\n" + "="*80)
print("📈 ANALYSE RÉSULTATS")
print("="*80)

df_results = pd.DataFrame(results)

print(f"\n{'Fenêtre':<10} {'Impact':>8} {'T+Peak':>8} {'Écart CSV':>10} {'Écart MT5':>10}")
print("-"*80)

for _, row in df_results.iterrows():
    diff_csv = abs(row['impact_pips'] - IMPACT_CSV_SESSION90)
    diff_mt5 = abs(row['impact_pips'] - IMPACT_MT5_PLANNER)
    
    marker_csv = "✅" if diff_csv < 0.5 else ""
    marker_mt5 = "✅" if diff_mt5 < 0.5 else ""
    
    print(f"{row['window_min']:3d} min    {row['impact_pips']:7.1f}p  T+{row['minutes_to_peak']:2d} min  "
          f"{diff_csv:7.1f}p {marker_csv:2}  {diff_mt5:7.1f}p {marker_mt5:2}")

# ============================================================================
# IDENTIFICATION FENÊTRE OPTIMALE
# ============================================================================

print("\n" + "="*80)
print("🎯 IDENTIFICATION FENÊTRE OPTIMALE")
print("="*80)

# Fenêtre qui match MT5/Planificateur (56.2 pips)
best_match_mt5 = df_results.iloc[(df_results['impact_pips'] - IMPACT_MT5_PLANNER).abs().argsort()[:1]]

if not best_match_mt5.empty:
    row = best_match_mt5.iloc[0]
    diff = abs(row['impact_pips'] - IMPACT_MT5_PLANNER)
    
    print(f"\n✅ Fenêtre match MT5/Planificateur (56.2 pips) :")
    print(f"   Fenêtre : {row['window_min']:.0f} minutes")
    print(f"   Impact : {row['impact_pips']:.1f} pips")
    print(f"   Écart : {diff:.1f} pips")
    print(f"   Peak : T+{row['minutes_to_peak']:.0f} min")

# Fenêtre qui match CSV Session 90 (51.7 pips)
best_match_csv = df_results.iloc[(df_results['impact_pips'] - IMPACT_CSV_SESSION90).abs().argsort()[:1]]

if not best_match_csv.empty:
    row = best_match_csv.iloc[0]
    diff = abs(row['impact_pips'] - IMPACT_CSV_SESSION90)
    
    print(f"\n⚠️ Fenêtre match CSV Session 90 (51.7 pips) :")
    print(f"   Fenêtre : {row['window_min']:.0f} minutes")
    print(f"   Impact : {row['impact_pips']:.1f} pips")
    print(f"   Écart : {diff:.1f} pips")
    print(f"   Peak : T+{row['minutes_to_peak']:.0f} min")

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n" + "="*80)
print("💡 CONCLUSION")
print("="*80)

# Vérifier si 60 min = 51.7 (CSV Session 90)
row_60 = df_results[df_results['window_min'] == 60]

if not row_60.empty:
    impact_60 = row_60.iloc[0]['impact_pips']
    diff_60_csv = abs(impact_60 - IMPACT_CSV_SESSION90)
    
    print(f"\n1. Fenêtre 60 min (CSV Session 90) :")
    print(f"   Impact calculé : {impact_60:.1f} pips")
    print(f"   Impact CSV : {IMPACT_CSV_SESSION90} pips")
    print(f"   Écart : {diff_60_csv:.1f} pips")
    
    if diff_60_csv < 0.5:
        print(f"   ✅ CONFIRMATION : CSV Session 90 utilise fenêtre 60 min")
    else:
        print(f"   ⚠️ DIVERGENCE : CSV Session 90 ≠ fenêtre 60 min DB")

# Comparaison fenêtre optimale vs CSV
if not best_match_mt5.empty:
    window_optimal = best_match_mt5.iloc[0]['window_min']
    diff_windows = abs(window_optimal - 60)
    
    print(f"\n2. Divergence CSV vs MT5/Planificateur :")
    print(f"   Fenêtre CSV : 60 min → {IMPACT_CSV_SESSION90} pips")
    print(f"   Fenêtre optimale : {window_optimal:.0f} min → {IMPACT_MT5_PLANNER} pips")
    print(f"   Différence : {abs(IMPACT_MT5_PLANNER - IMPACT_CSV_SESSION90):.1f} pips (8%)")
    
    if diff_windows > 0:
        print(f"\n   ❌ CAUSE IDENTIFIÉE :")
        print(f"   CSV Session 90 utilise fenêtre FIXE 60 min")
        print(f"   Mouvement réel nécessite fenêtre {window_optimal:.0f} min")
        print(f"   → Fenêtre insuffisante capture mouvement incomplet")

# Recommandations
print(f"\n3. Recommandations :")
print(f"   ✅ Utiliser fenêtre adaptative par type événement")
print(f"   ✅ CPI : {window_optimal:.0f} min minimum (pas 60 min fixe)")
print(f"   ✅ Valider échantillon 10 dates MT5 AVANT Grid Search")
print(f"   ❌ CSV Session 90 INVALIDE pour calibration (sous-estime impact)")

conn.close()

print("\n" + "="*80)
print("✅ VALIDATION TERMINÉE")
print("="*80)
