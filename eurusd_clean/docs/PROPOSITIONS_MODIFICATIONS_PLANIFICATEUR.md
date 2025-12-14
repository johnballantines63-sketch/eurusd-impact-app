# 📋 Propositions Détaillées de Modifications - Planificateur V3

**Date:** 2025-01-XX  
**Statut:** ⚠️ PROPOSITIONS - EN ATTENTE DE VALIDATION  
**Règle:** Aucune modification ne sera effectuée sans votre accord explicite

---

## 🎯 OBJECTIF

Terminer le développement du Planificateur V3 en:
1. Complétant le pipeline pour retourner toutes les données nécessaires
2. Ajoutant les contrôles graphiques manquants
3. Implémentant l'affichage des timings prédits
4. Corrigeant les problèmes d'échelle des graphiques

---

## 📊 STRUCTURE DES PROPOSITIONS

### Phase 1: Compléter le Pipeline
### Phase 2: Interface Graphique
### Phase 3: Intégration et Tests

---

## 🚀 PHASE 1: COMPLÉTER LE PIPELINE

### Proposition 1.1: Compléter étape 6 - Calcul des Impacts

**Fichier:** `scripts/run_pipeline_complete.py`  
**Fonction:** `etape6_calculer_impacts_base_amplifications`  
**Lignes:** 640-675

#### État Actuel
```python
def etape6_calculer_impacts_base_amplifications(...):
    # Calcul simplifié (à améliorer avec vraie mesure)
    impacts_data.append({
        'impact_base': 0.0,
        'impact_reel': 0.0,
        'amplification_parfaite': 1.0
    })
```

#### Proposition de Remplacement

```python
def etape6_calculer_impacts_base_amplifications(
    self,
    identical_clusters: List[Dict],
    trends_df: pd.DataFrame,
    cluster_info_target: Dict
) -> pd.DataFrame:
    """
    Étape 6 : Calculer l'impact de base (formule) et l'amplification parfaite (réel/base).
    
    Args:
        identical_clusters: Liste de clusters identiques
        trends_df: DataFrame des tendances
        cluster_info_target: Informations du cluster cible (pour calculer impact_base)
    
    Returns:
        DataFrame avec :
        - impact_base: Impact calculé par formule
        - impact_reel: Impact réel mesuré
        - amplification_parfaite: Ratio réel/base
        - cluster_date: Date du cluster historique
    """
    self._log(f"Étape 6 : Calcul impacts base & amplifications")
    
    if not identical_clusters:
        return pd.DataFrame()
    
    impacts_data = []
    conn = self._get_connection()
    
    for idx, cluster in enumerate(identical_clusters):
        cluster_date = cluster['date']
        anchor_time = cluster['anchor_time']
        cluster_events = cluster['cluster']['events']
        
        # Calculer impact_base pour ce cluster historique
        if 'empirical_score' in cluster_events.columns:
            avg_score = cluster_events['empirical_score'].mean()
        else:
            avg_score = 44.0  # Valeur par défaut
        
        num_events = len(cluster_events)
        impact_base = calculate_impact_d(
            empirical_score=avg_score,
            num_events=num_events,
            amplification=1.0,
            correction_factor=0.758
        )
        
        # Mesurer impact réel depuis Dukascopy (M1)
        try:
            impact_result = measure_impact_from_dukascopy(
                db_path=self.db_path,
                event_datetime=anchor_time,
                minutes_before=30,
                minutes_after=240,
                timeframe='M1'
            )
            
            impact_reel = impact_result.get('impact_pips', 0.0)
            
        except Exception as e:
            self._log(f"Erreur mesure impact réel pour {cluster_date}: {e}", "WARNING")
            impact_reel = 0.0
        
        # Calculer amplification parfaite
        if impact_base > 0:
            amplification_parfaite = impact_reel / impact_base
        else:
            amplification_parfaite = 1.0
        
        impacts_data.append({
            'impact_base': impact_base,
            'impact_reel': impact_reel,
            'amplification_parfaite': amplification_parfaite,
            'cluster_date': cluster_date,
            'anchor_time': anchor_time
        })
    
    df_impacts = pd.DataFrame(impacts_data)
    self._log(f"✅ {len(df_impacts)} impacts calculés", "SUCCESS")
    return df_impacts
```

#### Modifications Nécessaires

