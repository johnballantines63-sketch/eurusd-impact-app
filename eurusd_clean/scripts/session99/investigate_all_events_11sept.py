"""
INVESTIGATION COMPLÈTE - 11 SEPTEMBRE 2025
===========================================

Teste TOUS les événements du 11 septembre pour trouver
lequel produit un impact de ~56.2 pips

On va aussi tester différentes méthodes de calcul :
- Depuis premier close
- Depuis premier open  
- Depuis low de la bougie
- Depuis prix avant événement

Date : 30 octobre 2025
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import timedelta

project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))
from config import get_db_path

print("="*80)
print("🔍 INVESTIGATION COMPLÈTE 11 SEPTEMBRE 2025")
print("="*80)

DB_PATH = get_db_path()
REFERENCE_DATE = "2025-09-11"
TARGET_IMPACT = 56.2

# ============================================================================
# CHARGER TOUS LES ÉVÉNEMENTS
# ============================================================================

conn = duckdb.connect(str(DB_PATH), read_only=True)

print(f"\n📅 TOUS LES ÉVÉNEMENTS US DU {REFERENCE_DATE} :")
print("-"*80)

query_all_events = """
SELECT 
    e.ts_utc,
    e.event_title,
    e.actual,
    e.estimate,
    e.forecast,
    ef.empirical_score
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
ORDER BY e.ts_utc
"""

all_events = conn.execute(query_all_events, [REFERENCE_DATE]).fetchdf()

print(all_events[['ts_utc', 'event_title', 'empirical_score']].to_string(index=False))

print(f"\n✅ {len(all_events)} événements trouvés")

# ============================================================================
# FONCTION MESURE IMPACT (PLUSIEURS MÉTHODES)
# ============================================================================

def measure_impact_all_methods(event_time, window_min=120):
    """
    Mesure impact avec TOUTES les méthodes possibles
    """
    
    # Query prix
    start_time = event_time - timedelta(minutes=5)
    end_time = event_time + timedelta(minutes=window_min)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime ASC
    """
    
    prices = conn.execute(query, [start_time, end_time]).fetchdf()
    
    if prices.empty:
        return None
    
    prices_at_event = prices[prices['datetime'] >= event_time]
    if len(prices_at_event) == 0:
        return None
    
    prices_after = prices[prices['datetime'] >= event_time].copy()
    
    # Prix de référence (différentes méthodes)
    first_open = prices_at_event.iloc[0]['open']
    first_close = prices_at_event.iloc[0]['close']
    first_high = prices_at_event.iloc[0]['high']
    first_low = prices_at_event.iloc[0]['low']
    
    # Prix avant événement (si disponible)
    prices_before = prices[prices['datetime'] < event_time]
    price_before = prices_before.iloc[-1]['close'] if len(prices_before) > 0 else first_open
    
    # Peak
    max_high = prices_after['high'].max()
    max_high_idx = prices_after['high'].idxmax()
    max_high_time = prices_after.loc[max_high_idx, 'datetime']
    
    min_low = prices_after['low'].min()
    
    # Calculer impacts selon différentes méthodes
    results = {
        'from_first_close': (max_high - first_close) * 10000,
        'from_first_open': (max_high - first_open) * 10000,
        'from_first_low': (max_high - first_low) * 10000,
        'from_price_before': (max_high - price_before) * 10000,
        'price_before': price_before,
        'first_open': first_open,
        'first_close': first_close,
        'first_low': first_low,
        'first_high': first_high,
        'max_high': max_high,
        'max_high_time': max_high_time,
        'ttr': (max_high_time - event_time).total_seconds() / 60.0,
        'num_candles': len(prices_after)
    }
    
    return results

# ============================================================================
# TESTER CHAQUE ÉVÉNEMENT
# ============================================================================

print(f"\n{'='*80}")
print(f"🔬 TEST DE CHAQUE ÉVÉNEMENT")
print(f"{'='*80}\n")

