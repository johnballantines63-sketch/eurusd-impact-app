#!/usr/bin/env python3
"""
Script pour afficher la structure exacte des phases dans Streamlit
"""

import os
from datetime import datetime

project_root = "/Users/andrevalentin/Projects/eurusd_news_impact_calculator"
target_file = os.path.join(project_root, "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")

print("=" * 70)
print("🔍 DEBUG STRUCTURE PHASES")
print("=" * 70)

# Backup
backup = target_file + f".bak_debug_struct_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
with open(target_file, 'r') as f:
    content = f.read()

with open(backup, 'w') as f:
    f.write(content)

print(f"✅ Backup : {os.path.basename(backup)}")

# Ajouter du code de debug JUSTE AVANT l'appel à create_unified_prediction_chart
old_code = """                            unified_fig = create_unified_prediction_chart(phases, predictions_for_seq, real_prices_df)
                            st.plotly_chart(unified_fig, use_container_width=True)"""

new_code = """                            # 🔍 DEBUG : Afficher structure des phases
                            st.markdown("### 🔍 DEBUG - Structure des phases")
                            for idx, phase in enumerate(phases):
                                with st.expander(f"Phase {idx + 1} - Clés disponibles", expanded=True):
                                    st.write("**Clés de la phase :**")
                                    st.code(str(list(phase.keys())))
                                    
                                    st.write("**Contenu complet :**")
                                    st.json(phase)
                            
                            # Graphique (temporairement désactivé pour voir le debug)
                            # unified_fig = create_unified_prediction_chart(phases, predictions_for_seq, real_prices_df)
                            # st.plotly_chart(unified_fig, use_container_width=True)
                            
                            st.info("🔍 Graphique désactivé temporairement pour voir la structure des phases")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Code de debug ajouté")
else:
    print("⚠️ Pattern non trouvé, recherche alternative...")
    
    # Chercher juste la ligne create_unified_prediction_chart
    if "unified_fig = create_unified_prediction_chart" in content:
        # Insérer le debug avant
        content = content.replace(
            "unified_fig = create_unified_prediction_chart",
            """# 🔍 DEBUG : Afficher structure
                            st.markdown("### 🔍 DEBUG - Structure des phases")
                            for idx, phase in enumerate(phases):
                                with st.expander(f"Phase {idx + 1}", expanded=True):
                                    st.write("Clés:", list(phase.keys()))
                                    st.json(phase)
                            
                            st.warning("Graphique temporairement commenté")
                            # unified_fig = create_unified_prediction_chart"""
        )
        print("✅ Debug ajouté (méthode alternative)")

# Sauvegarder
with open(target_file, 'w') as f:
    f.write(content)

print(f"✅ Fichier mis à jour avec debug")

print("\n" + "=" * 70)
print("📋 INSTRUCTIONS")
print("=" * 70)
print("\n1. Rafraîchir Streamlit (F5)")
print("2. Sélectionner les événements du 11/09/2025")
print("3. Activer le mode séquentiel")
print("4. Regarder la section '🔍 DEBUG - Structure des phases'")
print("5. Copier-coller ici le contenu des clés affichées")
print("\nExemple de ce que vous verrez :")
print("   Phase 1 - Clés disponibles")
print("   ['start', 'end', 'duration', 'type', 'events', ...]")
print("\n💡 Une fois que j'aurai la structure exacte,")
print("   je pourrai créer le graphique avec les bonnes clés !")
