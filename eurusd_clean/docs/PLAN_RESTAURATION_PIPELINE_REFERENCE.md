# Plan de Restauration Pipeline de Référence

**Date** : Plan méthodique  
**Objectif** : Restaurer le pipeline de référence à l'identique, puis tester les améliorations une par une

---

## 🎯 STRATÉGIE GLOBALE

### Phase 1 : Restauration Pipeline de Référence
**Objectif** : Reconstituer le pipeline exactement comme décrit dans la documentation de référence

### Phase 2 : Intégration Améliorations
**Objectif** : Ajouter les améliorations récentes une par une, tester à chaque étape

---

## 📋 PHASE 1 : RESTAURATION PIPELINE DE RÉFÉRENCE

### Étape 1.1 : Restaurer Étape 8.1 - Calcul Impact de Base

**Référence** :
```
Utilise calculate_impact_d avec les événements du cluster cible
```

**Actuel** :
```
Méthode Session 88 (score moyen ajusté avec surprise MAX)
```

**Action** :
1. ✅ Identifier la méthode standard `calculate_impact_d` utilisée dans Étape 6
2. ✅ Appliquer la même méthode dans Étape 8.1 (somme impacts individuels)
3. ✅ Supprimer temporairement la méthode Session 88
4. ✅ Tester sur date de référence (2025-08-01)

**Fichier à modifier** : `scripts/run_pipeline_complete.py` - `etape8_appliquer_cluster_cible` (lignes 971-1019)

**Méthode standard (Étape 6)** :
```python
# Pour chaque événement :
base_score = event.get('empirical_score', 44.0)
surprise_pct = abs(actual - estimate) / abs(estimate) * 100
adjusted_score = calculate_adjusted_empirical_score(base_score, surprise_pct)
impact_individuel = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=1,
    amplification=1.0,
    correction_factor=1.0
)
total_impact_base += impact_individuel

# Correction vectorielle pour multi-événements
if num_events >= 2:
    total_impact_base = total_impact_base * 0.758
```

---

### Étape 1.2 : Restaurer Étape 8.3 - Hiérarchie d'Amplification

**Référence** :
```
Priorité :
1. Random Forest par date (si >= 5 clusters identiques)
2. Random Forest global (fallback)
3. Modèle linéaire (fallback)
4. Moyenne des amplifications historiques (dernier fallback)
```

**Actuel** :
```
Priorité :
0. Formule Session 88 (si surprise > 100%) ← À SUPPRIMER TEMPORAIREMENT
1. Random Forest par date (si >= 5 clusters identiques)
2. Random Forest global (non implémenté) ← À IMPLÉMENTER
3. Modèle linéaire R² (si tendance détectée)
4. Moyenne historique (dernier fallback)
```

**Actions** :
1. ✅ Supprimer temporairement la priorité 0 (Formule Session 88)
2. ✅ Implémenter Random Forest global (fallback si pas assez de clusters)
3. ✅ Vérifier que le modèle linéaire est utilisé correctement
4. ✅ Tester sur date de référence

**Fichier à modifier** : `scripts/run_pipeline_complete.py` - `etape8_appliquer_cluster_cible` (lignes 1082-1195)

**Random Forest Global** :
- Utiliser `core.amplification_random_forest.predict_amplification_random_forest`
- Features : trend_r2, trend_duration_h, trend_amplitude_pips, impact_base_pips, num_events
- Target : amplification_parfaite moyenne

---

### Étape 1.3 : Restaurer Étape 8.3 - Random Forest Features

**Référence** :
```
Features pour Random Forest :
- trend_r2
- trend_duration_h
- trend_amplitude_pips
- impact_base_pips
- num_events
- pattern_impact_pips (si disponible)
- pattern_wave1_pips (si disponible)
- pattern_wave2_pips (si disponible)
```

**Actuel** :
```
Features :
- max_surprise_pct
- mean_surprise_pct
- num_events
- mean_empirical_score
- trend_r2
- trend_direction_encoded
- trend_amplitude_pips
```

**Actions** :
1. ✅ Modifier `extract_features_for_rf` pour inclure les features de référence
2. ✅ Ajouter `trend_duration_h` (calculer depuis trends_df)
3. ✅ Ajouter `impact_base_pips` (impact_base calculé)
4. ✅ Ajouter `pattern_impact_pips`, `pattern_wave1_pips`, `pattern_wave2_pips` (si pattern détecté)
5. ✅ Supprimer features non référencées (max_surprise_pct, mean_surprise_pct, mean_empirical_score, trend_direction_encoded)
6. ✅ Tester sur date de référence

**Fichier à modifier** : `src/core/random_forest_amplification.py` - `extract_features_for_rf`

---

### Étape 1.4 : Restaurer Étape 8.5 - Ajustement Finnhub

