#!/bin/bash

# Script pour corriger les timestamps dans backtest_latency_predictions.py

cd /Users/andrevalentin/Projects/eurusd_news_impact_calculator

echo "🔧 Correction du script de backtesting..."

python3 << 'PYEOF'
import re

file_path = 'backtest_latency_predictions.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Créer un backup
with open(file_path + '.backup_timestamp', 'w', encoding='utf-8') as f:
    f.write(content)

print("💾 Backup créé: backtest_latency_predictions.py.backup_timestamp")

# Correction 1: Remplacer ts_utc par timestamp dans la requête prices_1m
content = re.sub(
    r"SELECT\s+ts_utc,\s+open, high, low, close\s+FROM prices_1m",
    "SELECT timestamp, open, high, low, close FROM prices_1m",
    content
)

# Correction 2: Ajouter la conversion epoch avant la requête
# Chercher la ligne "end_time = event_ts + timedelta"
pattern = r"(end_time = event_ts \+ timedelta\(minutes=window_minutes\))\s*\n\s*query = "
replacement = r"\1\n    \n    # Convertir en epoch Unix pour query prices_1m\n    event_epoch = int(event_ts.timestamp())\n    end_epoch = int(end_time.timestamp())\n    \n    query = "
content = re.sub(pattern, replacement, content)

# Correction 3: Remplacer les conditions WHERE avec epoch
content = re.sub(
    r"WHERE ts_utc >= '\{event_ts\.isoformat\(\)\}'",
    "WHERE timestamp >= {event_epoch}",
    content
)

content = re.sub(
    r"AND ts_utc <= '\{end_time\.isoformat\(\)\}'",
    "AND timestamp <= {end_epoch}",
    content
)

# Correction 4: ORDER BY
content = re.sub(
    r"ORDER BY ts_utc ASC",
    "ORDER BY timestamp ASC",
    content
)

# Correction 5: Dans la boucle de traitement des prix, mettre à jour la référence
# Chercher "for i, (ts, price) in enumerate(prices):"
# et s'assurer que ts est bien le timestamp epoch
content = re.sub(
    r"(\s+)# Prix de référence \(première minute\)\s+ref_price = prices\[0\]\[1\]",
    r"\1# Prix de référence (première minute)\n\1ref_price = prices[0][1]",
    content
)

# Sauvegarder
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Corrections appliquées:")
print("   - ts_utc → timestamp")
print("   - Ajout conversion epoch")
print("   - WHERE clauses mises à jour")
print("   - ORDER BY corrigé")

PYEOF

echo ""
echo "✅ Script corrigé !"
echo ""
echo "Relancez maintenant:"
echo "  python backtest_latency_predictions.py"
