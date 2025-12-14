# Comparaison Version Actuelle vs Version d'Il y a 2 Jours

**Date** : 3 décembre 2025  
**Objectif** : Comparer la version actuelle avec les évolutions récentes et proposer une version restaurée

---

## 📊 VERSION ACTUELLE (3 décembre 2025, 16:17)

### Modifications Récentes Identifiées

#### 1. ✅ ÉTAPE 3 : Seuil Adaptatif Noyau Dur
**Actuel** (lignes 404-500) :
- Support calculé sur **TOUS** les clusters pour événements génériques
- Seuil adaptatif : `support >= 60%` OU `(support >= 40% ET importance <= 2)` OU `(support >= 20% ET importance <= 3 ET GENERIC)`
- Jobless Claims inclus même avec support faible (19-21%)

**Avant** (hypothèse) :
- Support calculé uniquement dans clusters du même type (CPI/NFP)
- Seuil fixe : `support >= 60%` (ou 80% selon référence)
- Jobless Claims exclus si support < seuil

---

#### 2. ✅ ÉTAPE 8.1 : Méthode Session 88
**Actuel** (lignes 1185-1234) :
- Score moyen des événements (sans ajustement individuel)
- Surprise maximale du cluster
- Score ajusté moyen avec surprise MAX
- `calculate_impact_d` avec score ajusté moyen

**Avant** (hypothèse) :
- Calcul individuel pour chaque événement
- Somme des impacts individuels
- Correction vectorielle 0.758 appliquée après

---

#### 3. ✅ ÉTAPE 8.3 : Stratégie Hybride Conditionnelle
**Actuel** (lignes 2067-2101) :
- **Single Wave** : Stratégie hybride activée (pattern si écart >= 10 pips)
- **Double Wave** : Utiliser pattern si formules suspectes (amplification < 0.5x OU impact < 30% pattern)
- **Autres** : Stratégie hybride standard

**Avant** (hypothèse) :
- Stratégie identique pour tous les patterns
- Écart < 10 pips → Formules
- Écart >= 10 pips → Pattern

---

#### 4. ✅ ÉTAPE 8.6 : Timings Parfaits Session 64
**Actuel** (lignes 1776-1916) :
- `predict_double_wave_timeline_s64()` implémenté
- Timings fixes : T+5, T+11, T+15, T+40
- Adaptation pour clusters multiples

**Avant** (hypothèse) :
- Timings détectés depuis prix réels
- Pas de prédiction de timings fixes

---

#### 5. ✅ ÉTAPE 8.6 : Détection Pattern Réel vs Prédit
**Actuel** (lignes 1665-1705) :
- Détection pattern réel dans prix AVANT utilisation timings prédits
- Validation : Si pattern réel = Single Wave ET critères Double Wave remplis → Single Wave Fort

**Avant** (hypothèse) :
- Détection basée uniquement sur critères événements
- Pas de validation avec pattern réel

---

## 🔍 DIFFÉRENCES IDENTIFIÉES

### Modifications Récentes (3 décembre 2025)

| Étape | Modification | Date | Impact |
|-------|-------------|------|--------|
| **Étape 3** | Seuil adaptatif + support tous clusters | 3 déc | ✅ Jobless Claims inclus |
| **Étape 8.1** | Méthode Session 88 | Avant 3 déc | ✅ Amélioration 87% |
| **Étape 8.3** | Stratégie conditionnelle Double Wave | 3 déc | ✅ Correction 11 sept |
| **Étape 8.6** | Timings parfaits Session 64 | Avant 3 déc | ✅ 0.00 min erreur |
| **Étape 8.6** | Détection pattern réel | Avant 3 déc | ✅ Validation patterns |

---

## 📋 VERSION RESTAURÉE (Il y a 2 jours - 1er décembre 2025)

### Hypothèses sur la Version d'Avant

Basé sur la documentation de référence et les modifications récentes identifiées :

#### 1. ÉTAPE 3 : Noyau Dur - Version Avant

**Logique** :
```python
# Support calculé uniquement dans clusters du même type
if core_type == 'CPI':
    # Chercher uniquement dans clusters CPI historiques
    TYPE_PATTERN = r'(?i)(cpi|consumer price|...)'
elif core_type == 'NFP':
    # Chercher uniquement dans clusters NFP historiques
    TYPE_PATTERN = r'(?i)(non farm payrolls|...)'

# Seuil fixe (pas adaptatif)
for event_id, support in support_scores.items():
    if support >= support_threshold:  # 0.60 ou 0.80
        core_events.append(event_id)
```

