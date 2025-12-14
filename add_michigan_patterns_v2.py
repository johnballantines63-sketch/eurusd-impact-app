#!/usr/bin/env python3
"""Version robuste - Insère à la fin du dictionnaire FAMILY_PATTERNS"""
from pathlib import Path
from datetime import datetime
import shutil
import re

FILE = Path("fx_impact_app/src/event_families.py")
BACKUP_DIR = Path("fx_impact_app/src/backups")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
backup = BACKUP_DIR / f"event_families_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
shutil.copy2(FILE, backup)
print(f"✅ Backup: {backup}")

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Nouveaux patterns
new_patterns = """    # Michigan Consumer Sentiment - Composantes détaillées
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

# Chercher FAMILY_PATTERNS = {
if 'FAMILY_PATTERNS' not in content:
    print("❌ FAMILY_PATTERNS non trouvé")
    exit(1)

# Méthode robuste : trouver la fermeture du dictionnaire FAMILY_PATTERNS
# Chercher le pattern : FAMILY_PATTERNS = { ... }
pattern_start = content.find('FAMILY_PATTERNS')
if pattern_start == -1:
    print("❌ FAMILY_PATTERNS non trouvé")
    exit(1)

# Trouver l'ouverture du dictionnaire
brace_start = content.find('{', pattern_start)
if brace_start == -1:
    print("❌ Ouverture dictionnaire non trouvée")
    exit(1)

# Trouver la fermeture du dictionnaire (en comptant les accolades)
brace_count = 1
pos = brace_start + 1
while pos < len(content) and brace_count > 0:
    if content[pos] == '{':
        brace_count += 1
    elif content[pos] == '}':
        brace_count -= 1
    pos += 1

if brace_count != 0:
    print("❌ Fermeture dictionnaire non trouvée")
    exit(1)

# pos pointe maintenant juste après le '}'
# On insère juste avant le '}'
insert_pos = pos - 1

# Vérifier qu'il y a une virgule avant
before_insert = content[max(0, insert_pos-100):insert_pos].strip()
if not before_insert.endswith(','):
    # Ajouter une virgule à la fin du dernier pattern
    new_patterns = ',' + new_patterns

new_content = content[:insert_pos] + '\n' + new_patterns + '\n' + content[insert_pos:]

# Écrire
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Patterns ajoutés avec succès")
print(f"📊 Position d'insertion: caractère {insert_pos}")
print(f"📊 Taille: {len(content)} → {len(new_content)} caractères")
