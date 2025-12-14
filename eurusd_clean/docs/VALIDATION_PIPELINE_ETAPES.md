# Validation du Pipeline - Étape par Étape

**Date** : 2025-01-XX  
**Référence** : `docs/PIPELINE_REFERENCE/PIPELINE_KNOWLEDGE_BASE.md`  
**Objectif** : Valider chaque étape du pipeline selon la documentation, puis recréer le planificateur

---

## 📋 Plan de Validation

### Étape 1 : Charger Événements

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 39-42

**Spécifications** :
- ✅ Source : Table `events` (pas `economic_events`)
- ✅ Filtres : Date, pays (US, Zone Euro)
- ✅ Filtre CRITIQUE : `empirical_score > 40` (HIGH impact uniquement)
- ✅ Sortie : DataFrame avec événements et scores empiriques

**Validation** :
- [ ] Vérifier que `load_high_impact_events()` utilise bien `empirical_score > 40`
- [ ] Vérifier que la table utilisée est bien `events` (pas `economic_events`)
- [ ] Vérifier que les pays US, EU, DE sont bien inclus
- [ ] Vérifier la structure de sortie (colonnes attendues)

**Statut actuel** : ✅ Module existe (`core.event_loader.load_high_impact_events()`)

---

### Étape 2 : Détecter Clusters

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 44-47

**Spécifications** :
- ✅ Méthode : Fenêtre glissante de 30 minutes
- ✅ Groupement : Par heure d'ancrage
- ✅ Sortie : Liste de clusters avec anchor_time

**Validation** :
- [ ] Vérifier que la fenêtre est bien de 30 minutes (paramétrable)
- [ ] Vérifier que l'anchor_time est bien l'heure du premier événement
- [ ] Vérifier que les événements sont bien groupés dans la fenêtre
- [ ] Vérifier la structure de sortie (events, anchor_time, n_events)

**Statut actuel** : ✅ Implémenté dans PipelineExecutor (simplifié)

---

### Étape 3 : Définir Noyau Dur

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 49-53

**Spécifications** :
- ✅ Méthode : Analyse de fréquence sur 5 ans
- ✅ Seuil : Support >= 0.8 (80%)
- ✅ Support : Noyaux durs pré-définis (CPI, NFP)
- ✅ Sortie : Core events avec scores de support

**Validation** :
- [ ] Vérifier que l'analyse historique couvre bien 5 ans
- [ ] Vérifier que le seuil de support est bien 0.8
- [ ] Vérifier que les noyaux durs pré-définis sont utilisés
- [ ] Vérifier la structure de sortie (core_events, n_core_events, support_scores)

**Statut actuel** : ⚠️ Simplifié (analyse historique complète à implémenter)

**Fichiers de référence** :
- `docs/VALIDATION/CORE_EVENTS_CPI.txt`
- `docs/VALIDATION/CORE_EVENTS_NFP.txt`

---

### Étape 4 : Rechercher Clusters Identiques

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 55-59

**Spécifications** :
- ✅ Méthode : Similarité Jaccard sur noyaux durs
- ✅ Seuil : Jaccard >= 0.60
- ✅ Fenêtre : ±10 minutes autour de l'heure d'événement
- ✅ Sortie : Clusters historiques avec même noyau dur

**Validation** :
- [ ] Vérifier que le calcul Jaccard est correct : `J(A, B) = |A ∩ B| / |A ∪ B|`
- [ ] Vérifier que le seuil est bien 0.60 (pas 0.8)
- [ ] Vérifier que la fenêtre heure est bien ±10 minutes
- [ ] Vérifier que la recherche couvre bien 5 ans d'historique
- [ ] Vérifier la structure de sortie (date, jaccard_score, core_events)

**Statut actuel** : ⚠️ Simplifié (recherche historique complète à implémenter)

---

### Étape 5 : Calculer Tendances

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 61-65, 216-222

**Spécifications** :
- ✅ Méthode : Validated Inversion (multi-timeframe)
- ✅ Timeframes : M1, M5, M15, M30, H1
- ✅ Critères :
  - `min_hours_before_event` : 12 heures (assoupli de 24)
  - `min_duration_hours` : 6.0 heures (adapté selon timeframe)
    - M30, H1 : 6 heures minimum
    - M1, M5, M15 : 8 heures minimum
  - `lookback_days` : 14 jours
  - `min_r2` : 0.15
  - `min_amplitude_pips` : 15.0
- ✅ Sortie : Métriques de tendance pour chaque cluster historique

**Algorithme Validated Inversion** :
1. Charger prix sur 14 jours avant événement
2. Détecter extrema locaux avec prominence
3. Filtrer extrema à >= 12h avant événement
4. Prendre dernier extremum majeur (inversion)
5. Régression linéaire depuis inversion
6. Valider : R² >= 0.15, t-stat >= 2.0, amplitude >= 15 pips

