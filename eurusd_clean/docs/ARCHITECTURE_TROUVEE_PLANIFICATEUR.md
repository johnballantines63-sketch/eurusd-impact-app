# Architecture Trouvée dans les Planificateurs Existants

**Date** : 2025-01-XX  
**Objectif** : Documenter l'architecture intégrée dans les planificateurs existants

---

## 📋 Fichiers Examinés

1. `streamlit_app/pages/3_Planificateur_V3_CLEAN.py` - Planificateur principal
2. `streamlit_app/pages/4_Planificateur_V3_Pipeline_Valide.py` - Version pipeline
3. `streamlit_app/pages/5_Planificateur_Pipeline_Valide.py` - Version actuelle

---

## 🔍 Architecture Intégrée Trouvée

### 1. Utilisation du PipelineExecutor

**Dans `3_Planificateur_V3_CLEAN.py` (ligne 2994)** :
```python
from run_pipeline_complete import PipelineExecutor

executor = PipelineExecutor(
    db_path=DB_PATH,
    verbose=False,
    force_timeframe=None
)

result = executor.execute_complete_pipeline(date_str)
```

**Structure attendue du résultat** :
```python
{
    'success': bool,
    'final_prediction': {
        'prediction_finale': float,  # ou dict avec 'impact_pips'
        'exit_target': float,
        'exit_strategy': str,
        'amplification_predite': float,
        'pattern_info': {
            'pattern_type': str,
            'direction': str,
            'baseline_price': float,
            'wave1_pips': float,
            'wave1_peak_time': datetime,
            'pullback_pips': float,
            'pullback_time': datetime,
            'wave2_pips': float,
            'wave2_peak_time': datetime,
            'wave2_peak_pips_absolute': float,  # ⚠️ CRITIQUE : Pic absolu
            'wave2_peak_time_absolute': datetime,
            'wave2_peak_price_absolute': float
        },
        'pattern_type': str,
        'pattern_direction': str
    }
}
```

**Fallback** : Si le pipeline échoue, utilisation de `predict_double_wave_base()`

---

### 2. Modules Utilisés dans le Planificateur

#### Modules Existants ✅

1. **`src/core/doublewave_prediction.py`** ✅ EXISTE
   - Fonction : `predict_doublewave_overlap()`
   - Utilisé pour prédictions Double Wave

2. **`src/core/ensemble_prediction.py`** ✅ EXISTE
   - Fonction : `predict_pattern_based_ensemble()`
   - Utilisé pour prédictions avec ensemble methods

3. **`src/core/formulas_validated.py`** ✅ EXISTE
   - Fonctions :
     - `calculate_impact_d()`
     - `calculate_ttr_c()`
     - `calculate_pullback_v2()`
     - `calculate_amplification_extended()`
     - `calculate_adjusted_empirical_score()`

4. **`src/core/event_utils.py`** ✅ EXISTE
   - Fonctions :
     - `normalize_event_keys_list()`
     - `create_event_key_set()`
     - `normalize_event_key_with_variants()`

#### Modules Manquants ❌

1. **`src/core/amplification_prediction.py`** ❌ MANQUANT
   - Fonction attendue : `predict_impact_with_amplification()`
   - Utilisé dans `predict_double_wave_base()` (ligne 2089, 2276)
   - **Action** : Créer ce module ou intégrer la logique ailleurs

---

### 3. Détection de Pattern Intégrée

**Fonction `detect_pattern_type()` dans `3_Planificateur_V3_CLEAN.py`** (ligne 1739) :

**Paramètres** :
- `df_prices`: DataFrame avec prix M1
- `event_time`: datetime de l'événement
- `baseline_price`: Prix de référence

**Retour** :
```python
{
    'pattern_type': 'DOUBLE_WAVE' | 'SINGLE_WAVE_FORT' | 'SINGLE_WAVE_STANDARD' | 'INCONNU',
    'metrics': {
        'impact_pips': float,
        'wave1_pips': float,
        'pullback_pips': float,
        'wave2_pips': float,
        'baseline_price': float,
        'direction': 'UP' | 'DOWN'
    },
    'movement': {
        'baseline_price': float,
        'direction': 'UP' | 'DOWN'
    }
}
```

**Logique** :
1. Détermine direction depuis fenêtre 5-60 min après événement
2. Détecte Wave 1 (pic dans 90 min)
3. Détecte Pullback (dans 45 min après Wave 1)
4. Détecte Wave 2 (pic dans 180 min après pullback)
5. Valide critères (pips, ratios)

**⚠️ IMPORTANT** : Cette fonction est intégrée dans le planificateur mais ne calcule PAS le pic absolu. Il faut l'ajouter.

---

### 4. Prédiction Double Wave Intégrée

**Fonction `predict_double_wave_base()` dans `3_Planificateur_V3_CLEAN.py`** (ligne 2054) :

**Paramètres** :
- `df_events_enriched`: DataFrame événements enrichis
- `baseline_price`: Prix de référence
- `direction`: 'UP' | 'DOWN'
- `use_support_resistance`: bool (désactivé actuellement)
- `use_aggregate_indicators`: bool (désactivé actuellement)

**Retour** :
```python
{
    'prediction_pips': float,
    'base_impact': float,
    'amplification': float,
    'amplification_base': float,
    'amplification_predicted': float,
    'amplification_method': str,  # 'with_actuals' ou 'without_actuals'
    'status': 'predicted',
    'reason': str,
    'phase1_pips': float,
    'pullback_pips': float,
    'phase2_pips': float,
    'total_net_pips': float
}
```

**Logique** :
1. Calcule impact de base avec `calculate_impact_d()` (amplification=1.0)
2. Prédit amplification avec `predict_impact_with_amplification()` (module manquant)
3. Applique ratios Double Wave validés (Phase 1: 58%, Pullback: 84%, Phase 2: 90%)

