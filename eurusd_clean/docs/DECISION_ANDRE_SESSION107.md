# ✅✅✅ DÉCISION ANDRÉ SESSION 107

**Date :** 3 novembre 2025  
**Décideur :** André Valentin  
**Session :** 107 - Phase 2 Cluster #3

---

## 🎯 CHOIX FINAL : OPTION B - R² INVERSION 🔬

### Citation André

> "peu importe si on doit valider sur échantillon plus large le but étant d'avoir la meilleure précision possible donc il faut qu'on teste plus en avant"

---

## 📊 OPTIONS ÉVALUÉES

### Option A : Session 101 (R² 72h fixe) ⭐⭐

**Formule :**
```python
amplification = 0.5490 × R²_72h + 1.6988
```

**Performance Cluster #3 :**
- MAE : 0.82 pips (vs 15.69 baseline)
- 95% amélioration
- Production-ready immédiatement

**Status :** Validée mais **NON CHOISIE** par André

---

### ✅ Option B : R² INVERSION (Phase 2E) ⭐⭐⭐ **CHOISIE**

**Formule à calibrer :**
```python
amplification = f(R²_inversion)  # À développer Session 108
```

**Avantages :**
- ✅ **Meilleure corrélation (+0.346)** de toutes les approches
- ✅ Capte vraies inversions (9 sept pour 11.09)
- ✅ Durées réalistes (35-119h)
- ✅ Concept validé empiriquement
- ✅ **Objectif : Précision maximale** (priorité André)

**Inconvénients acceptés :**
- ⚠️ Nécessite validation Cluster #1 (11 dates) → Session 108
- ⚠️ Formule régression à calibrer (17 dates total)

---

### Option C : Hybride (Non retenue pour l'instant)

**Approche :**
- R² Inversion si détectée avec qualité > seuil
- R² 72h sinon (fallback)

**Status :** Envisageable après tests Session 108

---

## 🚀 PLAN SESSION 108

### Mission

**Calibrer formule R² Inversion sur Cluster #1 + Cluster #3**

### Étapes

```python
1. Appliquer Phase 2E (Inversion) sur Cluster #1 (11 dates Manufacturing)
2. Mesurer R²_inversion + amp_optimal pour chaque date
3. Dataset combiné : 6 dates Cluster #3 + 11 dates Cluster #1 = 17 dates
4. Régression linéaire :
   amp_optimal = β0 + β1 × R²_inversion
5. Validation Leave-One-Out (LOOCV)
6. Calculer MAE sur 17 dates
7. Comparer vs baseline 2.5 (MAE 15.69)
8. Comparer vs Session 101 (MAE 0.82) [optionnel]
```

### Critères Succès

**SUCCÈS si :**
- MAE R² Inversion < MAE baseline 2.5 ✅
- Corrélation R² Inversion vs amp_optimal significative (p<0.05)
- Pas d'overfitting (ratio 17 dates / 2 paramètres = 8.5 OK)

**BONUS si :**
- MAE R² Inversion < MAE Session 101 (0.82 pips)

### Scripts à Utiliser

**Base :**
- `phase2e_cluster3_inversion_trend.py` (adapter pour Cluster #1)

**Nouveau :**
- `calibrate_inversion_formula.py` (régression 17 dates)
- `validate_inversion_loocv.py` (validation croisée)

---

## 📈 MÉTRIQUES ATTENDUES SESSION 108

**Objectif :**
- Formule R² Inversion calibrée
- MAE < 15.69 pips minimum
- MAE < 5 pips si possible
- Publication décision finale

**Budget :**
- Tokens restants : ~97,000
- Durée estimée : 2-3h

---

## 💡 RATIONALE CHOIX ANDRÉ

### Pourquoi R² Inversion ?

**1. Meilleure corrélation (+0.346)**
- Supérieure à R² 72h (+0.301)
- Supérieure à R² dynamique basique (+0.266)
- **Meilleur indicateur potentiel**

**2. Concept validé empiriquement**
- Capte pic 9 sept 05:55 (graphique André)
- Pas de parasites (vs Phase 2C)
- Durées réalistes

**3. Objectif précision maximale**
- André priorise précision sur facilité
- Validation étendue acceptable
- Recherche meilleure formule possible

**4. Échantillon 17 dates suffisant**
- 17 dates / 2 paramètres = ratio 8.5 ✅
- Pas d'overfitting attendu
- Statistiques robustes possibles

---

## 🔄 ALTERNATIVES SI ÉCHEC

**Si R² Inversion échoue Session 108 :**

**Plan B :** Retour à Session 101 (R² 72h)
- MAE 0.82 pips validé
- Production-ready
- Formule simple

**Plan C :** Baseline 2.5 fixe
- MAE 15.69 pips
- Simplicité maximale
- Déjà en production

**Plan D :** Hybride
- Inversion si qualité > seuil
- 72h sinon

---

## ✅ DOCUMENTATION MISE À JOUR

**Fichiers à corriger :**
- ✅ `DECISION_ANDRE_SESSION107.md` (ce fichier)
- ⏳ `SESSION107_RAPPORT_COMPLET.md` (section décision)
- ⏳ `PROJECT_STATE_NEW.md` (section Session 107)
- ⏳ `MESSAGE_SESSION107_SESSION108.md` (plan Session 108)

---

**Décision validée par André le 3 novembre 2025** ✅

**Prochaine session : Calibration R² Inversion sur 17 dates** 🚀
