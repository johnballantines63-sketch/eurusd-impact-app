#!/bin/bash

cd /Users/andrevalentin/Projects/eurusd_news_impact_calculator

echo "🐛 Debug de measure_actual_market_reaction..."

python3 << 'PYEOF'
file_path = 'backtest_latency_predictions.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter du debug au début de measure_actual_market_reaction
old_func_start = '''def measure_actual_market_reaction(event_ts, threshold_pips=5.0, window_minutes=60):
    """Mesure la réaction réelle du marché après un événement"""
    conn = duckdb.connect(get_db_path())
    
    # Convertir timestamp
    if isinstance(event_ts, str):
        event_ts = pd.to_datetime(event_ts)
    
    end_time = event_ts + timedelta(minutes=window_minutes)
    
    # Convertir en epoch Unix pour query prices_1m
    event_epoch = int(event_ts.timestamp())
    end_epoch = int(end_time.timestamp())'''

new_func_start = '''def measure_actual_market_reaction(event_ts, threshold_pips=5.0, window_minutes=60):
    """Mesure la réaction réelle du marché après un événement"""
    
    # Debug
    import sys
    debug = getattr(sys, '_backtest_debug_count', 0) < 3
    if debug:
        print(f"    [measure] event_ts type: {type(event_ts)}, value: {event_ts}")
    
    conn = duckdb.connect(get_db_path())
    
    # Convertir timestamp
    if isinstance(event_ts, str):
        event_ts = pd.to_datetime(event_ts)
    
    end_time = event_ts + timedelta(minutes=window_minutes)
    
    if debug:
        print(f"    [measure] end_time: {end_time}")
    
    # Convertir en epoch Unix pour query prices_1m
    try:
        event_epoch = int(event_ts.timestamp())
        end_epoch = int(end_time.timestamp())
        if debug:
            print(f"    [measure] epochs: {event_epoch} → {end_epoch}")
    except Exception as e:
        if debug:
            print(f"    [measure] ❌ Erreur conversion epoch: {e}")
        conn.close()
        return None'''

content = content.replace(old_func_start, new_func_start)

# Ajouter debug pour la requête prices
old_query_section = '''    try:
        prices = conn.execute(query).fetchall()
        conn.close()
        
        if len(prices) == 0:
            return None'''

new_query_section = '''    try:
        if debug:
            print(f"    [measure] Exécution query...")
            print(f"    [measure] Query: {query[:200]}...")
        
        prices = conn.execute(query).fetchall()
        
        if debug:
            print(f"    [measure] Prix trouvés: {len(prices)} bars")
        
        conn.close()
        
        if len(prices) == 0:
            if debug:
                print(f"    [measure] ❌ Aucun prix trouvé")
            return None'''

content = content.replace(old_query_section, new_query_section)

# Ajouter compteur debug
old_imports = '''import sys
from pathlib import Path'''

new_imports = '''import sys
from pathlib import Path

# Compteur pour limiter le debug
sys._backtest_debug_count = 0'''

content = content.replace(old_imports, new_imports)

# Incrémenter le compteur après chaque mesure
old_measure_call = '''            actual_reaction = measure_actual_market_reaction(
                event['ts_utc'],
                threshold_pips=threshold_pips,
                window_minutes=60
            )
            
            if idx < 3:
                print(f"  actual_reaction: {actual_reaction}")'''

new_measure_call = '''            actual_reaction = measure_actual_market_reaction(
                event['ts_utc'],
                threshold_pips=threshold_pips,
                window_minutes=60
            )
            
            sys._backtest_debug_count += 1
            
            if idx < 3:
                print(f"  actual_reaction: {actual_reaction}")'''

content = content.replace(old_measure_call, new_measure_call)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Debug ajouté à measure_actual_market_reaction")

PYEOF

echo ""
echo "Relancez: python backtest_latency_predictions.py"
