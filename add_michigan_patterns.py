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
