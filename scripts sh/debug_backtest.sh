#!/bin/bash

cd /Users/andrevalentin/Projects/eurusd_news_impact_calculator

echo "🐛 Ajout debug détaillé..."

python3 << 'PYEOF'
file_path = 'backtest_latency_predictions.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter debug après detect_event_family
old_code1 = '''            if idx < 3:
                print(f"  family: {family}, pattern: {pattern}")
            
            # Filtrer par famille si demandé
            if families_filter and family not in families_filter:
                continue
            
            if not family:
                continue
            
            # Calculer la surprise
            surprise = calculate_surprise_magnitude('''

new_code1 = '''            if idx < 3:
                print(f"  family: {family}, pattern: {pattern}")
            
            # Filtrer par famille si demandé
            if families_filter and family not in families_filter:
                if idx < 3:
                    print(f"  ❌ Filtré par families_filter")
                continue
            
            if not family:
                if idx < 3:
                    print(f"  ❌ Pas de famille détectée")
                continue
            
            if idx < 3:
                print(f"  ✅ Famille OK, calcul surprise...")
            
            # Calculer la surprise
            surprise = calculate_surprise_magnitude('''

content = content.replace(old_code1, new_code1)

# Ajouter debug après calcul surprise
old_code2 = '''            )
            
            # Obtenir la prédiction de latence
            try:
                stats = analyzer.calculate_family_latency_stats('''

new_code2 = '''            )
            
            if idx < 3:
                print(f"  surprise: {surprise:.2f}%")
            
            # Obtenir la prédiction de latence
            try:
                if idx < 3:
                    print(f"  Récupération stats latence...")
                
                stats = analyzer.calculate_family_latency_stats('''

content = content.replace(old_code2, new_code2)

# Ajouter debug après stats
old_code3 = '''                )
                
                if "error" in stats or 'latency_mean' not in stats:
                    continue'''

new_code3 = '''                )
                
                if idx < 3:
                    print(f"  stats: {stats}")
                
                if "error" in stats or 'latency_mean' not in stats:
                    if idx < 3:
                        print(f"  ❌ Stats invalides")
                    continue'''

content = content.replace(old_code3, new_code3)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Debug v2 ajouté")

PYEOF

echo ""
echo "Relancez: python backtest_latency_predictions.py"
