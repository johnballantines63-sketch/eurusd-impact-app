# REF-036 : Amélioration Détection Début Mouvement FORT

**Date :** 2025-12-06  
**Problème :** La détection du début du mouvement était trop précoce (≥5 pips)  
**Référence :** REF-035

---

## 🔍 PROBLÈME IDENTIFIÉ

### Avant Correction

**Méthode :** Première bougie avec mouvement ≥5 pips

**Exemple 2025-04-10 :**
- Début détecté : **13:30** (5.4 pips)
- Mouvement FORT réel : **14:30** (visible sur graphique)
- Anchor time : **14:30**
- Coïncidence : ❌ NON (différence 60 min)

**Problème :** Détecte des petits mouvements précocement, pas le mouvement FORT.

---

## ✅ CORRECTION IMPLÉMENTÉE

### Nouvelle Stratégie

**Méthode améliorée :**
1. Identifier le pic maximum (mouvement le plus fort)
2. Calculer seuil = **30% du pic maximum**
3. Minimum absolu : **10 pips** (pour être considéré comme mouvement FORT)
4. Remonter depuis le pic pour trouver la première bougie **≥seuil**

**Formule :**
```python
threshold_pips = max(max_pips * 0.30, 10.0)
# Chercher première bougie avec current_pips >= threshold_pips
```

---

## 📊 RÉSULTATS

### Test 2025-04-10

**Avant correction :**
- Début détecté : 13:30 (5.4 pips)
- Coïncidence : ❌ NON (60 min)

**Après correction :**
- Début détecté : **14:16** (20.4 pips, seuil = 30% de 59.4 pips = 17.8 pips)
- Pic maximum : 15:57 (59.4 pips)
- Coïncidence : ✅ **OUI** (14:16 dans fenêtre ±15 min de 14:30)

**Conclusion :** ✅ **Correction fonctionne**

---

## 🎯 IMPACT

### Amélioration de la Coïncidence

**Avant :**
- Détection trop précoce → Coïncidence incorrecte
- Dates GENERIC exclues à tort

**Après :**
- Détection du mouvement FORT → Coïncidence correcte
- Meilleure validation des clusters

---

## 📋 FICHIERS MODIFIÉS

1. **`filter_dates_with_event_coincidence.py`**
   - Fonction `detect_movement_start` améliorée

2. **`test_generic_dates_after_correction.py`**
   - Fonction `detect_movement_start` améliorée

3. **`verify_movement_detection_2025_04_10.py`**
   - Script de vérification créé

---

## ✅ VALIDATION

### Test 2025-04-10

- ✅ Début mouvement FORT détecté : 14:16
- ✅ Coïncidence avec anchor_time 14:30 : OUI
- ✅ Fenêtre ±15 min : 14:01 - 14:31

**Conclusion :** La correction améliore significativement la détection du début du mouvement FORT.

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