**Différences** :
- ❌ Pas de calcul support sur tous clusters pour événements génériques
- ❌ Pas de seuil adaptatif selon importance
- ❌ Jobless Claims exclus si support < seuil

---

#### 2. ÉTAPE 8.1 : Impact de Base - Version Avant

**Logique** :
```python
# Calcul individuel pour chaque événement
total_impact_base = 0.0
for _, event in cluster_events.iterrows():
    base_score = event.get('empirical_score', 44.0)
    actual = event.get('actual')
    estimate = event.get('estimate') or event.get('forecast')
    
    # Calculer surprise individuelle
    surprise_pct = 0.0
    if actual is not None and estimate is not None and estimate != 0:
        surprise_pct = abs(actual - estimate) / abs(estimate) * 100
    
    # Ajuster score individuel
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=base_score,
        surprise_pct=surprise_pct
    )
    
    # Calculer impact individuel
    impact_individuel = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=1,
        amplification=1.0,
        correction_factor=1.0
    )
    
    total_impact_base += impact_individuel

# Correction vectorielle après
if num_events >= 2:
    total_impact_base = total_impact_base * 0.758
```

**Différences** :
- ❌ Pas de méthode Session 88 (score moyen ajusté)
- ✅ Calcul individuel pour chaque événement
- ✅ Correction vectorielle appliquée après

---

#### 3. ÉTAPE 8.3 : Stratégie Hybride - Version Avant

**Logique** :
```python
# Stratégie identique pour tous les patterns
ecart_absolu = abs(pattern_impact - impact_formules) if pattern_impact > 0 else 0

if ecart_absolu < 10 or pattern_impact == 0:
    prediction_finale = impact_formules
    prediction_method = 'formulas'
else:
    prediction_finale = pattern_impact
    prediction_method = 'pattern'
```

**Différences** :
- ❌ Pas de logique conditionnelle selon pattern type
- ✅ Stratégie identique pour Single Wave et Double Wave
- ❌ Pas de correction pour Double Wave avec formules suspectes

---

#### 4. ÉTAPE 8.6 : Timings - Version Avant

**Logique** :
```python
# Détection pattern depuis prix réels uniquement
pattern_result = detect_for_date_duckdb_rev12(...)

if pattern_result:
    pattern_type = 'DOUBLE_WAVE' if pattern_result.get('double_wave') else 'SINGLE_WAVE'
    wave1_peak_time = pattern_result.get('peak1_time')  # Détecté depuis prix
    wave2_peak_time = pattern_result.get('peak2_time')  # Détecté depuis prix
    timings_predicted = False  # Timings détectés, pas prédits
```

**Différences** :
- ❌ Pas de prédiction timings fixes (T+5, T+11, T+15, T+40)
- ✅ Timings détectés depuis prix réels
- ❌ Pas de validation pattern réel vs critères événements

---

## 🎯 PROPOSITION : VERSION RESTAURÉE

### Fichier : `scripts/run_pipeline_complete_restored_1dec.py`

**Modifications à appliquer** :

1. **Étape 3** : Restaurer calcul support uniquement dans clusters du même type
2. **Étape 3** : Restaurer seuil fixe (pas adaptatif)
3. **Étape 8.1** : Restaurer calcul individuel (méthode standard)
4. **Étape 8.3** : Restaurer stratégie hybride identique pour tous patterns
5. **Étape 8.6** : Retirer timings parfaits Session 64 (utiliser détection prix)
6. **Étape 8.6** : Retirer validation pattern réel vs critères événements

---

## 📝 NOTES IMPORTANTES

### Performance Attendue

**Version Actuelle** :
- MAE : ~8.4 pips (avec toutes les améliorations)
- Méthode Session 88 : Erreur réduite de 87%

**Version Restaurée** :
- MAE : Probablement > 10 pips (sans améliorations)
- Méthode standard : Erreur plus élevée

### Recommandation

**⚠️ ATTENTION** : La version restaurée sera probablement moins performante que la version actuelle car elle ne contient pas les améliorations validées (Session 88, timings parfaits, etc.).

**Utilisation recommandée** :
- Pour comparaison uniquement
- Pour comprendre l'évolution
- Pour identifier ce qui a changé

---

**Date création** : Comparaison version actuelle vs avant  
**Status** : ✅ Analyse complète, version restaurée proposée




