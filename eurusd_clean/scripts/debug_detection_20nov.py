"""
Debug : Pourquoi le mouvement à 14:29 n'est pas détecté pour le 20.11.2025
==========================================================================
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app' / 'pages'))

# Importer directement les fonctions sans Streamlit
import importlib.util
spec = importlib.util.spec_from_file_location(
    "planificateur", 
    PROJECT_ROOT / 'streamlit_app' / 'pages' / 'Planificateur_V3_CLEAN.py'
)
planificateur = importlib.util.module_from_spec(spec)
# Éviter les imports Streamlit en définissant un mock
import types
planificateur.st = types.SimpleNamespace()
planificateur.st.spinner = lambda x: types.SimpleNamespace(__enter__=lambda self: None, __exit__=lambda *args: None)
planificateur.st.success = lambda x: None
planificateur.st.warning = lambda x: None
planificateur.st.info = lambda x: None
planificateur.st.caption = lambda x: None
planificateur.st.metric = lambda *args, **kwargs: None
planificateur.st.columns = lambda n: [types.SimpleNamespace() for _ in range(n)]
planificateur.st.expander = lambda *args, **kwargs: types.SimpleNamespace(__enter__=lambda self: self, __exit__=lambda *args: None)
planificateur.st.dataframe = lambda *args, **kwargs: None
planificateur.st.subheader = lambda x: None
planificateur.st.header = lambda x: None
planificateur.st.selectbox = lambda *args, **kwargs: None
planificateur.st.slider = lambda *args, **kwargs: 35.0
planificateur.st.number_input = lambda *args, **kwargs: 35.0
planificateur.st.multiselect = lambda *args, **kwargs: ['US', 'EU']
planificateur.st.radio = lambda *args, **kwargs: "Saisie manuelle"
planificateur.st.text_input = lambda *args, **kwargs: "2025-11-20"
planificateur.st.select_slider = lambda *args, **kwargs: 2
planificateur.st.session_state = {}

spec.loader.exec_module(planificateur)

scan_price_movements = planificateur.scan_price_movements
detect_pattern_type = planificateur.detect_pattern_type

DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'

print("=" * 80)
print("🔍 DEBUG : DÉTECTION MOUVEMENT 20.11.2025")
print("=" * 80)
print()

# Date cible
target_date = datetime(2025, 11, 20)
timezone_str = 'Europe/Zurich'
tz = pytz.timezone(timezone_str)

print(f"📅 Date analysée : {target_date.strftime('%Y-%m-%d')}")
print()

# Charger les prix
conn = duckdb.connect(str(DB_PATH), read_only=True)

date_start = target_date.replace(hour=0, minute=0, second=0)
date_end = target_date.replace(hour=23, minute=59, second=59)

query_prices = """
SELECT 
    datetime as ts,
    open,
    high,
    low,
    close
FROM prices_bern
WHERE DATE(datetime) = ?
ORDER BY datetime
"""

df_prices = conn.execute(query_prices, [target_date.strftime('%Y-%m-%d')]).df()

if df_prices.empty:
    print("❌ Aucun prix trouvé pour cette date")
    conn.close()
    sys.exit(1)

# Convertir l'index en datetime avec timezone
df_prices['datetime'] = pd.to_datetime(df_prices['ts'])
df_prices = df_prices.set_index('datetime')
# Vérifier si déjà timezone-aware
if df_prices.index.tz is None:
    df_prices.index = df_prices.index.tz_localize(timezone_str)
else:
    df_prices.index = df_prices.index.tz_convert(timezone_str)

print(f"✅ {len(df_prices)} bougies de prix chargées")
print(f"   Période : {df_prices.index.min()} à {df_prices.index.max()}")
print()

# Filtrer autour de 14h00-16h00 pour voir les mouvements
df_prices_window = df_prices[
    (df_prices.index.hour >= 14) & 
    (df_prices.index.hour < 16)
].copy()

print(f"📊 Prix autour de 14h-16h : {len(df_prices_window)} bougies")
print()

# Vérifier le mouvement explosif à 14:29
print("1️⃣ VÉRIFICATION MOUVEMENT EXPLOSIF À 14:29")
print("-" * 80)

# Chercher la bougie à 14:29
candle_1429 = df_prices_window[df_prices_window.index.hour == 14]
candle_1429 = candle_1429[candle_1429.index.minute == 29]

if not candle_1429.empty:
    candle = candle_1429.iloc[0]
    candle_range = (candle['high'] - candle['low']) * 10000
    print(f"   ✅ Bougie à 14:29 trouvée")
    print(f"   Open: {candle['open']:.5f}, High: {candle['high']:.5f}, Low: {candle['low']:.5f}, Close: {candle['close']:.5f}")
    print(f"   Range: {candle_range:.1f} pips")
    
    if candle_range >= 15.0:
        print(f"   ✅ MOUVEMENT EXPLOSIF DÉTECTÉ ({candle_range:.1f} pips >= 15)")
    else:
        print(f"   ⚠️  Mouvement trop faible ({candle_range:.1f} pips < 15)")
else:
    print("   ❌ Aucune bougie à 14:29 trouvée")
    # Chercher la bougie la plus proche
    candle_1429_approx = df_prices_window[
        (df_prices_window.index.hour == 14) & 
        (df_prices_window.index.minute >= 28) &
        (df_prices_window.index.minute <= 30)
    ]
    if not candle_1429_approx.empty:
        print(f"   📍 Bougies proches de 14:29 trouvées :")
        for idx, row in candle_1429_approx.iterrows():
            range_pips = (row['high'] - row['low']) * 10000
            print(f"      {idx.strftime('%H:%M')} : Range = {range_pips:.1f} pips")

print()

# Scanner tous les mouvements
print("2️⃣ SCAN DE TOUS LES MOUVEMENTS")
print("-" * 80)

movements = scan_price_movements(df_prices, min_pips=35.0)

print(f"   ✅ {len(movements)} mouvement(s) détecté(s)")
print()

if movements:
    print("   Détails des mouvements :")
    for i, mov in enumerate(movements, 1):
        start_ts = pd.Timestamp(mov['start_time'])
        peak_ts = pd.Timestamp(mov['peak_time'])
        is_explosive = mov.get('is_explosive', False)
        explosive_mark = "💥 EXPLOSIF" if is_explosive else "📈 Normal"
        
        print(f"   {i}. {explosive_mark}")
        print(f"      Début: {start_ts.strftime('%H:%M')} | Pic: {peak_ts.strftime('%H:%M')}")
        print(f"      Impact: {mov['impact_pips']:.1f} pips | Direction: {mov['direction']}")
        print(f"      Baseline: {mov['baseline_price']:.5f}")
        print()

# Vérifier si le mouvement à 14:29 est dans la liste
print("3️⃣ VÉRIFICATION MOUVEMENT 14:29 DANS LA LISTE")
print("-" * 80)

movement_1429 = None
for mov in movements:
    start_ts = pd.Timestamp(mov['start_time'])
    if start_ts.hour == 14 and start_ts.minute >= 28 and start_ts.minute <= 30:
        movement_1429 = mov
        break

if movement_1429:
    print(f"   ✅ Mouvement à 14:29 trouvé dans la liste")
    print(f"      Impact: {movement_1429['impact_pips']:.1f} pips")
    print(f"      Explosif: {movement_1429.get('is_explosive', False)}")
else:
    print(f"   ❌ Mouvement à 14:29 NON trouvé dans la liste")
    print(f"   → Il n'a peut-être pas été détecté par scan_price_movements")
    print()

# Charger les événements pour obtenir l'heure du cluster
print("4️⃣ VÉRIFICATION HEURE DU CLUSTER")
print("-" * 80)

query_events = """
SELECT 
    datetime_utc as ts_utc,
    event_name as event_key,
    country
