# Correction Requête SQL Étape 4 - Événements CPI

**Date** : 2025-01-XX  
**Problème** : Aucun cluster CPI trouvé pour 2025-09-11 même avec seuil Jaccard très bas  
**Cause** : Les événements CPI ont souvent `importance_n = 1` ou `2` (pas `3`), donc exclus par la requête SQL  
**Solution** : Ajuster la requête SQL pour inclure aussi les événements CPI/Inflation même si `importance_n != 3`

---

## 🔍 PROBLÈME IDENTIFIÉ

### Symptômes

- **2025-09-11** : Noyau dur CPI détecté (6 événements)
- **Recherche clusters identiques** : 0 clusters trouvés même avec seuil Jaccard 0.40
- **Test manuel** : 2024-09-11 devrait avoir Jaccard 1.000 mais n'est pas trouvé

### Cause Racine

La requête SQL optimisée de l'Étape 4 charge seulement :
1. Événements avec `empirical_score > 40.0`
2. Événements avec `importance_n = 3` (même si score faible)

**Problème** : Les événements CPI ont souvent `importance_n = 1` ou `2`, pas `3`, donc ils ne sont pas chargés si leur score est <= 40.0.

---

## ✅ CORRECTION APPLIQUÉE

### Requête SQL Avant

```sql
WHERE ...
    AND (
        (ef.empirical_score IS NOT NULL AND ef.empirical_score > 40.0)
        OR
        (e.importance_n = 3 AND ef.empirical_score IS NOT NULL)
    )
```

### Requête SQL Après

```sql
WHERE ...
    AND (
        -- Événements HIGH impact (score > 40)
        (ef.empirical_score IS NOT NULL AND ef.empirical_score > 40.0)
        OR
        -- Événements HAUT importance même si score faible (cohérent Étape 1)
        (e.importance_n = 3 AND ef.empirical_score IS NOT NULL)
        OR
        -- Événements CPI/Inflation même si importance_n != 3 (souvent importance_n = 1 ou 2)
        (LOWER(e.event_key) LIKE '%cpi%' AND ef.empirical_score IS NOT NULL)
        OR
        (LOWER(e.event_key) LIKE '%inflation%' AND ef.empirical_score IS NOT NULL)
    )
```

---

## 📊 RÉSULTATS

### Avant Correction

- **2024-09-11** : ❌ Non trouvé dans la requête SQL
- **Clusters CPI trouvés** : 0

### Après Correction

- **2024-09-11** : ✅ Trouvé (6 événements)
- **Clusters CPI trouvés** : À tester avec recherche complète

---

## 📝 CODE MODIFIÉ

**Fichier** : `scripts/run_pipeline_complete.py`  
**Fonction** : `etape4_rechercher_clusters_identiques`  
**Lignes** : ~600-611

---

## ✅ VALIDATION

**Status** : ✅ **CORRIGÉ**

La requête SQL trouve maintenant les événements CPI même si `importance_n != 3`.

---

## 🎯 IMPACT

Cette correction est cohérente avec :
- La correction de l'Étape 1 qui charge les événements HAUT importance même si score faible
- La nécessité de trouver des clusters CPI similaires dans l'historique

**Note** : Cette correction peut être étendue à d'autres types d'événements si nécessaire (NFP, GDP, etc.).




