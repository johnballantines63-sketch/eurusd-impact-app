#!/usr/bin/env python3
"""
Correction Anchor Time - Cluster Principal
===========================================

Objectif : Corriger la détermination de l'anchor_time pour utiliser le cluster principal (US avec importance élevée)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

# Lire le fichier actuel
file_path = PROJECT_ROOT / 'scripts' / 'run_pipeline_complete.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print('='*100)
print('CORRECTION ANCHOR TIME - CLUSTER PRINCIPAL')
print('='*100)
print()

# Chercher la fonction etape3_definir_noyau_dur
import re

# Trouver où le cluster est sélectionné dans etape3
pattern_etape3 = r'def etape3_definir_noyau_dur\([^)]*\):.*?(?=def |\Z)'
match_etape3 = re.search(pattern_etape3, content, re.DOTALL)

if match_etape3:
    etape3_content = match_etape3.group(0)
    
    # Chercher où le cluster est utilisé
    # Le cluster est passé en paramètre, mais on doit identifier le cluster principal
    # parmi tous les clusters détectés
    
    print('📊 ANALYSE ACTUELLE')
    print('-'*100)
    print('Le cluster est passé en paramètre à etape3_definir_noyau_dur')
    print('Mais l\'anchor_time est déterminé dans etape2_detecter_clusters')
    print('comme le premier événement du cluster (ligne 297)')
    print()
    
    print('🔧 CORRECTION PROPOSÉE')
    print('-'*100)
    print('1. Dans etape2_detecter_clusters : Séparer clusters par pays')
    print('2. Identifier cluster principal (US avec score le plus élevé)')
    print('3. Utiliser anchor_time du cluster principal')
    print('4. Ou modifier etape3 pour recalculer anchor_time depuis core_events')
    print()

# Chercher etape2_detecter_clusters
pattern_etape2 = r'def etape2_detecter_clusters\([^)]*\):.*?(?=def |\Z)'
match_etape2 = re.search(pattern_etape2, content, re.DOTALL)

if match_etape2:
    etape2_content = match_etape2.group(0)
    
    # Chercher ligne avec anchor_time
    anchor_time_pattern = r'anchor_time\s*=\s*cluster_events\.iloc\[0\]\[\'ts_utc\'\]'
    if re.search(anchor_time_pattern, etape2_content):
        print('✅ Trouvé ligne anchor_time dans etape2_detecter_clusters')
        print('   Ligne actuelle : anchor_time = cluster_events.iloc[0][\'ts_utc\']')
        print()
        print('💡 SOLUTION 1 : Modifier etape2 pour séparer par pays')
        print('   - Grouper d\'abord par pays')
        print('   - Identifier cluster US principal')
        print('   - Utiliser son anchor_time')
        print()
        print('💡 SOLUTION 2 : Modifier etape3 pour recalculer anchor_time')
        print('   - Après identification core_events, trouver événement US avec score max')
        print('   - Utiliser son ts_utc comme anchor_time')
        print()

print('='*100)
print('✅ ANALYSE TERMINÉE')
print('='*100)




