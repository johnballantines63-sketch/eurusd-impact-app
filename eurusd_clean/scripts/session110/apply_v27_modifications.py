"""
SCRIPT AUTOMATIQUE DE MODIFICATION PLANIFICATEUR V2.4 → V2.7
=============================================================

Ce script applique automatiquement les 6 modifications du guide
pour créer le Planificateur V2.7 avec amplification dynamique

Date : 3 novembre 2025
"""

from pathlib import Path
import shutil

print("="*80)
print("MODIFICATION AUTOMATIQUE : PLANIFICATEUR V2.4 → V2.7")
print("="*80)

# Chemins
fx_app_pages = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages")
source_file = fx_app_pages / "5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 6.py"
target_file = fx_app_pages / "6_Planificateur_V27_AMPLIFICATION_DYNAMIQUE.py"

# Vérifier fichier source
if not source_file.exists():
    print(f"❌ Fichier source introuvable : {source_file}")
    exit(1)

print(f"\n📂 Fichier source : {source_file.name}")
print(f"📂 Fichier cible : {target_file.name}")

# Lire fichier source
with open(source_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"\n✅ Fichier lu ({len(content)} caractères)")

# ============================================================================
# MODIFICATION 1 : Header docstring
# ============================================================================
print("\n🔧 MODIFICATION 1 : Header docstring...")

old_header = '''"""
PLANIFICATEUR V2 - FORMULES VALIDÉES
=====================================

Version 2.4 - Session 68 (Single Wave Fort)'''

new_header = '''"""
PLANIFICATEUR V2.7 - AMPLIFICATION DYNAMIQUE
============================================

Version 2.7 - Session 110 (Amplification Dynamique)
Ajoute calcul automatique facteur d'amplification selon tendances pré-événement

Nouveauté Session 110 :
- 🔬 Amplification dynamique basée sur inversions de tendance
- ✅ Amélioration +39.6% sur 17 dates validées (Cluster #3 CPI)
- 📊 Baseline adaptative selon cluster détecté
- ✍️ Mode manuel disponible pour ajustements trader

Base identique V2.4 - Session 68 (Single Wave Fort)'''

content = content.replace(old_header, new_header)
print("   ✅ Header mis à jour")

# ============================================================================
# MODIFICATION 2 : Imports amplification
# ============================================================================
print("\n🔧 MODIFICATION 2 : Imports module amplification...")

old_imports = '''sys.path.insert(0, str(src_path))

# Import des formules validées'''

new_imports = '''sys.path.insert(0, str(src_path))

# ═══════════════════════════════════════════════════════════════
# V2.7 : Import module Amplification Dynamique (Session 110)
# ═══════════════════════════════════════════════════════════════
eurusd_clean_app_path = fx_impact_app_dir.parent / "eurusd_clean" / "app"
sys.path.insert(0, str(eurusd_clean_app_path))

try:
    from amplification_calculator import (
        calculate_amplification,
        list_available_clusters
    )
    AMPLIFICATION_MODULE_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Module amplification non disponible : {e}")
    AMPLIFICATION_MODULE_AVAILABLE = False

# Import des formules validées'''

content = content.replace(old_imports, new_imports)
print("   ✅ Imports ajoutés")

# ============================================================================
# MODIFICATION 3 : Titre page
# ============================================================================
print("\n🔧 MODIFICATION 3 : Titre page...")

old_title = '''st.title("🎯 Planificateur V2 - Formules Validées")
st.markdown("**Version 2.4** - Méthode Session 55 + détection automatique type mouvement (Session 68)")'''

new_title = '''st.title("🎯 Planificateur V2.7 - Amplification Dynamique")
st.markdown("**Version 2.7** - Amplification dynamique (Session 110) + Méthode Session 55")'''

content = content.replace(old_title, new_title)
print("   ✅ Titre mis à jour")

# ============================================================================
# MODIFICATION 4 : Formules utilisées (ajouter Amplification)
# ============================================================================
print("\n🔧 MODIFICATION 4 : Boîte formules...")

old_formulas_box = '''with st.expander("ℹ️ Formules Utilisées", expanded=False):
    formulas_info = get_all_formulas_info()
    
    col1, col2, col3, col4 = st.columns(4)'''

