import re

# Lire le rapport audit complet
audit_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/audit_scores_mapping.txt'

with open(audit_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("=" * 80)
print("EXTRACTION EVENT_KEY RÉELS DE LA DB (depuis rapport audit)")
print("=" * 80)
print()

# Recherche 1 : unemployment
print("RECHERCHE 1 : event_key contenant 'unemployment'")
print("-" * 80)

unemployment_pattern = r"event_key:\s*'([^']*unemployment[^']*)'"
unemployment_matches = re.findall(unemployment_pattern, content, re.IGNORECASE)

if unemployment_matches:
    print(f"✅ {len(unemployment_matches)} event_key trouvés :\n")
    for match in set(unemployment_matches):  # Dédupliquer
        print(f"  → '{match}'")
else:
    print("❌ Aucun event_key trouvé")

print()
print()

# Recherche 2 : gdp
print("RECHERCHE 2 : event_key contenant 'gdp'")
print("-" * 80)

gdp_pattern = r"event_key:\s*'([^']*gdp[^']*)'"
gdp_matches = re.findall(gdp_pattern, content, re.IGNORECASE)

if gdp_matches:
    print(f"✅ {len(gdp_matches)} event_key trouvés :\n")
    for match in set(gdp_matches):  # Dédupliquer
        print(f"  → '{match}'")
else:
    print("❌ Aucun event_key trouvé")

print()
print()

# Recherche 3 : mortgage (bonus)
print("RECHERCHE BONUS : event_key contenant 'mortgage'")
print("-" * 80)

mortgage_pattern = r"event_key:\s*'([^']*mortgage[^']*rate[^']*)'"
mortgage_matches = re.findall(mortgage_pattern, content, re.IGNORECASE)

if mortgage_matches:
    print(f"✅ {len(mortgage_matches)} event_key trouvés :\n")
    for match in set(mortgage_matches):  # Dédupliquer
        print(f"  → '{match}'")
else:
    print("❌ Aucun event_key trouvé")

print()
print()

# Recherche 4 : money supply (bonus)
print("RECHERCHE BONUS : event_key contenant 'money supply'")
print("-" * 80)

money_pattern = r"event_key:\s*'([^']*money[^']*supply[^']*)'"
money_matches = re.findall(money_pattern, content, re.IGNORECASE)

if money_matches:
    print(f"✅ {len(money_matches)} event_key trouvés :\n")
    for match in set(money_matches):  # Dédupliquer
        print(f"  → '{match}'")
else:
    print("❌ Aucun event_key trouvé")

print()
print("=" * 80)
print("✅ EXTRACTION COMPLÉTÉE")
print("=" * 80)
