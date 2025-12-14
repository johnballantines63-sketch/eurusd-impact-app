# Plan d'Action - Suite du Travail

**Date** : 2025-01-XX  
**Statut** : ✅ Corrections Zone 4a et script investigation terminées

---

## ✅ CE QUI A ÉTÉ FAIT

### 1. Clarification Prédiction vs Détection
- ✅ Identifié que 0.00 pips d'erreur = pattern détecté (pas vraie prédiction)
- ✅ Analysé vraie performance formules (erreur moyenne 367.25 pips)
- ✅ Documenté dans `RAPPORT_FINAL_COMPLET.md`

### 2. Corrections Amplification
- ✅ Corrigé Zone 4a (100-200%) : Limite à 3x max
- ⚠️ Zone 4b (> 200%) reste trop agressive (à corriger)

### 3. Vérification DB
- ✅ Confirmé DB correcte (Finnhub prix + événements)
- ✅ Identifié table `economic_events` (JBlanked) à supprimer (optionnel)

### 4. Correction Scripts
- ✅ Corrigé script investigation (utilise `event_title` au lieu de `name`)

---

## 🎯 PROCHAINES ÉTAPES PRIORITAIRES

### Priorité 1 : Corriger Zone 4b (> 200%)

**Problème** : Zone 4b trop agressive pour surprises > 200%
- Exemple : 2025-08-01 (266.7%) → 6.179x au lieu de 0.751x nécessaire

**Solution proposée** :
1. **Option A** : Limiter amplification maximale globale à 3x
2. **Option B** : Ajuster Zone 4b pour commencer plus bas (2.0x au lieu de 5.5x)
3. **Option C** : Utiliser amplification nécessaire comme référence si prédite > nécessaire × 2

**Action** : Implémenter Option A (plus simple et efficace)

---

### Priorité 2 : Corriger Timings Wave2 Peak

**Problème** : Pour certaines dates, `wave2_peak_time` utilise le pic réel au lieu de T+15
- Exemples : 2025-06-23 (T+310), 2025-10-10 (T+190), 2025-11-26 (T+115)

**Solution** : S'assurer que pour `DOUBLE_WAVE` avec `timings_predicted=True`, on utilise toujours `wave2_peak_time_predicted` (T+15)

**Action** : Vérifier code `scripts/run_pipeline_complete.py` lignes 2116-2120

---

### Priorité 3 : Tester Corrections

**Actions** :
1. Tester Zone 4b corrigée sur dates problématiques (2025-08-01, 2025-11-20, 2025-05-29)
2. Vérifier timings Wave2 peak sur toutes les dates
3. Comparer erreurs avant/après corrections

---

### Priorité 4 : Nettoyage Optionnel

**Action** : Supprimer table `economic_events` (JBlanked) pour DB 100% Finnhub
- Script : `SESSION_VALIDATION_ACTUELLE/scripts/cleanup_jblanked_from_db.py`
- Non critique (pipeline n'utilise pas cette table)

---

## 📋 ORDRE D'EXÉCUTION RECOMMANDÉ

1. **Corriger Zone 4b** (Priorité 1)
2. **Tester Zone 4b** sur dates problématiques
3. **Corriger Timings Wave2 Peak** (Priorité 2)
4. **Tester Timings** sur toutes les dates
5. **Validation complète** avec toutes les corrections
6. **Documentation finale**

---

## 🎯 OBJECTIF FINAL

**Améliorer performance formules** :
- Réduire erreur moyenne de 367.25 pips à < 50 pips
- Atteindre 80%+ des dates avec erreur < 20 pips

**Timings parfaits** :
- Wave2 peak (T+15) : 100% parfait (0.00 min erreur)

---

**Dernière mise à jour** : 2025-01-XX  
**Prochaine étape** : Corriger Zone 4b




