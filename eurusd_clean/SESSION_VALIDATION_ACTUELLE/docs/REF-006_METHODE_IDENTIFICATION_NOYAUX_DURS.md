# REF-006 : Méthode d'Identification des Noyaux Durs

**Date :** 2025-12-06  
**Référence :** Validation avant recalcul scores historiques  
**Statut :** ✅ Validé

---

## 🎯 OBJECTIF

Identifier correctement les noyaux durs (CPI, NFP, JOBLESS_PCE, etc.) avant de recalculer les scores historiques, en évitant les erreurs d'identification (ex. cluster 18:00 au lieu de 14:30 pour 2025-05-29).

---

## 📋 NOUVELLE APPROCHE VALIDÉE

### Processus en 4 Étapes

1. **Détecter mouvements forts depuis les prix**
   - Scanner prix historiques (fenêtre 14:00-20:00)
   - Identifier mouvements ≥ 20 pips
   - Extraire heure de début et pic

2. **Comparer avec événements économiques**
   - Chercher événements dans fenêtre temporelle (mouvement ± 30 min)
   - Correspondance mouvement ↔ événements

3. **Filtrer événements SANS estimate**
   - ⚠️ **CRITIQUE** : Exclure événements sans estimate (discours Fed, etc.)
   - Ces événements ne permettent pas de calculer une surprise
   - Donc pas de prédiction possible

4. **Identifier noyau dur**
   - Basé sur correspondance mouvement ↔ événements filtrés
   - Patterns : CPI, NFP, JOBLESS_PCE, GDP, JOBLESS, PCE, GENERIC

---

## 🔍 FILTRAGE ÉVÉNEMENTS SANS ESTIMATE

### Critères d'Exclusion

1. **Pas d'estimate valide**
   - `estimate`, `forecast`, `previous` tous `None` ou `NaN`
   - Aucune valeur de référence pour calculer surprise

2. **Patterns discours/statement**
   - Speech, Discours, Statement, Remarks
   - Fed Speech, ECB Speech, BOE Speech
   - Press Conference, Meeting Minutes
   - Beige Book

### Exemples d'Événements Exclus

- ❌ Fed Speech (pas d'estimate)
- ❌ ECB Press Conference (pas d'estimate)
- ❌ BOE Statement (pas d'estimate)
- ❌ Meeting Minutes (pas d'estimate)

### Exemples d'Événements Inclus

- ✅ CPI (avec estimate)
- ✅ NFP (avec estimate)
- ✅ Jobless Claims (avec estimate)
- ✅ PCE (avec estimate)

---

## 📊 RÉSULTATS VALIDATION

### Dates Testées

1. **2025-05-29** (Jobless Claims + PCE)
   - ✅ Mouvement détecté : 14:30
   - ✅ Anchor Time : 14:30
   - ✅ Core Type : JOBLESS_PCE
   - ✅ 9 événements avec estimate, 1 exclu (sans estimate)

2. **2025-09-11** (CPI US)
   - ✅ Mouvement détecté : 14:30
   - ✅ Anchor Time : 14:30
   - ✅ Core Type : CPI
   - ✅ 16 événements avec estimate

### Taux de Réussite

- **Mouvement correct** : 2/2 (100%)
- **Anchor Time correct** : 2/2 (100%)
- **Core Type correct** : 2/2 (100%)

**✅ VALIDATION COMPLÈTE**

---

## 🔧 IMPLÉMENTATION

### Script de Validation

**Fichier :** `SESSION_VALIDATION_ACTUELLE/scripts/validation_identification_noyaux_durs_v2.py`

**Fonctions Clés :**

1. `detect_strong_movements()` : Détecte mouvements forts depuis prix
2. `find_events_for_movement()` : Trouve événements correspondants (avec estimate)
3. `is_event_without_estimate()` : Filtre événements sans estimate
4. `identify_core_type_from_events()` : Identifie type noyau dur

### Patterns d'Exclusion

```python
EVENTS_WITHOUT_ESTIMATE_PATTERNS = [
    r'(?i)(speech|discours|statement|remarks|testimony|testifies)',
    r'(?i)(fed.*speech|ecb.*speech|boe.*speech)',
    r'(?i)(press conference|conference de presse)',
    r'(?i)(meeting minutes|compte-rendu)',
    r'(?i)(beige book|livre beige)',
]
```

---

## ✅ VALIDATION AVANT RECALCUL

**Conclusion :** La méthode d'identification est **validée** et **correcte**.

**Action :** On peut procéder au recalcul des scores historiques en utilisant cette méthode.

---

## 📝 PROCHAINES ÉTAPES

1. ✅ Valider méthode d'identification
2. ⏳ Créer script recalcul scores historiques (basé sur cette méthode)
3. ⏳ Tester recalcul sur dates de validation
4. ⏳ Appliquer recalcul sur 3 dernières années

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




