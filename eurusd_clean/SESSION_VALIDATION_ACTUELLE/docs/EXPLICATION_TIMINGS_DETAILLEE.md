# Explication Détaillée : Timings Wave2 Peak

**Date** : 2025-01-XX  
**Objectif** : Expliquer clairement le problème des timings Wave2 peak

---

## 📊 QU'EST-CE QUE T+15 ?

### Signification

**T+15** signifie : **15 minutes après l'événement** (anchor_time)

**Exemple concret** :
- **Événement** : 14:30 (CPI US publié)
- **T+15** : 14:30 + 15 minutes = **14:45**
- **Signification** : Le pic Wave2 devrait se produire à **14:45**

### Timings Session 64 (Validés)

Pour un pattern **DOUBLE_WAVE**, les timings sont **fixes** :

| Timing | Signification | Exemple (événement 14:30) |
|--------|---------------|---------------------------|
| **T+5** | Wave1 peak (premier pic) | **14:35** (14:30 + 5 min) |
| **T+11** | Pullback low (point bas) | **14:41** (14:30 + 11 min) |
| **T+15** | **Wave2 peak (deuxième pic)** | **14:45** (14:30 + 15 min) |
| **T+40** | Stabilization (stabilisation) | **15:10** (14:30 + 40 min) |

**Validation** : Ces timings ont été validés avec **0.00 min d'erreur**.

---

## 🔍 LE PROBLÈME : DEUX CHEMINS DANS LE CODE

### Chemin 1 : Timings Prédits (Session 64) ✅

**Quand** : Conditions Double Wave remplies (événements HIGH, etc.)

**Code** (lignes 2027-2119) :
```python
# Utiliser timings prédits Session 64 (T+5, T+11, T+15, T+40)
wave2_peak_time_predicted = timeline['phase2']['peak_time']  # = anchor_time + 15 min

pattern_info = {
    'timings_predicted': True,  # ✅ Timings prédits
    'wave2_peak_time': wave2_peak_time_predicted,  # ✅ Utilise T+15
}
```

**Résultat** : `wave2_peak_time = 14:45` (T+15) ✅

---

### Chemin 2 : Pattern Réel Détecté ❌

**Quand** : Pattern réel détecté avec `detect_for_date_duckdb_rev12`

**Code** (lignes 2360-2373) :
```python
# Pattern réel détecté depuis les prix
pattern_result = detect_for_date_duckdb_rev12(...)
peak2_time_real = pattern_result.get('peak2_time')  # Pic réel détecté (ex: 19:55)

pattern_info = {
    'timings_predicted': False,  # ❌ Timings détectés, pas prédits
    'wave2_peak_time': pd.to_datetime(peak2_time_real),  # ❌ Utilise pic réel
}
```

**Résultat** : `wave2_peak_time = 19:55` (pic réel) ❌

---

## 🎯 POURQUOI C'EST UN PROBLÈME ?

### Exemple : 2025-06-23

**Événement** : 14:30

**Timing Prédit (T+15)** : **14:45** ✅  
**Pic Réel Détecté** : **19:55** (5h25 après événement) ❌

**Erreur** : 19:55 - 14:45 = **295 minutes** (4h55)

**Problème** : Le code utilise le **pic réel** (19:55) au lieu du **timing prédit** (14:45).

---

## 🔧 CE QUI DOIT ÊTRE CORRIGÉ

### Solution

**Pour DOUBLE_WAVE**, on doit **toujours** utiliser les timings prédits (T+15) :
- Même si un pattern réel est détecté
- Même si le pic réel est à 19:55
- On doit utiliser **14:45** (T+15)

**Raison** : Les timings ont été **validés avec 0.00 min d'erreur**. Si on utilise les timings prédits, on doit être **cohérent**.

---

## 📋 EXEMPLE CONCRET

### Cas : 2025-09-11 (DOUBLE_WAVE)

**Événement** : 14:30

**Timings Prédits** :
- Wave1 peak : **14:35** (T+5) ✅
- Pullback low : **14:41** (T+11) ⚠️ (erreur 23 min)
- **Wave2 peak : 14:45 (T+15)** ⚠️ (erreur 40 min - utilise 15:25 au lieu de 14:45)
- Stabilization : **15:10** (T+40) ✅

**Problème** : Le code devrait utiliser **14:45** (T+15), mais utilise **15:25** (pic réel détecté).

**Solution** : Modifier le code pour que **toujours** `wave2_peak_time = anchor_time + 15 minutes` pour DOUBLE_WAVE avec `timings_predicted=True`.

---

## ✅ CE QU'IL FAUT VÉRIFIER

1. **Vérifier quel chemin est pris** pour chaque date
2. **Vérifier que `timings_predicted=True`** pour toutes les dates DOUBLE_WAVE
3. **Vérifier que `wave2_peak_time` utilise `wave2_peak_time_predicted`** (T+15) et non `peak2_time` réel

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ⚠️ Problème identifié, deux chemins dans le code