**Référence** :
```
Multiplicateurs :
- Patterns forts validant direction : +5% à +10%
- Patterns forts invalidant direction : -10% à -15%
- Pas de patterns : -5% (réduction confiance)
```

**Actuel** :
```
Multiplicateurs :
- validating_patterns > 0 : +5% à +10%
- invalidating_patterns > 0 : -10% à -10% (limité)
- Pas de patterns : 0% (pas d'ajustement)
```

**Actions** :
1. ✅ Ajouter ajustement -5% si pas de patterns trouvés
2. ✅ Tester sur date de référence

**Fichier à modifier** : `scripts/run_pipeline_complete.py` - `etape8_appliquer_cluster_cible` (lignes 1330-1365)

---

### Étape 1.5 : Restaurer Étape 8.7 - Stratégie Hybride

**Référence** :
```
Option C (révisée) :
- Écart < 10 pips : Garder formules
- Écart >= 10 pips : Utiliser pattern directement (100%)
Pas de pondération hybride
Identique pour tous les patterns
```

**Actuel** :
```
Option C (révisée) selon pattern détecté :
- SINGLE_WAVE_STRONG : Stratégie hybride activée
- DOUBLE_WAVE : Toujours Formules (stratégie hybride désactivée)
- Autres : Stratégie hybride standard
```

**Actions** :
1. ✅ Supprimer la logique conditionnelle selon pattern type
2. ✅ Appliquer la même stratégie pour tous les patterns
3. ✅ Tester sur date de référence

**Fichier à modifier** : `scripts/run_pipeline_complete.py` - `etape8_appliquer_cluster_cible` (lignes 1837-1879)

---

### Étape 1.6 : Restaurer Étape 8.8 - Target de Sortie

**Référence** :
```python
exit_target = min(
    impact_predicted × 0.80,
    impact_predicted × 1.5
)
```

**Actuel** :
```python
exit_target = prediction_finale * 0.80
exit_target = max(prediction_finale * 0.80, min(prediction_finale * 1.5, exit_target))
```

**Actions** :
1. ✅ Simplifier la formule pour correspondre à la référence
2. ✅ Tester sur date de référence

**Fichier à modifier** : `scripts/run_pipeline_complete.py` - `etape8_appliquer_cluster_cible` (lignes 1881-1892)

---

## 🧪 VALIDATION PHASE 1

### Test sur Date de Référence : 2025-08-01

**Résultats attendus** (selon référence) :
- Impact réel : 188.4 pips
- MAE cible : ~8.4 pips (selon documentation référence)

**Métriques à mesurer** :
- Impact de base calculé
- Amplification prédite
- Prédiction finale
- Erreur absolue
- Pattern détecté

**Critère de succès** :
- Pipeline fonctionne sans erreurs
- Résultats cohérents avec documentation référence
- Prêt pour Phase 2

---

## 📋 PHASE 2 : INTÉGRATION AMÉLIORATIONS

### Étape 2.1 : Tester Méthode Session 88 (Étape 8.1)

**Amélioration** : Méthode Session 88 (score moyen ajusté avec surprise MAX)

**Test** :
1. ✅ Activer méthode Session 88 dans Étape 8.1
2. ✅ Tester sur 2025-08-01
3. ✅ Comparer avec Phase 1 (méthode standard)
4. ✅ Mesurer amélioration

**Critère de décision** :
- ✅ Garder si erreur réduite de >10%
- ❌ Rejeter si erreur augmentée ou amélioration <5%

**Documentation** : `docs/ANALYSE_DIFFERENCES_SESSION88.md`

---

### Étape 2.2 : Tester Formule Session 88 (Étape 8.3)

**Amélioration** : Formule Session 88 en priorité 0 (surprises >100%)

**Test** :
1. ✅ Activer formule Session 88 en priorité 0
2. ✅ Tester sur dates avec surprises extrêmes (>100%)
3. ✅ Comparer avec Phase 1 (sans priorité 0)
4. ✅ Mesurer amélioration

**Critère de décision** :
- ✅ Garder si erreur réduite pour surprises extrêmes
- ❌ Rejeter si pas d'amélioration significative

**Documentation** : `docs/INTEGRATION_FORMULE_SESSION88.md`

---

### Étape 2.3 : Tester Stratégie Conditionnelle (Étape 8.7)

**Amélioration** : Stratégie hybride conditionnelle selon pattern type

**Test** :
1. ✅ Activer stratégie conditionnelle (Single Wave hybride, Double Wave formules)
2. ✅ Tester sur dates avec Single Wave et Double Wave
3. ✅ Comparer avec Phase 1 (stratégie identique)
4. ✅ Mesurer amélioration par pattern type

**Critère de décision** :
- ✅ Garder si amélioration pour au moins un pattern type sans dégrader l'autre
- ❌ Rejeter si dégradation globale

