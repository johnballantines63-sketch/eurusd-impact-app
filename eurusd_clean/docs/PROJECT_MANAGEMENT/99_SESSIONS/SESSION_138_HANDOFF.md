# SESSION 137 → SESSION 138 - HANDOFF (MISE À JOUR CRITIQUE)

**Date :** 14 novembre 2025  
**Session complétée :** 137  
**Prochaine session :** 138  
**Statut Session 137 :** ✅ SUCCÈS PARTIEL + 🚨 DÉCOUVERTE CRITIQUE

---

## 🚨 ALERTE : PROBLÈME CRITIQUE IDENTIFIÉ

**Algorithme step3_classify_patterns.py est BIAISÉ BULLISH**

- **Mouvements UP (bullish) :** Classifications probablement OK (~50%)
- **Mouvements DOWN (bearish) :** Classifications COMPLÈTEMENT FAUSSES (~50%)
- **73 DOUBLE_WAVE détectés :** Majorité sont FAUX POSITIFS

**MISSION SESSION 138 CHANGÉE :**
Refonte complète algorithme détection patterns avec direction-awareness OBLIGATOIRE

---

## 🎉 CE QUI A ÉTÉ ACCOMPLI (SESSION 137)

### **ÉTAPES 2-3-4 Complétées**

1. ✅ **ÉTAPE 2 (2.0 → 2.4)** : 100% scores disponibles
   - 295 scores calculés et insérés dans event_families
   - 694 event_keys avec scores (2,467 total)
   - total_score ajouté pour 396 mouvements

2. ✅ **ÉTAPE 3** : Classification patterns (TECHNIQUE OK, CRITÈRES NOK)
   - 396 mouvements classifiés
   - ⚠️ Classifications invalides pour mouvements DOWN

3. ✅ **ÉTAPE 4** : Grouping patterns identiques
   - 4 groupes créés (≥3 cas)
   - 66 mouvements dans groupes

4. ✅ **Investigation hypothèse André**
   - Σ(MED) ≈ HIGH validé partiellement
   - Découverte corrélation nulle impact × total_score

5. ✅ **Vérification manuelle + Découverte critique**
   - Cas #310 analysé manuellement
   - Problème algorithme biaisé bullish identifié
   - Timezone calendrier = standard validé

### **Fichiers Créés (9 scripts production)**
```
step2_0_match_events.py
step2_1_check_scores.py
step2_2_calculate_missing_scores.py
step2_3_verify_scores.py
step2_4_enrich_csv_final.py
step3_classify_patterns.py              ⚠️ À CORRIGER
step4_group_patterns.py
investigate_medium_high_hypothesis.py
extract_price_details.py
```

---

## 🎯 OBJECTIF SESSION 138 (CHANGÉ)

**Mission principale :** Refonte algorithme détection patterns avec direction-awareness

**Workflow SESSION 138 :**
```
ÉTAPE 3-BIS (Session 138) : Refonte algorithme détection
    ↓
    1. Réécrire step3 avec direction-awareness
    2. Critères stricts (peak_min 20 pips, dip_ratio [0.30,0.70])
    3. Re-classifier 396 mouvements
    4. Vérification manuelle 20 cas
    5. Validation taux précision ≥80%
    ↓
ÉTAPE 4-BIS (si temps) : Re-grouping avec vraies classifications
```

**Critère de succès :**
- Algorithme direction-aware implémenté
- 396 mouvements re-classifiés
- 20 cas vérifiés manuellement
- Taux précision ≥80%

**Durée estimée :** 3-4h

---

## 🚨 PROBLÈME ALGORITHME DÉTAILLÉ

### **Code Actuel (INCORRECT)**

```python
# step3_classify_patterns.py (ligne ~140)
def classify_pattern(df_prices, baseline_price, impact_pips):
    # ❌ PROBLÈME : Cherche seulement pics dans HIGH
    peaks_idx = detect_peaks(df_prices['high'], window=5)
    
    # ❌ PROBLÈME : Calcule amplitudes montantes uniquement
    for idx in peaks_idx:
        peak_price = df_prices['high'].iloc[idx]
        amplitude_pips = (peak_price - baseline_price) * 10000
        # ↑ ASSUME toujours mouvement MONTANT !
    
    # ❌ PROBLÈME : Logique double wave assume UP
    if dip_ratio >= 0.30:  # Creux entre peaks
        return 'DOUBLE_WAVE'
```

### **Comportement sur Mouvements BEARISH**

**Exemple réel : Mouvement #310 (2025-04-23 15:14)**

