#!/bin/bash
# ========================================
# Script Tout-en-Un : Patterns Michigan
# ========================================

set -e

echo "=========================================="
echo "🚀 SETUP PATTERNS MICHIGAN"
echo "=========================================="
echo ""

# ========================================
# ÉTAPE 1 : Créer add_michigan_patterns.py
# ========================================
echo "📝 Création script ajout patterns..."
cat > add_michigan_patterns.py << 'ENDSCRIPT1'
#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil

FILE = Path("fx_impact_app/src/event_families.py")
BACKUP_DIR = Path("fx_impact_app/src/backups")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
backup = BACKUP_DIR / f"event_families_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
shutil.copy2(FILE, backup)
print(f"✅ Backup: {backup}")

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

new_patterns = """
    # Michigan Consumer Sentiment - Composantes détaillées
    'Michigan_Inflation_Expectations': r'(?i)michigan.*inflation.*expectation(?!.*5.*year)',
    'Michigan_5Y_Inflation_Expectations': r'(?i)michigan.*(5|five).*year.*inflation',
    'Michigan_Consumer_Expectations': r'(?i)michigan.*consumer.*expectation',
    'Michigan_Current_Conditions': r'(?i)michigan.*current.*condition',
    
    # Inflation Expectations (sans Michigan)
    'Inflation_Expectations': r'(?i)^inflation.*expectation(?!.*michigan)',
    
    # Baker Hughes
    'Baker_Hughes_Rig_Count': r'(?i)baker.*hughes.*(rig|oil).*count',
    
    # Budget variants
    'Federal_Budget': r'(?i)federal.*budget',
    'Monthly_Budget_Statement': r'(?i)monthly.*budget.*statement',
"""

if "'Consumer_Confidence':" in content:
    lines = content.split('\n')
    insert_idx = None
    for i, line in enumerate(lines):
        if "'Consumer_Confidence':" in line:
            for j in range(i+1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    insert_idx = j
                    break
            break
    
    if insert_idx:
        lines.insert(insert_idx, new_patterns)
        new_content = '\n'.join(lines)
    else:
        print("❌ Position d'insertion non trouvée")
        exit(1)
else:
    print("❌ Consumer_Confidence non trouvé")
    exit(1)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Patterns ajoutés avec succès")
ENDSCRIPT1

chmod +x add_michigan_patterns.py
echo "✅ Script 1 créé"
echo ""

# ========================================
# ÉTAPE 2 : Créer recalculate_michigan_scores.py
# ========================================
echo "📝 Création script calcul scores..."
cat > recalculate_michigan_scores.py << 'ENDSCRIPT2'
#!/usr/bin/env python3
import sys
from pathlib import Path

src_path = Path(__file__).parent / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
from event_families import FAMILY_PATTERNS
from scoring_engine import ScoringEngine

print("=" * 70)
print("📊 RECALCUL SCORES EMPIRIQUES - Patterns Michigan")
print("=" * 70)
print()

new_families = [
    'Michigan_Inflation_Expectations',
    'Michigan_5Y_Inflation_Expectations',
    'Michigan_Consumer_Expectations',
    'Michigan_Current_Conditions',
    'Inflation_Expectations',
    'Baker_Hughes_Rig_Count',
    'Federal_Budget',
    'Monthly_Budget_Statement'
]

print(f"🎯 Calcul pour {len(new_families)} nouvelles familles")
print()

engine = ScoringEngine(get_db_path())

results = []
for family in new_families:
    if family not in FAMILY_PATTERNS:
        print(f"⚠️  {family}: Pattern non trouvé")
        continue
    
    print(f"⏳ {family:45}...", end=" ")
    
    try:
        score = engine.calculate_empirical_score(
            family_pattern=FAMILY_PATTERNS[family],
            lookback_years=3,
            min_events=3
        )
        
        if score:
            results.append({
                'family': family,
                'score': score['empirical_score'],
                'impact': score['empirical_impact'],
                'n_events': score['n_events']
            })
            print(f"✅ Score: {score['empirical_score']:3.0f} ({score['empirical_impact']:6}) - {score['n_events']} events")
        else:
            print(f"⚠️  Pas assez de données")
    except Exception as e:
        print(f"❌ {e}")

engine.close()

print()
print("=" * 70)
print("📊 RÉSUMÉ")
print("=" * 70)
print()

if results:
    print(f"✅ {len(results)} familles calculées:")
    print()
    for r in results:
        icon = "🔴" if r['impact'] == "HIGH" else "🟡" if r['impact'] == "MEDIUM" else "🟢"
        print(f"{icon} {r['family']:40} Score: {r['score']:3.0f}")
else:
    print("❌ Aucun score calculé")

print()
print("🔄 Redémarrez Streamlit pour voir les changements")
ENDSCRIPT2

chmod +x recalculate_michigan_scores.py
echo "✅ Script 2 créé"
echo ""

# ========================================
# ÉTAPE 3 : Exécuter
# ========================================
echo "=========================================="
echo "⚡ EXÉCUTION"
echo "=========================================="
echo ""

echo "🔧 Étape 1/2 : Ajout patterns..."
python3 add_michigan_patterns.py
echo ""

echo "📊 Étape 2/2 : Calcul scores (peut prendre 1-2 min)..."
python3 recalculate_michigan_scores.py
echo ""

# ========================================
# FIN
# ========================================
echo "=========================================="
echo "🎉 TERMINÉ !"
echo "=========================================="
echo ""
echo "📋 Prochaines étapes :"
echo "1. Redémarrer Streamlit :"
echo "   streamlit run fx_impact_app/streamlit_app/Home.py"
echo ""
echo "2. Tester :"
echo "   - Planificateur Multi-Événements"
echo "   - Date : 10 octobre 2025"
echo "   - Pays : US"
echo "   - Charger événements"
echo ""
echo "✅ Attendu : 12 événements avec scores complets"
echo ""
