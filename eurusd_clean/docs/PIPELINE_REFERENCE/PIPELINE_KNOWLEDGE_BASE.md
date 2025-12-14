# Base de Connaissances du Pipeline - Point de Référence

> **Document de référence unique** pour comprendre, maintenir et développer le pipeline de prédiction d'impact.

**Date de création** : 2025-01-XX  
**Version Pipeline** : Final (avec pic absolu)  
**Statut** : ✅ Validé et documenté

---

## 🎯 Objectif du Pipeline

Prédire l'impact en pips des événements économiques sur EUR/USD avec une précision maximale pour le trading, en combinant :
- Analyse d'événements économiques
- Détection de tendances pré-événement
- Machine Learning (Random Forest)
- Détection de patterns de prix
- Ajustements avec données externes (Finnhub)

---

## 🏗️ Architecture en 8 Étapes

### Vue d'Ensemble
```
1. Charger Événements → 2. Détecter Clusters → 3. Définir Noyau Dur
    ↓
4. Rechercher Clusters Identiques → 5. Calculer Tendances
    ↓
6. Calculer Impacts Base & Amplifications → 7. Analyser Relations
    ↓
8. Appliquer au Cluster Cible + Pattern + Ajustements
    ↓
PRÉDICTION FINALE
```

### Détails par Étape

#### Étape 1 : Charger Événements
- **Source** : Table `economic_events` (Finnhub)
- **Filtres** : Date, pays (US, Zone Euro)
- **Sortie** : DataFrame avec événements et scores empiriques

#### Étape 2 : Détecter Clusters
- **Méthode** : Fenêtre glissante de 30 minutes
- **Groupement** : Par heure d'ancrage
- **Sortie** : Liste de clusters avec anchor_time

#### Étape 3 : Définir Noyau Dur
- **Méthode** : Analyse de fréquence sur 5 ans
- **Seuil** : Support >= 0.8 (80%)
- **Support** : Noyaux durs pré-définis (CPI, NFP)
- **Sortie** : Core events avec scores de support

#### Étape 4 : Rechercher Clusters Identiques
- **Méthode** : Similarité Jaccard sur noyaux durs
- **Seuil** : Jaccard >= 0.60
- **Fenêtre** : ±10 minutes autour de l'heure d'événement
- **Sortie** : Clusters historiques avec même noyau dur

#### Étape 5 : Calculer Tendances
- **Méthode** : Validated Inversion (multi-timeframe)
- **Timeframes** : M1, M5, M15, M30, H1
- **Critères** : R² >= 0.15, amplitude >= 15 pips, durée adaptative
- **Sortie** : Métriques de tendance pour chaque cluster historique

#### Étape 6 : Calculer Impacts Base & Amplifications
- **Impact Base** : Formule `calculate_impact_d` avec correction RF
- **Impact Réel** : Mesure depuis prix M1 (pic réel)
- **Amplification** : Ratio réel/base
- **Sortie** : DataFrame avec impacts et amplifications parfaites

#### Étape 7 : Analyser Relations
- **Méthodes** : Corrélations, modèle linéaire, Random Forest
- **Features** : R², durée, amplitude, impact_base, num_events, pattern
- **Sortie** : Modèles et corrélations pour prédiction

#### Étape 8 : Appliquer au Cluster Cible
- **Sous-étapes** :
  1. Calcul impact de base
  2. Détection tendance
  3. Prédiction amplification (RF par date → RF global → linéaire)
  4. Ajustements support/résistance
  5. Ajustements patterns Finnhub
  6. Détection pattern de prix
  7. Stratégie hybride pattern/formules
  8. Calcul target de sortie
- **Sortie** : Prédiction finale complète

---

## 🔑 Concepts Clés

### 1. Noyau Dur (Core Events)
Événements qui apparaissent fréquemment ensemble dans l'historique. Utilisé pour trouver des clusters identiques.

