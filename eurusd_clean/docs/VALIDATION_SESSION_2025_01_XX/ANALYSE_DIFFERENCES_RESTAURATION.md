# Analyse des Différences - Version Restaurée vs Validée

**Date** : 2025-01-XX  
**Objectif** : Identifier toutes les différences entre la version restaurée et la version validée

---

## 🔍 DIFFÉRENCES IDENTIFIÉES

### 1. Étape 1 : Charger Événements

**Version restaurée** :
- Seuil US/EU : 29.0 (réduit de 40.0)
- Seuil DE : 20.0 ✅
- `verbose=False` pour chargements individuels ✅

**Version validée (selon docs)** :
- Seuil US/EU : 40.0 (ou 29.0 selon Session 88 ?)
- Seuil DE : 20.0 ✅
- `verbose=False` ✅

**Action** : Vérifier quelle version était validée (40.0 ou 29.0 pour US/EU)

---

### 2. Étape 6 : Calcul Impacts Base & Amplifications

**Version restaurée** :
- Utilise `measure_impact_from_finnhub` ❌
- Table : `prices_finnhub_m1` (implicite dans fonction)
- Calcul impact base : Par événement avec correction vectorielle 0.758 ✅

**Version validée (selon CORRECTIONS_APPLIQUEES.md)** :
- Utilise `measure_impact_from_dukascopy` ✅
- Table : `prices_finnhub_m1` ✅
- Calcul impact base : Par événement avec correction vectorielle 0.758 ✅

**Action** : Remplacer `measure_impact_from_finnhub` par `measure_impact_from_dukascopy`

---

### 3. Étape 8.1 : Calcul Impact Base

**Version restaurée** :
- Méthode Session 88 : Score moyen ajusté avec surprise MAX ❌
- Utilise `calculate_impact_d` avec `correction_factor=0.758` ✅

**Version validée (selon CORRECTIONS_APPLIQUEES.md)** :
- Calcul par événement avec scores ajustés selon surprise ✅
- Utilisation de `calculate_adjusted_empirical_score` pour chaque événement ✅
- Somme des impacts individuels ✅
- Application correction vectorielle 0.758 pour multi-événements ✅

**Action** : Remplacer méthode Session 88 par méthode détaillée par événement

---

### 4. Étape 8.2 : Détection Tendance

**Version restaurée** :
- Table : `prices_finnhub_m30` ✅
- Fonction : `detect_trend_by_inversion_s107` ✅
- Paramètres : `segment_hours=12`, `min_r2_for_trend=0.15`, `min_hours_before_event=12` ✅

**Version validée** :
- Table : `prices_finnhub_m30` ✅
- Fonction : `detect_trend_by_inversion_s107` ✅
- Paramètres : Selon documentation ✅

**Action** : Vérifier paramètres exacts

---

### 5. Étape 8.3 : Prédiction Amplification

**Version restaurée** :
- Hiérarchie : Formule Session 88 → RF par date → RF global → Modèle linéaire → Moyenne
- Formule Session 88 pour surprises >100% ❌

**Version validée (selon docs)** :
- Hiérarchie : RF par date → RF global → Modèle linéaire → Moyenne ✅
- Pas de formule Session 88 mentionnée

**Action** : Vérifier si formule Session 88 doit être incluse ou non

---

### 6. Problème : Clusters Non Détectés

**Observation** : Tous les tests montrent 0 clusters détectés

**Causes possibles** :
1. Étape 1 ne trouve pas d'événements (seuil trop élevé ?)
2. Étape 2 ne crée pas de clusters (fenêtre trop petite ?)
3. `execute_complete_pipeline` ne retourne pas les clusters

**Action** : Debugger pourquoi aucun cluster n'est détecté

---

## 📋 PLAN DE RESTAURATION

### Priorité 1 : Corrections Critiques

1. **Étape 6** : Remplacer `measure_impact_from_finnhub` par `measure_impact_from_dukascopy`
2. **Étape 8.1** : Remplacer méthode Session 88 par méthode détaillée par événement
3. **Debug clusters** : Identifier pourquoi 0 clusters sont détectés

### Priorité 2 : Vérifications

1. **Étape 1** : Vérifier seuil US/EU (29.0 vs 40.0)
2. **Étape 8.3** : Vérifier si formule Session 88 doit être incluse
3. **Paramètres** : Vérifier tous les paramètres contre documentation

---

## ✅ VALIDATION

Après chaque correction, tester sur cas de base pour vérifier que les résultats s'améliorent.




