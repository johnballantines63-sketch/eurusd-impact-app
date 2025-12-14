# Résumé Validation avec Direction

**Date** : 2025-12-07  
**Dates testées** : 50 dates significatives

---

## 📊 Résultats

### Amplitude

- **MAE moyen** : 50.34 pips
- **MAE médian** : 49.60 pips
- **Ratio médian** : 2.609
- **Corrélation** : -0.102

### Direction ⭐ NOUVEAU

- **Accuracy directionnelle** : **64.0%** ⚠️
- **Directions correctes** : 32 / 50

### Détails par Direction

| Direction Réelle | Cas | Corrects | Accuracy |
|------------------|-----|----------|----------|
| **UP** | 28 | 24 | **85.7%** ✅ |
| **DOWN** | 22 | 8 | **36.4%** ❌ |

---

## ⚠️ Problème Critique

### Biais vers UP

- **59% des DOWN réels** sont prédits comme UP
- **13 cas** DOWN → UP (sur 22 DOWN réels)
- **Accuracy DOWN** : 36.4% (inacceptable)

### Causes Probables

1. **Surprise incorrecte** : Calcul de surprise signée peut être erroné
2. **Famille incorrecte** : Mapping famille peut échouer
3. **Sentiment incorrect** : FAMILY_SENTIMENT peut être incomplet
4. **Somme vectorielle** : Annulation incorrecte entre événements

---

## 📋 Actions Requises

1. **Analyser** les 13 cas DOWN → UP pour identifier la cause
2. **Corriger** le problème (surprise, famille, ou sentiment)
3. **Re-tester** pour valider l'amélioration
4. **Objectif** : ≥ 80% accuracy directionnelle

---

**Status** : ⚠️ **Problème identifié - Analyse en cours**