**Exemple** : CPI + Core CPI + CPI YoY (noyau dur CPI)

### 2. Clusters Identiques
Clusters historiques avec le même noyau dur (similarité Jaccard >= 0.60). Leurs impacts réels servent à prédire l'amplification.

### 3. Amplification
Ratio entre impact réel et impact de base. Indique si le mouvement réel est plus fort ou plus faible que prévu par la formule.

```
amplification = impact_reel / impact_base
```

### 4. Pic Absolu
Pic réel dans toute la fenêtre de détection, pas seulement Wave 2 détecté. Capture Wave 3 et continuations.

**⚠️ CRITIQUE** : Toujours utiliser `wave2_peak_pips_absolute` au lieu de `impact_pips`.

### 5. Pattern Double Wave
Pattern avec 2 vagues : Wave 1 → Pullback → Wave 2. Peut avoir une Wave 3 non détectée, d'où l'importance du pic absolu.

### 6. Tendance Pré-Événement
Tendance détectée avant l'événement (12h-14 jours avant). Utilisée pour prédire l'amplification.

---

## 📐 Formules Principales

### Impact de Base
```
impact_base = Σ(score_empirique_i × importance_factor_i × surprise_factor_i)
impact_final = impact_base × correction_factor_rf
```

### Amplification Parfaite
```
amplification_parfaite = impact_reel / impact_base
```

### Prédiction Finale
```
impact_formules = impact_base × amplification_predite
impact_pattern = wave2_peak_pips_absolute  # Pic absolu
prediction_finale = pattern si écart >= 10 pips, sinon formules
```

### Target de Sortie
```
exit_target = min(impact_predicted × 0.80, impact_predicted × 1.5)
```

---

## 🎛️ Paramètres Critiques

### Clusters
- `window_minutes` : 30 (fenêtre de groupement)
- `support_threshold` : 0.8 (80% de fréquence pour noyau dur)
- `jaccard_threshold` : 0.60 (similarité pour clusters identiques)

### Tendance
- `min_hours_before_event` : 12 (assoupli de 24)
- `min_duration_hours` : 6.0 (adapté : 6h pour M30/H1, 8h pour M1/M5/M15)
- `lookback_days` : 14
- `min_r2` : 0.15
- `min_amplitude_pips` : 15.0

### Pattern
- `MIN_PHASE1_PIPS` : 20.0
- `MIN_PHASE2_PIPS` : 14.0
- `MIN_PULLBACK_RATIO` : 0.20
- `MAX_PULLBACK_RATIO` : 0.80
- `PHASE1_WINDOW_MINUTES` : 90
- `PULLBACK_WINDOW_MINUTES` : 45
- `PHASE2_WINDOW_MINUTES` : 180

### Exit Strategy
- `EXIT_PERCENTAGE` : 0.80 (80% du prédit)
- `MAX_IMPACT_MULTIPLIER` : 1.5 (limite maximale)

---

## 🧠 Logique de Décision

### Pattern vs Formules (Option C)
```
SI écart_absolu < 10 pips :
    → Utiliser formules (protection bons cas)
SINON :
    → Utiliser pattern directement (100%)
```

### Ajustements Support/Résistance
```
SI breakout ET distance_norm < 0.15 :
    → +15% (cassure violente)
SINON SI breakout ET distance_norm < 0.40 :
    → +5% (cassure modérée)
SINON SI pas breakout ET distance_norm < 0.10 :
    → -30% (risque rebond)
SINON SI pas breakout ET distance_norm < 0.20 :
    → -10% (proche barrière)
SINON SI distance_norm > 1.40 :
    → +15% (beaucoup de marge)
SINON :
    → Neutre (1.00)
```

### Prédiction Amplification (Priorité)
```
1. Random Forest par date (si >= 5 clusters identiques)
2. Random Forest global (fallback)
3. Modèle linéaire (fallback)
4. Moyenne historique (dernier fallback)
```