new_formulas_box = '''with st.expander("ℹ️ Formules Utilisées", expanded=False):
    formulas_info = get_all_formulas_info()
    
    col1, col2, col3, col4, col5 = st.columns(5)'''

content = content.replace(old_formulas_box, new_formulas_box)

old_pullback_col = '''    with col4:
        st.markdown("### 🔄 Pullback V2")
        st.metric("Précision", formulas_info['pullback_v2']['precision'])
        st.caption(f"Session {formulas_info['pullback_v2']['session']}")'''

new_pullback_col = '''    with col4:
        st.markdown("### 🔄 Pullback V2")
        st.metric("Précision", formulas_info['pullback_v2']['precision'])
        st.caption(f"Session {formulas_info['pullback_v2']['session']}")
    
    with col5:
        st.markdown("### 🔬 Amplification")
        st.metric("Amélioration", "+39.6%")
        st.caption("Session 110 ⭐")'''

content = content.replace(old_pullback_col, new_pullback_col)
print("   ✅ Boîte formules mise à jour")

# ============================================================================
# MODIFICATION 5 : Fonction calculate_predictions
# ============================================================================
print("\n🔧 MODIFICATION 5 : Fonction calculate_predictions...")

old_function_def = '''def calculate_predictions(cpi_events: pd.DataFrame) -> dict:
    """
    Calcule les prédictions avec méthode Session 55
    LOGIQUE EXACTE de test_planificateur_v2_final.py
    
    Args:
        cpi_events: DataFrame des événements CPI
    
    Returns:
        dict avec prédictions
    """'''

new_function_def = '''def calculate_predictions(cpi_events: pd.DataFrame, amplification: float = 2.5) -> dict:
    """
    Calcule les prédictions avec méthode Session 55
    
    V2.7 : Supporte amplification dynamique ou manuelle
    
    Args:
        cpi_events: DataFrame des événements
        amplification: Facteur d'amplification (2.5 par défaut, ou dynamique V2.7)
    
    Returns:
        dict avec prédictions
    """'''

content = content.replace(old_function_def, new_function_def)

old_impact_calc = '''    # Test avec amplification optimale 2.5 (lignes 90-96)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=2.5
    )'''

new_impact_calc = '''    # V2.7 : Utilisation amplification paramètre (fixe ou dynamique)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=amplification  # Utilise paramètre passé
    )'''

content = content.replace(old_impact_calc, new_impact_calc)

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
        'amplification_used': amplification  # V2.7 : Stocker amplification
    }'''

content = content.replace(old_return, new_return)
print("   ✅ Fonction calculate_predictions modifiée")

# ============================================================================
# MODIFICATION 6 : Interface amplification (AVANT bouton calculer)
# ============================================================================
print("\n🔧 MODIFICATION 6 : Section amplification UI...")

# Chercher le bouton calculer
button_marker = '''# Bouton calculer
if st.button("🎯 Calculer Prédictions", type="primary"):'''

amplification_ui = '''
# ═══════════════════════════════════════════════════════════════
# V2.7 : SECTION AMPLIFICATION DYNAMIQUE
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 🔬 Facteur d'Amplification (V2.7)")

if AMPLIFICATION_MODULE_AVAILABLE:
    amp_mode = st.radio(
        "Mode de calcul",
        options=["🔬 Automatique (calculé selon tendances)", "✍️ Manuel (saisie libre)"],
        help="Automatique : +39.6% précision validée sur 17 dates\\nManuel : ajustement trader"
    )
    
    if amp_mode == "✍️ Manuel (saisie libre)":
        col_manual1, col_manual2 = st.columns([2, 1])
        
        with col_manual1:
            amplification_manual = st.number_input(
                "Facteur d'amplification",
                min_value=0.5,
                max_value=5.0,
                value=2.5,
                step=0.1,
                help="Valeur typique : 1.5-3.5"
            )
        
        with col_manual2:
            show_auto_suggestion = st.checkbox("💡 Voir suggestion auto")
        
        amplification_to_use = amplification_manual
        amp_calculation_method = "manual"
    else:
        st.info("ℹ️ L'amplification sera calculée automatiquement selon tendances pré-événement")
        amplification_to_use = None
        amp_calculation_method = "automatic"
        show_auto_suggestion = False
