# GUIDE MODIFICATION PLANIFICATEUR V2.6 → V2.7
## Session 110 - Amplification Dynamique

**Date :** 3 novembre 2025  
**Objectif :** Ajouter calcul amplification dynamique au planificateur existant

---

## 📋 FICHIERS NÉCESSAIRES

### Déjà créés ✅
- `eurusd_clean/data/clusters_database.json` ✅
- `eurusd_clean/app/amplification_calculator.py` ✅

### À modifier
- Planificateur actuel : `5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 6.py`

---

## ✏️ MODIFICATIONS EXACTES

### MODIFICATION 1 : Imports (Ligne ~50)

**Après les imports existants, ajouter :**

```python
# Import module Amplification Dynamique (Session 110) ⭐ NOUVEAU V2.7
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
```

---

### MODIFICATION 2 : Fonction calculate_predictions (Ligne ~174)

**AVANT (V2.4) :**
```python
def calculate_predictions(cpi_events: pd.DataFrame) -> dict:
    # ...
    # Test avec amplification optimale 2.5 (lignes 90-96)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=2.5  # ← FIXE
    )
```

**APRÈS (V2.7) :**
```python
def calculate_predictions(cpi_events: pd.DataFrame, amplification: float = 2.5) -> dict:
    # ...
    # V2.7 : Utilisation amplification paramètre (fixe ou dynamique)
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cpi_events),
        amplification=amplification  # ← PARAMÈTRE
    )
    # ...
    return {
        # ... tous les champs existants
        'amplification_used': amplification  # ← AJOUTER ce champ
    }
```

---

### MODIFICATION 3 : Interface principale (Ligne ~650)

**Juste AVANT le bouton "Calculer Prédictions", ajouter cette section :**

```python
# ═══════════════════════════════════════════════════════════════
# SECTION AMPLIFICATION V2.7 ⭐ NOUVEAU
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("## 🔬 Facteur d'Amplification (V2.7)")

if AMPLIFICATION_MODULE_AVAILABLE:
    # Mode sélection
    amp_mode = st.radio(
        "Mode de calcul",
        options=["🔬 Automatique (calculé selon tendances)", "✍️ Manuel (saisie libre)"],
        help="Automatique : +39.6% précision validée sur 17 dates\nManuel : ajustement trader personnalisé"
    )
    
    if amp_mode == "✍️ Manuel (saisie libre)":
        # Mode manuel
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
            show_auto_suggestion = st.checkbox(
                "💡 Voir suggestion auto",
                help="Affiche la valeur calculée automatiquement"
            )
        
        amplification_to_use = amplification_manual
        amp_calculation_method = "manual"
        
    else:
        # Mode automatique
        st.info("ℹ️ L'amplification sera calculée automatiquement selon les tendances pré-événement")
        amplification_to_use = None  # Sera calculé plus tard
        amp_calculation_method = "automatic"
        show_auto_suggestion = False

else:
    # Module non disponible : mode manuel uniquement
    st.warning("⚠️ Module amplification dynamique non disponible - Mode manuel uniquement")
    amplification_to_use = st.number_input(
        "Facteur d'amplification",
        min_value=0.5,
        max_value=5.0,
        value=2.5,
        step=0.1
    )
    amp_calculation_method = "manual_fallback"
    show_auto_suggestion = False
```

---

### MODIFICATION 4 : Dans le bouton "Calculer" (Ligne ~680)

**APRÈS avoir chargé les événements, AVANT calculate_predictions :**