---

## 🔬 Méthodes de Détection

### Détection de Tendance (Validated Inversion)
1. Charger prix sur 14 jours avant événement
2. Détecter extrema locaux avec prominence
3. Filtrer extrema à >= 12h avant événement
4. Prendre dernier extremum majeur (inversion)
5. Régression linéaire depuis inversion
6. Valider : R² >= 0.15, t-stat >= 2.0, amplitude >= 15 pips

### Détection Pattern Double Wave
1. Déterminer direction (UP/DOWN)
2. Détecter Wave 1 (pic dans 90 min)
3. Détecter Pullback (dans 45 min après Wave 1)
4. Détecter Wave 2 (pic dans 180 min après pullback)
5. Valider critères (pips, ratios)
6. **Calculer pic absolu dans toute fenêtre** ⭐

### Similarité Jaccard
```
J(A, B) = |A ∩ B| / |A ∪ B|
```
- A, B : Noyaux durs de deux clusters
- Seuil : 0.60 (permet variations mineures)

---

## 🎯 Solutions Implémentées

### 1. Pic Absolu ⭐
**Problème** : Pattern s'arrêtait à Wave 2 alors que mouvement continuait.

**Solution** : Utiliser `wave2_peak_pips_absolute` au lieu de `impact_pips`.

**Résultat** : MAE réduit de 23.4 à 8.4 pips (64.3%).

**Fichier** : `docs/VALIDATION/SOLUTION_PATTERN_INCOMPLET.md`

### 2. Critères Tendance Assouplis ⭐
**Problème** : Critères trop stricts empêchaient détection.

**Solution** : 12h avant (au lieu de 24h), durée adaptative (6h pour M30/H1).

**Résultat** : 2 tendances au lieu d'1 pour certains cas.

**Fichier** : `docs/VALIDATION/ANALYSE_ERREUR_23_06.md`

### 3. Seuil Jaccard 0.60 ⭐
**Problème** : Seuil 0.8 trop strict.

**Solution** : Réduire à 0.60.

**Résultat** : Plus de clusters identiques trouvés.

---

## 📊 Performance Actuelle

### Métriques Globales
- **MAE** : 8.4 pips
- **Taux acceptable** : 63.2% (erreur < 20%)
- **Taux excellent** : 55.3% (erreur < 10%)
- **Taux médiocre** : 21.1% (erreur 20-40%)
- **Taux dégradé** : 15.8% (erreur > 40%)

### Tests sur 15 Dates
- **Cas améliorés** : 7/15 (46.7%)
- **Cas dégradés** : 0/15 (0%)
- **Amélioration moyenne** : 32.3 pips par cas amélioré

### Cas de Référence
- **2025-09-11** : 63.8 pips réel, SINGLE_WAVE
- **2025-08-01** : 188.3 pips réel, SINGLE_WAVE_FORT
- **2025-06-23** : 89.6 pips réel, DOUBLE_WAVE (résolu avec pic absolu)
- **2025-08-12** : 92.1 pips réel, DOUBLE_WAVE

---

## 🚫 Décisions Abandonnées

### 1. Volume comme Feature
**Raison** : Corrélation très faible (-0.114), pas de discrimination.

### 2. Pondération Hybride Pattern/Formules
**Raison** : Dégradait les bons cas où formules étaient déjà précises.

### 3. Corrections Dynamiques DOUBLE_WAVE
**Raison** : Dégradation globale malgré améliorations locales.

### 4. Random Forest Per Date avec Corrélations
**Raison** : Approche trop complexe, pas d'amélioration significative.

---

## 🎓 Leçons Apprises

### 1. Toujours Utiliser Pic Absolu
Le pic absolu capture toujours le mouvement complet, même avec Wave 3.

### 2. Protéger les Bons Cas
Ne pas dégrader les cas où le système fonctionne déjà bien.

