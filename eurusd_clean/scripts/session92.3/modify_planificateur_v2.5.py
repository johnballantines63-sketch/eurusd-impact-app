"""
Script Session 92.3 : Modification automatique du Planificateur V2.4
=================================================================

Ce script modifie le Planificateur pour implémenter les amplifications calibrées.

AVANT D'EXÉCUTER :
1. Backup manuel du Planificateur recommandé
2. Vérifier que le chemin vers le Planificateur est correct

MODIFICATIONS APPORTÉES :
1. Ajout dictionnaire FAMILY_TO_TYPE
2. Ajout dictionnaire AMPLIFICATIONS_BY_TYPE  
3. Ajout fonction get_amplification_for_type()
4. Modification calculate_predictions() pour utiliser amplification dynamique
5. Ajout métadonnées amplification au return

Auteur : Session 92.3
Date : 27 octobre 2025
"""

from pathlib import Path
import re

# Chemins
BASE_DIR = Path(__file__).parent.parent.parent
PLANIFICATEUR_PATH = BASE_DIR / "fx_impact_app" / "streamlit_app" / "pages" / "5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 2.py"

# Backup automatique
BACKUP_PATH = PLANIFICATEUR_PATH.with_suffix('.py.backup_session92.3_avant_amplification_dynamique')

print("\n" + "="*80)
print("🔧 SCRIPT SESSION 92.3 : Modification Planificateur V2.4")
print("="*80)

# 1. Créer backup
print(f"\n📋 1. Création backup...")
print(f"   Source : {PLANIFICATEUR_PATH.name}")
print(f"   Backup : {BACKUP_PATH.name}")

with open(PLANIFICATEUR_PATH, 'r', encoding='utf-8') as f:
    original_content = f.read()

with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
    f.write(original_content)

print("   ✅ Backup créé")

# 2. Modifier header version
print(f"\n📝 2. Modification header (Version 2.4 → 2.5)...")
content = original_content

# Remplacer header
old_header = '''PLANIFICATEUR V2 - FORMULES VALIDÉES
=====================================

Version 2.4 - Session 68 (Single Wave Fort)
Utilise EXACTEMENT la méthode validée Session 55 + détection automatique type de mouvement'''

new_header = '''PLANIFICATEUR V2 - FORMULES VALIDÉES
=====================================

Version 2.5 - Session 92.3 (Amplifications Calibrées par Type)
Utilise EXACTEMENT la méthode validée Session 55 + amplifications dynamiques'''

content = content.replace(old_header, new_header)

# Ajouter mention Session 92.3
old_backup_line = "BACKUP SESSION 93 : Avant ajout facteurs d'amplification calibrés"
new_backup_line = """SESSION 92.3 : Amplifications calibrées par type (Grid Search Session 92.2)
- CPI: 2.2, NFP: 1.4, FOMC: 1.0, ISM: 0.5, Employment: 0.6, PMI: 0.6
- Détection type majoritaire (≥70%) avec fallback DEFAULT 2.5
- Amélioration MAE attendue : < 25 pips (vs 39.5 pips Session 91.2)"""

content = content.replace(old_backup_line, new_backup_line)

# Modifier markdown version
content = content.replace(
    'st.markdown("**Version 2.4** - Méthode Session 55 + détection automatique type mouvement (Session 68)")',
    'st.markdown("**Version 2.5** - Session 92.3 : Amplifications calibrées par type")'
)

print("   ✅ Header modifié")

# 3. Ajouter import Counter
print(f"\n📝 3. Ajout import Counter...")
old_imports = "from config import get_db_path\nimport duckdb"
new_imports = "from config import get_db_path\nimport duckdb\nfrom collections import Counter"
content = content.replace(old_imports, new_imports)
print("   ✅ Import ajouté")

# 4. Ajouter constantes et fonction
print(f"\n📝 4. Ajout constantes AMPLIFICATIONS_BY_TYPE et fonction get_amplification_for_type()...")

# Chercher la section "FONCTIONS - MÉTHODE SESSION 55"
section_marker = "# " + "═"*63 + "\n# FONCTIONS - MÉTHODE SESSION 55\n# " + "═"*63

new_section = '''# ═══════════════════════════════════════════════════════════════
# SESSION 92.3 : AMPLIFICATIONS CALIBRÉES PAR TYPE
# ═══════════════════════════════════════════════════════════════

# Mapping famille → type événement
FAMILY_TO_TYPE = {
    'CPI': 'CPI',
    'Core CPI': 'CPI',
    'CPI_YoY': 'CPI',
    'CPI_MoM': 'CPI',
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
    'CPI': 2.2,         # MAE: 10.8 pips (10 dates)
    'NFP': 1.4,         # MAE: 27.8 pips (10 dates)
    'FOMC': 1.0,        # MAE: 2.8 pips (3 dates)
    'ISM': 0.5,         # MAE: 7.4 pips (9 dates)
    'Employment': 0.6,  # MAE: 0.5 pips (1 date)
    'PMI': 0.6,         # MAE: 1.0 pips (1 date)
    'DEFAULT': 2.5      # Fallback pour types inconnus ou clusters mixtes
}


def get_amplification_for_type(events_df):
    """
    Détermine l'amplification selon le type événement dominant.
    
    Stratégie (Session 92.3) :
    1. Si 1 seul type unique → utiliser son amplification
    2. Si type majoritaire ≥70% → utiliser son amplification
    3. Sinon (cluster mixte) → DEFAULT 2.5
    
    Args:
        events_df: DataFrame des événements
    
    Returns:
        tuple: (amplification, type_detected, percentage)
    
    Examples:
        >>> get_amplification_for_type(cpi_events)
        (2.2, 'CPI', 100.0)  # 100% CPI
        
        >>> get_amplification_for_type(mixed_events)
        (2.5, 'MIXED', 50.0)  # 50% CPI, 50% NFP → DEFAULT
    """
    if events_df.empty:
        return 2.5, 'UNKNOWN', 0.0
    
    # Mapper familles → types
    types = [FAMILY_TO_TYPE.get(f, 'UNKNOWN') for f in events_df['family']]
    
    # Compter occurrences
    type_counts = Counter(types)
    
    # Cas 1 : Type unique
    if len(type_counts) == 1:
        dominant_type = list(type_counts.keys())[0]
        amplification = AMPLIFICATIONS_BY_TYPE.get(dominant_type, 2.5)
        return amplification, dominant_type, 100.0
    
    # Cas 2 : Type majoritaire (≥70%)
    most_common_type, count = type_counts.most_common(1)[0]
    percentage = (count / len(types)) * 100
    
    if percentage >= 70.0:
        amplification = AMPLIFICATIONS_BY_TYPE.get(most_common_type, 2.5)
        return amplification, most_common_type, percentage
    
    # Cas 3 : Cluster mixte
    return 2.5, 'MIXED', percentage


# ═══════════════════════════════════════════════════════════════
# FONCTIONS - MÉTHODE SESSION 55
# ═══════════════════════════════════════════════════════════════'''