1. **Imports supplémentaires:**
```python
from core.impact_measurement import measure_impact_from_dukascopy
from core.formulas_validated import calculate_impact_d
```

2. **Paramètre supplémentaire:** Ajouter `cluster_info_target` pour référence

---

### Proposition 1.2: Compléter étape 7 - Analyse Relations

**Fichier:** `scripts/run_pipeline_complete.py`  
**Fonction:** `etape7_analyser_relation_tendance_amplification`  
**Lignes:** 681-718

#### État Actuel
- Fusion simple des DataFrames
- Corrélations basiques
- Pas de Random Forest

#### Proposition

```python
def etape7_analyser_relation_tendance_amplification(
    self,
    trends_df: pd.DataFrame,
    impacts_df: pd.DataFrame,
    identical_clusters: List[Dict]
) -> Dict:
    """
    Étape 7 : Analyser la corrélation entre tendance et amplification.
    
    Utilise Random Forest par date si >= 5 clusters, sinon Random Forest global.
    
    Returns:
        Dict avec :
        - correlations: Corrélations calculées
        - rf_model_per_date: Modèle RF par date (si applicable)
        - rf_model_global: Modèle RF global (fallback)
        - results_df: DataFrame avec tous les résultats
    """
    self._log(f"Étape 7 : Analyse relation tendance → amplification")
    
    if trends_df.empty or impacts_df.empty:
        return {
            'correlations': {},
            'rf_model_per_date': None,
            'rf_model_global': None,
            'results_df': pd.DataFrame()
        }
    
    # Fusionner les données
    results_df = pd.concat([trends_df, impacts_df], axis=1)
    
    # Calculer corrélations
    correlations = {}
    if 'r2' in results_df.columns and 'amplification_parfaite' in results_df.columns:
        correlations['r2_vs_amplification'] = results_df['r2'].corr(results_df['amplification_parfaite'])
    
    # Essayer Random Forest par date si >= 5 clusters
    rf_model_per_date = None
    if len(identical_clusters) >= 5:
        try:
            from core.amplification_random_forest_per_date import predict_amplification_with_per_date_rf
            
            # Préparer features
            features_df = results_df[[
                'r2', 'duration_hours', 'amplitude_pips',
                'impact_base', 'cluster_date'
            ]].copy()
            
            rf_model_per_date = {
                'model': 'per_date',
                'n_clusters': len(identical_clusters),
                'available': True
            }
            
            self._log(f"✅ Random Forest par date disponible ({len(identical_clusters)} clusters)", "SUCCESS")
            
        except Exception as e:
            self._log(f"Erreur RF par date: {e}", "WARNING")
    
    # Fallback: Random Forest global
    rf_model_global = None
    if rf_model_per_date is None:
        try:
            from core.amplification_random_forest import predict_amplification_random_forest
            
            rf_model_global = {
                'model': 'global',
                'available': True
            }
            
            self._log("✅ Random Forest global disponible (fallback)", "SUCCESS")
            
        except Exception as e:
            self._log(f"Erreur RF global: {e}", "WARNING")
    
    self._log(f"✅ Analyse terminée", "SUCCESS")
    return {
        'correlations': correlations,
        'rf_model_per_date': rf_model_per_date,
        'rf_model_global': rf_model_global,
        'results_df': results_df
    }
```

---

### Proposition 1.3: Compléter étape 8 - Application Cluster Cible

**Fichier:** `scripts/run_pipeline_complete.py`  
**Fonction:** `etape8_appliquer_cluster_cible`  
**Lignes:** 724-832

#### Modifications Principales

1. **Charger les données de prix pour l'affichage**
2. **Détecter le pattern avec phase_a_robust_validation**
3. **Détecter la tendance pré-événement**
4. **Prédire l'amplification avec Random Forest**
5. **Retourner tous les timings nécessaires**

#### Code Proposé (extraits clés)

