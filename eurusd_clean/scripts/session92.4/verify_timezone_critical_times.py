"""
VÉRIFICATION TIMEZONE - 11 SEPTEMBRE 2025
=========================================

Objectif : Afficher prix exacts aux charnières critiques pour vérifier timezone

Charnières Session 64 (Bern time +02:00) :
- 14h30 : Départ (publication CPI)
- 14h35 : Premier pic Phase 1 (+31 pips)
- 14h45 : Peak absolu (+53 pips)
- 15h10 : Stabilisation finale

Date : 28 octobre 2025
"""

import duckdb
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

# Timestamps critiques (Bern time +02:00)
CRITICAL_TIMES = [
    ('14:30', '12:30:00', 'Départ - Publication CPI'),
    ('14:35', '12:35:00', 'Premier pic Phase 1 (Session 64)'),
    ('14:45', '12:45:00', 'Peak absolu (Session 64)'),
    ('15:10', '13:10:00', 'Stabilisation finale (Session 64)')
]

print("="*80)
print("🕐 VÉRIFICATION TIMEZONE - 11 SEPTEMBRE 2025")
print("="*80)
print("\nTimestamps critiques Session 64 (Bern time +02:00)")

# ============================================================================
# CONNEXION DB
# ============================================================================

conn = duckdb.connect(str(DB_PATH), read_only=True)

# ============================================================================
# AFFICHAGE PRIX CRITIQUES
# ============================================================================

print("\n" + "="*80)
print("📊 PRIX AUX CHARNIÈRES CRITIQUES")
print("="*80)

prices_data = []

for bern_time, utc_time, description in CRITICAL_TIMES:
    # Query prix à ce timestamp exact
    query = f"""
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM prices_1m
    WHERE datetime = '2025-09-11 {utc_time}+02:00'::TIMESTAMP
    """
    
    result = conn.execute(query).fetchone()
    
    print(f"\n🕐 {bern_time} Bern ({utc_time} stocké) - {description}")
    
    if result:
        dt, open_price, high_price, low_price, close_price = result
        
        print(f"   Datetime : {dt}")
        print(f"   Open  : {open_price:.5f}")
        print(f"   High  : {high_price:.5f}")
        print(f"   Low   : {low_price:.5f}")
        print(f"   Close : {close_price:.5f}")
        
        prices_data.append({
            'time_bern': bern_time,
            'time_utc': utc_time,
            'description': description,
            'datetime': dt,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price
        })
    else:
        print(f"   ❌ AUCUNE DONNÉE à ce timestamp")

# ============================================================================
# CALCUL IMPACTS ENTRE CHARNIÈRES
# ============================================================================

print("\n" + "="*80)
print("📈 CALCUL IMPACTS ENTRE CHARNIÈRES")
print("="*80)

if len(prices_data) >= 2:
    start_price = prices_data[0]['open']
    
    print(f"\nPrix départ (14:30) : {start_price:.5f}")
    
    for i, price_point in enumerate(prices_data[1:], 1):
        # Impact depuis départ
        impact_high = (price_point['high'] - start_price) * 10000
        impact_low = (start_price - price_point['low']) * 10000
        impact_max = max(impact_high, abs(impact_low))
        
        direction = "UP" if impact_high > abs(impact_low) else "DOWN"
        
        print(f"\n{price_point['time_bern']} - {price_point['description']}")
        print(f"   High : {price_point['high']:.5f} (+{impact_high:+.1f} pips depuis départ)")
        print(f"   Low  : {price_point['low']:.5f} ({impact_low:+.1f} pips depuis départ)")
        print(f"   Impact MAX : {impact_max:.1f} pips ({direction})")

# ============================================================================
# SCAN MOUVEMENT COMPLET 14:30 → 15:30
# ============================================================================

print("\n" + "="*80)
print("🔍 SCAN MOUVEMENT COMPLET 14:30 → 15:30 (60 min)")
print("="*80)

query_full = """
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime >= '2025-09-11 12:30:00+02:00'::TIMESTAMP
  AND datetime <= '2025-09-11 13:30:00+02:00'::TIMESTAMP
ORDER BY datetime
"""

df = conn.execute(query_full).df()

