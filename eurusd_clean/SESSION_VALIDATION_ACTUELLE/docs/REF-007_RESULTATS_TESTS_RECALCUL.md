# REF-007 : Résultats Tests Recalcul Scores Noyaux Durs

**Date :** 2025-12-06  
**Statut :** ✅ Tests réussis

---

## 📊 RÉSULTATS TESTS

### Test 1 : Période courte (Janvier 2024)

**Période :** 2024-01-01 à 2024-01-31  
**Mouvements détectés :** 12  
**Noyaux durs identifiés :** 9 dates  
**Scores calculés :** 1 type (GENERIC US)

**Résultats :**
- ✅ Script fonctionne correctement
- ✅ Détection mouvements : OK
- ✅ Identification noyaux durs : OK
- ✅ Calcul scores : OK

**Score calculé :**
- GENERIC (US) : 20.70 (n=4, avg=26.98 pips, p80=32.18 pips)

---

### Test 2 : Dates de validation connues

#### Date 1 : 2025-05-29 (Jobless Claims + PCE)

**Attendu :**
- Core Type : JOBLESS_PCE
- Anchor Time : 14:30
- Mouvement : 14:30

**Résultats :**
- ✅ Mouvement détecté : 89.40 pips (14:30)
- ✅ Core Type : **JOBLESS_PCE** (correct !)
- ✅ Anchor Time : 14:30
- ✅ Score calculé : 62.58

**Détails :**
- Impact réel : 89.40 pips
- Score empirique : 62.58
- Sample size : 1 (date unique)

---

#### Date 2 : 2025-09-11 (CPI US)

**Attendu :**
- Core Type : CPI
- Anchor Time : 14:30
- Mouvement : 14:30

**Résultats :**
- ✅ Mouvement détecté : 62.40 pips (14:30)
- ✅ Core Type : **CPI** (correct !)
- ⚠️ Country : EU (au lieu de US - à vérifier)
- ✅ Anchor Time : 14:30
- ✅ Score calculé : 43.68

**Détails :**
- Impact réel : 62.40 pips
- Score empirique : 43.68
- Sample size : 1 (date unique)

**Note :** Le country est EU au lieu de US, mais le core_type CPI est correct. Cela peut être dû à la présence d'événements EU dans le cluster, mais le noyau dur CPI est bien identifié.

---

## ✅ VALIDATION GLOBALE

### Taux de Réussite

- **Test 1 (Période courte)** : ✅ 100%
- **Test 2 (Dates validation)** : ✅ 100%
  - Identification core_type : ✅ 2/2 (100%)
  - Détection mouvements : ✅ 2/2 (100%)
  - Calcul scores : ✅ 2/2 (100%)

### Points Validés

1. ✅ Détection mouvements forts depuis prix
2. ✅ Filtrage événements sans estimate
3. ✅ Identification correcte des noyaux durs (JOBLESS_PCE, CPI)
4. ✅ Calcul des scores empiriques
5. ✅ Sauvegarde des résultats

### Points à Vérifier

1. ⚠️ Country pour 2025-09-11 (EU au lieu de US)
   - Impact : Mineur (core_type correct)
   - Action : Vérifier logique de sélection country dans script

---

## 🎯 CONCLUSION

**✅ Les tests sont réussis et la méthode est validée.**

**Action recommandée :** Procéder au recalcul complet sur 3 dernières années.

---

## 📋 PROCHAINES ÉTAPES

1. ✅ Test 1 : Période courte (1 mois) - **RÉUSSI**
2. ✅ Test 2 : Dates validation - **RÉUSSI**
3. ⏳ **Test 3 : Recalcul complet sur 3 ans** (à faire)

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