**Validation** :
- [ ] Vérifier que la méthode Validated Inversion est utilisée
- [ ] Vérifier que les critères sont bien assouplis (12h au lieu de 24h)
- [ ] Vérifier que la durée est adaptée selon timeframe
- [ ] Vérifier que tous les timeframes sont testés (M1, M5, M15, M30, H1)
- [ ] Vérifier la structure de sortie (trend_exists, r2, amplitude_pips, duration_minutes, direction, timeframe_used)

**Statut actuel** : ⚠️ Module existe (`core.trend_detection_pre_event_s107.detect_trend_by_inversion_s107()`) mais intégration incomplète

---

### Étape 6 : Calculer Impacts Base & Amplifications

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 67-71, 130-133

**Spécifications** :
- ✅ Impact Base : Formule `calculate_impact_d` avec correction RF
- ✅ Impact Réel : Mesure depuis prix M1 (pic réel)
- ✅ Amplification : Ratio réel/base
- ✅ Sortie : DataFrame avec impacts et amplifications parfaites

**Formules** :
```
impact_base = Σ(score_empirique_i × importance_factor_i × surprise_factor_i)
impact_final = impact_base × correction_factor_rf
amplification_parfaite = impact_reel / impact_base
```

**Validation** :
- [ ] Vérifier que `calculate_impact_d()` est utilisé pour impact base
- [ ] Vérifier que `measure_impact_from_dukascopy()` est utilisé pour impact réel
- [ ] Vérifier que l'amplification parfaite est bien calculée (réel/base)
- [ ] Vérifier la structure de sortie (impact_base, impact_reel, amplification_parfaite)

**Statut actuel** : ⚠️ Modules existent mais intégration incomplète

---

### Étape 7 : Analyser Relation Tendance → Amplification

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 73-76, 204-210

**Spécifications** :
- ✅ Méthodes : Corrélations, modèle linéaire, Random Forest
- ✅ Features : R², durée, amplitude, impact_base, num_events, pattern
- ✅ Priorité :
  1. Random Forest par date (si >= 5 clusters identiques)
  2. Random Forest global (fallback)
  3. Modèle linéaire (fallback)
  4. Moyenne historique (dernier fallback)
- ✅ Sortie : Modèles et corrélations pour prédiction

**Validation** :
- [ ] Vérifier que les corrélations sont calculées (R², durée, amplitude vs amplification)
- [ ] Vérifier que le modèle linéaire est implémenté
- [ ] Vérifier que Random Forest par date est utilisé si >= 5 clusters
- [ ] Vérifier que Random Forest global est utilisé en fallback
- [ ] Vérifier que la moyenne historique est utilisée en dernier fallback
- [ ] Vérifier la structure de sortie (correlations, model, rf_model_per_date, rf_model_global, results_df)

**Statut actuel** : ⚠️ Simplifié (modèles ML à implémenter)

**Modules à créer** :
- `src/core/amplification_random_forest.py`
- `src/core/amplification_random_forest_per_date.py`

---

### Étape 8 : Appliquer au Cluster Cible

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 78-88

#### 8.1 : Calcul de l'Impact de Base

**Validation** :
- [ ] Vérifier que `calculate_impact_d()` est utilisé avec événements du cluster cible
- [ ] Vérifier que les scores empiriques sont bien ajustés selon surprise

#### 8.2 : Détection de Tendance

**Validation** :
- [ ] Vérifier que `detect_trend_pre_event_robust()` est utilisé avec paramètres assouplis
- [ ] Vérifier que la timeframe par défaut est M30
- [ ] Vérifier que les critères sont bien assouplis (12h avant, durée adaptative)

#### 8.3 : Prédiction d'Amplification

**Validation** :
- [ ] Vérifier la priorité : RF par date → RF global → linéaire → moyenne historique
- [ ] Vérifier que RF par date est utilisé si >= 5 clusters identiques
- [ ] Vérifier que les fallbacks fonctionnent correctement

#### 8.4 : Ajustements Support/Résistance

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 188-202

**Validation** :
- [ ] Vérifier la détection de breakout (direction cluster ≠ direction tendance)
- [ ] Vérifier le calcul de distance normalisée (distance_norm = |distance| / ATR)
- [ ] Vérifier tous les ajustements :
  - Breakout + très proche (< 0.15 ATR) : +15%
  - Breakout + proche (< 0.40 ATR) : +5%
  - Pas de breakout + très proche (< 0.10 ATR) : -30%
  - Pas de breakout + proche (< 0.20 ATR) : -10%
  - Beaucoup de marge (> 1.40 ATR) : +15%

**Statut actuel** : ⚠️ À implémenter

#### 8.5 : Ajustements Patterns Finnhub

**Validation** :
- [ ] Vérifier la recherche de patterns Finnhub dans fenêtre 24h
- [ ] Vérifier la validation de direction (pattern vs prédiction)
- [ ] Vérifier les multiplicateurs :
  - Patterns forts validant direction : +5% à +10%
  - Patterns forts invalidant direction : -10% à -15%
  - Pas de patterns : -5%