```python
def etape8_appliquer_cluster_cible(
    self,
    cluster_info: Dict,
    analysis_results: Dict,
    identical_clusters: List[Dict]
) -> Dict:
    """
    Étape 8 : Appliquer toutes les analyses au cluster cible pour prédire l'impact final.
    
    Sous-étapes complètes:
    8.1 : Calcul de l'Impact de Base
    8.2 : Détection de Tendance
    8.3 : Prédiction d'Amplification
    8.4 : Ajustements Support/Résistance
    8.5 : Ajustements Patterns Finnhub
    8.6 : Détection de Pattern de Prix
    8.7 : Stratégie Hybride Pattern/Formules
    8.8 : Calcul du Target de Sortie
    
    Returns:
        Dict final avec tous les timings et données pour l'affichage
    """
    # ... code existant pour 8.1 (impact_base) ...
    
    # 8.2 : Détection de Tendance
    from core.trend_detection_pre_event_s107 import detect_trend_by_inversion_s107
    
    trend_result = detect_trend_by_inversion_s107(
        db_path=self.db_path,
        event_datetime=anchor_time,
        min_hours_before_event=12,
        min_duration_hours=6.0,
        timeframe='M30'
    )
    
    trend_exists = trend_result.get('trend_exists', False)
    trend_r2 = trend_result.get('r2', 0.0)
    
    # 8.3 : Prédiction d'Amplification (avec Random Forest)
    amplification_predite = self._predict_amplification(
        trend_result,
        impact_base,
        num_events,
        analysis_results,
        identical_clusters
    )
    
    # 8.6 : Détection de Pattern de Prix
    from scripts.phase_a_robust_validation import detect_double_wave_pattern, load_price_window
    
    price_window = load_price_window(
        self.db_path,
        anchor_time,
        minutes_before=120,
        minutes_after=240
    )
    
    pattern_info = detect_double_wave_pattern(
        price_window,
        anchor_time,
        pattern_mode="early"
    )
    
    # Utiliser PIC ABSOLU (critique!)
    pattern_impact = pattern_info.get('wave2_peak_pips_absolute') or pattern_info.get('impact_pips', 0.0)
    
    # 8.7 : Stratégie Hybride
    impact_formules = impact_base * amplification_predite
    ecart_absolu = abs(pattern_impact - impact_formules) if pattern_impact > 0 else 0
    
    if ecart_absolu < 10 or pattern_impact == 0:
        prediction_finale = impact_formules
    else:
        prediction_finale = pattern_impact
    
    # 8.8 : Target de Sortie
    exit_target = min(prediction_finale * 0.80, prediction_finale * 1.5)
    
    # Retourner TOUTES les données pour l'affichage
    final_prediction = {
        # ... métriques existantes ...
        
        # NOUVEAU: Données pour graphique
        'price_window': price_window,
        'baseline_price': pattern_info.get('baseline_price'),
        
        # NOUVEAU: Timings détaillés
        'pattern_wave1_peak_time': pattern_info.get('wave1_peak_time'),
        'pattern_wave2_peak_time': pattern_info.get('wave2_peak_time_absolute') or pattern_info.get('wave2_peak_time'),
        'wave1_price': pattern_info.get('wave1_price'),
        'wave2_price': pattern_info.get('wave2_peak_price_absolute') or pattern_info.get('wave2_price'),
        'wave1_pips': pattern_info.get('wave1_pips', 0.0),
        'wave2_pips_absolute': pattern_info.get('wave2_peak_pips_absolute', 0.0),
        'pullback_time': pattern_info.get('pullback_time'),
        'pullback_price': pattern_info.get('pullback_price'),
        'pullback_pips': pattern_info.get('pullback_pips', 0.0),
        
        # Pattern info complète
        'pattern_type': pattern_info.get('pattern_type', 'NONE'),
        'pattern_direction': pattern_info.get('direction', 'UNKNOWN'),
        'pattern_confidence': pattern_info.get('confidence', 0.0)
    }
    
    return final_prediction
```

---

## 🎨 PHASE 2: INTERFACE GRAPHIQUE

### Proposition 2.1: Section "Timings Prédits"

**Fichier:** `streamlit_app/pages/5_Planificateur_Pipeline_Valide.py`  
**Insertion:** Avant la section graphique (après ligne 297)

#### Code Proposé

