# Architecture : Validation vs Prédiction Temps Réel

## 🎯 Distinction Fondamentale

### ❌ CE QU'ON NE FAIT PAS
- Prédire l'impact SANS actuals (c'est de la loterie)
- Utiliser des modèles de corrélation (R², amplification) pour prédire l'amplification en temps réel
- Essayer de deviner les actuals avant leur publication

### ✅ CE QU'ON FAIT

#### Phase 1 : VALIDATION/CALIBRATION (sur données historiques)
**Objectif** : Valider que les formules fonctionnent sur le passé

1. Prendre des cas historiques avec actuals connus
2. Calculer l'amplification idéale (impact_réel / impact_base)
3. Chercher des corrélations (R², scores, etc.) pour comprendre les patterns
4. Calibrer les formules pour qu'elles soient précises
5. **Résultat** : Formules validées et calibrées

**Les modèles de corrélation servent UNIQUEMENT à valider les formules, pas à prédire.**

#### Phase 2 : PRÉDICTION TEMPS RÉEL (avec actuals du jour)
**Objectif** : Prédire l'impact pour un événement EN COURS

**AVANT les actuals (ex: avant 14h30 le 11.09)** :
- Identifier le cluster attendu (ex: 10 US events + 1 DE)
- Prédire le PATTERN attendu (Double Wave, Single Wave, etc.)
- Basé sur l'historique : "Ce cluster a produit X% Double Wave"
- Afficher : "Attendu : Double Wave, Impact moyen historique : 55 pips"
- **Mais PAS de prédiction précise (pas d'actuals)**

**À 14h30 (quand les actuals sont publiés)** :
1. L'utilisateur renseigne les actuals dans l'interface
2. Calculer avec formules validées :
   - Surprises : `surprise_pct = abs((actual - estimate) / estimate) * 100`
   - Scores ajustés : `calculate_adjusted_empirical_score(empirical_score, surprise_pct)`
   - Amplification dynamique : `calculate_amplification_extended(surprise_max)`
   - Impact base : `calculate_impact_d(mean_adjusted_score, num_events, amplification)`
3. **Prédire amplification avec modèle 'APRÈS'** (plus précis avec actuals) :
   - Calculer `total_score`, `mean_adjusted_score` (avec actuals)
   - Utiliser modèle de régression multiple : `predict_amplification_with_actuals()`
   - R² = 0.68, MAE = 0.59 (plus précis que modèle 'AVANT')
4. **Ajuster impact** : `impact_adjusted = impact_base × amplification_predicted`
5. **Combiner avec Ensemble Methods** (optionnel) :
   - Calculer `impact_ensemble` avec Ensemble Methods
   - Combiner : `impact_final = 0.7 × impact_adjusted + 0.3 × impact_ensemble`
6. Détecter pattern réel : `scan_price_movements()` + `detect_pattern_type()`
7. Afficher prédiction PRÉCISE :
   - Impact : X pips
   - Direction : BUY/SELL
   - Entrée : dans Y minutes
   - Sortie : après Z minutes ou à W pips
   - Confiance : basée sur similarité avec historique

## 🔧 Workflow Planificateur V3 CLEAN

### MODE 'CALENDRIER' (avant l'événement)

**Fonctionnalités** :
1. Afficher les clusters futurs identifiés
2. Pour chaque cluster, afficher :
   - Pattern historique dominant (ex: 85% Double Wave)
   - Impact moyen historique (ex: 55 pips)
   - Occurrences (ex: 12 fois dans le passé)
   - Heure d'ancrage (ex: 14h30)
3. L'utilisateur sélectionne une date/cluster
4. Afficher : "Attendu : Double Wave, Impact moyen : 55 pips"
   - **Mais PAS de prédiction précise (pas d'actuals)**

**Données utilisées** :
- Cache des clusters historiques (`cache_clusters.csv`)
- Patterns historiques (`cache_cluster_patterns.csv`)
- Pas de calcul d'impact (pas d'actuals)

### MODE 'PRÉDICTION' (quand actuals disponibles)

**Fonctionnalités** :
1. L'utilisateur renseigne les actuals dans l'interface
2. Calculer avec formules validées (PAS de modèles de corrélation) :
   ```python
   # Pour chaque événement
   surprise_pct = abs((actual - estimate) / estimate) * 100
   adjusted_score = calculate_adjusted_empirical_score(empirical_score, surprise_pct)
   
   # Pour le cluster
   surprise_max = max(surprises_pct)
   amplification = calculate_amplification_extended(surprise_max)
   mean_adjusted_score = mean(adjusted_scores)
   
   # Impact final
   impact_base = calculate_impact_d(
       empirical_score=mean_adjusted_score,
       num_events=len(events),
       amplification=amplification,
       correction_factor=0.758
   )
   ```
3. Détecter pattern réel : `scan_price_movements()` + `detect_pattern_type()`
4. Afficher prédiction PRÉCISE :
   - Impact : X pips
   - Direction : BUY/SELL
   - Entrée : dans Y minutes (latence)
   - Sortie : après Z minutes (TTR) ou à W pips
   - Confiance : basée sur similarité avec historique

**Données utilisées** :
- Actuals renseignés par l'utilisateur
- Formules validées (Impact D, Adjusted Score, Amplification Extended)
- Prix en temps réel (pour détection pattern)

## 📊 Formules Validées (à utiliser directement)

### 1. Adjusted Empirical Score
```python
from core.formulas_validated import calculate_adjusted_empirical_score

adjusted_score = calculate_adjusted_empirical_score(
    base_empirical_score=empirical_score,
    surprise_pct=surprise_pct
)
```

### 2. Amplification Dynamique
```python
from core.formulas_validated import calculate_amplification_extended

amplification = calculate_amplification_extended(surprise_max)
```

### 3. Impact D
```python
from core.formulas_validated import calculate_impact_d

impact_base = calculate_impact_d(
    empirical_score=mean_adjusted_score,
    num_events=len(events),
    amplification=amplification,
    correction_factor=0.758
)
```

### 4. Pattern Detection
```python
from core.pattern_detection import scan_price_movements, detect_pattern_type

movements = scan_price_movements(df_prices, min_pips=35.0)
pattern_info = detect_pattern_type(movements, df_events, min_pips=35.0)
```

## ✅ Ce qu'on UTILISE pour la prédiction (avec actuals)

- ✅ **Modèle de régression multiple 'APRÈS'** pour prédire l'amplification
  - R² = 0.68, MAE = 0.59 (plus précis que modèle 'AVANT')
  - Utilisé quand on a les actuals (scores ajustés disponibles)
  - Formule : `amp = 9.02 + 0.0084×total_score - 0.141×mean_adjusted_score - 0.416×num_events - 0.0148×mean_empirical_score`
- ✅ **Impact D** comme base de calcul
- ✅ **Amplification prédite** pour ajuster l'Impact D
- ✅ **Ensemble Methods** comme méthode principale
- ✅ **Combinaison** : Impact ajusté + Ensemble Methods (moyenne pondérée)

## 🚫 Ce qu'on N'UTILISE PAS pour la prédiction

- ❌ Prédiction d'impact SANS actuals (c'est de la loterie)
- ❌ Modèle 'AVANT' pour prédiction précise (utilisé uniquement pour pattern attendu)

## ✅ Ce qu'on UTILISE pour la prédiction

- ✅ Formules validées directement (Impact D, Adjusted Score, Amplification Extended)
- ✅ Actuals renseignés par l'utilisateur
- ✅ Surprises calculées (actual - estimate)
- ✅ Détection de pattern en temps réel
- ✅ Historique pour confiance (similarité avec clusters passés)

## 📝 Résumé

**Validation** : Les modèles de corrélation servent à valider que les formules fonctionnent sur l'historique. Une fois validées, on ne les utilise plus.

**Prédiction** : On utilise directement les formules validées avec les actuals du jour. Pas de modèles de corrélation, pas de prédiction sans actuals.

