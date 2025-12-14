# Réponse : Le Planificateur prédit-il correctement la direction ?

**Date** : 2025-12-07

---

## ⚠️ Constat Important

### La Formule Linéaire : Amplitude Uniquement

La fonction `calculate_impact_linear()` que nous avons intégrée retourne **seulement l'amplitude** (en pips, valeur absolue), **pas la direction**.

```python
def calculate_impact_linear(...) -> float:
    """
    Returns:
        float: Impact prédit en pips (valeur absolue, minimum 0.0)
    """
    return max(abs(impact), 0.0)  # ← Valeur absolue seulement
```

---

## 🔍 Comment la Direction est Actuellement Gérée

### 1. Dans le Planificateur V3.2

La direction est un **paramètre** passé aux fonctions de prédiction :

```python
def predict_double_wave_base(
    df_events: pd.DataFrame,
    baseline_price: Optional[float] = None,
    direction: str = 'UP',  # ← Paramètre avec défaut 'UP'
    ...
) -> Dict:
```

### 2. Détermination de la Direction

**À VÉRIFIER** : Comment la direction est-elle déterminée avant d'appeler ces fonctions ?

Options possibles :
1. **Depuis le pattern détecté** (cache) - si disponible
2. **Depuis les événements** - en utilisant `get_event_direction()`
3. **Par défaut** - souvent 'UP'

---

## ✅ Méthode Correcte pour Calculer la Direction

### Utiliser `get_event_direction()`

Il existe une fonction qui calcule la direction selon :

- **Type de famille d'événement** (inversé ou normal)
- **Signe de la surprise** (positive ou négative)

**Logique** :

```python
FAMILY_SENTIMENT = {
    # INVERSÉ : Surprise+ = BAD for USD → EUR/USD UP
    'Jobless_Claims': -1,
    'CPI': 1,  # ⚠️ CPI = +1 (inflation plus forte = BAD pour EUR)
    
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
        # Logique inverse pour surprise négative
        ...
```

**Exemples** :
- CPI surprise +2.0% → direction = **+1 (EUR/USD UP)** si sentiment = -1
- NFP surprise +100K → direction = **-1 (EUR/USD DOWN)** ✅
- Jobless Claims +28K → direction = **+1 (EUR/USD UP)** ✅

---

## 📋 Recommandation

### Pour une Prédiction Correcte de la Direction

1. ✅ **Calculer la direction** pour chaque événement avec `get_event_direction()`
2. ✅ **Pour événements multiples** : Utiliser la **somme vectorielle** des directions
3. ✅ **Combiner** avec l'impact de la formule linéaire :
   - Impact amplitude = `calculate_impact_linear(...)` (valeur absolue)
   - Direction = `get_event_direction(...)` (signe)
   - Impact directionnel final = `amplitude * direction`

---

## ⚠️ Validation Nécessaire

### Points à Vérifier

1. **Comment la direction est-elle actuellement calculée** dans le Planificateur ?
2. **La fonction `get_event_direction()` est-elle utilisée** ?
3. **La direction est-elle validée** sur des dates de test connues ?

---

## 🎯 Conclusion

### Réponse à la Question

**Le Planificateur peut prédire la direction**, mais il faut **vérifier** :
- ✅ Si `get_event_direction()` est utilisée correctement
- ✅ Si la direction est combinée correctement avec l'amplitude
- ✅ Si la direction est validée sur des cas réels

**La formule linéaire que nous avons intégrée calcule l'amplitude**, mais **la direction doit être calculée séparément** et combinée avec l'amplitude pour avoir une prédiction complète.

---

## 📝 Prochaines Étapes

1. **Analyser** le code actuel du Planificateur pour voir comment la direction est déterminée
2. **Vérifier** si `get_event_direction()` est utilisée
3. **Valider** la direction sur quelques dates de test connues
4. **Documenter** ou **corriger** si nécessaire

---

**Status** : ⏳ **Nécessite vérification du code actuel pour réponse définitive**


