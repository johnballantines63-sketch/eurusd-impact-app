# Explication : Problème Timings Wave2 Peak

**Date** : 2025-01-XX  
**Objectif** : Expliquer clairement le problème des timings Wave2 peak

---

## 📊 QU'EST-CE QUE LES TIMINGS PRÉDITS ?

### Timings Session 64 (Validés)

Pour un pattern **DOUBLE_WAVE**, les timings sont **fixes** et validés :

| Timing | Signification | Exemple (événement 14:30) |
|--------|---------------|---------------------------|
| **T+5** | Wave1 peak (premier pic) | 14:35 (14:30 + 5 min) |
| **T+11** | Pullback low (point bas) | 14:41 (14:30 + 11 min) |
| **T+15** | Wave2 peak (deuxième pic) | 14:45 (14:30 + 15 min) |
| **T+40** | Stabilization (stabilisation) | 15:10 (14:30 + 40 min) |

**Validation** : Ces timings ont été validés avec **0.00 min d'erreur** dans une session précédente.

---

## 🔍 LE PROBLÈME ACTUEL

### Ce Qui Devrait Se Passer

**Pour DOUBLE_WAVE avec `timings_predicted=True`** :
- Le code devrait **toujours** utiliser `wave2_peak_time_predicted = anchor_time + 15 minutes`
- Exemple : Si événement à 14:30 → Wave2 peak à **14:45** (T+15)

### Ce Qui Se Passe Parfois

**Pour certaines dates**, le code utilise le **pic réel détecté** au lieu du timing prédit :

| Date | Événement | Timing Prédit (T+15) | Timing Réel Utilisé | Erreur |
|------|-----------|---------------------|---------------------|--------|
| 2025-11-20 | 14:30 | **14:45** | 14:45 | ✅ 0 min (parfait) |
| 2025-09-11 | 14:30 | **14:45** | 15:25 | ❌ 40 min |
| 2025-10-10 | 16:00 | **16:15** | 19:25 | ❌ 190 min |
| 2025-06-23 | 14:30 | **14:45** | 19:55 | ❌ 295 min |
| 2025-11-26 | 14:30 | **14:45** | 16:25 | ❌ 100 min |

**Problème** : Le code utilise parfois le **pic réel détecté** (ex: 19:55) au lieu du **timing prédit** (14:45).

---

## 🎯 POURQUOI C'EST UN PROBLÈME ?

### 1. Incohérence

**Si on utilise les timings prédits**, on doit être **cohérent** :
- Wave1 peak : T+5 ✅ (toujours parfait)
- Pullback low : T+11 ⚠️ (parfois erreur)
- **Wave2 peak : T+15** ⚠️ (parfois erreur importante)
- Stabilization : T+40 ✅ (toujours parfait)

**Problème** : Wave2 peak devrait être **toujours T+15**, mais parfois le code utilise le pic réel.

### 2. Validation

**Les timings ont été validés avec 0.00 min d'erreur** :
- Si on utilise les timings prédits, on doit **toujours** les utiliser
- Mélanger timings prédits et pics réels = incohérence

### 3. Prédiction vs Détection

**Timings prédits** = **Prédiction** (on prédit que le pic sera à T+15)  
**Pic réel détecté** = **Détection** (on détecte où le pic s'est réellement produit)

**Si on utilise les timings prédits**, on fait une **prédiction**, pas une détection.

---

## 🔧 CE QUI DOIT ÊTRE CORRIGÉ

### Code Actuel (Ligne 2116)

```python
pattern_info = {
    ...
    'wave2_peak_time': wave2_peak_time_predicted,  # ✅ Utilise timing prédit
    ...
}
```

**Le code utilise bien `wave2_peak_time_predicted`**, mais le problème vient peut-être d'ailleurs.

### Hypothèses

1. **Problème dans le calcul des erreurs** : Le script de test compare peut-être avec le mauvais timing
2. **Problème dans l'affichage** : Le timing affiché n'est pas le bon
3. **Problème dans la détection** : Pour certaines dates, `timings_predicted=False` au lieu de `True`

---

## 📋 EXEMPLE CONCRET

### Cas : 2025-09-11 (DOUBLE_WAVE)

**Événement** : 14:30 (anchor_time)

**Timings Prédits (Session 64)** :
- Wave1 peak : **14:35** (T+5) ✅
- Pullback low : **14:41** (T+11) ⚠️ (erreur 23 min)
- **Wave2 peak : 14:45 (T+15)** ⚠️ (erreur 40 min - utilise 15:25 au lieu de 14:45)
- Stabilization : **15:10** (T+40) ✅

**Problème** : Le code devrait utiliser **14:45** (T+15), mais utilise **15:25** (pic réel détecté).

**Solution** : S'assurer que `wave2_peak_time` utilise **toujours** `wave2_peak_time_predicted` (14:45) pour DOUBLE_WAVE avec `timings_predicted=True`.

---

## ✅ CE QU'IL FAUT VÉRIFIER

1. **Vérifier que `timings_predicted=True`** pour toutes les dates DOUBLE_WAVE
2. **Vérifier que `wave2_peak_time` utilise `wave2_peak_time_predicted`** (T+15)
3. **Vérifier le calcul des erreurs** dans les scripts de test

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ⚠️ Problème identifié, à investiguer




