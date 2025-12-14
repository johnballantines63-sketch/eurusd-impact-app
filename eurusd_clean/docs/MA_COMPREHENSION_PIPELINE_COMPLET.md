# Ma Compréhension du Pipeline Complet - Version de Référence

**Date** : 2025-01-XX  
**Objectif** : Présenter ma compréhension du pipeline complet pour validation avant implémentation

---

## 🎯 Vue d'Ensemble

Le pipeline complet est un système en **8 étapes séquentielles** qui prédit l'impact des événements économiques sur EUR/USD en combinant :
- Analyse d'événements économiques (clusters, noyaux durs)
- Recherche de clusters historiques identiques
- Détection de tendances pré-événement
- Prédiction d'amplification avec Random Forest
- Détection de patterns de prix (Double Wave, Single Wave)
- Stratégie de sortie optimisée

**Performance attendue** :
- MAE : 8.4 pips
- Taux acceptable : 63.2% (erreur < 20%)
- Taux excellent : 55.3% (erreur < 10%)

---

## 📊 Architecture en 8 Étapes

### Étape 1 : Charger Événements

**Objectif** : Charger tous les événements HIGH impact pour une date donnée

**Source** : Table `events` (pas `economic_events`)

**Filtres** :
- Date cible
- Pays : US, EU, DE (par défaut)
- `empirical_score > 40` (HIGH impact uniquement) ⚠️ CRITIQUE

**Module utilisé** : `core.event_loader.load_high_impact_events()`

**Sortie** : DataFrame avec colonnes :
- `event_key`, `country`, `importance_n`, `empirical_score`, `actual`, `forecast`, `previous`, `ts_utc`

**Statut** : ✅ Implémenté (utilise module existant)

---

### Étape 2 : Détecter Clusters

**Objectif** : Grouper les événements qui se produisent dans une fenêtre temporelle

**Méthode** : Fenêtre glissante de 30 minutes par défaut

**Algorithme** :
1. Trier événements par `ts_utc`
2. Pour chaque événement non traité :
   - Créer fenêtre [event_time, event_time + 30 min]
   - Grouper tous les événements dans cette fenêtre
   - Anchor time = heure du premier événement (arrondie à la minute)
   - Marquer comme traités

**Paramètres** :
- `window_minutes` : 30 (défaut)

