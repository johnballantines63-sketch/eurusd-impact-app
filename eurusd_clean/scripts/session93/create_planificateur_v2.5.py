#!/usr/bin/env python3
"""
Script de création Planificateur V2.5 avec amplifications calibrées
Session 93 → Session 94
Applique les 7 modifications Session 92.4 sur fichier copie 3 (baseline V2.4)
"""

import shutil
from pathlib import Path

print("=" * 70)
print("🔧 CRÉATION PLANIFICATEUR V2.5 - SESSION 93")
print("=" * 70)

# Chemins
pages_dir = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages")
source_file = pages_dir / "5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 3.py"
dest_file = pages_dir / "5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 2.py"

print(f"\n📁 Fichiers:")
print(f"   Source (V2.4) : copie 3.py")
print(f"   Destination (V2.5) : copie 2.py")

# Vérifier que source existe
if not source_file.exists():
    print(f"\n❌ ERREUR : Fichier source introuvable !")
    print(f"   Chemin : {source_file}")
    exit(1)

print(f"   ✅ Source existe ({source_file.stat().st_size} octets)")

# Étape 1 : Backup fichier cassé s'il existe
if dest_file.exists():
    backup_broken = str(dest_file) + ".broken_session92.4"
    print(f"\n📦 Backup fichier cassé...")
    shutil.copy2(dest_file, backup_broken)
    print(f"   ✅ Sauvegardé : {Path(backup_broken).name}")

# Étape 2 : Copier le bon fichier
print(f"\n📋 Copie fichier source...")
shutil.copy2(source_file, dest_file)
print(f"   ✅ Copié ({dest_file.stat().st_size} octets)")

# Étape 3 : Lire le contenu
print(f"\n📖 Lecture contenu...")
with open(dest_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"   Taille originale : {len(content)} caractères")

# Étape 4 : Appliquer les modifications
print(f"\n🔧 Application des 7 modifications Session 92.4...")

modifications = []

# Modification 1 : Header Version
old = 'Version 2.4 - Session 68 (Single Wave Fort)\nUtilise EXACTEMENT la méthode validée Session 55 + détection automatique type de mouvement'
new = '''Version 2.5 - Session 92.4 (Amplifications Calibrées par Type)
Utilise EXACTEMENT la méthode validée Session 55 + amplifications dynamiques selon type événement

SESSION 92.4 : Amplifications calibrées par type (Grid Search Session 92.2)
- CPI: 2.2, NFP: 1.4, FOMC: 1.0, ISM: 0.5, Employment: 0.6, PMI: 0.6
- Détection type majoritaire (≥70%) avec fallback DEFAULT 2.5
- Amélioration MAE attendue : < 25 pips (vs 39.5 pips Session 91.2)'''

if old in content:
    content = content.replace(old, new)
    modifications.append("✅ Modification 1 : Header Version 2.5")
    print("   ✅ 1/7 Header Version 2.5")
else:
    print("   ⚠️  1/7 Header non trouvé (déjà modifié ?)")

# Modification 2 : st.markdown
old = 'st.markdown("**Version 2.4** - Méthode Session 55 + détection automatique type mouvement (Session 68)")'
new = 'st.markdown("**Version 2.5** - Amplifications calibrées par type (Session 92.4) + Méthode Session 55")'

if old in content:
    content = content.replace(old, new)
    modifications.append("✅ Modification 2 : st.markdown Version 2.5")
    print("   ✅ 2/7 st.markdown Version 2.5")
else:
    print("   ⚠️  2/7 st.markdown non trouvé")

# Modification 3 : Import Counter
old = 'from config import get_db_path\nimport duckdb'
new = 'from config import get_db_path\nimport duckdb\nfrom collections import Counter'

if old in content and 'from collections import Counter' not in content:
    content = content.replace(old, new)
    modifications.append("✅ Modification 3 : Import Counter")
    print("   ✅ 3/7 Import Counter")
elif 'from collections import Counter' in content:
    print("   ⚠️  3/7 Counter déjà importé")
else:
    print("   ⚠️  3/7 Import section non trouvée")

# Modification 4 : Constantes après CONFIGURATION PAGE
marker = '# ═══════════════════════════════════════════════════════════════\n# CONFIGURATION PAGE\n# ═══════════════════════════════════════════════════════════════'

constants = '''

# ═══════════════════════════════════════════════════════════════
# SESSION 92.4 : AMPLIFICATIONS CALIBRÉES PAR TYPE
# ═══════════════════════════════════════════════════════════════

# Mapping famille → type événement
FAMILY_TO_TYPE = {
    'CPI': 'CPI',
    'Core CPI': 'CPI',
    'Inflation': 'CPI',
    'NFP': 'NFP',
    'Nonfarm Payrolls': 'NFP',
    'FOMC': 'FOMC',
    'ISM': 'ISM',
    'ISM Manufacturing': 'ISM',
    'ISM Services': 'ISM',
    'Jobless Claims': 'Employment',
    'Unemployment': 'Employment',
    'PMI': 'PMI',
    'Retail Sales': 'Retail',
}

# Amplifications calibrées (Session 92.2 - Grid Search 29,700 combinaisons)
AMPLIFICATIONS_BY_TYPE = {
    'CPI': 2.2,
    'NFP': 1.4,
    'FOMC': 1.0,
    'ISM': 0.5,
    'Employment': 0.6,
    'PMI': 0.6,
    'DEFAULT': 2.5
}


def get_amplification_for_type(events_df):
    """
    Détermine l'amplification selon le type événement dominant.
    
    Stratégie (Session 92.3) :
    1. Si 1 seul type unique → utiliser son amplification
    2. Si type majoritaire ≥70% → utiliser son amplification
    3. Sinon (cluster mixte) → DEFAULT 2.5
    
    Returns:
        tuple: (amplification, type_detected, percentage)
    """
    if events_df.empty:
        return 2.5, 'UNKNOWN', 0.0
    
    types = [FAMILY_TO_TYPE.get(f, 'UNKNOWN') for f in events_df['family']]
    type_counts = Counter(types)
    
    if len(type_counts) == 1:
        dominant_type = list(type_counts.keys())[0]
        amplification = AMPLIFICATIONS_BY_TYPE.get(dominant_type, 2.5)
        return amplification, dominant_type, 100.0
    
    most_common_type, count = type_counts.most_common(1)[0]
    percentage = (count / len(types)) * 100
    
    if percentage >= 70.0:
        amplification = AMPLIFICATIONS_BY_TYPE.get(most_common_type, 2.5)
        return amplification, most_common_type, percentage
    
    return 2.5, 'MIXED', percentage


'''

