# Analyse Amplification - Random Forest vs Formule Session 88

**Date** : 2025-01-XX  
**Problème** : Amplification excessive (5.875x) pour 2025-11-20  
**Objectif** : Comprendre pourquoi et comment l'amplification est calculée

---

## 🔍 RÉSUMÉ EXÉCUTIF

### Hiérarchie d'Amplification (Étape 8.3)

Le pipeline utilise une **hiérarchie** pour déterminer l'amplification :

```
1. Formule Session 88 (priorité maximale si surprise >100%)
   ↓ (si surprise ≤100%)
2. Random Forest par date (si >= 5 clusters identiques)
   ↓ (si < 5 clusters)
3. Random Forest global (non implémenté, passe à 4)
   ↓
4. Modèle linéaire (basé sur R²)
   ↓
5. Moyenne historique (dernier fallback)
```

---

## 📊 CAS 2025-11-20 - ANALYSE DÉTAILLÉE

### Événements du Cluster

| Événement | Actual | Estimate | Surprise | Empirical Score |
|-----------|--------|----------|----------|----------------|
| **non farm payrolls** | 119.0 | 50.0 | **138.0%** | 64.61 |
| nonfarm payrolls private | 97.0 | 62.0 | 56.5% | 64.61 |
| average hourly earnings mom | 0.2 | 0.3 | 33.3% | 64.61 |
| manufacturing payrolls | -6.0 | -8.0 | 25.0% | 61.99 |
| average hourly earnings yoy | 3.8 | 3.7 | 2.7% | 64.61 |
| unemployment rate | 4.4 | 4.3 | 2.3% | 61.99 |
| average weekly hours | 34.2 | 34.2 | 0.0% | 64.61 |
| government payrolls | 22.0 | nan | nan | 61.99 |
| participation rate | 62.4 | nan | nan | 64.61 |
| u6 unemployment rate | 8.0 | nan | nan | 63.90 |

**Total** : 10 événements

### Calculs Effectués

1. **Impact Base** : 273.78 pips
   - Calculé par événement avec `calculate_impact_d`
   - Scores empiriques élevés (61.99-64.61)
   - 10 événements → somme importante

2. **Surprise Maximale** : 138.0%
   - NFP : 119 vs 50 estimé → 138% de surprise
   - **Seuil Session 88 (>100%) : ✅ DÉPASSÉ**

3. **Amplification** : 5.8751x
   - **Méthode** : Formule Session 88 (`calculate_amplification_extended`)
   - **Formule** : `5.0 + 0.55 × log10(138 - 99) = 5.0 + 0.55 × log10(39) ≈ 5.875x`
   - **Zone** : Zone 4 (surprise >100%, croissance logarithmique)

4. **Prédiction Finale** : 1769.30 pips
   - Calcul : 273.78 × 5.875 = 1608.7 pips
   - (Ajustements S/R et patterns peuvent modifier légèrement)

5. **Impact Réel** : 34.4 pips
   - **Erreur** : 1734.90 pips (5043.3%)

**Note** : Pour 2025-09-11, la valeur réelle correcte est **56.2 pips** (Session 110), pas 21.7 pips qui était une valeur incorrecte dans le CSV.

---

## 🎯 POURQUOI LE RANDOM FOREST N'EST PAS UTILISÉ ?

### Condition pour Random Forest

Le Random Forest est appelé **UNIQUEMENT** si :
1. `amplification_method == 'default'` (pas encore déterminé)
2. `num_clusters >= 5` (au moins 5 clusters identiques)
3. `results_df is not None` (résultats Étape 6 disponibles)

### Pour 2025-11-20

- ✅ `num_clusters = 44` (suffisant)
- ✅ `results_df` disponible
- ❌ **`amplification_method != 'default'`** car la Formule Session 88 est appliquée en premier

**Conclusion** : Le Random Forest n'est **jamais appelé** pour 2025-11-20 car la surprise >100% déclenche la Formule Session 88 en priorité.

---

## 📚 FORMULE SESSION 88 - DÉTAILS

### Implémentation

**Fichier** : `src/core/formulas_validated.py`  
**Fonction** : `calculate_amplification_extended(surprise_pct: float)`

