# Résolution Cas Problématiques

**Date** : 2025-01-XX  
**Statut** : 🔍 Investigation en cours

---

## 🔴 PROBLÈMES IDENTIFIÉS

### 1. 2025-06-23 - Erreur 73.10 pips (82.5%)

**Symptômes** :
- Impact base : **NaN** ❌
- Pattern impact : 0.00 pips
- **Impact prédit : 15.50 pips** (d'où vient cette valeur ?)
- Impact réel : 88.60 pips

**Hypothèse** :
- Le 15.50 pips pourrait venir de `wave2_pips_predicted` du timeline
- Si `impact_base = NaN`, alors `base_impact_for_timeline` pourrait être une valeur par défaut ou `wave2_pips_predicted`

### 2. 2025-05-29 - Erreur 59.40 pips (79.8%)

**Symptômes** :
- Impact base : 71.17 pips ✅
- Amplification : 5.740x
- Impact formules : 408.49 pips (beaucoup trop élevé)
- Pattern impact : 0.00 pips
- **Impact prédit : 15.00 pips** (d'où vient cette valeur ?)
- Impact réel : 74.40 pips

**Hypothèse** :
- Le 15.00 pips pourrait venir de `wave2_pips_predicted` du timeline
- Si `pattern_impact = 0.0`, la stratégie hybride devrait utiliser les formules (408.49)
- Mais peut-être qu'il y a un fallback vers `wave2_pips_predicted` si les formules sont trop élevées ?

---

## 🔍 CODE À VÉRIFIER

### Ligne 2092-2094 : Calcul base_impact_for_timeline

```python
# Calculer impact de base pour prédiction timeline
# ✅ CORRECTION : Appliquer amplification à l'impact de base pour le pattern
base_impact_for_timeline = impact_base * amplification_predite
```

**Problème potentiel** :
- Si `impact_base = NaN`, alors `base_impact_for_timeline = NaN`
- Le timeline pourrait utiliser une valeur par défaut ou `wave2_pips_predicted`

### Ligne 2265 : wave2_pips_predicted

```python
wave2_pips_predicted = timeline['phase2']['impact_pips']
```

**Hypothèse** :
- Si `base_impact_for_timeline` est très faible ou NaN, alors `wave2_pips_predicted` pourrait être ~15 pips
- Cette valeur pourrait être utilisée comme fallback dans la stratégie hybride

---

## ✅ SOLUTIONS PROPOSÉES

### Pour 2025-06-23

1. **Corriger calcul impact base** :
   - Vérifier pourquoi `impact_base = NaN`
   - Vérifier étape 8.1 (calcul impact base)
   - S'assurer que tous les événements ont des scores empiriques valides

2. **Vérifier fallback** :
   - Si `impact_base = NaN`, utiliser une valeur par défaut ou calculer depuis les événements
   - Ne pas utiliser `wave2_pips_predicted` comme prédiction finale

### Pour 2025-05-29

1. **Corriger pattern impact** :
   - Vérifier pourquoi `wave2_peak_pips_absolute = 0` malgré pattern détecté
   - Vérifier la détection de pattern (Étape 8.6)

2. **Corriger stratégie hybride** :
   - Si `pattern_impact = 0.0`, utiliser les formules (même si élevées)
   - Ne pas utiliser `wave2_pips_predicted` comme fallback

3. **Corriger amplification** :
   - L'amplification 5.740x (surprise 203%) est peut-être excessive
   - Vérifier si la formule Session 88 est correcte pour surprises 200-300%

---

## 📋 PROCHAINES ÉTAPES

1. ⏳ Vérifier pourquoi `impact_base = NaN` pour 2025-06-23
2. ⏳ Vérifier d'où vient le 15.00/15.50 pips (wave2_pips_predicted ?)
3. ⏳ Corriger la stratégie hybride pour ne pas utiliser wave2_pips_predicted comme fallback
4. ⏳ Corriger la détection de pattern pour mesurer wave2_peak_pips_absolute correctement

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : 🔍 Investigation en cours




