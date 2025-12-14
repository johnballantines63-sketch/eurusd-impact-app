# Problème Identifié : Biais vers UP

**Date** : 2025-12-07

---

## 🔍 Problème Principal

### Accuracy Directionnelle : 64.0%

- **UP réel** : 85.7% accuracy ✅
- **DOWN réel** : 36.4% accuracy ❌
- **13 cas** DOWN réel → UP prédit (sur 22 DOWN réels)

---

## 🚨 Cause Identifiée

### 1. Surprise Nulle = Direction UP par Défaut

Dans `get_event_direction()` (ligne 784-785) :

```python
# Si surprise nulle, direction neutre (défaut +1)
if abs(surprise) < 0.01:
    return 1  # ← TOUJOURS UP !
```

**Problème** : Quand surprise ≈ 0, la fonction retourne **toujours +1 (UP)**.

### 2. Conséquence

- Beaucoup d'événements ont `surprise = 0.00`
- Tous ces événements contribuent **+1** à la somme vectorielle
- Cela crée un **biais systématique vers UP**
- Les cas DOWN réels sont souvent prédits comme UP

### 3. Exemple Observé

**Date 2025-10-29** (DOWN réel → UP prédit) :
- 1 événement : Fed Interest Rate Decision
- Surprise : +0.00
- Direction calculée : UP (par défaut)
- Direction réelle : DOWN

**Date 2025-01-15** (DOWN réel → UP prédit) :
- 11 événements CPI
- Beaucoup avec surprise = 0.00 → tous contribuent +1
- Somme vectorielle : +5 → Direction UP
- Direction réelle : DOWN

---

## ✅ Solution Proposée

### Option 1 : Exclure Événements avec Surprise Nulle

```python
# Si surprise nulle, ne pas contribuer à la direction
if abs(surprise) < 0.01:
    return 0  # Neutre, ne contribue pas
```

### Option 2 : Utiliser Direction depuis Pattern Historique

Si surprise nulle, utiliser la direction depuis le pattern historique (cache) au lieu de UP par défaut.

### Option 3 : Améliorer Calcul de Surprise

S'assurer que la surprise est calculée correctement même pour les événements où actual ≈ estimate.

---

## 📋 Actions Immédiates

1. **Corriger** `get_event_direction()` pour gérer surprise nulle
2. **Re-tester** sur les 50 dates
3. **Vérifier** amélioration accuracy directionnelle
4. **Objectif** : ≥ 80% accuracy

---

**Status** : 🔍 **Cause identifiée - Correction requise**