**Mouvement réel (DOWN) :**
```
Baseline : 1.14063
Chute    : 1.13286 (-77.7 pips) ← Mouvement principal BEARISH
Recovery : 1.13656 (-40.7 pips depuis baseline)

Pattern réel = SINGLE_WAVE_FORT_DOWN + Recovery
```

**Ce que l'algorithme voit :**
```
"Peak1"  : 1.14127 (+6.4 pips)   ← Petit bruit insignifiant
"Trough" : 1.13286 (-77.7 pips)  ← Point le plus bas
"Peak2"  : 1.13656 (-40.7 pips)  ← Recovery partielle

dip_ratio = (1.14127 - 1.13286) / (1.14127 - 1.14063) = 1314% !!

Pattern détecté = DOUBLE_WAVE (FAUX !)
```

**Pourquoi c'est faux :**
- "Peak1" de 6 pips n'est pas le mouvement principal
- "Trough" est EN DESSOUS de baseline (pas un creux entre pics)
- dip_ratio >100% est absurde (creux plus grand que peak !)
- Pattern réel inversé complètement

### **Impact Global**

**Sur 396 mouvements :**
```
~200 UP   : Classifications probablement OK
~200 DOWN : Classifications FAUSSES
   → SINGLE_WAVE_DOWN mal classés DOUBLE_WAVE
   → DOUBLE_WAVE_DOWN non détectés
   → Patterns inversés
```

**Sur 73 DOUBLE_WAVE détectés :**
```
Vrais DOUBLE_WAVE_UP         :  5-10 cas (OK)
SINGLE_WAVE_DOWN mal classés : 50-60 cas (FAUX)
CRASH+RECOVERY mal classés   :  5-10 cas (FAUX)
```

---

## 🔧 SOLUTION DÉTAILLÉE

### **Architecture Correcte**

```python
def classify_pattern(df_prices, baseline_price, impact_pips, direction):
    """
    Classifier pattern mouvement avec direction-awareness
    
    Args:
        df_prices: DataFrame prix
        baseline_price: Prix référence
        impact_pips: Impact détecté ÉTAPE 1
        direction: "UP" ou "DOWN" (depuis step1)
    
    Returns:
        Dict: {pattern_type, métriques, confidence}
    """
    
    if direction == "UP":
        return classify_bullish_pattern(df_prices, baseline_price, impact_pips)
    elif direction == "DOWN":
        return classify_bearish_pattern(df_prices, baseline_price, impact_pips)
    else:
        return {'pattern_type': 'INCONNU', 'reason': 'direction_unknown'}
```

### **Logique BULLISH**

```python
def classify_bullish_pattern(df_prices, baseline_price, impact_pips):
    # 1. Détecter pics dans HIGH
    peaks_idx = detect_peaks(df_prices['high'], window=5)
    
    # 2. Premier pic (plus fort)
    peak1 = find_highest_peak(peaks_idx)
    peak1_amplitude = (peak1_price - baseline_price) * 10000
    
    # CRITÈRE STRICT : Peak1 minimum 20 pips
    if peak1_amplitude < 20.0:
        return {
            'pattern_type': 'SINGLE_WAVE_FAIBLE_UP',
            'reason': 'peak1_too_small'
        }
    
    # 3. Chercher deuxième pic APRÈS peak1
    peak2 = find_second_peak_after(peaks_idx, peak1)
    
    if peak2 exists:
        # 4. Trouver creux ENTRE peak1 et peak2
        trough = find_trough_between(peak1, peak2)
        
        # CRITÈRE STRICT : Trough doit être > baseline
        if trough_price < baseline_price:
            return {
                'pattern_type': 'CRASH_RECOVERY_UP',
                'reason': 'trough_below_baseline'
            }
        
        # 5. Calculer dip ratio
        dip_from_peak1 = (peak1_price - trough_price) * 10000
        dip_ratio = dip_from_peak1 / peak1_amplitude
        
        # CRITÈRE STRICT : dip_ratio entre 30-70%
        if 0.30 <= dip_ratio <= 0.70:
            return {
                'pattern_type': 'DOUBLE_WAVE_UP',
                'peak1_amplitude': peak1_amplitude,
                'peak2_amplitude': peak2_amplitude,
                'dip_ratio': dip_ratio,
                'confidence': 0.9
            }
    
    # 6. SINGLE_WAVE (pas de double wave)
    if peak1_amplitude >= 35.0:
        return {'pattern_type': 'SINGLE_WAVE_FORT_UP'}
    elif peak1_amplitude >= 15.0:
        return {'pattern_type': 'SINGLE_WAVE_STANDARD_UP'}
    else:
        return {'pattern_type': 'SINGLE_WAVE_FAIBLE_UP'}
```

### **Logique BEARISH**

