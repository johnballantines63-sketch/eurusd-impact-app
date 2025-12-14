# Problèmes Identifiés Pipeline - 11 Septembre 2025

## Date
2025-01-XX

## Problèmes Critiques Identifiés

### 1. Aucun Cluster Identique Trouvé

**Symptôme** : 0 clusters identiques trouvés malgré 9/12 événements core

**Impact** :
- Amplification calculée avec valeur par défaut très faible : **0.125x**
- Pas de données historiques pour calibrer l'amplification
- Prédiction finale très faible : **4.24 pips** au lieu d'utiliser le pattern détecté (56.8 pips)

**Cause probable** :
- Le seuil Jaccard de 0.60 est peut-être trop strict avec 9 événements core
- Les Jobless Claims inclus changent la composition du noyau dur
- Les clusters historiques CPI n'incluaient peut-être pas les Jobless Claims

### 2. Double Wave Pattern Ignoré

**Symptôme** : Pattern Double Wave détecté avec Wave2 = 56.8 pips, mais prédiction finale = 4.24 pips

**Code problématique** (ligne 2078-2083) :
```python
elif pattern_type == 'DOUBLE_WAVE':
    # Pour Double Wave, les formules sont plus fiables que le pattern détecté
    prediction_finale = impact_formules  # ❌ PROBLÈME
    prediction_method = 'formulas'
```

**Impact** :
- Le pattern réel détecté (56.8 pips) est ignoré
- Les formules avec amplification faible (0.125x) donnent 4.24 pips
- Perte d'information précieuse du pattern détecté

### 3. Amplification Très Faible

**Symptôme** : Amplification = 0.125x

**Calcul** :
- Impact de base : 29.58 pips
- Amplification : 0.125x
- Impact formules : 29.58 × 0.125 = 3.70 pips
- Ajustements : +15% S/R → 4.24 pips

**Cause** :
- Aucun cluster identique → pas de Random Forest
- Fallback vers moyenne historique très faible
- Ou utilisation d'une valeur par défaut incorrecte

### 4. Écart du Pipeline de Référence

**Problèmes identifiés** :
1. Méthode Session 88 pour impact de base (au lieu de méthode standard)
2. Seuil adaptatif pour noyau dur (modification récente)
3. Calcul support sur tous clusters pour événements génériques (modification récente)
4. Logique Double Wave qui ignore le pattern détecté

## Solutions Proposées

### Solution Immédiate : Utiliser Pattern Détecté pour Double Wave

**Modification ligne 2078-2083** :
```python
elif pattern_type == 'DOUBLE_WAVE':
    # Pour Double Wave, utiliser le pattern détecté si disponible
    if pattern_impact > 0:
        prediction_finale = pattern_impact
        prediction_method = 'pattern'
        self._log(f"   ✅ Stratégie: Pattern (Double Wave, impact: {pattern_impact:.2f} pips)", "INFO")
    else:
        prediction_finale = impact_formules
        prediction_method = 'formulas'
        self._log(f"   ✅ Stratégie: Formules (Double Wave, pas de pattern)", "INFO")
```

### Solution Long Terme : Restaurer Pipeline de Référence

1. **Restaurer méthode standard pour impact de base** (au lieu de Session 88)
2. **Vérifier logique amplification** quand aucun cluster identique
3. **Réviser seuil Jaccard** pour clusters avec Jobless Claims
4. **Documenter toutes les modifications** par rapport à la référence

## Tests à Effectuer

1. **Test avec pattern Double Wave** : Vérifier que 56.8 pips est utilisé
2. **Test amplification sans clusters identiques** : Vérifier valeur par défaut
3. **Test clusters identiques** : Vérifier pourquoi 0 clusters trouvés avec 9 événements core
4. **Comparaison avec pipeline de référence** : Vérifier toutes les différences

## Impact Attendu

**Avant correction** :
- Prédiction : 4.24 pips
- Pattern détecté ignoré : 56.8 pips

**Après correction** :
- Prédiction : 56.8 pips (pattern Double Wave utilisé)
- Amélioration : +1240% (mais nécessite validation)