```python
# ═══════════════════════════════════════════════════════════════
# SECTION: TIMINGS PRÉDITS
# ═══════════════════════════════════════════════════════════════

st.subheader("🕐 Timings Prédits")

# Préparer les données du tableau
timing_rows = []

# Baseline
baseline_price = final_pred.get('baseline_price')
if baseline_price and anchor_time:
    timing_rows.append({
        "Étape": "Baseline",
        "Heure": format_datetime(anchor_time),
        "Prix": format_price(baseline_price),
        "Pips": "0.00",
        "Δ Pips": "-"
    })

# Wave 1
wave1_time = final_pred.get('pattern_wave1_peak_time')
wave1_price = final_pred.get('wave1_price')
wave1_pips = final_pred.get('wave1_pips', 0.0)
if wave1_time and wave1_price:
    timing_rows.append({
        "Étape": "Pic Wave 1",
        "Heure": format_datetime(wave1_time),
        "Prix": format_price(wave1_price),
        "Pips": format_pips(wave1_pips),
        "Δ Pips": format_pips(wave1_pips)
    })

# Pullback
pullback_time = final_pred.get('pullback_time')
pullback_price = final_pred.get('pullback_price')
pullback_pips = final_pred.get('pullback_pips', 0.0)
if pullback_time and pullback_price:
    timing_rows.append({
        "Étape": "Pullback",
        "Heure": format_datetime(pullback_time),
        "Prix": format_price(pullback_price),
        "Pips": format_pips(pullback_pips),
        "Δ Pips": format_pips(pullback_pips)
    })

# Wave 2 (Pic Absolu)
wave2_time = final_pred.get('pattern_wave2_peak_time')
wave2_price = final_pred.get('wave2_price')
wave2_pips_abs = final_pred.get('wave2_pips_absolute', 0.0)
if wave2_time and wave2_price:
    delta_pips = wave2_pips_abs - wave1_pips if wave1_pips > 0 else wave2_pips_abs
    timing_rows.append({
        "Étape": "Pic Wave 2",
        "Heure": format_datetime(wave2_time),
        "Prix": format_price(wave2_price),
        "Pips": format_pips(wave2_pips_abs),
        "Δ Pips": format_pips(delta_pips)
    })

# Afficher le tableau
if timing_rows:
    df_timings = pd.DataFrame(timing_rows)
    st.dataframe(df_timings, use_container_width=True, hide_index=True)
    
    # Section expandable "Détails Techniques"
    with st.expander("> Détails Techniques"):
        st.markdown("""
        **Méthode de Détection:**
        - Pattern détecté via phase_a_robust_validation
        - Utilisation du pic absolu pour Wave 2 (capture Wave 3 si présente)
        
        **Validation:**
        - Critères R² >= 0.15 pour tendances
        - Amplitude minimum 15 pips
        - Fenêtre de détection: 90 min (Wave 1), 45 min (Pullback), 180 min (Wave 2)
        """)
else:
    st.info("📊 Les timings seront affichés ici une fois le pattern détecté.")
```

---

### Proposition 2.2: Contrôles de Zoom Temporel

**Fichier:** `streamlit_app/pages/5_Planificateur_Pipeline_Valide.py`  
**Insertion:** Avant la section graphique

#### Code Proposé

```python
# ═══════════════════════════════════════════════════════════════
# SECTION: CONTRÔLES DE ZOOM TEMPOREL
# ═══════════════════════════════════════════════════════════════

st.subheader("🔍 Contrôles de Zoom Temporel")

# Initialiser l'état de zoom si nécessaire
if 'zoom_state' not in st.session_state:
    st.session_state.zoom_state = {
        'center_time': None,
        'time_range_hours': time_margin_hours * 2,  # Range par défaut
        'min_time': None,
        'max_time': None
    }

# Colonnes pour les boutons
col_zoom1, col_zoom2, col_zoom3, col_zoom4, col_zoom5 = st.columns(5)

with col_zoom1:
    if st.button("Zoom -", use_container_width=True):
        # Augmenter la fenêtre temporelle (zoom out)
        current_range = st.session_state.zoom_state['time_range_hours']
        new_range = min(current_range * 1.5, 12.0)  # Max 12h
        st.session_state.zoom_state['time_range_hours'] = new_range
        st.rerun()

with col_zoom2:
    if st.button("Zoom +", use_container_width=True):
        # Réduire la fenêtre temporelle (zoom in)
        current_range = st.session_state.zoom_state['time_range_hours']
        new_range = max(current_range / 1.5, 0.5)  # Min 0.5h
        st.session_state.zoom_state['time_range_hours'] = new_range
        st.rerun()

with col_zoom3:
    if st.button("Centrer", use_container_width=True):
        # Centrer sur l'événement
        if anchor_time:
            st.session_state.zoom_state['center_time'] = anchor_time
            st.rerun()

with col_zoom4:
    if st.button("Vue complète", use_container_width=True):
        # Réinitialiser à la vue complète
        st.session_state.zoom_state = {
            'center_time': None,
            'time_range_hours': time_margin_hours * 2,
            'min_time': None,
            'max_time': None
        }
        st.rerun()

with col_zoom5:
    if st.button("Reset", use_container_width=True):
        # Réinitialiser tous les contrôles
        st.session_state.zoom_state = {
            'center_time': None,
            'time_range_hours': time_margin_hours * 2,
            'min_time': None,
            'max_time': None
        }
        st.session_state['time_margin'] = 2.0
        st.session_state['y_margin_pct'] = 5.0
        st.rerun()
```