```python
# ... code existant jusqu'à "st.success(...événements trouvés)"

# ═══════════════════════════════════════════════════════════════
# V2.7 : CALCUL AMPLIFICATION DYNAMIQUE
# ═══════════════════════════════════════════════════════════════

if amp_calculation_method == "automatic" and AMPLIFICATION_MODULE_AVAILABLE:
    with st.spinner("🔬 Calcul amplification dynamique..."):
        try:
            # Préparer événements pour calcul
            events_list = []
            for _, event in high_events.iterrows():
                events_list.append({
                    'event': event['label'],
                    'actual': event.get('actual'),
                    'estimate': event.get('estimate')
                })
            
            # Heure événement (premier événement)
            event_time = pd.to_datetime(high_events.iloc[0]['ts_utc'])
            
            # Path DB
            db_path = Path(get_db_path())
            
            # CALCUL AMPLIFICATION
            amp_result = calculate_amplification(
                events=events_list,
                event_time=event_time,
                db_path=db_path
            )
            
            amplification_to_use = amp_result['amplification']
            
            # Afficher résultat
            st.success(f"✅ Amplification calculée : **{amplification_to_use:.3f}**")
            
            with st.expander("📊 Détails calcul amplification"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Cluster identifié**")
                    st.write(f"ID : {amp_result['cluster_id']}")
                    st.write(f"Nom : {amp_result['cluster_name']}")
                
                with col2:
                    st.write(f"**Méthode**")
                    st.write(f"Type : {amp_result['method']}")
                    st.write(f"Baseline : {amp_result['cluster_baseline']:.3f}")
                
                with col3:
                    st.write(f"**Inversion**")
                    if amp_result['inversion_detected']:
                        st.success(f"✅ Détectée")
                        st.write(f"Durée : {amp_result['duration_hours']:.1f}h")
                        if amp_result['ecart_calculated']:
                            st.write(f"Écart : {amp_result['ecart_calculated']:+.3f}")
                    else:
                        st.info(f"❌ Non détectée")
        
        except Exception as e:
            st.error(f"❌ Erreur calcul amplification : {e}")
            st.warning("→ Utilisation baseline 2.5")
            amplification_to_use = 2.5

elif amp_calculation_method == "manual" and show_auto_suggestion and AMPLIFICATION_MODULE_AVAILABLE:
    # Mode manuel mais afficher suggestion
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
# FIN SECTION AMPLIFICATION
# ═══════════════════════════════════════════════════════════════

# PUIS appeler calculate_predictions avec amplification
with st.spinner("Calcul avec formules validées Session 51-55..."):
    predictions = calculate_predictions(high_events, amplification=amplification_to_use)
```

---

### MODIFICATION 5 : Affichage métrique amplification (Ligne ~730)

**APRÈS les métriques Impact/TTR/Pullback, ajouter :**

```python
# Métriques principales
col1, col2, col3, col4, col5, col6 = st.columns(6)  # ← 6 colonnes au lieu de 5

# ... col1 à col5 existantes ...

with col6:
    st.metric(
        "Amplification Utilisée",
        f"{predictions['amplification_used']:.3f}",
        help="Facteur d'amplification (V2.7)"
    )
```

---

### MODIFICATION 6 : Footer (dernières lignes)

**Remplacer footer par :**

```python
st.markdown("---")
st.markdown("""
**Planificateur V2.7** - Amplification Dynamique (Session 110) ⭐  

**Base V2.4 :**
- Méthode Session 55 validée  
- Formules : Ajustement Score (99.9%), Impact D (98.6%), TTR C (94.4%), Pullback V2 (99.3%)  
- Détection automatique type mouvement (Session 68)  

**Nouveauté V2.7 :**
- 🔬 Calcul amplification dynamique selon tendances pré-événement  
- ✅ Amélioration +39.6% sur 17 dates validées (Cluster #3 CPI)  
- 📊 Baseline adaptative selon cluster détecté  
- ✍️ Mode manuel pour ajustements trader  
""")
```

---

## 🧪 TEST

**Après modifications, tester :**

1. **Lancer Streamlit :**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app
streamlit run Home.py
```

2. **Aller sur page Planificateur V2.4** (fichier modifié)

3. **Tester mode automatique :**
   - Date : 11.09.2025
   - Mode : Automatique
   - Vérifier amplification calculée ≈ 1.73

4. **Tester mode manuel :**
   - Saisir 3.0
   - Vérifier prédictions changent

---

## 📝 NOTES

- **Rétrocompatibilité** : Si module non disponible, fonctionne en mode manuel avec 2.5
- **Fallback sécurisé** : Erreur → amplification 2.5
- **Mode manuel** : Permet ajustements trader même en mode auto disponible
- **Suggestion** : Mode manuel peut afficher suggestion auto

---

## ⚠️ POINTS D'ATTENTION

1. **Paths** : Vérifier chemins eurusd_clean/app et data/
2. **DB** : Fonction get_db_path() doit retourner bon chemin
3. **Timezone** : Événement ts_utc doit être timezone-aware
4. **Erreurs** : Toujours try/catch avec fallback 2.5

---

**FIN DU GUIDE**
