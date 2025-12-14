# SESSION 128 - REPRISE APRÈS CORRECTION DB
**Date :** 12 novembre 2025  
**Statut :** 🔄 REPRISE après correction DB structure MASTER_PLAN

---

## 🎯 SITUATION ACTUELLE

### **Problème Résolu**
✅ **DB structure corrigée** - Table `events` maintenant conforme MASTER_PLAN :
- event_key avec ESPACES (match event_families) : `inflation rate_mom`
- ts_utc avec timezone
- importance_n numérique
- LEFT JOIN fonctionne → scores empiriques trouvés

### **Impact Correction**
- ✅ Script Session 115 ORIGINAL fonctionne : **MAE 0.35 pips** ✅✅✅
- ⚠️ TOUS les scripts Session 128 développés AVANT correction sont obsolètes
- ⚠️ Tests effectués Session 128 étaient erronés (mauvaise DB)

---

## 📋 PLAN DE REPRISE RATIONNEL

### **PHASE 1 : VALIDATION INFRASTRUCTURE** ⏰ 30 min

**Objectif :** S'assurer que correction DB n'a pas cassé d'autres scripts

**Actions :**
1. ✅ Tester script Session 115 ORIGINAL → **VALIDÉ (MAE 0.35 pips)**
2. ⏳ Tester script Session 113 (cluster isolé)
3. ⏳ Tester déduplication Session 113
4. ⏳ Tester formules validées Sessions 51-55
5. ⏳ Vérifier event_families accessible

**Critères succès :**
- Session 115 : MAE < 2 pips ✅
- Session 113 : MAE < 5 pips
- Déduplication : Retire doublons correctement
- Scores empiriques : Tous trouvés via LEFT JOIN

**Livrables :**
```
scripts/session128/validation_infrastructure.py
  → Test tous scripts critiques
  → Rapport validation (pass/fail)
```

---

### **PHASE 2 : VALIDATION MAPPING VARIANTES** ⏰ 30 min

**Objectif :** Vérifier que mapping Session 127 fonctionne avec nouvelle DB

**Actions :**
1. Tester `get_empirical_score_with_variants()` sur 11 septembre
2. Tester mapping avec nouveaux event_key (espaces)
3. Vérifier `strip_variant_suffix()` fonctionne correctement
4. Comparer scores : direct LEFT JOIN vs mapping Session 127

**Test critique :**
```python
# event_key DB : 'inflation rate_mom' (espaces)
# strip_variant_suffix('inflation rate_mom') → 'inflation rate'
# Chercher dans CSV : 'inflation rate' OU 'inflation_rate' ?
```

**Critères succès :**
- Mapping trouve 100% scores événements 11 septembre
- Scores identiques : LEFT JOIN = mapping Session 127
- Pas de régression vs Session 115 ORIGINAL

**Livrables :**
```
scripts/session128/test_mapping_with_new_db.py
  → Validation mapping Session 127 compatible nouvelle DB
```

---

### **PHASE 3 : NETTOYAGE SESSION 128** ⏰ 15 min

**Objectif :** Supprimer/archiver scripts obsolètes développés avant correction DB

**Actions :**
1. Identifier tous scripts Session 128 AVANT correction DB
2. Archiver dans `session128/archive_before_db_fix/`
3. Garder seulement :
   - `import_to_events_MASTERPLAN.py` ✅ (correction DB)
   - Scripts validation infrastructure (Phase 1-2)

**Scripts obsolètes à archiver :**
```
test_session115_ORIGINAL_adapted.py  (utilisait economic_events)
import_eodhd_corrected.py           (importait dans economic_events)
analyze_eodhd_source.py             (debug pré-correction)
debug_import_11sept.py              (debug pré-correction)
check_*.py                          (tous checks pré-correction)
```

**Livrables :**
```
session128/archive_before_db_fix/
  → Tous scripts obsolètes
  → README_ARCHIVE.md (pourquoi archivés)
```

---

### **PHASE 4 : REPRENDRE OBJECTIFS SESSION 128 ORIGINAUX** ⏰ 1h30

**Objectif :** Maintenant qu'infrastructure validée, reprendre plan Session 128 handoff

#### **4A. Tests Non-Régression Pipeline (30 min)**

**Actions :**
1. Tester pipeline calibration Session 125-126
2. Vérifier fonction amplification universelle
3. Tester sur 3 familles (CPI, NFP, GDP)

