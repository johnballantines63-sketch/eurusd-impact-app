"""
Session 95 - Exécution intégration ADD-ON
Applique les modifications au Planificateur V2
"""

from pathlib import Path
import sys

# Chemins
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PLANIFICATEUR_PATH = PROJECT_ROOT / "fx_impact_app" / "streamlit_app" / "pages" / "5_Planificateur_V2_FORMULES_VALIDEES.py"

print("🚀 EXÉCUTION INTÉGRATION ADD-ON - SESSION 95")
print("=" * 80)
print(f"Fichier cible : {PLANIFICATEUR_PATH.name}")
print()

# Lire le fichier
print("📖 Lecture fichier...")
with open(PLANIFICATEUR_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"✅ Fichier lu : {len(content)} caractères")
print()

# ============================================================================
# MODIFICATION 1 : Import amplification_wrapper
# ============================================================================
print("📝 MODIFICATION 1 : Ajout import amplification_wrapper")

import_block = """

# ============================================================================
# IMPORTS SESSION 94 - AMPLIFICATION HYBRIDE ADD-ON
# ============================================================================

# Import module amplification wrapper (Session 94 - ADD-ON)
sys.path.insert(0, str(src_path.parent.parent / 'eurusd_clean' / 'scripts' / 'session92'))

try:
    from amplification_wrapper import get_amplification_factor_hybrid
    AMPLIFICATION_HYBRID_AVAILABLE = True
    print("✅ Module amplification_wrapper importé (Session 94)")
except ImportError as e:
    AMPLIFICATION_HYBRID_AVAILABLE = False
    print(f"⚠️ Module amplification_wrapper non disponible : {e}")
    print("   → Utilisation coefficient fixe 2.5 (fallback)")

# ============================================================================
"""

# Chercher position d'insertion après imports formulas_validated
search_pattern = "from single_wave_strong import"
pos = content.find(search_pattern)
if pos != -1:
    # Trouver la fin de ce bloc d'imports
    end_pos = content.find(")", pos) + 1
    # Trouver les deux prochains \n\n
    next_double_newline = content.find("\n\n", end_pos)
    content = content[:next_double_newline] + import_block + content[next_double_newline:]
    print("✅ Import ajouté")
else:
    print("⚠️ Position d'insertion non trouvée")

# ============================================================================
# MODIFICATION 2 : Modification calculate_predictions() - Calcul impact
# ============================================================================
print("\n📝 MODIFICATION 2 : Modification calcul impact avec amplification hybride")

old_calc = """    # Test avec amplification optimale 2.5 (lignes 90-96)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=2.5
    )"""

new_calc = """    # Calcul impact avec amplification hybride (Session 94 - ADD-ON)
    if AMPLIFICATION_HYBRID_AVAILABLE:
        # Utiliser amplification calibrée par cluster (Session 92)
        event_families = cpi_events['family'].tolist() if 'family' in cpi_events.columns else ['UNKNOWN'] * len(cpi_events)
        
        ampl_result = get_amplification_factor_hybrid(
            event_families=event_families,
            surprises=surprises,
            num_events=len(cpi_events)
        )
        
        amplification_factor = ampl_result['amplification_factor']
        base_impact_empirical = ampl_result['base_impact']
        cluster_type = ampl_result['cluster_type']
        cluster_sensitivity = ampl_result['sensitivity']
        surprise_vectorielle = ampl_result['surprise_vectorielle']
        using_default = ampl_result['using_default']
        
        print(f"🎯 Amplification hybride : {amplification_factor:.3f} (cluster: {cluster_type})")
    else:
        # Fallback coefficient fixe si module non disponible
        amplification_factor = 2.5
        base_impact_empirical = None
        cluster_type = "FIXED_2.5"
        cluster_sensitivity = None
        surprise_vectorielle = None
        using_default = False
        print(f"⚠️ Amplification fixe : {amplification_factor:.3f} (module non disponible)")
    
    # Calcul impact avec amplification (garde formule S51 calculate_impact_d)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=amplification_factor  # ✅ Calibré ou fixe 2.5
    )"""

if old_calc in content:
    content = content.replace(old_calc, new_calc)
    print("✅ Calcul impact modifié")
else:
    print("⚠️ Bloc calcul impact non trouvé")

# ============================================================================
# MODIFICATION 3 : Enrichissement return dict
# ============================================================================
print("\n📝 MODIFICATION 3 : Enrichissement return dict avec données amplification")

old_return = """    return {
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
    }"""

new_return = """    return {
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
        # Session 94 - ADD-ON Amplification Hybride
        'amplification_factor': amplification_factor,
        'base_impact_empirical': base_impact_empirical,
        'cluster_type': cluster_type,
        'cluster_sensitivity': cluster_sensitivity,
        'surprise_vectorielle': surprise_vectorielle,
        'using_default_cluster': using_default,
        'amplification_method': 'HYBRID' if AMPLIFICATION_HYBRID_AVAILABLE else 'FIXED_2.5'
    }"""

if old_return in content:
    content = content.replace(old_return, new_return)
    print("✅ Return dict enrichi")
else:
    print("⚠️ Return dict non trouvé")

# ============================================================================
# MODIFICATION 4 : Affichage interface cluster
# ============================================================================
print("\n📝 MODIFICATION 4 : Ajout affichage cluster dans interface")

old_display = """    with col3:
        st.markdown("**Formules Utilisées**")
        st.write("• ✅ Ajustement Score (S55)")
        st.write("• ✅ Impact D (S51)")
        st.write("• ✅ TTR C (S52)")
        st.write("• ✅ Pullback V2 (S53)")"""

new_display = """    with col3:
        st.markdown("**Formules Utilisées**")
        st.write("• ✅ Ajustement Score (S55)")
        st.write("• ✅ Impact D (S51)")
        st.write("• ✅ TTR C (S52)")
        st.write("• ✅ Pullback V2 (S53)")
        
        # Session 94 - Affichage amplification hybride
        if 'amplification_method' in predictions:
            st.markdown("---")
            st.markdown("**Amplification (S94)**")
            
            if predictions['amplification_method'] == 'HYBRID':
                st.write(f"✅ **Hybride calibrée**")
                st.write(f"• Cluster: {predictions['cluster_type']}")
                st.write(f"• Base: {predictions['base_impact_empirical']:.1f}p")
                st.write(f"• Factor: {predictions['amplification_factor']:.3f}x")
                
                if predictions['using_default_cluster']:
                    st.write("⚠️ Cluster inconnu (defaults)")
            else:
                st.write(f"⚠️ **Fixe 2.5** (fallback)")"""

if old_display in content:
    content = content.replace(old_display, new_display)
    print("✅ Affichage interface enrichi")
else:
    print("⚠️ Section affichage non trouvée")

# ============================================================================
# Écriture fichier modifié
# ============================================================================
print("\n💾 Écriture fichier modifié...")
with open(PLANIFICATEUR_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Fichier écrit : {PLANIFICATEUR_PATH}")
print()
print("=" * 80)
print("✅✅✅ INTÉGRATION TERMINÉE")
print("=" * 80)
print(f"Backup disponible : 5_Planificateur_V2_FORMULES_VALIDEES.backup_session94_addon_20251026.py")
print()
print("🎯 PROCHAINE ÉTAPE : Tests Streamlit")
print("   → Lancer : streamlit run streamlit_app/app.py")
print("   → Tester dates : 11.09.2025, 12.02.2025, 01.08.2025")
