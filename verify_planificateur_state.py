"""
Vérification état actuel du Planificateur V2.4.1
"""

from pathlib import Path

PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")
PLANIFICATEUR_PATH = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py"

print("="*60)
print("VÉRIFICATION PLANIFICATEUR V2.4.1")
print("="*60)

with open(PLANIFICATEUR_PATH, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# 1. Vérifier version
print("\n1. VERSION:")
for i, line in enumerate(lines[:10]):
    if 'Version' in line:
        print(f"   Ligne {i+1}: {line.strip()}")
        break

# 2. Chercher la section de détection
print("\n2. SECTION DÉTECTION TYPE MOUVEMENT:")
for i, line in enumerate(lines):
    if 'Calculer timeline selon le type' in line:
        print(f"\n   Trouvée à ligne {i+1}")
        print("\n   Extrait (30 lignes suivantes):")
        for j in range(i, min(i+35, len(lines))):
            print(f"   {j+1:4d}: {lines[j]}")
        break

# 3. Vérifier ordre if/elif
print("\n3. VÉRIFICATION HIÉRARCHIE:")

# Chercher positions
swf_if_pos = -1
dw_elif_pos = -1
dw_if_pos = -1

for i, line in enumerate(lines):
    if 'if is_single_wave_strong:' in line:
        swf_if_pos = i
    if 'elif is_double_wave:' in line:
        dw_elif_pos = i
    if 'if is_double_wave:' in line and swf_if_pos == -1:
        dw_if_pos = i

print(f"   • 'if is_single_wave_strong:' à ligne {swf_if_pos + 1 if swf_if_pos >= 0 else 'NON TROUVÉ'}")
print(f"   • 'elif is_double_wave:' à ligne {dw_elif_pos + 1 if dw_elif_pos >= 0 else 'NON TROUVÉ'}")
print(f"   • 'if is_double_wave:' (ancien) à ligne {dw_if_pos + 1 if dw_if_pos >= 0 else 'NON TROUVÉ'}")

print("\n4. RÉSULTAT:")
if swf_if_pos > 0 and dw_elif_pos > swf_if_pos:
    print("   ✅ HIÉRARCHIE CORRECTE!")
    print("   • Single Wave Fort testé EN PREMIER (if)")
    print("   • Double Wave testé ENSUITE (elif)")
    print("   • Conforme aux statistiques 95% SWF / 5% DW")
elif dw_if_pos > 0 and (swf_if_pos < 0 or dw_if_pos < swf_if_pos):
    print("   ❌ HIÉRARCHIE INCORRECTE!")
    print("   • Double Wave testé EN PREMIER")
    print("   • Besoin de correction")
else:
    print("   ⚠️ STRUCTURE INATTENDUE")
    print("   • Vérification manuelle requise")

# 4. Commentaires SESSION 69
print("\n5. COMMENTAIRES SESSION 69:")
has_comment = 'SESSION 69' in content
print(f"   • Commentaire 'SESSION 69': {'✅ Présent' if has_comment else '❌ Absent'}")

# 5. Résumé
print("\n" + "="*60)
print("RÉSUMÉ:")
print("="*60)

checks = {
    "Version 2.4.1": "Version 2.4.1" in content or "Version 2.4.1" in lines[4] if len(lines) > 4 else False,
    "Hiérarchie corrigée": swf_if_pos > 0 and dw_elif_pos > swf_if_pos,
    "Commentaire SESSION 69": has_comment,
}

all_ok = all(checks.values())

for check_name, result in checks.items():
    status = "✅" if result else "❌"
    print(f"{status} {check_name}")

print("\n" + "="*60)
if all_ok:
    print("✅ PLANIFICATEUR CORRECTEMENT CONFIGURÉ!")
    print("   Le fichier a déjà été modifié en Session 69.")
    print("   Vous pouvez tester directement dans Streamlit.")
else:
    print("⚠️ CORRECTIONS NÉCESSAIRES")
    print("   Le fichier nécessite des modifications.")
print("="*60)