**Statut actuel** : ⚠️ Peut être désactivé pour l'instant

#### 8.6 : Détection de Pattern de Prix ⚠️ CRITIQUE

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 224-230, 135-140

**Spécifications** :
- ✅ Paramètres :
  - `MIN_PHASE1_PIPS` : 20.0
  - `MIN_PHASE2_PIPS` : 14.0
  - `MIN_PULLBACK_RATIO` : 0.20
  - `MAX_PULLBACK_RATIO` : 0.80
  - `PHASE1_WINDOW_MINUTES` : 90
  - `PULLBACK_WINDOW_MINUTES` : 45
  - `PHASE2_WINDOW_MINUTES` : 180
- ✅ Algorithme :
  1. Déterminer direction (UP/DOWN)
  2. Détecter Wave 1 (pic dans 90 min)
  3. Détecter Pullback (dans 45 min après Wave 1)
  4. Détecter Wave 2 (pic dans 180 min après pullback)
  5. Valider critères (pips, ratios)
  6. **⚠️ CRITIQUE** : Calculer pic absolu dans toute fenêtre

**Validation** :
- [ ] Vérifier que tous les paramètres sont corrects
- [ ] Vérifier que l'algorithme de détection est correct
- [ ] ⚠️ CRITIQUE : Vérifier que le pic absolu est calculé (`wave2_peak_pips_absolute`)
- [ ] Vérifier que le pic absolu est utilisé au lieu de `impact_pips`
- [ ] Vérifier la structure de sortie (pattern_type, pattern_info avec pic absolu)

**Statut actuel** : ⚠️ Fonction `detect_pattern_type()` existe dans planificateur mais manque pic absolu

#### 8.7 : Stratégie Hybride Pattern/Formules

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 180-186, 135-140

**Spécifications** :
- ✅ Option C (révisée) :
  - Écart < 10 pips : Garder formules (protection bons cas)
  - Écart >= 10 pips : Utiliser pattern directement (100%)
- ✅ Pas de pondération hybride

**Validation** :
- [ ] Vérifier que l'écart absolu est bien calculé : `|pattern_impact - impact_formules|`
- [ ] Vérifier que si écart < 10 pips, on garde formules
- [ ] Vérifier que si écart >= 10 pips, on utilise pattern directement
- [ ] Vérifier qu'il n'y a PAS de pondération hybride

**Statut actuel** : ⚠️ À implémenter

#### 8.8 : Calcul du Target de Sortie

**Référence** : PIPELINE_KNOWLEDGE_BASE.md ligne 142-145, 172-174

**Spécifications** :
- ✅ Stratégie : Sortie à 80% de l'impact prédit
- ✅ Limite maximale : 1.5x du prédit
- ✅ Pas de compensation

**Formule** :
```
exit_target = min(impact_predicted × 0.80, impact_predicted × 1.5)
```

**Validation** :
- [ ] Vérifier que le calcul est correct : `min(prediction × 0.80, prediction × 1.5)`
- [ ] Vérifier que la limite maximale est bien 1.5x
- [ ] Vérifier qu'il n'y a pas de compensation

**Statut actuel** : ⚠️ À implémenter

---

## 📝 Checklist Complète

### Modules à Vérifier/Créer

- [ ] `core.event_loader.load_high_impact_events()` - ✅ Existe
- [ ] `core.formulas_validated.calculate_impact_d()` - ✅ Existe
- [ ] `core.trend_detection_pre_event_s107.detect_trend_by_inversion_s107()` - ✅ Existe
- [ ] `core.impact_measurement.measure_impact_from_dukascopy()` - ✅ Existe
- [ ] `scripts/phase_a_robust_validation.py` - ⚠️ À créer OU utiliser `detect_pattern_type()` du planificateur
- [ ] `src/core/amplification_random_forest.py` - ⚠️ À créer
- [ ] `src/core/amplification_random_forest_per_date.py` - ⚠️ À créer
- [ ] `src/core/exit_strategy.py` - ⚠️ À créer

### Points Critiques à Vérifier

- [ ] ⚠️ CRITIQUE : Pic absolu utilisé (`wave2_peak_pips_absolute`)
- [ ] ⚠️ CRITIQUE : Filtre HIGH impact (`empirical_score > 40`)
- [ ] ⚠️ CRITIQUE : Critères tendance assouplis (12h avant, durée adaptative)
- [ ] ⚠️ CRITIQUE : Seuil Jaccard 0.60 (pas 0.8)
- [ ] ⚠️ CRITIQUE : Option C sans pondération hybride

---

## 🎯 Prochaines Étapes

1. **Valider chaque étape** selon cette checklist
2. **Créer/Compléter les modules manquants**
3. **Intégrer dans PipelineExecutor**
4. **Recréer le planificateur Streamlit**

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ⏳ En cours de validation