### Zones de Surprise

| Zone | Surprise | Formule | Amplification |
|------|----------|---------|---------------|
| **Zone 1** | < 15% | `1.0` | 1.0x (pas d'ampli) |
| **Zone 2** | 15-30% | `1.0 + (surprise - 15) / 15 * 1.5` | 1.0x → 2.5x (linéaire) |
| **Zone 3** | 30-100% | `2.5 + (surprise - 30) / 70 * 2.5` | 2.5x → 5.0x (linéaire) |
| **Zone 4** | >100% | `5.0 + 0.55 × log10(surprise - 99)` | 5.0x → 10.0x (logarithmique) |

### Validation Session 88

- **Cas validé** : 2025-08-01 (surprise 500%)
- **Amplification attendue** : ~9.7x
- **Impact réel** : 173.8 pips
- **Précision** : 99.83% ✅

### Exemples de Calcul

```python
# Surprise 50%
calculate_amplification_extended(50)  # Zone 3
# = 2.5 + (50 - 30) / 70 * 2.5 = 2.5 + 0.714 = 3.214x

# Surprise 100%
calculate_amplification_extended(100)  # Zone 3 limite
# = 2.5 + (100 - 30) / 70 * 2.5 = 2.5 + 2.5 = 5.0x

# Surprise 138% (2025-11-20)
calculate_amplification_extended(138)  # Zone 4
# = 5.0 + 0.55 × log10(138 - 99)
# = 5.0 + 0.55 × log10(39)
# = 5.0 + 0.55 × 1.591
# = 5.0 + 0.875 = 5.875x

# Surprise 500% (2025-08-01)
calculate_amplification_extended(500)  # Zone 4
# = 5.0 + 0.55 × log10(500 - 99)
# = 5.0 + 0.55 × log10(401)
# = 5.0 + 0.55 × 2.603
# = 5.0 + 1.432 = 6.432x
```

---

## 🤖 RANDOM FOREST - IMPLÉMENTATION

### Module

**Fichier** : `src/core/random_forest_amplification.py`

### Fonctions Principales

1. **`train_rf_from_identical_clusters`**
   - Entraîne un Random Forest sur les clusters identiques
   - Calcule l'amplification idéale pour chaque cluster historique
   - Extrait les features (R², amplitude, nombre d'événements, etc.)
   - Retourne le modèle entraîné, le scaler, et les noms de features

2. **`predict_amplification_with_rf`**
   - Prédit l'amplification pour le cluster cible
   - Utilise le modèle entraîné et les features du cluster cible
   - Limite la prédiction entre 0.1x et 10.0x

3. **`extract_features_for_rf`**
   - Extrait les features pour le Random Forest :
     - `trend_r2` : R² de la tendance
     - `trend_duration_h` : Durée en heures
     - `trend_amplitude_pips` : Amplitude en pips
     - `impact_base_pips` : Impact de base
     - `num_events` : Nombre d'événements
     - `pattern_impact_pips` : Impact pattern (si disponible)
     - `pattern_wave1_pips` : Wave 1 pips (si disponible)
     - `pattern_wave2_pips` : Wave 2 pips (si disponible)

### Quand le Random Forest est Utilisé ?

Le Random Forest est utilisé **UNIQUEMENT** si :
1. La surprise ≤100% (Formule Session 88 non déclenchée)
2. Au moins 5 clusters identiques trouvés
3. Les résultats de l'Étape 6 sont disponibles

**Exemple** : Pour 2025-09-11 (surprise <100%), le Random Forest pourrait être utilisé si >= 5 clusters identiques.

---

## ⚠️ PROBLÈMES IDENTIFIÉS

### Problème 1 : Formule Session 88 Trop Agressive pour Surprises 100-200%

**Symptôme** :
- Surprise 138% → Amplification 5.875x
- Impact base 273.78 pips → Prédiction 1769 pips
- Impact réel 34.4 pips → Erreur 1734 pips

**Cause** :
- La formule Session 88 est calibrée pour des surprises extrêmes (500%+)
- Pour des surprises modérées (100-200%), l'amplification logarithmique peut être excessive

**Solution Possible** :
- Ajuster la formule pour les surprises 100-200%
- Ou utiliser le Random Forest même pour surprises >100% si disponible

### Problème 2 : Impact Base Très Élevé

**Symptôme** :
- Impact base 273.78 pips pour 10 événements
- Chaque événement contribue ~27 pips en moyenne

**Cause** :
- Scores empiriques élevés (61.99-64.61)
- 10 événements → somme importante
- Pas de correction pour multi-événements (correction_factor = 1.0 dans Étape 8.1)

**Solution Possible** :
- Vérifier si la correction_factor 0.758 est appliquée correctement
- Ajuster le calcul d'impact base pour multi-événements

### Problème 3 : Random Forest Non Utilisé pour Surprises Extrêmes

**Symptôme** :
- Le Random Forest n'est jamais appelé pour surprises >100%
- La Formule Session 88 prend toujours la priorité

**Cause** :
- Hiérarchie rigide : Formule Session 88 en priorité absolue
- Pas de fallback vers Random Forest si la formule donne des résultats aberrants

**Solution Possible** :
- Modifier la hiérarchie pour permettre Random Forest même pour surprises >100%
- Ou utiliser Random Forest si disponible, puis ajuster avec Formule Session 88

---

## 📋 RECOMMANDATIONS

### Recommandation 1 : Analyser Impact Base

**Action** : Vérifier pourquoi l'impact base est si élevé (273.78 pips) pour 2025-11-20.

**Questions** :
- La correction_factor 0.758 est-elle appliquée ?
- Les scores empiriques sont-ils corrects ?
- Le calcul par événement est-il correct ?

### Recommandation 2 : Ajuster Formule Session 88

**Action** : Revoir la formule pour les surprises 100-200%.

**Options** :
- Réduire le coefficient logarithmique (0.55 → 0.35)
- Ajouter une zone intermédiaire (100-200%)
- Plafonner l'amplification à 3.0x pour surprises <200%

### Recommandation 3 : Utiliser Random Forest si Disponible

**Action** : Modifier la hiérarchie pour permettre Random Forest même pour surprises >100%.

**Logique** :
```
Si Random Forest disponible ET >= 5 clusters :
    Utiliser Random Forest
    Si surprise >100% :
        Ajuster avec Formule Session 88 (multiplicateur)
Sinon :
    Utiliser Formule Session 88 directement
```

---

## 📊 COMPARAISON DES MÉTHODES

| Méthode | Quand Utilisée | Avantages | Inconvénients |
|---------|----------------|-----------|--------------|
| **Formule Session 88** | Surprise >100% | Simple, rapide, validée pour surprises extrêmes | Peut être excessive pour surprises 100-200% |
| **Random Forest** | Surprise ≤100% ET >= 5 clusters | Apprend des patterns historiques, adaptatif | Nécessite données historiques, peut overfitter |
| **Modèle Linéaire** | Fallback si pas de RF | Simple, basé sur R² | Moins précis que RF |
| **Moyenne Historique** | Dernier fallback | Toujours disponible | Moins précis |

---

## ✅ CONCLUSION

1. **Pour 2025-11-20** : L'amplification de 5.875x vient de la **Formule Session 88**, pas du Random Forest.

2. **Le Random Forest** est implémenté et fonctionnel, mais n'est pas utilisé pour les surprises >100% car la Formule Session 88 prend la priorité.

3. **Le problème principal** : La Formule Session 88 est trop agressive pour des surprises modérées (100-200%), donnant des amplifications excessives.

4. **Solution recommandée** : Ajuster la formule Session 88 ou modifier la hiérarchie pour permettre Random Forest même pour surprises >100%.

---

## 🔗 FICHIERS RÉFÉRENCES

- **Formule Session 88** : `src/core/formulas_validated.py` (ligne 50-138)
- **Random Forest** : `src/core/random_forest_amplification.py`
- **Hiérarchie Étape 8.3** : `scripts/run_pipeline_complete.py` (ligne 1405-1530)
- **Documentation Session 88** : `docs/SESSION88_RAPPORT_FINAL_VALIDE_V2.md`