```python
def classify_bearish_pattern(df_prices, baseline_price, impact_pips):
    # 1. Détecter creux dans LOW (inversé)
    troughs_idx = detect_troughs(df_prices['low'], window=5)
    
    # 2. Premier creux (plus fort) = équivalent peak1
    trough1 = find_lowest_trough(troughs_idx)
    trough1_amplitude = (baseline_price - trough1_price) * 10000  # Inversé !
    
    # CRITÈRE STRICT : Trough1 minimum 20 pips
    if trough1_amplitude < 20.0:
        return {
            'pattern_type': 'SINGLE_WAVE_FAIBLE_DOWN',
            'reason': 'trough1_too_small'
        }
    
    # 3. Chercher deuxième creux APRÈS trough1
    trough2 = find_second_trough_after(troughs_idx, trough1)
    
    if trough2 exists:
        # 4. Trouver pic ENTRE trough1 et trough2 (inversé)
        peak_between = find_peak_between(trough1, trough2)
        
        # CRITÈRE STRICT : Peak doit être < baseline
        if peak_between_price > baseline_price:
            return {
                'pattern_type': 'SPIKE_REVERSAL_DOWN',
                'reason': 'peak_above_baseline'
            }
        
        # 5. Calculer rise ratio (inversé de dip_ratio)
        rise_from_trough1 = (peak_between_price - trough1_price) * 10000
        rise_ratio = rise_from_trough1 / trough1_amplitude
        
        # CRITÈRE STRICT : rise_ratio entre 30-70%
        if 0.30 <= rise_ratio <= 0.70:
            return {
                'pattern_type': 'DOUBLE_WAVE_DOWN',
                'trough1_amplitude': trough1_amplitude,
                'trough2_amplitude': trough2_amplitude,
                'rise_ratio': rise_ratio,
                'confidence': 0.9
            }
    
    # 6. SINGLE_WAVE (pas de double wave)
    if trough1_amplitude >= 35.0:
        return {'pattern_type': 'SINGLE_WAVE_FORT_DOWN'}
    elif trough1_amplitude >= 15.0:
        return {'pattern_type': 'SINGLE_WAVE_STANDARD_DOWN'}
    else:
        return {'pattern_type': 'SINGLE_WAVE_FAIBLE_DOWN'}
```

### **Critères Stricts (TOUS OBLIGATOIRES)**

```python
# 1. Peak/Trough minimum (filtrer bruit)
MIN_AMPLITUDE = 20.0  # pips

# 2. Dip/Rise ratio valide (filtrer extrêmes)
MIN_DIP_RATIO = 0.30  # 30%
MAX_DIP_RATIO = 0.70  # 70%

# 3. Position trough/peak cohérente
# UP   : trough > baseline
# DOWN : peak < baseline

# 4. Direction depuis ÉTAPE 1 (step1 CSV)
# Utiliser colonne 'direction' existante
```

---

## 📋 PLAN D'ACTION SESSION 138

### **PHASE 1 : Réécriture Algorithme (90-120 min)**

**Fichier :** `step3_classify_patterns_v2.py`

**Actions :**
1. Copier step3_classify_patterns.py → step3_classify_patterns_v2.py
2. Ajouter paramètre `direction` à classify_pattern()
3. Implémenter classify_bullish_pattern() (60 lignes)
4. Implémenter classify_bearish_pattern() (60 lignes)
5. Ajouter critères stricts (MIN_AMPLITUDE, dip_ratio range)
6. Tester sur 3-5 mouvements manuellement

**Livrable :** step3_classify_patterns_v2.py testé

### **PHASE 2 : Re-Classification Complète (30 min)**

**Actions :**
1. Charger step1_scan_price_movements.csv (direction incluse)
2. Exécuter step3_v2 sur 396 mouvements
3. Créer step3_movements_with_patterns_v2.csv
4. Comparer distributions v1 vs v2

**Livrable :** step3_movements_with_patterns_v2.csv

### **PHASE 3 : Vérification Manuelle (60 min)**

**Actions :**
1. Sélectionner 20 mouvements aléatoires :
   - 5 DOUBLE_WAVE_UP
   - 5 DOUBLE_WAVE_DOWN
   - 5 SINGLE_WAVE_FORT_UP
   - 5 SINGLE_WAVE_FORT_DOWN

2. Pour chaque : Extraire prix avec extract_price_details.py

3. Vérifier visuellement sur MT5 ou via prix

4. Calculer taux précision

**Critère succès :** ≥80% précision

**Livrable :** validation_report_v2.txt

### **PHASE 4 : Documentation (30 min)**