if marker in content and 'FAMILY_TO_TYPE' not in content:
    content = content.replace(marker, constants + marker)
    modifications.append("✅ Modification 4 : Constantes + fonction")
    print("   ✅ 4/7 Constantes FAMILY_TO_TYPE + fonction")
elif 'FAMILY_TO_TYPE' in content:
    print("   ⚠️  4/7 Constantes déjà présentes")
else:
    print("   ⚠️  4/7 Marker CONFIGURATION PAGE non trouvé")

# Modification 5 : Amplification dynamique
old = '''    # Test avec amplification optimale 2.5 (lignes 90-96)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=2.5
    )'''

new = '''    # SESSION 92.4 : Amplification dynamique par type
    amplification, type_detected, type_percentage = get_amplification_for_type(cpi_events)
    
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=amplification
    )'''

if old in content:
    content = content.replace(old, new)
    modifications.append("✅ Modification 5 : Amplification dynamique")
    print("   ✅ 5/7 Amplification dynamique")
else:
    print("   ⚠️  5/7 Section amplification non trouvée")

# Modification 6 : Métadonnées return
old = '''        'is_single_wave_strong': is_single_wave_strong,
        'is_double_wave': is_double_wave,
        'single_wave_timeline': single_wave_timeline,
        'double_wave_timeline': double_wave_timeline
    }'''

new = '''        'is_single_wave_strong': is_single_wave_strong,
        'is_double_wave': is_double_wave,
        'single_wave_timeline': single_wave_timeline,
        'double_wave_timeline': double_wave_timeline,
        'amplification': amplification,
        'type_detected': type_detected,
        'type_percentage': type_percentage
    }'''

if old in content and "'amplification':" not in content:
    content = content.replace(old, new)
    modifications.append("✅ Modification 6 : Métadonnées return")
    print("   ✅ 6/7 Métadonnées amplification au return")
elif "'amplification':" in content:
    print("   ⚠️  6/7 Métadonnées déjà présentes")
else:
    print("   ⚠️  6/7 Section return non trouvée")

# Modification 7 : Badge UI
marker = '''    st.markdown(f"### {badge_color.get(movement_type, '⚪')} Type : **{movement_type}**")
    
    # Détails calcul'''

insert = '''    st.markdown(f"### {badge_color.get(movement_type, '⚪')} Type : **{movement_type}**")
    
    # SESSION 92.4 : Badge amplification calibrée
    st.info(f"""
    📊 **Amplification Calibrée (Session 92.4)**
    
    - Type détecté : **{predictions['type_detected']}** ({predictions['type_percentage']:.1f}%)
    - Amplification appliquée : **{predictions['amplification']}x**
    - Calibration : Grid Search 29,700 combinaisons (Session 92.2)
    
    {f"✅ Type majoritaire ≥70%" if predictions['type_percentage'] >= 70 else "⚠️ Cluster mixte → DEFAULT 2.5"}
    """)
    
    # Détails calcul'''

if marker in content and '# SESSION 92.4 : Badge amplification' not in content:
    content = content.replace(marker, insert)
    modifications.append("✅ Modification 7 : Badge UI")
    print("   ✅ 7/7 Badge UI amplification")
elif '# SESSION 92.4 : Badge amplification' in content:
    print("   ⚠️  7/7 Badge déjà présent")
else:
    print("   ⚠️  7/7 Section badge non trouvée")

# Étape 5 : Écrire le fichier modifié
print(f"\n💾 Écriture fichier modifié...")
with open(dest_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"   Taille finale : {len(content)} caractères")
print(f"   ✅ Fichier écrit")

# Résumé
print(f"\n" + "=" * 70)
if len(modifications) == 7:
    print(f"✅ SUCCÈS COMPLET - Planificateur V2.5 créé !")
elif len(modifications) >= 5:
    print(f"⚠️  SUCCÈS PARTIEL - {len(modifications)}/7 modifications appliquées")
else:
    print(f"❌ ÉCHEC - Seulement {len(modifications)}/7 modifications appliquées")

print(f"\n📊 Modifications appliquées : {len(modifications)}/7")
for mod in modifications:
    print(f"   {mod}")

if len(modifications) < 7:
    print(f"\n⚠️  Certaines modifications non appliquées.")
    print(f"   Raison probable : Fichier déjà modifié ou structure différente")
    print(f"   Action : Vérifier manuellement le fichier")

print(f"\n📁 Fichier créé :")
print(f"   {dest_file}")

print(f"\n🚀 Prochaine étape : Tester avec Streamlit")
print(f"\nCommande :")
print(f'   cd fx_impact_app')
print(f'   streamlit run "streamlit_app/pages/{dest_file.name}"')

print(f"\n" + "=" * 70)
