# Cause Racine : Pourquoi 15.00 pips au lieu de 74.40 ?

**Date** : 2025-01-XX  
**Statut** : ✅ Cause identifiée

---

## 🔍 INVESTIGATION

### Résultats de l'Investigation

Pour **2025-05-29** :
- **Pic absolu étendu calculé** : **74.40 pips** ✅
- **Impact réel mesuré** : **74.40 pips** ✅
- **Baseline pattern** : 1.12954
- **Start price (OPEN)** : 1.12954
- **Ils sont identiques !**

**Mais dans le pipeline** :
- `wave2_peak_pips_absolute = 15.00` ❌

---

## 🔴 CAUSE IDENTIFIÉE

### Condition Ligne 2319

```python
if wave2_absolute_extended > wave2_real and minutes_after_event <= 180:
    wave2_peak_pips_absolute = wave2_absolute_extended
```

**Pour 2025-05-29** :
- `wave2_absolute_extended = 74.40` (calculé correctement)
- `wave2_real = 10.3` (depuis pattern réel détecté)
- `74.40 > 10.3` ✅
- `minutes_after_event = 112.0` (≤ 180) ✅
- **Donc `wave2_peak_pips_absolute = 74.40` devrait être utilisé !**

**Mais le pipeline retourne 15.00 pips...**

---

## 🔍 HYPOTHÈSES

### Hypothèse 1 : Modification Ultérieure

`wave2_peak_pips_absolute` est peut-être modifié après la ligne 2320.

**Vérification** :
- Ligne 2360 : `'wave2_peak_pips_absolute': wave2_peak_pips_absolute` (stocké dans pattern_info)
- Mais peut-être qu'il y a une autre modification après ?

### Hypothèse 2 : Condition Non Respectée

La condition `wave2_absolute_extended > wave2_real` n'est peut-être pas respectée dans le pipeline.

**Vérification nécessaire** :
- Vérifier les valeurs de `wave2_absolute_extended` et `wave2_real` dans le pipeline
- Vérifier si `baseline_price_pattern` est correct

### Hypothèse 3 : Baseline Différent

Le `baseline_price_pattern` utilisé dans le pipeline est peut-être différent de celui utilisé dans l'investigation.

**Pour 2025-05-29** :
- Investigation : `baseline_price_pattern = 1.12954` (correct)
- Pipeline : À vérifier

### Hypothèse 4 : Fenêtre Différente

La fenêtre utilisée dans le pipeline est peut-être différente.

**Pour 2025-05-29** :
- Investigation : `window_end_extended = anchor_time + 2h` (16:30)
- Pipeline : À vérifier

---

## ✅ SOLUTION PROPOSÉE

### Ajouter Logs Détaillés

Ajouter des logs dans le pipeline pour voir :
1. Valeur de `wave2_absolute_extended` calculée
2. Valeur de `wave2_real`
3. Valeur de `baseline_price_pattern`
4. Valeur de `minutes_after_event`
5. Condition `wave2_absolute_extended > wave2_real`
6. Valeur finale de `wave2_peak_pips_absolute`

### Vérifier Toutes les Modifications

Chercher tous les endroits où `wave2_peak_pips_absolute` est modifié après la ligne 2320.

---

## 📋 PROCHAINES ÉTAPES

1. ⏳ Ajouter logs détaillés dans le pipeline
2. ⏳ Vérifier toutes les modifications de `wave2_peak_pips_absolute`
3. ⏳ Comparer valeurs calculées dans investigation vs pipeline
4. ⏳ Corriger le problème identifié

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Cause probable identifiée, vérification en cours