**Actions :**
1. Créer SESSION_138_CLOTURE.md
2. Mettre à jour MASTER_PLAN.md (version 3.5)
3. Documenter taux précision
4. Préparer ÉTAPE 4-BIS si applicable

---

## 📁 FICHIERS À LIRE (ORDRE)

### **OBLIGATOIRE (30k tokens)**

```
1. /Users/.../SESSION_137_CLOTURE_FINAL.md
   → Comprendre problème algorithme détaillé
   → Section "DÉCOUVERTE CRITIQUE" mot par mot

2. /Users/.../step3_classify_patterns.py
   → Code actuel (à corriger)
   → Identifier lignes problématiques

3. /Users/.../step1_scan_price_movements.csv
   → Colonne 'direction' disponible (UP/DOWN)
   → Input pour step3_v2
```

### **RÉFÉRENCE**

```
4. /Users/.../step3_movements_with_patterns.csv
   → Classifications v1 (invalides) pour comparaison

5. /Users/.../extract_price_details.py
   → Outil vérification manuelle (réutilisable)
```

---

## ⚠️ POINTS D'ATTENTION CRITIQUES

### **1. Direction OBLIGATOIRE**

```python
# ❌ FAUX - assume mouvement montant
amplitude = (price - baseline) * 10000

# ✅ CORRECT - considère direction
if direction == "UP":
    amplitude = (price - baseline) * 10000
elif direction == "DOWN":
    amplitude = (baseline - price) * 10000
```

### **2. Position Trough/Peak Cohérente**

```python
# ❌ FAUX - accepte trough en dessous baseline
if dip_ratio >= 0.30:
    return 'DOUBLE_WAVE'

# ✅ CORRECT - vérifie position
if direction == "UP" and trough_price < baseline_price:
    return 'CRASH_RECOVERY'  # Pas DOUBLE_WAVE
if direction == "DOWN" and peak_price > baseline_price:
    return 'SPIKE_REVERSAL'  # Pas DOUBLE_WAVE
```

### **3. Peak/Trough Minimum**

```python
# ❌ FAUX - accepte bruit (6 pips)
peak1_amplitude = calculate_amplitude(peak1)

# ✅ CORRECT - filtre minimum
if peak1_amplitude < MIN_AMPLITUDE:  # 20 pips
    return 'SINGLE_WAVE_FAIBLE'
```

### **4. Dip Ratio Valide**

```python
# ❌ FAUX - accepte 1314%
if dip_ratio >= 0.30:
    return 'DOUBLE_WAVE'

# ✅ CORRECT - range strict
if 0.30 <= dip_ratio <= 0.70:
    return 'DOUBLE_WAVE'
else:
    return 'SINGLE_WAVE'  # Creux trop profond ou faible
```

---

## 💡 SI BLOQUÉ

### **Problème : Distribution bizarre patterns v2**

**Exemple :**
```
DOUBLE_WAVE_UP   :   5 (OK, ~0.5%)
DOUBLE_WAVE_DOWN :   5 (OK, ~0.5%)
SINGLE_WAVE_*    : 380 (OK, ~95%)
INCONNU          :   6 (OK, <2%)
```

**Si DOUBLE_WAVE > 20 cas :**
- Critères encore trop permissifs
- Augmenter MIN_AMPLITUDE à 30 pips
- Réduire MAX_DIP_RATIO à 0.60

### **Problème : Taux précision <80%**

**Actions :**
1. Analyser types erreurs (faux positifs/négatifs)
2. Ajuster seuils selon erreurs
3. Re-run classification
4. Re-vérifier échantillon

### **Problème : Timezone errors**

**Solution :**
- Calendrier = heure STANDARD
- Été : ajouter +1h
- Hiver : ajouter +0h
- Vérifier mois mouvement pour ajustement

---

## 📊 MÉTRIQUES SESSION 138

**Budget estimé :**
- Lecture problème : 10k tokens
- Phase 1 (réécriture) : 30-40k tokens
- Phase 2 (re-classification) : 10k tokens
- Phase 3 (vérification) : 20-30k tokens
- Phase 4 (documentation) : 15k tokens
- **Total :** ~85-105k / 190k tokens (45-55%)

**Livrables attendus :**
1. step3_classify_patterns_v2.py (~500 lignes)
2. step3_movements_with_patterns_v2.csv (396 lignes)
3. validation_report_v2.txt (20 cas vérifiés)
4. SESSION_138_CLOTURE.md

---

**Auteur :** André Valentin avec Claude  
**Date :** 14 novembre 2025  
**Tokens Session 137 :** 92,305 / 190,000 (49%)  
**Statut :** ✅ HANDOFF COMPLET - MISSION SESSION 138 REDÉFINIE