### 3. Tester Avant Implémentation
Valider systématiquement les modifications avant production.

### 4. Simplicité > Complexité
Solutions simples qui fonctionnent > solutions complexes qui dégradent.

### 5. Multi-Timeframe
Utiliser différentes timeframes pour différents objectifs (M30 pour impact, M1 pour timings).

---

## 📁 Structure des Fichiers

### Pipeline Principal
```
scripts/run_pipeline_complete.py
  ├── etape1_charger_evenements()
  ├── etape2_detecter_clusters()
  ├── etape3_definir_noyau_dur()
  ├── etape4_rechercher_clusters_identiques()
  ├── etape5_calculer_tendances_impacts()
  ├── etape6_calculer_impacts_base_amplifications()
  ├── etape7_analyser_relation_tendance_amplification()
  └── etape8_appliquer_cluster_cible()
```

### Détection
```
scripts/phase_a_robust_validation.py
  ├── detect_double_wave_pattern()
  ├── detect_double_wave_trend_based()
  └── find_local_extrema()

src/core/trend_detection_pre_event.py
  ├── detect_trend_pre_event_robust()
  └── detect_validated_inversion_trend()
```

### Calculs
```
scripts/validate_coefficients_empirical.py
  └── calculate_impact_d()

src/core/amplification_random_forest.py
  └── predict_amplification_random_forest()

src/core/amplification_random_forest_per_date.py
  ├── train_random_forest_per_date()
  └── predict_amplification_with_per_date_rf()
```

### Ajustements
```
src/core/finnhub_amplification_adjustment.py
  └── adjust_amplification_with_finnhub_patterns()

src/core/smart_cap_amplification.py
  └── apply_smart_cap()

src/core/exit_strategy.py
  └── calculate_exit_target()
```

---

## 🔍 Points d'Attention

### ⚠️ CRITIQUE : Pic Absolu
**TOUJOURS** utiliser `wave2_peak_pips_absolute` au lieu de `impact_pips` pour l'impact final.

### ⚠️ CRITIQUE : Critères Tendance
Les critères sont adaptés selon timeframe. Ne pas utiliser les mêmes pour toutes.

### ⚠️ IMPORTANT : Option C
Ne pas utiliser de pondération hybride. Protection des bons cas est prioritaire.

### ⚠️ IMPORTANT : Pas de Corrections DOUBLE_WAVE
Les corrections dynamiques sont désactivées car elles dégradent globalement.

---

## 🧪 Validation

### Tests Essentiels
1. **Test complet** : `scripts/test_pipeline_validation_finale.py`
2. **Test pic absolu** : `scripts/test_pic_absolu_multiples_dates.py`
3. **Test erreur** : `scripts/analyser_erreur_23_06.py`

### Vérifications
- Impact prédit > 0
- Exit target <= 1.5x prédit
- Pic absolu >= Wave 2 détecté
- MAE < 10 pips
- Taux acceptable > 60%

---

## 📚 Documentation Complète

Voir **[INDEX_DOCUMENTATION_COMPLETE.md](INDEX_DOCUMENTATION_COMPLETE.md)** pour la liste complète de toute la documentation.

### Documents Principaux
- `PIPELINE_REFERENCE_COMPLETE.md` : Référence complète
- `PIPELINE_ARCHITECTURE_DETAILED.md` : Architecture détaillée
- `PIPELINE_FORMULAS_REFERENCE.md` : Formules
- `PIPELINE_DECISIONS_LOG.md` : Décisions
- `PIPELINE_TESTING_GUIDE.md` : Tests

---

## 🚀 Prochaines Étapes

1. ✅ **Documentation complète** : Terminé
2. ⏳ **Réécriture planificateur UI** : À faire
3. ⏳ **Tests production** : À faire
4. ⏳ **Optimisations** : À faire

---

**Ce document est le point de référence unique pour le développement futur du pipeline.**

