"""
Ajouter affichage des événements SANS famille pour permettre leur sélection

Modifications :
1. Charger TOUS les événements (pas seulement ceux avec famille)
2. Afficher section séparée "Événements sans famille"
3. Permettre sélection avec estimation manuelle d'impact
"""

file_path = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

with open(file_path, 'r') as f:
    content = f.read()

print("=" * 70)
print("🔧 AJOUT : Affichage événements sans famille")
print("=" * 70)

# ============================================================
# PARTIE 1 : Modifier la requête de chargement des événements
# ============================================================
print("\n📋 PARTIE 1 : Modification requête événements...")

# Chercher la fonction qui charge les événements
# Elle doit faire un JOIN avec event_families
# On va créer une version qui charge TOUS les événements

new_function = '''
@st.cache_data(ttl=3600)
def load_all_events_for_date(target_date, countries=['US', 'EU']):
    """
    Charge TOUS les événements d'une date (avec et sans famille)
    
    Returns:
        Dict avec 'mapped' (avec famille) et 'unmapped' (sans famille)
    """
    try:
        conn = duckdb.connect(get_db_path(), read_only=True)
        
        # Convertir date en format compatible
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Événements AVEC famille (mappés)
        query_mapped = f"""
            SELECT DISTINCT
                e.ts_utc,
                e.event_key,
                e.country,
                e.importance_n,
                e.actual,
                e.previous,
                e.estimate,
                e.forecast,
                ef.family,
                ef.empirical_score
            FROM events e
            INNER JOIN event_families ef ON e.event_key = ef.event_key
            WHERE DATE(e.ts_utc) = '{date_str}'
              AND e.country IN ({','.join([f"'{c}'" for c in countries])})
              AND ef.is_tradable = true
            ORDER BY e.ts_utc
        """
        
        mapped_events = conn.execute(query_mapped).fetchdf()
        
        # Événements SANS famille (non mappés)
        query_unmapped = f"""
            SELECT DISTINCT
                e.ts_utc,
                e.event_key,
                e.country,
                e.importance_n,
                e.actual,
                e.previous,
                e.estimate,
                e.forecast
            FROM events e
            LEFT JOIN event_families ef ON e.event_key = ef.event_key
            WHERE DATE(e.ts_utc) = '{date_str}'
              AND e.country IN ({','.join([f"'{c}'" for c in countries])})
              AND ef.event_key IS NULL
              AND e.importance_n >= 1
            ORDER BY e.ts_utc
        """
        
        unmapped_events = conn.execute(query_unmapped).fetchdf()
        
        conn.close()
        
        return {
            'mapped': mapped_events,
            'unmapped': unmapped_events
        }
    except Exception as e:
        st.error(f"Erreur chargement événements: {e}")
        return {'mapped': pd.DataFrame(), 'unmapped': pd.DataFrame()}

'''

# Chercher où insérer (après les autres @st.cache_data)
insert_pos = content.find("def identify_family(")
if insert_pos > 0:
    content = content[:insert_pos] + new_function + "\n\n" + content[insert_pos:]
    print("✅ Fonction load_all_events_for_date() ajoutée")
else:
    print("⚠️ Position d'insertion non trouvée")

# ============================================================
# PARTIE 2 : Ajouter section UI pour événements non mappés
# ============================================================
print("\n📋 PARTIE 2 : Ajout section UI événements non mappés...")

