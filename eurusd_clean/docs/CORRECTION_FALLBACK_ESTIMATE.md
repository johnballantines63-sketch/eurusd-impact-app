# Correction : Fallback Estimate/Forecast/Previous

**Date** : Correction effectuée  
**Status** : ✅ **Corrigé**

---

## 🔍 PROBLÈME IDENTIFIÉ

### Symptôme

Certains événements affichaient "Estimate N/A" dans les résultats, même si `previous` était disponible dans la base de données.

**Exemples** :
- Government Payrolls : estimate=N/A, previous=11.0
- Participation Rate : estimate=N/A, previous=62.3
- U-6 Unemployment Rate : estimate=N/A, previous=7.7

### Cause Racine

La fonction `load_high_impact_events()` dans `src/core/event_loader.py` ne récupérait **pas** les colonnes `forecast` et `previous` dans sa requête SQL.

**Requête avant** :
```sql
SELECT 
    e.event_key,
    e.event_title as label,
    e.ts_utc,
    e.actual,
    e.estimate,  -- ✅ Présent
    -- ❌ forecast MANQUANT
    -- ❌ previous MANQUANT
    e.country,
    ...
```

**Conséquence** :
- Le fallback `estimate or forecast or previous` ne pouvait pas utiliser `previous`
- Les événements sans `estimate` avaient `surprise_pct = 0.0`
- Impact sur les calculs d'ajustement de score et de direction

---

## ✅ CORRECTION APPLIQUÉE

### Modification

**Fichier** : `src/core/event_loader.py` (lignes 100-121)

**Ajout** : Colonnes `forecast` et `previous` dans la requête SQL

**Requête après** :
```sql
SELECT 
    e.event_key,
    e.event_title as label,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.forecast,  -- ✅ AJOUTÉ
    e.previous,  -- ✅ AJOUTÉ
    e.country,
    ...
```

---

## 📊 RÉSULTATS APRÈS CORRECTION

### Pour 1er août 2025

**Avant** :
- 7 événements avec estimate
- 3 événements sans baseline (estimate=N/A, previous non disponible)

**Après** :
- 7 événements utilisent `estimate`
- 3 événements utilisent `previous` (fallback) ✅
- 0 événements sans baseline ✅

**Détails** :
- Government Payrolls : utilise `previous=11.0` ✅
- Participation Rate : utilise `previous=62.3` ✅
- U-6 Unemployment Rate : utilise `previous=7.7` ✅

---

## ✅ VALIDATION

### Impact sur les Calculs

**Avant** :
- Surprise = 0.0 pour événements sans estimate
- Score ajusté = score base (pas d'ajustement)
- Direction = +1 par défaut (surprise = 0)

**Après** :
- Surprise calculée avec `previous` comme baseline ✅
- Score ajusté selon surprise réelle ✅
- Direction calculée selon surprise signée ✅

---

## 📋 STATISTIQUES

### Pour 1er août 2025

| Type Baseline | Nombre | Pourcentage |
|---------------|--------|-------------|
| Estimate | 7 | 70% |
| Previous (fallback) | 3 | 30% |
| Forecast (fallback) | 0 | 0% |
| Sans baseline | 0 | 0% ✅ |

---

## ✅ STATUS

**Problème** : ✅ Identifié (colonnes forecast/previous manquantes)  
**Correction** : ✅ Appliquée (colonnes ajoutées à la requête)  
**Validation** : ✅ Vérifiée (fallback fonctionne correctement)

---

_Date création : Correction fallback estimate_  
_Conclusion : Fallback estimate/forecast/previous fonctionne maintenant correctement_




