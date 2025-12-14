# REF-033 : Correction Priorisation US/EU pour EUR/USD

**Date :** 2025-12-06  
**Problème :** La logique de sélection du cluster principal ne priorisait pas assez les événements US/EU pour EUR/USD  
**Référence :** REF-032

---

## 🔍 PROBLÈME IDENTIFIÉ

### Cas 2025-04-10

**Avant correction :**
- Cluster 11:15 (ECB Speech, EU, 1 événement) → **Sélectionné** ❌
- Cluster 14:30 (US HIGH, 9 événements) → Non sélectionné ❌
- Core Type : GENERIC
- Mouvement réel : 13:30-14:00 (57.10 pips)

**Problème :** Le cluster EU (11:15) était sélectionné au lieu du cluster US HIGH (14:30), alors que pour EUR/USD, on doit prioriser US/EU.

---

## ✅ CORRECTION IMPLÉMENTÉE

### Nouvelle Logique de Priorisation

**Bonus hiérarchique pour EUR/USD :**

1. **PRIORITÉ ABSOLUE** : Clusters avec événements US HIGH → **Bonus x2.0**
2. **PRIORITÉ ÉLEVÉE** : Clusters avec événements EU HIGH → Bonus x1.5
3. **PRIORITÉ MOYENNE** : Clusters avec événements US → Bonus x1.3
4. **PRIORITÉ FAIBLE** : Clusters avec événements EU → Bonus x1.2
5. **AUTRES** : Pas de bonus

**Formule :**
```python
score_qualite = score_qualite_base × bonus_us_eu
```

**Pays européens considérés :**
- EU, DE, FR, IT, ES, NL, BE, AT, PT, FI, IE, GR, CH, UK, GB

---

## 📊 RÉSULTATS

### Test 2025-04-10

**Après correction :**
- Cluster 11:15 (ECB Speech, EU, 1 événement) → Non sélectionné ✅
- Cluster 14:30 (US HIGH, 9 événements) → **Sélectionné** ✅
- Core Type : **CPI** (au lieu de GENERIC)
- Anchor Time : **14:30** ✅

**Score qualité :**
- Cluster 11:15 : score_base × 1.5 (EU HIGH) = score plus faible
- Cluster 14:30 : score_base × 2.0 (US HIGH) = **score plus élevé** ✅

**Conclusion :** ✅ **Correction fonctionne**

---

## 🎯 IMPACT ATTENDU

### Dates GENERIC Potentiellement Corrigées

Les dates GENERIC qui avaient le mauvais cluster sélectionné devraient maintenant :
1. Sélectionner le bon cluster (US/EU HIGH)
2. Avoir un meilleur core_type (CPI, NFP, etc. au lieu de GENERIC)
3. Améliorer les prédictions

**Dates à retester :**
- 2025-04-10 (corrigé : CPI au lieu de GENERIC)
- 2025-03-12
- 2024-11-08
- 2024-02-13
- 2025-06-23

---

## 📋 CODE MODIFIÉ

**Fichier :** `scripts/run_pipeline_complete.py`

**Section :** Sélection du cluster principal (lignes ~3182-3225)

**Changements :**
1. Ajout comptage événements EU (pays européens)
2. Bonus hiérarchique US/EU
3. Score qualité = score_base × bonus_us_eu
4. Log amélioré avec raison de priorité

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