FROM economic_events
WHERE DATE(datetime_utc) = ?
  AND country IN ('US', 'DE', 'EU')
  AND actual IS NOT NULL
ORDER BY datetime_utc
"""

df_events = conn.execute(query_events, [target_date.strftime('%Y-%m-%d')]).df()

if not df_events.empty:
    df_events['ts_bern'] = pd.to_datetime(df_events['ts_utc']).dt.tz_localize('UTC').dt.tz_convert(timezone_str)
    
    # Filtrer autour de 14h30-15h30
    events_cluster = df_events[
        (df_events['ts_bern'].dt.hour >= 14) & 
        (df_events['ts_bern'].dt.hour < 16)
    ]
    
    print(f"   ✅ {len(events_cluster)} événement(s) autour de 14h-16h")
    
    if not events_cluster.empty:
        cluster_anchor_time = events_cluster['ts_bern'].min()
        print(f"   📍 Heure du cluster (premier événement) : {cluster_anchor_time.strftime('%H:%M')}")
        print()
        
        # Vérifier si le mouvement à 14:29 est dans la fenêtre
        window_start = cluster_anchor_time - pd.Timedelta(minutes=60)
        window_end = cluster_anchor_time + pd.Timedelta(minutes=120)
        
        print(f"   Fenêtre de recherche : {window_start.strftime('%H:%M')} à {window_end.strftime('%H:%M')}")
        print()
        
        movements_in_window = [
            m for m in movements
            if window_start <= pd.Timestamp(m['start_time']) <= window_end
        ]
        
        print(f"   ✅ {len(movements_in_window)} mouvement(s) dans la fenêtre")
        if movements_in_window:
            print("   Mouvements dans la fenêtre :")
            for i, mov in enumerate(movements_in_window, 1):
                start_ts = pd.Timestamp(mov['start_time'])
                is_explosive = mov.get('is_explosive', False)
                explosive_mark = "💥 EXPLOSIF" if is_explosive else "📈 Normal"
                print(f"      {i}. {explosive_mark} - {start_ts.strftime('%H:%M')} - {mov['impact_pips']:.1f} pips")
            
            # Trouver le plus fort
            strongest = max(movements_in_window, key=lambda x: x['impact_pips'])
            print()
            print(f"   🏆 Mouvement le plus fort dans la fenêtre :")
            print(f"      {pd.Timestamp(strongest['start_time']).strftime('%H:%M')} - {strongest['impact_pips']:.1f} pips")
            print(f"      Explosif: {strongest.get('is_explosive', False)}")
        else:
            print("   ⚠️  Aucun mouvement dans la fenêtre !")
            print("   → Le système utilisera le mouvement le plus proche ou le plus fort globalement")
    else:
        print("   ⚠️  Aucun événement trouvé autour de 14h-16h")
else:
    print("   ❌ Aucun événement trouvé pour cette date")

conn.close()

print()
print("=" * 80)
print("✅ DEBUG TERMINÉ")
print("=" * 80)