---

### 5. Stratégie de Sortie

**Dans le planificateur** (ligne 3018) :
- `exit_target` extrait depuis `final_prediction.get('exit_target')`
- `exit_strategy` extrait depuis `final_prediction.get('exit_strategy')`

**Attendu** :
- Sortie à 80% du prédit
- Limite maximale : 1.5x du prédit

**⚠️ MANQUANT** : Module `src/core/exit_strategy.py` avec `calculate_exit_target()`

---

## 🎯 Ce qui Fonctionnait Hier Soir

### Architecture Probable

1. **PipelineExecutor** dans `scripts/run_pipeline_complete.py`
   - Implémenté avec les 8 étapes
   - Utilisait probablement les modules existants pour certaines étapes

2. **Détection Pattern**
   - Utilisait `detect_pattern_type()` intégrée dans le planificateur
   - OU utilisait un module externe `phase_a_robust_validation.py`

3. **Prédiction Amplification**
   - Utilisait `predict_impact_with_amplification()` depuis `amplification_prediction.py`
   - OU logique intégrée dans le PipelineExecutor

4. **Stratégie de Sortie**
   - Calculée dans le PipelineExecutor (étape 8.8)
   - OU utilisait `exit_strategy.py`

---

## 📝 Plan d'Action pour Retrouver la Situation Fonctionnelle

### Phase 1 : Compléter le PipelineExecutor

1. **Étape 8.6 : Détection Pattern**
   - Option A : Utiliser `detect_pattern_type()` du planificateur (intégrée)
   - Option B : Créer `scripts/phase_a_robust_validation.py` avec `detect_double_wave_pattern()`
   - ⚠️ CRITIQUE : Ajouter calcul du pic absolu (`wave2_peak_pips_absolute`)

2. **Étape 8.3 : Prédiction Amplification**
   - Option A : Créer `src/core/amplification_prediction.py` avec `predict_impact_with_amplification()`
   - Option B : Intégrer Random Forest directement dans le PipelineExecutor
   - Option C : Utiliser `calculate_amplification_extended()` existant

3. **Étape 8.8 : Target de Sortie**
   - Créer `src/core/exit_strategy.py` avec `calculate_exit_target()`
   - OU intégrer directement dans le PipelineExecutor

### Phase 2 : Intégrer dans le Planificateur Streamlit

1. **Chargement des Prix**
   - Utiliser `load_prices_for_date()` du planificateur (ligne 476)
   - Retourner `price_window` dans les résultats du pipeline

2. **Graphique**
   - Les contrôles d'échelle sont déjà présents ✅
   - Intégrer les données de prix réelles
   - Afficher marqueurs (Wave 1, Wave 2, baseline, événement)

3. **Affichage des Résultats**
   - Structure déjà présente ✅
   - Compléter avec toutes les métriques du pipeline

---

## 🔧 Modules à Créer/Compléter

### 1. `src/core/amplification_prediction.py` ⚠️ PRIORITÉ 1

**Fonction attendue** :
```python
def predict_impact_with_amplification(
    df_events: pd.DataFrame,
    surprise_max: float,
    db_path: Path,
    use_actuals: bool = True
) -> Dict:
    """
    Prédit amplification avec modèle de régression multiple
    
    Returns:
    {
        'amplification': float,
        'impact_adjusted': float,
        'impact_base': float,
        'impact_final': float,
        'method': str  # 'with_actuals' ou 'without_actuals'
    }
    """
```

**Utilisé dans** :
- `predict_double_wave_base()` (ligne 2089, 2276)
- Prédiction amplification pour Double Wave et Single Wave

---

### 2. `src/core/exit_strategy.py` ⚠️ PRIORITÉ 2

**Fonction attendue** :
```python
def calculate_exit_target(
    impact_predicted: float,
    exit_percentage: float = 0.80,
    max_multiplier: float = 1.5
) -> Dict:
    """
    Calcule target de sortie optimisé
    
    Returns:
    {
        'exit_target': float,
        'exit_strategy': str,
        'exit_percentage': float,
        'max_limit': float
    }
    """
```

---

### 3. `scripts/phase_a_robust_validation.py` ⚠️ PRIORITÉ 3 (Optionnel)

**Si on veut séparer la détection de pattern** :
- `detect_double_wave_pattern()` - Détection complète avec pic absolu
- `load_price_window()` - Chargement fenêtre de prix

**Sinon** : Utiliser `detect_pattern_type()` intégrée dans le planificateur

---

## ✅ Ce qui Est Déjà Fonctionnel

1. **Structure du planificateur** ✅
   - Interface Streamlit complète
   - Contrôles d'échelle du graphique
   - Affichage des résultats

2. **Détection de pattern** ✅
   - `detect_pattern_type()` intégrée
   - Logique complète (Wave 1, Pullback, Wave 2)

3. **Calcul impact de base** ✅
   - `calculate_impact_d()` dans `formulas_validated.py`
   - Formules validées

4. **Chargement données** ✅
   - `load_events_for_date()` - Chargement événements
   - `load_prices_for_date()` - Chargement prix

---

## 🚀 Prochaines Étapes

1. **Créer `amplification_prediction.py`** avec logique de prédiction amplification
2. **Créer `exit_strategy.py`** avec calcul target de sortie
3. **Compléter PipelineExecutor** avec implémentations complètes des 8 étapes
4. **Ajouter calcul pic absolu** dans la détection de pattern
5. **Intégrer chargement prix** dans le pipeline
6. **Tester sur date de référence** (2025-09-11)

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Architecture identifiée, prêt pour implémentation