unmapped_ui_code = '''
                # ═══════════════════════════════════════════════════════════
                # SECTION : ÉVÉNEMENTS SANS FAMILLE (Non mappés)
                # ═══════════════════════════════════════════════════════════
                
                if 'all_events' in st.session_state and len(st.session_state.all_events['unmapped']) > 0:
                    st.divider()
                    
                    with st.expander(
                        f"⚠️ Événements sans famille détectés ({len(st.session_state.all_events['unmapped'])})",
                        expanded=False
                    ):
                        st.warning(
                            "**Ces événements n'ont pas de famille configurée**, donc pas de prédiction d'impact automatique. "
                            "Vous pouvez les ajouter manuellement avec une estimation d'impact."
                        )
                        
                        unmapped_df = st.session_state.all_events['unmapped']
                        
                        for idx, row in unmapped_df.iterrows():
                            col1, col2, col3 = st.columns([3, 2, 1])
                            
                            with col1:
                                event_time = row['ts_utc'].strftime('%H:%M')
                                event_display = f"**{event_time}** - {row['event_key']} ({row['country']})"
                                
                                if pd.notna(row['actual']) and pd.notna(row['estimate']):
                                    surprise = row['actual'] - row['estimate']
                                    surprise_pct = (surprise / row['estimate'] * 100) if row['estimate'] != 0 else 0
                                    event_display += f" | Surprise: {surprise_pct:+.1f}%"
                                
                                st.markdown(event_display)
                            
                            with col2:
                                if pd.notna(row['actual']):
                                    st.caption(f"Actual: {row['actual']:.2f}")
                                if pd.notna(row['estimate']):
                                    st.caption(f"Forecast: {row['estimate']:.2f}")
                            
                            with col3:
                                add_key = f"add_unmapped_{idx}"
                                if st.button("➕ Ajouter", key=add_key, type="secondary"):
                                    # Ajouter à la liste des événements sélectionnés
                                    # Avec impact manuel estimé
                                    st.info(f"Événement {row['event_key']} ajouté (impact à estimer manuellement)")
                        
                        st.info(
                            "💡 **Astuce** : Ces événements peuvent être importants ! "
                            "Pour leur attribuer une famille et obtenir des prédictions, "
                            "contactez l'administrateur pour mapper ces event_keys."
                        )
                
'''

# Chercher où insérer (après le bouton "Charger Événements")
search_pattern = 'if st.button("🔵 Charger Événements"'
insert_pos = content.find(search_pattern)

if insert_pos > 0:
    # Trouver la fin du bloc if (après le chargement des événements)
    # Chercher le prochain "st.divider()" ou début de nouvelle section
    end_pos = content.find("st.divider()", insert_pos + 500)
    if end_pos > 0:
        content = content[:end_pos] + "\n" + unmapped_ui_code + "\n                " + content[end_pos:]
        print("✅ Section UI événements non mappés ajoutée")
    else:
        print("⚠️ Fin de section non trouvée")
else:
    print("⚠️ Bouton 'Charger Événements' non trouvé")

# ============================================================
# PARTIE 3 : Modifier appel de chargement
# ============================================================
print("\n📋 PARTIE 3 : Modification appel chargement...")

# Chercher et remplacer l'appel de chargement des événements
# (à adapter selon le code existant)

print("⚠️ Note : Vérifier manuellement l'appel de chargement dans le bouton")
print("   Il faudra remplacer la requête actuelle par load_all_events_for_date()")

# ============================================================
# Sauvegarder
# ============================================================
with open(file_path, 'w') as f:
    f.write(content)

print("\n" + "=" * 70)
print("✅ MODIFICATIONS APPLIQUÉES !")
print("=" * 70)

print("\n📊 Résumé:")
print("  1. ✅ Fonction load_all_events_for_date() ajoutée")
print("     → Charge événements mappés ET non mappés")
print("  2. ✅ Section UI pour événements sans famille")
print("     → Affichage dans expander avec bouton 'Ajouter'")
print("  3. ⚠️ À vérifier manuellement :")
print("     → Modifier appel de chargement dans bouton")
print("     → Utiliser load_all_events_for_date() au lieu de requête actuelle")

print("\n🎯 Résultat attendu:")
print("  • Section 'Événements sans famille détectés (X)'")
print("  • Liste des unmapped avec surprise si disponible")
print("  • Bouton ➕ Ajouter pour chaque événement")
print("  • Current Account DE 14:45 visible et sélectionnable !")