best_match = None
best_ecart = 999

for idx, event in all_events.iterrows():
    event_time = pd.to_datetime(event['ts_utc'])
    event_title = event['event_title']
    score = event['empirical_score']
    
    print(f"\n{'─'*80}")
    print(f"📊 EVENT: {event_title}")
    print(f"   Time: {event_time.strftime('%H:%M:%S')}")
    print(f"   Score: {score}")
    
    # Mesurer impact
    results = measure_impact_all_methods(event_time)
    
    if results is None:
        print(f"   ❌ Pas de prix disponibles")
        continue
    
    print(f"\n   💰 PRIX DE RÉFÉRENCE:")
    print(f"      Prix avant event   : {results['price_before']:.5f}")
    print(f"      First open         : {results['first_open']:.5f}")
    print(f"      First close        : {results['first_close']:.5f}")
    print(f"      First low          : {results['first_low']:.5f}")
    print(f"      First high         : {results['first_high']:.5f}")
    
    print(f"\n   📈 PEAK:")
    print(f"      Max high           : {results['max_high']:.5f}")
    print(f"      Peak time          : {results['max_high_time'].strftime('%H:%M:%S')}")
    print(f"      TTR                : {results['ttr']:.1f} min")
    
    print(f"\n   🎯 IMPACTS CALCULÉS (selon méthode):")
    
    methods = [
        ('from_price_before', 'Depuis prix avant event'),
        ('from_first_open', 'Depuis first OPEN'),
        ('from_first_close', 'Depuis first CLOSE'),
        ('from_first_low', 'Depuis first LOW'),
    ]
    
    for method_key, method_name in methods:
        impact = results[method_key]
        ecart = abs(impact - TARGET_IMPACT)
        
        status = "✅✅✅" if ecart < 2 else ("✅✅" if ecart < 5 else ("✅" if ecart < 10 else ""))
        
        print(f"      {method_name:<30}: {impact:>6.1f} pips (écart: {ecart:>5.1f}) {status}")
        
        # Tracker meilleur match
        if ecart < best_ecart:
            best_ecart = ecart
            best_match = {
                'event': event_title,
                'event_time': event_time,
                'method': method_name,
                'impact': impact,
                'ecart': ecart,
                'results': results
            }

conn.close()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print(f"\n{'='*80}")
print(f"🏆 MEILLEUR MATCH")
print(f"{'='*80}\n")

if best_match:
    print(f"Event        : {best_match['event']}")
    print(f"Time         : {best_match['event_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Méthode      : {best_match['method']}")
    print(f"Impact       : {best_match['impact']:.1f} pips")
    print(f"Target       : {TARGET_IMPACT} pips")
    print(f"Écart        : {best_match['ecart']:.1f} pips")
    
    if best_match['ecart'] < 2:
        print(f"\n✅ ✅ ✅ MATCH PARFAIT !")
        print(f"   → Événement identifié : {best_match['event']}")
        print(f"   → Méthode correcte : {best_match['method']}")
    elif best_match['ecart'] < 5:
        print(f"\n✅ ✅ TRÈS PROCHE !")
        print(f"   → Probablement le bon événement et méthode")
    elif best_match['ecart'] < 10:
        print(f"\n✅ PROCHE")
        print(f"   → Possiblement le bon événement")
    else:
        print(f"\n❌ AUCUN MATCH SATISFAISANT")
        print(f"   → Le meilleur écart est {best_match['ecart']:.1f} pips")
        print(f"   → Investiguer plus :")
        print(f"      - Vérifier référence MT5 de 56.2 pips")
        print(f"      - Tester autres fenêtres temporelles")
        print(f"      - Vérifier si c'est une somme d'événements")
else:
    print(f"❌ Aucun événement testé avec succès")

print("\n" + "="*80)
print("✅ INVESTIGATION TERMINÉE")
print("="*80)