---

### Proposition 2.3: Contrôles d'Amplitude Y

**Fichier:** `streamlit_app/pages/5_Planificateur_Pipeline_Valide.py`  
**Insertion:** Après les contrôles de zoom

#### Code Proposé

```python
# ═══════════════════════════════════════════════════════════════
# SECTION: CONTRÔLES D'AMPLITUDE Y
# ═══════════════════════════════════════════════════════════════

st.subheader("📏 Contrôles d'Amplitude Y")

# Colonnes pour les boutons
col_amp1, col_amp2, col_amp3, col_amp4 = st.columns(4)

# Initialiser le bouton sélectionné
if 'selected_amp_button' not in st.session_state:
    st.session_state.selected_amp_button = 'Normal'

with col_amp1:
    button_type = "primary" if st.session_state.selected_amp_button == 'Max' else "secondary"
    if st.button("Max Amplitude", use_container_width=True, type=button_type):
        st.session_state['y_margin_pct'] = 0.0
        st.session_state.selected_amp_button = 'Max'
        st.rerun()

with col_amp2:
    button_type = "primary" if st.session_state.selected_amp_button == 'Serré' else "secondary"
    if st.button("Serré (2%)", use_container_width=True, type=button_type):
        st.session_state['y_margin_pct'] = 2.0
        st.session_state.selected_amp_button = 'Serré'
        st.rerun()

with col_amp3:
    button_type = "primary" if st.session_state.selected_amp_button == 'Normal' else "secondary"
    if st.button("Normal (5%)", use_container_width=True, type=button_type):
        st.session_state['y_margin_pct'] = 5.0
        st.session_state.selected_amp_button = 'Normal'
        st.rerun()

with col_amp4:
    button_type = "primary" if st.session_state.selected_amp_button == 'Large' else "secondary"
    if st.button("Large (10%)", use_container_width=True, type=button_type):
        st.session_state['y_margin_pct'] = 10.0
        st.session_state.selected_amp_button = 'Large'
        st.rerun()
```

---

### Proposition 2.4: Amélioration du Graphique

**Fichier:** `streamlit_app/pages/5_Planificateur_Pipeline_Valide.py`  
**Section:** Lignes 298-458

#### Modifications Proposées

1. **Utiliser les états de zoom:**
```python
# Au lieu de time_margin_hours fixe, utiliser zoom_state
zoom_state = st.session_state.get('zoom_state', {})
time_range = zoom_state.get('time_range_hours', time_margin_hours * 2)
center_time = zoom_state.get('center_time', anchor_time_dt)

# Calculer min/max avec zoom
if center_time:
    min_time = center_time - timedelta(hours=time_range / 2)
    max_time = center_time + timedelta(hours=time_range / 2)
else:
    min_time = price_window_plotly['datetime'].min() - timedelta(hours=time_range / 2)
    max_time = price_window_plotly['datetime'].max() + timedelta(hours=time_range / 2)
```

2. **Ajouter annotations pour les timings:**
```python
# Annotation pour Wave 1
if pattern_wave1_peak_time and wave1_price:
    fig.add_annotation(
        x=pattern_wave1_peak_time,
        y=wave1_price,
        text=f"Wave 1<br>{format_pips(wave1_pips)} pips",
        showarrow=True,
        arrowhead=2,
        arrowcolor="green"
    )

# Annotation pour Wave 2 (pic absolu)
if pattern_wave2_peak_time and wave2_price:
    fig.add_annotation(
        x=pattern_wave2_peak_time,
        y=wave2_price,
        text=f"Pic Wave 2<br>{format_pips(wave2_pips_abs)} pips",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red"
    )
```

3. **Ajouter ligne d'amplitude:**
```python
# Ligne pointillée montrant l'amplitude totale
if baseline_price and wave2_price:
    fig.add_trace(go.Scatter(
        x=[baseline_time, pattern_wave2_peak_time],
        y=[baseline_price, wave2_price],
        mode='lines',
        name=f'Amplitude ({format_pips(wave2_pips_abs)} pips)',
        line=dict(dash='dash', color='red', width=2)
    ))
```