**Tests :**
```
scripts/session128/test_pipeline_nonregression.py
  → CPI : MAE < 5 pips
  → NFP : MAE < 5 pips
  → GDP : MAE < 10 pips
```

#### **4B. Intégration Planificateur V2.5 (1h)**

**Actions :**
1. Intégrer `get_empirical_score_with_variants()` dans Planificateur
2. Intégrer `calculate_amplification_from_r2()` (fonction universelle)
3. Remplacer amplifications fixes par dynamiques
4. Tests interface sur 3+ dates

**Critères :**
- Planificateur charge scores via mapping Session 127
- Fonction amplification universelle active
- Tests sur 11 septembre : MAE < 2 pips

---

### **PHASE 5 : DOCUMENTATION & HANDOFF** ⏰ 30 min

**Actions :**
1. Créer `SESSION_128_RAPPORT_FINAL.md`
2. Mettre à jour `MASTER_PLAN.md`
3. Créer `SESSION_129_HANDOFF.md`

**Contenu rapport :**
- Problème DB découvert et résolu
- Impact correction DB
- Validation infrastructure
- Objectifs Session 128 atteints
- Prochaines étapes Session 129

---

## 🎯 WORKFLOW SIMPLIFIÉ

```
┌─────────────────────────────────────────┐
│ PHASE 1 : Validation Infrastructure     │ 30 min
│ ✅ Session 115 OK (MAE 0.35)           │
│ ⏳ Session 113, formules, scores        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ PHASE 2 : Validation Mapping S127       │ 30 min
│ ⏳ Mapping compatible nouveaux keys     │
│ ⏳ Scores identiques LEFT JOIN vs map   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ PHASE 3 : Nettoyage Session 128         │ 15 min
│ ⏳ Archiver scripts obsolètes           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ PHASE 4 : Objectifs Session 128         │ 1h30
│ ⏳ Tests pipeline non-régression        │
│ ⏳ Intégration Planificateur V2.5       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ PHASE 5 : Documentation & Handoff       │ 30 min
│ ⏳ Rapport final Session 128            │
│ ⏳ Handoff Session 129                  │
└─────────────────────────────────────────┘

TOTAL : ~3h
```

---

## ⚠️ DÉCISIONS CRITIQUES

### **1. Scripts Session 128 pré-correction**
**Décision :** ARCHIVER (pas supprimer)
**Raison :** Documentation problème DB + historique debug

### **2. Ordre validation**
**Décision :** Infrastructure AVANT mapping AVANT objectifs
**Raison :** Éviter cascade échecs si base non solide

### **3. Tests non-régression**
**Décision :** OBLIGATOIRES avant continuer
**Raison :** Correction DB = changement fondamental structure

---

## 📊 ESTIMATION TOKENS

```
Phase 1 : 15k tokens (validation scripts)
Phase 2 : 15k tokens (tests mapping)
Phase 3 :  5k tokens (nettoyage)
Phase 4 : 40k tokens (pipeline + planificateur)
Phase 5 : 10k tokens (documentation)
──────────────────────────────────
TOTAL : 85k / 190k tokens (45%)
```

**Tokens déjà utilisés Session 128 :** 120k  
**Tokens restants :** 70k  
**Conclusion :** Reprendre en Session 129 si nécessaire

---

## 🚀 PROCHAINE ACTION IMMÉDIATE

**ACTION 1 : Valider infrastructure (Phase 1)**

```bash
# Tester Session 113 (cluster isolé)
cd scripts/session113
python test_cluster_isolé_11sept.py  # (s'il existe)

# Tester formules Sessions 51-55
cd scripts/session51
python test_formulas_validated.py  # (s'il existe)
```

**Si scripts n'existent pas** → Créer script validation infrastructure unifié :
```
scripts/session128/validate_all_infrastructure.py
  → Teste Session 115 ✅ (déjà fait)
  → Teste Session 113
  → Teste formules
  → Teste déduplication
  → Teste scores empiriques
```

---

## 📝 QUESTIONS POUR ANDRÉ

1. **Priorités :** Valider infrastructure OU direct objectifs Session 128 ?
2. **Tests :** Scripts validation infrastructure existent-ils déjà ?
3. **Temps :** Combien temps dispo Session 128 actuelle (finir ou reprendre S129) ?
4. **Mapping S127 :** Besoin test compatibilité nouveaux event_key (espaces) ?

---

**Auteur :** André Valentin avec Claude  
**Date :** 12 novembre 2025  
**Statut :** 🔄 PLAN REPRISE PRÊT - ATTENTE VALIDATION ANDRÉ