**Sortie** : Liste de clusters avec :
- `events` : DataFrame des événements du cluster
- `anchor_time` : datetime (heure d'ancrage)
- `n_events` : int (nombre d'événements)

**Statut** : ✅ Implémenté (logique simple mais fonctionnelle)

---

### Étape 3 : Définir Noyau Dur

**Objectif** : Identifier les événements "core" qui apparaissent fréquemment ensemble dans l'historique

**Méthode** : Analyse de fréquence sur 5 ans d'historique

**Algorithme** :
1. Créer identifiants canoniques pour chaque événement : `{event_key}_{country}_{importance}`
2. Analyser fréquence d'apparition de chaque événement avec les autres dans l'historique
3. Calculer support score (fréquence d'apparition ensemble)
4. Filtrer par seuil de support (>= 0.8 = 80%)

**Paramètres** :
- `support_threshold` : 0.8 (80% de fréquence)
- `years_lookback` : 5 ans

**Support** : Noyaux durs pré-définis (CPI, NFP) dans :
- `docs/VALIDATION/CORE_EVENTS_CPI.txt`
- `docs/VALIDATION/CORE_EVENTS_NFP.txt`

**Sortie** : Cluster info avec :
- `cluster` : Cluster original
- `core_events` : Liste des identifiants des événements du noyau dur
- `n_core_events` : Nombre d'événements core
- `n_total_events` : Nombre total d'événements
- `support_scores` : Dict {event_id: support_score}

**Statut** : ⚠️ Simplifié (analyse historique complète à implémenter)

---

### Étape 4 : Rechercher Clusters Identiques

**Objectif** : Trouver des clusters historiques avec le même noyau dur pour utiliser leurs impacts réels

**Méthode** : Similarité Jaccard entre noyaux durs

**Algorithme** :
1. Pour chaque date dans l'historique (5 ans) :
   - Charger événements pour cette date
   - Détecter clusters (Étape 2)
   - Définir noyau dur pour chaque cluster (Étape 3)
   - Calculer similarité Jaccard avec noyau dur du cluster cible
2. Filtrer par :
   - Jaccard >= 0.60 (seuil assoupli)
   - Heure d'événement ±10 minutes autour de l'heure cible

**Formule Jaccard** :
```
J(A, B) = |A ∩ B| / |A ∪ B|
```

**Paramètres** :
- `jaccard_threshold` : 0.60 (assoupli de 0.8)
- `years_lookback` : 5 ans
- Fenêtre heure : ±10 minutes

**Sortie** : Liste de clusters identiques avec :
- `date` : Date du cluster historique
- `jaccard_score` : Score de similarité (0.0 - 1.0)
- `core_events` : Liste des événements du noyau dur
- `cluster` : Cluster historique complet

**Statut** : ⚠️ Simplifié (recherche historique complète à implémenter)

---

### Étape 5 : Calculer Tendances

**Objectif** : Détecter et mesurer les tendances pré-événement pour chaque cluster identique

**Méthode** : `detect_trend_pre_event_robust` (multi-timeframe)

**Timeframes testées** : M1, M5, M15, M30, H1

**Critères de détection** :
- `min_hours_before_event` : 12 heures (assoupli de 24)
- `min_duration_hours` : 6.0 heures (adapté selon timeframe)
  - M30, H1 : 6 heures minimum
  - M1, M5, M15 : 8 heures minimum
- `lookback_days` : 14 jours
- `min_r2` : 0.15
- `min_amplitude_pips` : 15.0

**Méthode de détection** : Validated Inversion (Session 107)
1. Charger prix sur 14 jours avant événement
2. Détecter extrema locaux (peaks/troughs) avec prominence
3. Filtrer extrema à >= 12h avant événement
4. Prendre le dernier extremum majeur (inversion)
5. Calculer régression linéaire depuis inversion jusqu'à événement
6. Valider avec R² >= 0.15, t-stat >= 2.0, amplitude >= 15 pips

**Module utilisé** : `core.trend_detection_pre_event_s107.detect_trend_by_inversion_s107()`

**Sortie** : DataFrame avec pour chaque cluster :
- `trend_exists` : bool
- `r2` : float (coefficient de détermination)
- `amplitude_pips` : float
- `duration_minutes` : int
- `direction` : 'UP' | 'DOWN'
- `timeframe_used` : str

**Statut** : ⚠️ Simplifié (intégration complète à faire)

---

### Étape 6 : Calculer Impacts Base & Amplifications

**Objectif** : Calculer l'impact de base (formule) et l'amplification parfaite (réel/base) pour chaque cluster historique

**Impact de Base** : Formule `calculate_impact_d`
- Somme des impacts individuels des événements
- Correction avec facteur empirique (Random Forest)
- Ajustements selon importance et scores

**Module utilisé** : `core.formulas_validated.calculate_impact_d()`

**Impact Réel** : Mesure depuis prix M1
- Utilise `measure_impact_from_dukascopy` (M1)
- Détection du pic réel dans la fenêtre post-événement
- Direction UP ou DOWN selon le mouvement dominant

**Module utilisé** : `core.impact_measurement.measure_impact_from_dukascopy()`

**Amplification Parfaite** :
```
amplification_parfaite = impact_reel / impact_base
```

**Sortie** : DataFrame avec :
- `impact_base` : float (impact calculé par formule)
- `impact_reel` : float (impact réel mesuré)
- `amplification_parfaite` : float (ratio réel/base)

**Statut** : ⚠️ Simplifié (intégration complète à faire)

---

### Étape 7 : Analyser Relation Tendance → Amplification

**Objectif** : Analyser la corrélation entre les métriques de tendance et l'amplification pour prédire l'amplification du cluster cible

**Méthodes** :
1. **Corrélations** : R², durée, amplitude vs amplification
2. **Modèle linéaire** : Régression multivariée
3. **Random Forest par date** : Si >= 5 clusters identiques
4. **Random Forest global** : Fallback si pas assez de clusters

**Features pour Random Forest** :
- `trend_r2` : R² de la tendance
- `trend_duration_h` : Durée en heures
- `trend_amplitude_pips` : Amplitude en pips
- `impact_base_pips` : Impact de base
- `num_events` : Nombre d'événements
- `pattern_impact_pips` : Impact du pattern détecté (si disponible)
- `pattern_wave1_pips`, `pattern_wave2_pips` : Pips des vagues

**Modules à créer** :
- `core.amplification_random_forest.py` - Random Forest global
- `core.amplification_random_forest_per_date.py` - Random Forest par date

**Sortie** : Dict avec :
- `correlations` : Dict {metric: correlation}
- `model` : Modèle linéaire (si applicable)
- `rf_model_per_date` : Modèle Random Forest par date (si applicable)
- `rf_model_global` : Modèle Random Forest global (si applicable)
- `results_df` : DataFrame avec tous les résultats fusionnés

**Statut** : ⚠️ Simplifié (modèles ML à implémenter)

---

### Étape 8 : Appliquer au Cluster Cible

**Objectif** : Appliquer toutes les analyses au cluster cible pour prédire l'impact final

**Sous-étapes** :

#### 8.1 : Calcul de l'Impact de Base
- Utilise `calculate_impact_d` avec les événements du cluster cible
- Module : `core.formulas_validated.calculate_impact_d()`

#### 8.2 : Détection de Tendance
- Utilise `detect_trend_pre_event_robust` avec paramètres assouplis
- Timeframe par défaut : M30 (meilleure performance pour impact)
- Module : `core.trend_detection_pre_event_s107.detect_trend_by_inversion_s107()`

#### 8.3 : Prédiction d'Amplification
**Priorité** :
1. Random Forest par date (si >= 5 clusters identiques)
2. Random Forest global (fallback)
3. Modèle linéaire (fallback)
4. Moyenne des amplifications historiques (dernier fallback)

**Modules** :
- `core.amplification_random_forest_per_date.predict_amplification_with_per_date_rf()`
- `core.amplification_random_forest.predict_amplification_random_forest()`
- Modèle linéaire (à implémenter)
- Moyenne historique (simple)

#### 8.4 : Ajustements Support/Résistance
**Logique** :
- Détection de breakout (direction cluster ≠ direction tendance)
- Distance normalisée à la barrière directionnelle
- Ajustement selon proximité et type de breakout

**Ajustements** :
- Breakout + très proche (< 0.15 ATR) : +15%
- Breakout + proche (< 0.40 ATR) : +5%
- Pas de breakout + très proche (< 0.10 ATR) : -30%
- Pas de breakout + proche (< 0.20 ATR) : -10%
- Beaucoup de marge (> 1.40 ATR) : +15%

**Statut** : ⚠️ À implémenter

#### 8.5 : Ajustements Patterns Finnhub
**Méthode** :
- Recherche de patterns Finnhub dans fenêtre 24h
- Validation de direction (pattern vs prédiction)
- Ajustement de confiance selon patterns trouvés

**Multiplicateurs** :
- Patterns forts validant direction : +5% à +10%
- Patterns forts invalidant direction : -10% à -15%
- Pas de patterns : -5% (réduction de confiance)

**Module** : `core.finnhub_amplification_adjustment.py` (mentionné mais peut être désactivé)

**Statut** : ⚠️ Peut être désactivé pour l'instant

#### 8.6 : Détection de Pattern de Prix ⚠️ CRITIQUE
**Méthode** : Détection Double Wave ou Single Wave

**Paramètres** :
- `MIN_PHASE1_PIPS` : 20.0 pips
- `MIN_PHASE2_PIPS` : 14.0 pips
- `MIN_PULLBACK_RATIO` : 0.20 (20%)
- `MAX_PULLBACK_RATIO` : 0.80 (80%)
- `PHASE1_WINDOW_MINUTES` : 90 minutes
- `PULLBACK_WINDOW_MINUTES` : 45 minutes
- `PHASE2_WINDOW_MINUTES` : 180 minutes

**Algorithme** :
1. Charger prix M1 pour fenêtre [event_time - 120 min, event_time + 240 min]
2. Déterminer direction depuis fenêtre 5-60 min après événement
3. Détecter Wave 1 (pic dans fenêtre 90 min)
4. Détecter Pullback (dans fenêtre 45 min après Wave 1)
5. Détecter Wave 2 (pic dans fenêtre 180 min après pullback)
6. Valider critères (pips, ratios)
7. **⚠️ CRITIQUE** : Calculer pic absolu dans toute la fenêtre (`wave2_peak_pips_absolute`)

**Patterns détectés** :
- `DOUBLE_WAVE` : Wave 1 → Pullback → Wave 2
- `SINGLE_WAVE_FORT` : Impact >= 40 pips
- `SINGLE_WAVE_STANDARD` : Impact < 40 pips
- `NONE` : Aucun pattern détecté

**⚠️ IMPORTANT** : Utilisation du pic absolu
- `wave2_peak_pips_absolute` : Pic réel dans toute la fenêtre (capture Wave 3)
- Utilisé au lieu de `impact_pips` (basé sur Wave 2 détecté uniquement)

**Options** :
- Option A : Utiliser `detect_pattern_type()` du planificateur (intégrée)
- Option B : Créer `scripts/phase_a_robust_validation.py` avec `detect_double_wave_pattern()`

**Statut** : ⚠️ À compléter (ajouter pic absolu)

#### 8.7 : Stratégie Hybride Pattern/Formules
**Option C (révisée)** :

**Condition 1** : Écart < 10 pips
- → Garder formules (ignorer pattern)
- **Raison** : Protection des bons cas

**Condition 2** : Écart >= 10 pips
- → Utiliser pattern directement (100%)
- **Raison** : Pattern plus fiable pour écarts importants

**Pas de pondération hybride** : Dégradait les bons cas

**Calcul** :
```python
impact_formules = impact_base * amplification_predite * adjustment_factor
pattern_impact = wave2_peak_pips_absolute  # Pic absolu

ecart_absolu = abs(pattern_impact - impact_formules)

if ecart_absolu < 10 or pattern_impact == 0:
    prediction_finale = impact_formules  # Garder formules
else:
    prediction_finale = pattern_impact  # Utiliser pattern
```

**Statut** : ⚠️ À implémenter

#### 8.8 : Calcul du Target de Sortie
**Stratégie** :
- Sortie à 80% de l'impact prédit
- Limite maximale : 1.5x du prédit
- Pas de compensation (stratégie originale)

**Calcul** :
```python
exit_target = min(impact_predicted * 0.80, impact_predicted * 1.5)
```

**Module** : `core.exit_strategy.calculate_exit_target()`

**Sortie** : Dict final avec :
- `prediction_finale` : float (impact prédit final en pips)
- `exit_target` : float (target de sortie optimisé)
- `exit_strategy` : str ("80% du prédit")
- `pattern_type` : str
- `pattern_info` : Dict complet avec toutes les métriques
- `pattern_wave1_peak_time`, `pattern_wave2_peak_time` : datetime
- Toutes les métriques de tendance, amplification, etc.

**Statut** : ⚠️ À implémenter

---

## 🔄 Flux de Données

```
Événements DB
    ↓
[Étape 1] Charger Événements
    ↓
[Étape 2] Détecter Clusters
    ↓
[Étape 3] Définir Noyau Dur
    ↓
[Étape 4] Rechercher Clusters Identiques (historique)
    ↓
[Étape 5] Calculer Tendances (pour chaque cluster identique)
    ↓
[Étape 6] Calculer Impacts Base & Amplifications (pour chaque cluster identique)
    ↓
[Étape 7] Analyser Relation Tendance → Amplification (ML models)
    ↓
[Étape 8] Appliquer au Cluster Cible
    ├─ 8.1 Impact Base
    ├─ 8.2 Tendance
    ├─ 8.3 Amplification (RF)
    ├─ 8.4 Ajustements Support/Résistance
    ├─ 8.5 Ajustements Finnhub (optionnel)
    ├─ 8.6 Pattern de Prix (avec pic absolu) ⚠️
    ├─ 8.7 Stratégie Hybride Pattern/Formules
    └─ 8.8 Target de Sortie
    ↓
PRÉDICTION FINALE
```

---

## 📦 Structure de Sortie du Pipeline

```python
{
    'success': bool,
    'final_prediction': {
        'impact_base': float,
        'amplification_predite': float,
        'prediction_finale': float,  # Impact final prédit
        'exit_target': float,
        'exit_strategy': str,
        'pattern_type': str,  # 'DOUBLE_WAVE' | 'SINGLE_WAVE_FORT' | 'SINGLE_WAVE_STANDARD' | 'NONE'
        'pattern_info': {
            'pattern_type': str,
            'confidence': float,
            'direction': 'UP' | 'DOWN',
            'baseline_price': float,
            'wave1_pips': float,
            'wave1_peak_time': datetime,
            'pullback_pips': float,
            'pullback_time': datetime,
            'wave2_pips': float,
            'wave2_peak_time': datetime,
            'impact_pips': float,  # Basé sur Wave 2 détecté
            'wave2_peak_pips_absolute': float,  # ⚠️ CRITIQUE : Pic réel dans toute fenêtre
            'wave2_peak_time_absolute': datetime,
            'wave2_peak_price_absolute': float
        },
        'trend_exists': bool,
        'trend_r2': float,
        'trend_duration_h': float,
        'trend_amplitude_pips': float,
        'cluster_direction': 'UP' | 'DOWN',
        'baseline_price': float,
        'pattern_wave1_peak_time': datetime,
        'pattern_wave2_peak_time': datetime
    },
    'results': {
        'etape1_events': DataFrame,
        'etape2_clusters': List[Dict],
        'etape3_cluster_info': Dict,
        'etape4_identical_clusters': List[Dict],
        'etape5_trends': DataFrame,
        'etape6_impacts': DataFrame,
        'etape7_analysis': Dict,
        'price_window': DataFrame  # ⚠️ Pour graphique
    },
    'error': str  # Si success == False
}
```

---

## ⚠️ Points Critiques

### 1. Pic Absolu ⭐ CRITIQUE
**TOUJOURS** utiliser `wave2_peak_pips_absolute` au lieu de `impact_pips` pour l'impact final.

**Raison** : Capture Wave 3 et continuations, réduit MAE de 23.4 à 8.4 pips (64.3%)

### 2. Critères Tendance
Les critères sont adaptés selon timeframe. Ne pas utiliser les mêmes pour toutes.

### 3. Option C
Ne pas utiliser de pondération hybride. Protection des bons cas est prioritaire.

### 4. Pas de Corrections DOUBLE_WAVE
Les corrections dynamiques sont désactivées car elles dégradent globalement.

### 5. Filtre HIGH Impact
**TOUJOURS** utiliser `empirical_score > 40` pour filtrer les événements.

---

## 📝 Modules à Créer/Compléter

### Priorité 1 : Modules Critiques

1. **`src/core/amplification_prediction.py`**
   - `predict_impact_with_amplification()` - Prédiction amplification avec modèle régression
   - Utilisé dans le planificateur existant

2. **`src/core/exit_strategy.py`**
   - `calculate_exit_target()` - Calcul target de sortie (80% du prédit)

3. **Ajout pic absolu dans détection pattern**
   - Dans `detect_pattern_type()` du planificateur OU
   - Dans `scripts/phase_a_robust_validation.py` si créé

### Priorité 2 : Modules ML

4. **`src/core/amplification_random_forest.py`**
   - `predict_amplification_random_forest()` - Random Forest global

5. **`src/core/amplification_random_forest_per_date.py`**
   - `predict_amplification_with_per_date_rf()` - Random Forest par date

### Priorité 3 : Complétions

6. **Compléter PipelineExecutor**
   - Implémentations complètes des 8 étapes
   - Intégration des modules existants
   - Gestion d'erreurs et fallbacks

---

## ✅ Ce qui Est Déjà Fonctionnel

1. **Structure PipelineExecutor** ✅
   - Classe créée avec structure des 8 étapes
   - Gestion connexion DB
   - Logs verbose

2. **Étape 1** ✅
   - Utilise `load_high_impact_events()` existant

3. **Étape 2** ✅
   - Logique de détection clusters implémentée

4. **Modules Core Existants** ✅
   - `event_loader.py`
   - `formulas_validated.py`
   - `trend_detection_pre_event_s107.py`
   - `impact_measurement.py`

---

## 🎯 Questions pour Validation

1. **Détection Pattern** : Préférez-vous utiliser `detect_pattern_type()` intégrée dans le planificateur ou créer `phase_a_robust_validation.py` séparé ?

2. **Random Forest** : Avez-vous des modèles Random Forest pré-entraînés ou dois-je les créer de zéro ?

3. **Support/Résistance** : Les ajustements support/résistance sont-ils critiques ou peuvent-ils être simplifiés/désactivés pour l'instant ?

4. **Finnhub** : Les ajustements Finnhub doivent-ils être désactivés (comme dans le planificateur actuel) ?

5. **Pic Absolu** : Confirmez-vous que le pic absolu doit TOUJOURS être utilisé au lieu de `impact_pips` ?

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ⏳ En attente de validation




