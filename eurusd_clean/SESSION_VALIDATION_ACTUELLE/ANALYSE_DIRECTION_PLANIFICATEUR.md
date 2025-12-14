# Analyse : Prédiction de Direction dans le Planificateur

**Date** : 2025-12-07  
**Question** : Le Planificateur prédit-il correctement la direction (UP/DOWN) des mouvements ?

---

## ⚠️ Point Important Découvert

### Formule Linéaire : Amplitude Uniquement

La fonction `calculate_impact_linear()` que nous avons intégrée retourne **seulement l'amplitude** (en pips, valeur absolue), **pas la direction**.

```python
def calculate_impact_linear(...) -> float:
    """
    Returns:
        float: Impact prédit en pips (valeur absolue, minimum 0.0)
    """
    # ...
    return max(abs(impact), 0.0)  # ← Valeur absolue seulement
```

---

## 🔍 Comment la Direction est Calculée

### 1. Dans les Formules Validées

Il existe une fonction `get_event_direction()` qui calcule la direction selon :

- **Type de famille d'événement** (inversé ou normal)
- **Signe de la surprise** (positive ou négative)

**Exemple de logique** :

```python
FAMILY_SENTIMENT = {
    # INVERSÉ : Surprise+ = BAD for USD → EUR/USD UP
    'Jobless_Claims': -1,
    'CPI': -1,
    
    # NORMAL : Surprise+ = GOOD for USD → EUR/USD DOWN
    'NFP': 1,
    'GDP': 1,
    # ...
}

def get_event_direction(family, surprise):
    sentiment = FAMILY_SENTIMENT.get(family, 1)
    
    if surprise > 0:
        if sentiment == -1:  # Inversé
            return 1   # EUR/USD UP
        else:  # Normal
            return -1  # EUR/USD DOWN
    else:
        if sentiment == -1:  # Inversé
            return -1  # EUR/USD DOWN
        else:  # Normal
            return 1   # EUR/USD UP
```

**Exemples** :
- CPI surprise +2.0% → direction = +1 (EUR/USD UP) ✅
- NFP surprise +100K → direction = -1 (EUR/USD DOWN) ✅
- Jobless Claims +28K → direction = +1 (EUR/USD UP) ✅

### 2. Dans le Planificateur Actuel

**À VÉRIFIER** : Comment le Planificateur calcule-t-il la direction actuellement ?

Le Planificateur peut utiliser :
1. La direction depuis le pattern détecté (cache)
2. La direction depuis les événements (si disponible)
3. Une direction par défaut ('UP')

---

## ✅ Recommandation : Valider la Direction

Pour que le Planificateur prédise correctement la direction, il faut :

1. ✅ **Calculer la direction** avec `get_event_direction()` basée sur :
   - Famille d'événement
   - Surprise (actual - estimate)

2. ✅ **Pour événements multiples** : Utiliser la **somme vectorielle** des directions

3. ✅ **Combiner** avec l'impact de la formule linéaire :
   - Impact = `calculate_impact_linear(...)` (amplitude)
   - Direction = `get_event_direction(...)` (signe)
   - Impact directionnel = `impact * direction`

---

## 📋 Prochaines Étapes

1. **Vérifier** comment la direction est actuellement calculée dans le Planificateur
2. **S'assurer** que `get_event_direction()` est utilisée correctement
3. **Valider** la direction sur quelques dates de test connues
4. **Documenter** la méthode de calcul de direction

---

## ⚠️ Note Importante

La formule linéaire valide **l'amplitude** de l'impact, mais **ne valide pas la direction**.

La direction doit être validée séparément avec une méthode appropriée (analyse des mouvements réels vs prédits).

---

**Status** : ⏳ **Analyse en cours - Nécessite vérification du code actuel**