**Documentation** : `docs/ANALYSE_CONFIGURATIONS_PATTERNS.md`

---

### Étape 2.4 : Tester Random Forest Méthode 4 Étapes

**Amélioration** : Random Forest avec méthode en 4 étapes (amplifications idéales)

**Test** :
1. ✅ Activer méthode 4 étapes (si pas déjà activée)
2. ✅ Comparer avec RF standard (features de référence)
3. ✅ Tester sur dates avec >= 5 clusters identiques
4. ✅ Mesurer amélioration

**Critère de décision** :
- ✅ Garder si amélioration >5%
- ❌ Rejeter si pas d'amélioration ou dégradation

**Documentation** : `docs/IMPLEMENTATION_RANDOM_FOREST_AMPLIFICATION.md`

---

## 📊 PLAN DE TEST

### Dates de Test

**Date principale** : 2025-08-01
- Impact réel : 188.4 pips
- Pattern : Single Wave Strong
- Surprise : ~266.7% (Construction Spending)

**Dates supplémentaires** :
- 2025-06-23 : Double Wave, 89.6 pips réel
- 2025-08-12 : Double Wave, 92.1 pips réel
- 2025-09-11 : Multiple clusters, CPI US

### Métriques à Mesurer

Pour chaque test :
- Impact de base
- Amplification prédite
- Prédiction finale
- Erreur absolue (pips)
- Erreur relative (%)
- Pattern détecté
- Méthode d'amplification utilisée

### Comparaison

**Baseline** : Phase 1 (Pipeline de référence restauré)

**Comparaison** : Phase 2 (avec amélioration testée)

**Critère** : Amélioration >5% pour garder, sinon rejeter

---

## 🔧 FICHIERS À MODIFIER

### Phase 1 : Restauration

1. `scripts/run_pipeline_complete.py`
   - `etape8_appliquer_cluster_cible` (lignes 971-1019) : Restaurer méthode standard
   - `etape8_appliquer_cluster_cible` (lignes 1082-1195) : Restaurer hiérarchie RF
   - `etape8_appliquer_cluster_cible` (lignes 1330-1365) : Ajouter -5% Finnhub
   - `etape8_appliquer_cluster_cible` (lignes 1837-1879) : Stratégie identique
   - `etape8_appliquer_cluster_cible` (lignes 1881-1892) : Simplifier exit_target

2. `src/core/random_forest_amplification.py`
   - `extract_features_for_rf` : Restaurer features de référence

3. `src/core/amplification_random_forest.py` (à vérifier/créer)
   - Implémenter Random Forest global

### Phase 2 : Améliorations

1. `scripts/run_pipeline_complete.py`
   - Activer/désactiver améliorations selon tests

---

## ✅ CHECKLIST PHASE 1

- [ ] Étape 1.1 : Restaurer méthode standard Étape 8.1
- [ ] Étape 1.2 : Restaurer hiérarchie RF (supprimer Session 88 priorité 0)
- [ ] Étape 1.3 : Implémenter RF global
- [ ] Étape 1.4 : Restaurer features RF de référence
- [ ] Étape 1.5 : Ajouter -5% Finnhub si pas de patterns
- [ ] Étape 1.6 : Restaurer stratégie hybride identique
- [ ] Étape 1.7 : Simplifier exit_target
- [ ] Test Phase 1 : Valider sur 2025-08-01
- [ ] Documenter résultats Phase 1

---

## ✅ CHECKLIST PHASE 2

- [ ] Étape 2.1 : Tester méthode Session 88 (Étape 8.1)
- [ ] Étape 2.2 : Tester formule Session 88 (Étape 8.3)
- [ ] Étape 2.3 : Tester stratégie conditionnelle (Étape 8.7)
- [ ] Étape 2.4 : Tester RF méthode 4 étapes
- [ ] Documenter résultats Phase 2
- [ ] Décider quelles améliorations garder

---

## 📝 NOTES IMPORTANTES

### Sauvegarde Avant Modifications

**Créer backup** :
```bash
cp scripts/run_pipeline_complete.py scripts/run_pipeline_complete.py.backup_avant_restauration
cp src/core/random_forest_amplification.py src/core/random_forest_amplification.py.backup_avant_restauration
```

### Git Branches

**Créer branches** :
```bash
git checkout -b phase1_restauration_reference
# Faire modifications Phase 1
git commit -m "Phase 1: Restauration pipeline de référence"

git checkout -b phase2_ameliorations
# Faire modifications Phase 2
git commit -m "Phase 2: Test amélioration X"
```

### Tests Incrémentaux

**Tester après chaque modification** :
- Ne pas attendre la fin de Phase 1 pour tester
- Valider chaque étape avant de passer à la suivante

---

_Date création : Plan de restauration méthodique_  
_Status : ✅ Plan prêt pour exécution_