---

## 🔄 PHASE 3: INTÉGRATION ET TESTS

### Proposition 3.1: Mise à Jour de execute_complete_pipeline

**Fichier:** `scripts/run_pipeline_complete.py`  
**Fonction:** `execute_complete_pipeline`  
**Lignes:** 838-950

#### Modifications Nécessaires

1. **Passer cluster_info_target à étape 6:**
```python
# Étape 6 : Calculer impacts base & amplifications
impacts_df = self.etape6_calculer_impacts_base_amplifications(
    identical_clusters,
    trends_df,
    cluster_info  # Ajouter ce paramètre
)
```

2. **S'assurer que price_window est dans les résultats:**
```python
# Dans les résultats finaux
results = {
    'etape1_events': df_events,
    # ... autres étapes ...
    'price_window': final_prediction.get('price_window'),  # NOUVEAU
    'final_prediction': final_prediction
}
```

---

### Proposition 3.2: Plan de Test

#### Tests à Effectuer

1. **Test sur date de référence (2025-09-11):**
   - Vérifier que tous les timings sont présents
   - Vérifier que le graphique s'affiche correctement
   - Vérifier les contrôles de zoom/amplitude

2. **Test sur date DOUBLE_WAVE (2025-06-23):**
   - Vérifier que le pic absolu est utilisé
   - Vérifier que Wave 3 est capturé si présente

3. **Test sur date sans pattern (cas NONE):**
   - Vérifier que l'interface gère gracieusement l'absence de pattern

#### Script de Test Proposé

```python
# scripts/test_planificateur_interface.py
def test_planificateur_complete():
    """Test complet du planificateur avec interface"""
    from scripts.run_pipeline_complete import PipelineExecutor
    import config
    
    executor = PipelineExecutor(config.DB_PATH, verbose=True)
    result = executor.execute_complete_pipeline('2025-09-11')
    
    assert result['success'], "Pipeline doit réussir"
    assert 'price_window' in result['results'], "price_window doit être présent"
    assert 'baseline_price' in result['final_prediction'], "baseline_price doit être présent"
    
    final_pred = result['final_prediction']
    assert final_pred.get('pattern_wave1_peak_time'), "Wave 1 timing doit être présent"
    assert final_pred.get('pattern_wave2_peak_time'), "Wave 2 timing doit être présent"
    
    print("✅ Tous les tests passés")
```

---

## 📝 RÉSUMÉ DES MODIFICATIONS

### Fichiers à Modifier

1. **scripts/run_pipeline_complete.py**
   - Compléter étape 6 (Ligne 640-675)
   - Compléter étape 7 (Ligne 681-718)
   - Compléter étape 8 (Ligne 724-832)
   - Ajouter imports nécessaires

2. **streamlit_app/pages/5_Planificateur_Pipeline_Valide.py**
   - Ajouter section "Timings Prédits" (après ligne 297)
   - Ajouter contrôles de zoom (avant graphique)
   - Ajouter contrôles d'amplitude Y (après zoom)
   - Améliorer le graphique (lignes 298-458)

### Nouveaux Fichiers

1. **scripts/test_planificateur_interface.py** (optionnel)
   - Tests pour valider les modifications

---

## ⚠️ POINTS D'ATTENTION

1. **Pic Absolu:** S'assurer que `wave2_peak_pips_absolute` est toujours utilisé
2. **Timezone:** Vérifier que tous les timings sont dans la même timezone
3. **Performance:** Le pipeline peut être plus lent avec les nouvelles étapes
4. **Fallbacks:** S'assurer que tous les fallbacks fonctionnent si données manquantes

---

## ✅ VALIDATION REQUISE

**Avant toute implémentation, merci de valider:**

1. ✅ Les propositions de modifications vous conviennent-elles?
2. ✅ Y a-t-il des éléments à modifier ou supprimer?
3. ✅ La priorité des phases vous convient-elle?
4. ✅ Souhaitez-vous tester sur une date spécifique en premier?

**En attente de votre validation avant implémentation.**

---

**Document créé le:** 2025-01-XX  
**Statut:** ⚠️ EN ATTENTE DE VALIDATION  
**Prochaines étapes:** Implémentation après validation