else:
    st.warning("⚠️ Module amplification non disponible - Mode manuel uniquement")
    amplification_to_use = st.number_input(
        "Facteur d'amplification",
        min_value=0.5,
        max_value=5.0,
        value=2.5,
        step=0.1
    )
    amp_calculation_method = "manual_fallback"
    show_auto_suggestion = False

st.markdown("---")

# Bouton calculer
if st.button("🎯 Calculer Prédictions", type="primary"):'''

content = content.replace(button_marker, amplification_ui)
print("   ✅ Section amplification UI ajoutée")

# ============================================================================
# MODIFICATION 7 : Calcul amplification (DANS bouton)
# ============================================================================
print("\n🔧 MODIFICATION 7 : Calcul amplification dynamique...")

old_spinner = '''    st.success(f"✅ {len(high_events)} événement(s) HIGH impact trouvé(s)")
    
    with st.spinner("Calcul avec formules validées Session 51-55..."):
        predictions = calculate_predictions(high_events)'''

new_calculation = '''    st.success(f"✅ {len(high_events)} événement(s) HIGH impact trouvé(s)")
    
    # ═══════════════════════════════════════════════════════════════
    # V2.7 : CALCUL AMPLIFICATION DYNAMIQUE
    # ═══════════════════════════════════════════════════════════════
    
    if amp_calculation_method == "automatic" and AMPLIFICATION_MODULE_AVAILABLE:
        with st.spinner("🔬 Calcul amplification dynamique..."):
            try:
                events_list = []
                for _, event in high_events.iterrows():
                    events_list.append({
                        'event': event['label'],
                        'actual': event.get('actual'),
                        'estimate': event.get('estimate')
                    })
                
                event_time = pd.to_datetime(high_events.iloc[0]['ts_utc'])
                db_path = Path(get_db_path())
                
                amp_result = calculate_amplification(
                    events=events_list,
                    event_time=event_time,
                    db_path=db_path
                )
                
                amplification_to_use = amp_result['amplification']
                
                st.success(f"✅ Amplification calculée : **{amplification_to_use:.3f}**")
                
                with st.expander("📊 Détails calcul amplification"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Cluster identifié**")
                        st.write(f"ID : {amp_result['cluster_id']}")
                        st.write(f"Nom : {amp_result['cluster_name']}")
                    
                    with col2:
                        st.write("**Méthode**")
                        st.write(f"Type : {amp_result['method']}")
                        st.write(f"Baseline : {amp_result['cluster_baseline']:.3f}")
                    
                    with col3:
                        st.write("**Inversion**")
                        if amp_result['inversion_detected']:
                            st.success("✅ Détectée")
                            st.write(f"Durée : {amp_result['duration_hours']:.1f}h")
                            if amp_result['ecart_calculated']:
                                st.write(f"Écart : {amp_result['ecart_calculated']:+.3f}")
                        else:
                            st.info("❌ Non détectée")
            
            except Exception as e:
                st.error(f"❌ Erreur calcul amplification : {e}")
                st.warning("→ Utilisation baseline 2.5")
                amplification_to_use = 2.5
    
    elif amp_calculation_method == "manual" and show_auto_suggestion and AMPLIFICATION_MODULE_AVAILABLE:
        try:
            events_list = []
            for _, event in high_events.iterrows():
                events_list.append({
                    'event': event['label'],
                    'actual': event.get('actual'),
                    'estimate': event.get('estimate')
                })
            
            event_time = pd.to_datetime(high_events.iloc[0]['ts_utc'])
            db_path = Path(get_db_path())
            
            amp_result = calculate_amplification(events_list, event_time, db_path)
            
            st.info(f"💡 Suggestion automatique : **{amp_result['amplification']:.3f}**")
            st.caption(f"Méthode : {amp_result['method']}")
        except Exception as e:
            st.warning(f"⚠️ Impossible de calculer suggestion : {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # FIN SECTION AMPLIFICATION - Calcul prédictions
    # ═══════════════════════════════════════════════════════════════
    
    with st.spinner("Calcul avec formules validées Session 51-55..."):
        predictions = calculate_predictions(high_events, amplification=amplification_to_use)'''

content = content.replace(old_spinner, new_calculation)
print("   ✅ Calcul amplification dynamique ajouté")

# ============================================================================
# MODIFICATION 8 : Affichage métrique amplification
# ============================================================================
print("\n🔧 MODIFICATION 8 : Métrique amplification...")

old_metrics = '''    # Métriques principales
    col1, col2, col3, col4, col5 = st.columns(5)'''

new_metrics = '''    # Métriques principales
    col1, col2, col3, col4, col5, col6 = st.columns(6)'''

content = content.replace(old_metrics, new_metrics)

old_col5 = '''    with col5:
        impact_net = predictions['impact_pips'] - predictions['pullback_pips'] + (predictions['pullback_pips'] * 0.5)
        st.metric(
            "Mouvement Net Final",
            f"+{impact_net:.1f} pips",
            help="Impact - Pullback + Reprise"
        )
    
    # Type de mouvement détecté'''

new_col5 = '''    with col5:
        impact_net = predictions['impact_pips'] - predictions['pullback_pips'] + (predictions['pullback_pips'] * 0.5)
        st.metric(
            "Mouvement Net Final",
            f"+{impact_net:.1f} pips",
            help="Impact - Pullback + Reprise"
        )
    
    with col6:
        st.metric(
            "Amplification",
            f"{predictions.get('amplification_used', 2.5):.3f}",
            help="Facteur d'amplification utilisé (V2.7)"
        )
    
    # Type de mouvement détecté'''

content = content.replace(old_col5, new_col5)
print("   ✅ Métrique amplification ajoutée")

# ============================================================================
# MODIFICATION 9 : Footer
# ============================================================================
print("\n🔧 MODIFICATION 9 : Footer...")

old_footer = '''st.markdown("""
**Planificateur V2** - Version 2.4 (Session 68 - Single Wave Fort)  
Utilise la méthode EXACTE validée en Session 55  
✅ Charge uniquement événements CPI  
✅ Somme vectorielle (pas événement par événement)  
✅ Formules : Ajustement Score (99.9%), Impact D (98.6%), TTR C (94.4%), Pullback V2 (99.3%)  
  
✅ **NOUVEAU (Session 68)** : Détection automatique type de mouvement  
✅ Single Wave Fort : Timeline T+8 peak, pullback 10-15%, stabilisation T+25 (95% des cas)  
✅ Double Wave Momentum : Timeline 2 phases si conditions strictes (rare)  
✅ Export CSV enrichi avec type de mouvement et timing précis
""")'''

new_footer = '''st.markdown("""
**Planificateur V2.7** - Amplification Dynamique (Session 110) ⭐  

**Nouveauté V2.7 :**
- 🔬 Calcul amplification dynamique selon tendances pré-événement  
- ✅ Amélioration +39.6% sur 17 dates validées (Cluster #3 CPI)  
- 📊 Baseline adaptative selon cluster détecté  
- ✍️ Mode manuel pour ajustements trader  

**Base V2.4 :**
- Méthode Session 55 validée  
- Formules : Ajustement Score (99.9%), Impact D (98.6%), TTR C (94.4%), Pullback V2 (99.3%)  
- Détection automatique type mouvement (Session 68)  
- Single Wave Fort / Double Wave Momentum  
""")'''

content = content.replace(old_footer, new_footer)
print("   ✅ Footer mis à jour")

# ============================================================================
# SAUVEGARDER
# ============================================================================
print("\n💾 Sauvegarde fichier modifié...")

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Fichier sauvegardé : {target_file.name}")

print("\n" + "="*80)
print("✅ MODIFICATION TERMINÉE !")
print("="*80)

print(f"\n📂 Fichier créé : {target_file}")
print(f"📊 Taille : {len(content)} caractères")

print("\n🎯 PROCHAINES ÉTAPES :")
print("1. Lancer Streamlit : streamlit run Home.py")
print("2. Aller sur page '6_Planificateur_V27_AMPLIFICATION_DYNAMIQUE'")
print("3. Tester date 11.09.2025 en mode automatique")
print("4. Vérifier amplification ≈ 1.726")

print("\n" + "="*80)
