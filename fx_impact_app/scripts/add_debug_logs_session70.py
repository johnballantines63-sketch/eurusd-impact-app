"""
FIX DÉFINITIF - Ajoute logs debug dans Planificateur
Session 70 - Investigation date ignorée
"""

from pathlib import Path


planificateur_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py")

print("🔧 Ajout logs debug...")

with open(planificateur_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
backup_path = planificateur_path.with_suffix('.py.backup_session70_debug')
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Backup: {backup_path.name}")

# Chercher ligne problématique et ajouter debug
old_code = """# Bouton calculer
if st.button("🎯 Calculer Prédictions", type="primary"):
    with st.spinner("Récupération des événements CPI..."):
        cpi_events = get_cpi_events_for_date(datetime.combine(target_date, datetime.min.time()))"""

new_code = """# Bouton calculer
if st.button("🎯 Calculer Prédictions", type="primary"):
    # DEBUG Session 70
    st.write(f"🐛 DEBUG - Date saisie: {target_date}")
    st.write(f"🐛 DEBUG - Type: {type(target_date)}")
    date_to_query = datetime.combine(target_date, datetime.min.time())
    st.write(f"🐛 DEBUG - Date pour query: {date_to_query}")
    
    with st.spinner("Récupération des événements CPI..."):
        cpi_events = get_cpi_events_for_date(date_to_query)
        st.write(f"🐛 DEBUG - Événements trouvés: {len(cpi_events)}")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(planificateur_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Logs debug ajoutés")
    print("\n📝 INSTRUCTIONS:")
    print("1. Redémarrer Streamlit")
    print("2. Saisir date 2025-02-12")
    print("3. Cliquer Calculer")
    print("4. Observer messages 🐛 DEBUG")
    print("5. Vérifier quelle date est RÉELLEMENT utilisée")
else:
    print("❌ Pattern non trouvé - ajout manuel requis")
    print("\nAjouter AVANT la ligne:")
    print("  cpi_events = get_cpi_events_for_date(...)")
    print("\nCe code:")
    print("  st.write(f'🐛 Date saisie: {target_date}')")
    print("  st.write(f'🐛 Date query: {datetime.combine(target_date, datetime.min.time())}')")