if not df.empty:
    start_price = df.iloc[0]['open']
    
    # Trouver peak absolu
    max_high = df['high'].max()
    min_low = df['low'].min()
    
    impact_up = (max_high - start_price) * 10000
    impact_down = (start_price - min_low) * 10000
    
    peak_direction = "UP" if impact_up > impact_down else "DOWN"
    peak_price = max_high if peak_direction == "UP" else min_low
    peak_impact = max(impact_up, impact_down)
    
    # Trouver timestamp peak
    if peak_direction == "UP":
        peak_row = df[df['high'] == max_high].iloc[0]
    else:
        peak_row = df[df['low'] == min_low].iloc[0]
    
    peak_time = peak_row['datetime']
    minutes_to_peak = (peak_time - df.iloc[0]['datetime']).total_seconds() / 60
    
    print(f"\nPrix départ (14:30) : {start_price:.5f}")
    print(f"Peak absolu : {peak_price:.5f}")
    print(f"Peak time : {peak_time}")
    print(f"Peak timing : T+{minutes_to_peak:.0f} min")
    print(f"Impact peak : {peak_impact:.1f} pips ({peak_direction})")
    
    # Comparer avec Session 64
    print(f"\n📊 Comparaison Session 64 :")
    print(f"   Session 64 dit : Peak 14:45 (T+15), Impact 53 pips")
    print(f"   DB montre : Peak {peak_time.strftime('%H:%M')} (T+{minutes_to_peak:.0f}), Impact {peak_impact:.1f} pips")
    
    if abs(minutes_to_peak - 15) > 10:
        print(f"\n   ⚠️ DIVERGENCE TIMING : {abs(minutes_to_peak - 15):.0f} min écart")
    
    if abs(peak_impact - 53) > 2:
        print(f"   ⚠️ DIVERGENCE IMPACT : {abs(peak_impact - 53):.1f} pips écart")

# ============================================================================
# SCAN ÉTENDU 14:30 → 16:30 (120 min)
# ============================================================================

print("\n" + "="*80)
print("🔍 SCAN ÉTENDU 14:30 → 16:30 (120 min)")
print("="*80)

query_extended = """
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime >= '2025-09-11 12:30:00+02:00'::TIMESTAMP
  AND datetime <= '2025-09-11 14:30:00+02:00'::TIMESTAMP
ORDER BY datetime
"""

df_ext = conn.execute(query_extended).df()

if not df_ext.empty:
    start_price = df_ext.iloc[0]['open']
    
    # Trouver peak absolu
    max_high = df_ext['high'].max()
    min_low = df_ext['low'].min()
    
    impact_up = (max_high - start_price) * 10000
    impact_down = (start_price - min_low) * 10000
    
    peak_direction = "UP" if impact_up > impact_down else "DOWN"
    peak_price = max_high if peak_direction == "UP" else min_low
    peak_impact = max(impact_up, impact_down)
    
    # Trouver timestamp peak
    if peak_direction == "UP":
        peak_row = df_ext[df_ext['high'] == max_high].iloc[0]
    else:
        peak_row = df_ext[df_ext['low'] == min_low].iloc[0]
    
    peak_time = peak_row['datetime']
    minutes_to_peak = (peak_time - df_ext.iloc[0]['datetime']).total_seconds() / 60
    
    print(f"\nPrix départ (14:30) : {start_price:.5f}")
    print(f"Peak absolu : {peak_price:.5f}")
    print(f"Peak time : {peak_time}")
    print(f"Peak timing : T+{minutes_to_peak:.0f} min")
    print(f"Impact peak : {peak_impact:.1f} pips ({peak_direction})")
    
    # Comparer avec MT5/Planificateur
    print(f"\n📊 Comparaison MT5/Planificateur :")
    print(f"   Planificateur dit : Impact 56.2 pips")
    print(f"   DB fenêtre 120 min : Impact {peak_impact:.1f} pips")
    
    if abs(peak_impact - 56.2) < 1:
        print(f"   ✅ MATCH : Écart {abs(peak_impact - 56.2):.1f} pips")
    else:
        print(f"   ⚠️ DIVERGENCE : {abs(peak_impact - 56.2):.1f} pips écart")

conn.close()

print("\n" + "="*80)
print("✅ VÉRIFICATION TERMINÉE")
print("="*80)
