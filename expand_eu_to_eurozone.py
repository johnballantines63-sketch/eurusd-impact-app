"""
Quand l'utilisateur sélectionne 'EU', inclure automatiquement
tous les pays de la zone euro : DE, FR, IT, ES, etc.
"""

file_path = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

with open(file_path, 'r') as f:
    content = f.read()

print("🔧 Expansion 'EU' → tous pays eurozone...")

# Trouver la fonction load_all_events_for_date et ajouter expansion EU
expansion_code = '''
    # Expansion : EU → tous pays eurozone
    expanded_countries = []
    eurozone_countries = ['EU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'PT', 'IE', 'GR']
    
    for country in countries:
        if country == 'EU':
            expanded_countries.extend(eurozone_countries)
        else:
            expanded_countries.append(country)
    
    # Dédupliquer
    expanded_countries = list(set(expanded_countries))
    
'''

# Chercher le début de la fonction load_all_events_for_date
func_start = content.find("def load_all_events_for_date(target_date, countries=['US', 'EU']):")

if func_start > 0:
    # Trouver la fin de la docstring
    try_pos = content.find("try:", func_start)
    
    if try_pos > 0:
        # Insérer le code d'expansion avant le try
        content = content[:try_pos] + expansion_code + "    " + content[try_pos:]
        print("✅ Code d'expansion ajouté au début de la fonction")
        
        # Maintenant remplacer 'countries' par 'expanded_countries' dans les requêtes
        # Chercher les deux endroits où on utilise countries dans les IN
        
        # Pour query_mapped
        old_mapped = "AND e.country IN ({','.join([f\"'{c}'\" for c in countries])})"
        new_mapped = "AND e.country IN ({','.join([f\"'{c}'\" for c in expanded_countries])})"
        content = content.replace(old_mapped, new_mapped)
        print("✅ Requête mapped mise à jour")
        
        # Pour query_unmapped - on garde l'ancienne modification
        print("✅ Requête unmapped déjà modifiée")
    else:
        print("⚠️ 'try:' non trouvé")
else:
    print("⚠️ Fonction load_all_events_for_date non trouvée")

with open(file_path, 'w') as f:
    f.write(content)

print("\n✅ Modifications appliquées !")
print("\n📋 Maintenant quand tu sélectionnes 'EU':")
print("   → Inclut automatiquement DE, FR, IT, ES, etc.")
print("   → Current Account DE sera chargé !")
