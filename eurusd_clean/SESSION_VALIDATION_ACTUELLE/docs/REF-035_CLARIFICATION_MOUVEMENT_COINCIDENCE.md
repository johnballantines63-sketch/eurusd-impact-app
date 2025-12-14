# REF-035 : Clarification - Colonne Mouvement et Coïncidence

**Date :** 2025-12-06  
**Question :** Que représente la colonne "Mouvement" et que signifie "Coïncidence" ?

---

## 📊 CLARIFICATION

### 1. Colonne "Mouvement"

**Définition :** Représente le **DÉBUT du mouvement** détecté par l'algorithme.

**Méthode de détection actuelle :**
- Baseline : 13:30 (OPEN première bougie après 13:30)
- Seuil : Première bougie avec mouvement ≥5 pips
- Résultat : 13:30 (5.4 pips) pour 2025-04-10

**Problème identifié :**
- Le graphique montre un mouvement **FORT** à **14:30** (grande bougie rouge)
- Mais l'algorithme détecte le début à **13:30** (petit mouvement de 5.4 pips)
- Le vrai mouvement fort commence à **14:30**, pas à 13:30

**Conclusion :**
- La colonne "Mouvement" représente le **début détecté** (première bougie ≥5 pips)
- Mais ce n'est **pas nécessairement** le début du mouvement **FORT**
- Pour 2025-04-10, le début du mouvement FORT est à **14:30**, pas 13:30

---

### 2. "Coïncidence"

**Définition :** Vérifie si l'`anchor_time` du cluster est dans une fenêtre de **±15 minutes** autour du début du mouvement détecté.

**Formule :**
```
Coïncidence = (mouvement - 15 min) ≤ anchor_time ≤ (mouvement + 15 min)
```

**Exemple 2025-04-10 :**
- Début mouvement détecté : **13:30**
- Anchor time cluster : **14:30**
- Fenêtre coïncidence : **13:15 - 13:45** (±15 min autour de 13:30)
- **Résultat :** ❌ PAS DE COÏNCIDENCE (différence 60 minutes)

**Problème :**
- Si le début détecté est à 13:30 mais le mouvement FORT est à 14:30
- Et l'anchor_time est à 14:30
- Alors il **devrait y avoir coïncidence** (14:30 est le vrai début du mouvement fort)
- Mais l'algorithme dit "pas de coïncidence" car il compare avec 13:30

---

## 🔍 PROBLÈME IDENTIFIÉ

### Détection du Début Trop Précoce

**Problème :** L'algorithme détecte le début à 13:30 (petit mouvement 5.4 pips) au lieu de 14:30 (mouvement fort).

**Pourquoi ?**
- Seuil trop bas : 5 pips détecte des petits mouvements
- Ne distingue pas entre petit mouvement et mouvement FORT

**Impact :**
- Coïncidence incorrecte : 14:30 n'est pas dans ±15 min de 13:30
- Mais 14:30 **est** le vrai début du mouvement fort
- Donc la coïncidence devrait être **OUI**, pas NON

---

## ✅ SOLUTION PROPOSÉE

### Améliorer la Détection du Début du Mouvement

**Option 1 : Seuil Plus Élevé**
- Utiliser seuil ≥10 pips au lieu de ≥5 pips
- Détecte seulement les mouvements significatifs

**Option 2 : Détection du Mouvement FORT**
- Identifier le pic maximum d'abord
- Remonter pour trouver le début du mouvement FORT (≥30% du pic)
- Ignorer les petits mouvements avant

**Option 3 : Détection Multi-Seuils**
- Détecter premier mouvement ≥5 pips (début précoce)
- Détecter mouvement ≥10 pips (début significatif)
- Utiliser le mouvement significatif pour coïncidence

---

## 📋 RECOMMANDATION

### Pour la Coïncidence

**Utiliser le début du mouvement FORT** (pas juste le premier mouvement ≥5 pips) :
1. Identifier le pic maximum
2. Calculer 30% du pic comme seuil
3. Remonter depuis le pic pour trouver la première bougie ≥seuil
4. Utiliser ce début pour vérifier la coïncidence

**Avantages :**
- Détecte le vrai début du mouvement fort
- Coïncidence plus précise
- Meilleure validation des clusters

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




