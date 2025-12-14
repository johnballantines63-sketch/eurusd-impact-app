#!/bin/bash

cd /Users/andrevalentin/Projects/eurusd_news_impact_calculator

echo "🔧 Correction des clés stats..."

python3 << 'PYEOF'
file_path = 'backtest_latency_predictions.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer la vérification des stats invalides
old_check = """                if "error" in stats or 'latency_mean' not in stats:
                    if idx < 3:
                        print(f"  ❌ Stats invalides")
                    continue
                
                predicted_latency = stats['latency_mean']
                predicted_peak = stats['peak_mean']
                predicted_movement = stats['movement_mean']"""

new_check = """                if "error" in stats:
                    if idx < 3:
                        print(f"  ❌ Stats avec erreur")
                    continue
                
                # Adapter aux nouvelles clés de stats
                if 'initial_reaction' not in stats or 'peak_timing' not in stats:
                    if idx < 3:
                        print(f"  ❌ Structure stats invalide")
                    continue
                
                predicted_latency = stats['initial_reaction']['mean_minutes']
                predicted_peak = stats['peak_timing']['mean_minutes']
                predicted_movement = stats['peak_timing']['mean_movement_pips']"""

content = content.replace(old_check, new_check)

# Sauvegarder
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Clés stats corrigées")
print("   latency_mean → initial_reaction.mean_minutes")
print("   peak_mean → peak_timing.mean_minutes")
print("   movement_mean → peak_timing.mean_movement_pips")

PYEOF

echo ""
echo "Relancez: python backtest_latency_predictions.py"