content = content.replace(section_marker, new_section)
print("   ✅ Constantes et fonction ajoutées")

# 5. Modifier calculate_predictions()
print(f"\n📝 5. Modification calculate_predictions() - amplification dynamique...")

# Chercher et remplacer le bloc amplification
old_amplification_block = '''    # NOUVEAU : Ajuster le score (lignes 84-88)
    adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
    
    # Test avec amplification optimale 2.5 (lignes 90-96)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=2.5
    )'''

new_amplification_block = '''    # NOUVEAU : Ajuster le score (lignes 84-88)
    adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)
    
    # SESSION 92.3 : Amplification dynamique par type (lignes 90-96)
    amplification, type_detected, type_percentage = get_amplification_for_type(cpi_events)
    
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=amplification  # ← Dynamique selon type détecté
    )'''

content = content.replace(old_amplification_block, new_amplification_block)
print("   ✅ Amplification dynamique implémentée")

# 6. Ajouter métadonnées au return
print(f"\n📝 6. Ajout métadonnées amplification au return de calculate_predictions()...")

old_return = '''    return {
        'num_events': len(cpi_events),
        'base_score_avg': base_score_avg,
        'adjusted_score': adjusted_score,
        'max_surprise': max_surprise,
        'avg_surprise': avg_surprise,
        'impact_pips': impact,
        'ttr_minutes': ttr_predicted,
        'pullback_pips': pullback,
        'events': cpi_events,
        'movement_type': movement_type,
        'is_single_wave_strong': is_single_wave_strong,
        'is_double_wave': is_double_wave,
        'single_wave_timeline': single_wave_timeline,
        'double_wave_timeline': double_wave_timeline
    }'''

new_return = '''    return {
        'num_events': len(cpi_events),
        'base_score_avg': base_score_avg,
        'adjusted_score': adjusted_score,
        'max_surprise': max_surprise,
        'avg_surprise': avg_surprise,
        'impact_pips': impact,
        'ttr_minutes': ttr_predicted,
        'pullback_pips': pullback,
        'events': cpi_events,
        'movement_type': movement_type,
        'is_single_wave_strong': is_single_wave_strong,
        'is_double_wave': is_double_wave,
        'single_wave_timeline': single_wave_timeline,
        'double_wave_timeline': double_wave_timeline,
        # SESSION 92.3 : Métadonnées amplification
        'amplification': amplification,
        'type_detected': type_detected,
        'type_percentage': type_percentage
    }'''

content = content.replace(old_return, new_return)
print("   ✅ Métadonnées ajoutées")

# 7. Écrire fichier modifié
print(f"\n💾 7. Écriture fichier modifié...")
with open(PLANIFICATEUR_PATH, 'w', encoding='utf-8') as f:
    f.write(content)
print("   ✅ Fichier modifié sauvegardé")

# 8. Vérifications
print(f"\n🔍 8. Vérifications...")
verification_ok = True

# Vérifier présence des nouveaux éléments
checks = [
    ("AMPLIFICATIONS_BY_TYPE", "AMPLIFICATIONS_BY_TYPE" in content),
    ("FAMILY_TO_TYPE", "FAMILY_TO_TYPE" in content),
    ("get_amplification_for_type", "def get_amplification_for_type" in content),
    ("Amplification dynamique", "amplification, type_detected, type_percentage" in content),
    ("Import Counter", "from collections import Counter" in content),
    ("Version 2.5", "Version 2.5" in content),
]

for check_name, check_result in checks:
    status = "✅" if check_result else "❌"
    print(f"   {status} {check_name}")
    if not check_result:
        verification_ok = False

# Résultat final
print("\n" + "="*80)
if verification_ok:
    print("✅ SUCCÈS : Planificateur V2.5 modifié avec succès !")
    print("\n📁 Fichiers créés :")
    print(f"   - Backup : {BACKUP_PATH.name}")
    print(f"   - Modifié : {PLANIFICATEUR_PATH.name}")
    print("\n🎯 Prochaines étapes :")
    print("   1. Tester Planificateur sur date 11.09.2024")
    print("   2. Vérifier affichage badge amplification")
    print("   3. Valider impact prédit ~49-50 pips (au lieu de 56 pips)")
    print("   4. Tester sur 4+ autres dates")
else:
    print("❌ ERREUR : Certaines modifications ont échoué")
    print("   → Restaurer depuis backup si nécessaire")
print("="*80)
