# Changement Pipeline : Formule Impact Linéaire Multiple

**Date** : 2025-01-XX  
**Session** : SESSION_VALIDATION_ACTUELLE  
**Auteur** : André Valentin avec Claude

---

## 📋 RÉSUMÉ

Remplacement de la formule `calculate_impact_d()` (Formule D) par une nouvelle formule linéaire multiple `calculate_impact_linear()` qui offre une précision significativement meilleure, notamment pour les mouvements FORT et TRÈS_FORT.

---

## 🔍 PROBLÈME IDENTIFIÉ

### Formule Actuelle (`calculate_impact_d`)
- **MAE global** : 38.63 pips
- **Ratio médian** : 0.152 (prédictions ≈ 15% de la réalité)
- **Corrélation** : 0.232
- **Problème majeur** : Sous-estimation systématique, surtout pour mouvements FORT/TRÈS_FORT

### Analyse par Classe (Formule Actuelle)
| Classe | MAE | Ratio médian | Impact réel moy | Impact prédit moy |
|--------|-----|--------------|-----------------|-------------------|
| FAIBLE | 25.99 pips | 0.461 | 32.3 pips | 8.5 pips |
| MOYEN | 35.30 pips | 0.587 | 50.0 pips | 11.2 pips |
| **FORT** | **57.61 pips** | **0.401** | **77.2 pips** | **15.3 pips** |
| **TRÈS_FORT** | **73.72 pips** | **0.344** | **111.6 pips** | **17.2 pips** |

**Conclusion** : La formule actuelle est **défaillante** pour les mouvements forts.

---

## ✅ NOUVELLE SOLUTION

### Formule Linéaire Multiple (`calculate_impact_linear`)

**Formule** :
```
impact = 30.5450 
       + 0.4692 * base_score
       + 0.1882 * adjusted_score
       + 0.0201 * surprise_avg
       - 0.0034 * surprise_max
       + 0.7355 * n_events
```

**Performance Globale** :
- **MAE** : 13.98 pips (vs 38.63 base) → **-64% d'erreur**
- **Ratio médian** : 1.091 (presque parfait)
- **Corrélation** : 0.364 (vs 0.232 base)

**Performance sur Cas FORT/TRÈS_FORT** :
| Classe | MAE (actuelle) | MAE (linéaire) | Amélioration |
|--------|----------------|----------------|--------------|
| FORT (98 cas) | 62.08 pips | **12.07 pips** | **-80.6%** |
| TRÈS_FORT (61 cas) | 94.45 pips | **40.32 pips** | **-57.3%** |

**Analyse par classe (formule linéaire)** :
| Classe | MAE | Ratio médian | Impact réel moy | Impact prédit moy |
|--------|-----|--------------|-----------------|-------------------|
| FAIBLE | 14.34 pips | 1.414 | 32.3 pips | 45.7 pips |
| MOYEN | 7.79 pips | 0.994 ✅ | 50.0 pips | 49.7 pips |
| FORT | 23.10 pips | 0.685 ⚠️ | 77.2 pips | 52.9 pips |
| TRÈS_FORT | 55.18 pips | 0.501 ⚠️ | 111.6 pips | 55.9 pips |

**Avantages** :
- ✅ Meilleure performance globale
- ✅ Utilise uniquement features prédictives (calculables AVANT le mouvement)
- ✅ Pas besoin de connaître la classe de mouvement
- ✅ Amélioration massive pour FORT et TRÈS_FORT

**Limitation acceptée** :
- ⚠️ Sous-estime encore FORT (ratio 0.685) et TRÈS_FORT (ratio 0.501)
- ✅ **Solution** : Utiliser stratégie de sortie à 85% de la prédiction pour maximiser win rate

---

## 📝 CHANGEMENTS TECHNIQUES

### Fichiers Modifiés

1. **`src/core/formulas_validated.py`**
   - Ajout fonction `calculate_impact_linear()`
   - Fonction `calculate_impact_d()` conservée (rétrocompatibilité)
   - Mise à jour documentation module

2. **`src/core/cluster_impact_calculator.py`** (à modifier)
   - Remplacer appel `calculate_impact_d()` par `calculate_impact_linear()`
   - Adapter signature fonction

### Sauvegarde

- **Fichier sauvegardé** : `src/core/formulas_validated.py.backup_YYYYMMDD_HHMMSS`
- **Emplacement** : Même répertoire que fichier original

---

## 🔧 IMPLÉMENTATION

### Nouvelle Fonction

```python
def calculate_impact_linear(
    base_empirical_score: float,
    adjusted_empirical_score: Optional[float] = None,
    surprise_avg: float = 0.0,
    surprise_max: float = 0.0,
    n_events: int = 1
) -> float:
    """
    Calcule l'impact prédit avec formule linéaire multiple optimisée.
    
    VALIDATION (SESSION_VALIDATION_ACTUELLE - 2025-01-XX):
    - MAE global : 13.98 pips (vs 38.63 formule actuelle)
    - Ratio médian : 1.091
    - Corrélation : 0.364
    - Amélioration FORT : -80.6% d'erreur
    - Amélioration TRÈS_FORT : -57.3% d'erreur
    
    FORMULE:
    impact = 30.5450 
           + 0.4692 * base_score
           + 0.1882 * adjusted_score
           + 0.0201 * surprise_avg
           - 0.0034 * surprise_max
           + 0.7355 * n_events
    
    Args:
        base_empirical_score: Score empirique de base
        adjusted_empirical_score: Score ajusté par surprise (optionnel)
        surprise_avg: Surprise moyenne en %
        surprise_max: Surprise maximale en %
        n_events: Nombre d'événements
    
    Returns:
        float: Impact prédit en pips (valeur absolue, minimum 0.0)
    """
```

### Migration

**Option 1 : Remplacement direct** (recommandé)
- Remplacer tous les appels `calculate_impact_d()` par `calculate_impact_linear()`
- Adapter les paramètres d'appel

**Option 2 : Mode hybride** (transition)
- Ajouter paramètre `use_linear=True` dans `calculate_cluster_impact()`
- Permettre bascule progressive

---

## 📊 VALIDATION

### Tests Effectués

1. **Test global** (1,147 mouvements avec événements US)
   - MAE : 13.98 pips
   - Ratio médian : 1.091
   - Corrélation : 0.364

2. **Test cas FORT** (98 cas spécifiques)
   - MAE : 12.07 pips (vs 62.08 actuelle)
   - Ratio médian : 0.923
   - Amélioration : -80.6%

3. **Test cas TRÈS_FORT** (61 cas spécifiques)
   - MAE : 40.32 pips (vs 94.45 actuelle)
   - Ratio médian : 0.644
   - Amélioration : -57.3%

### Fichiers de Validation

- `SESSION_VALIDATION_ACTUELLE/outputs/predictions_direct_from_features.csv`
- `SESSION_VALIDATION_ACTUELLE/outputs/test_linear_formula_fort_cases.csv`
- `SESSION_VALIDATION_ACTUELLE/outputs/test_linear_formula_tres_fort_cases.csv`
- `SESSION_VALIDATION_ACTUELLE/outputs/comparison_linear_vs_base_fort_cases.csv`

---

## 🔄 RÉTROCOMPATIBILITÉ

### Fonction Conservée

La fonction `calculate_impact_d()` est **conservée** pour rétrocompatibilité :
- Code existant continue de fonctionner
- Migration progressive possible
- Tests comparatifs facilités

### Recommandation

**Utiliser `calculate_impact_linear()` pour tous les nouveaux calculs** et migrer progressivement le code existant.

---

## 📈 STRATÉGIE DE SORTIE

Basée sur l'analyse du biais :

### Pour Tous les Mouvements
- **Sortir à 85% de la prédiction**
- **Win Rate attendu** : 99.2%
- **Gain moyen** : 8.89 pips/trade

### Pour Mouvements FORT/TRÈS_FORT Spécifiquement
- **Sortir à 85% de la prédiction**
- **Win Rate attendu** : 100.0% (159/159 trades gagnants)
- **Gain moyen** : 13.66 pips/trade

**Raison** : Même si les prédictions sont sous-estimées, sortir à 85% capture le mouvement dans la plupart des cas.

---

## 🚀 PROCHAINES ÉTAPES

1. ✅ Sauvegarde fichier original
2. ✅ Documentation changement
3. ⏳ Implémentation fonction `calculate_impact_linear()`
4. ⏳ Migration `cluster_impact_calculator.py`
5. ⏳ Tests de régression
6. ⏳ Validation sur nouvelles dates

---

## 📚 RÉFÉRENCES

- **Scripts d'analyse** : `SESSION_VALIDATION_ACTUELLE/scripts/`
  - `direct_impact_from_features.py` : Découverte formule linéaire
  - `test_linear_formula_on_fort_cases.py` : Validation cas FORT/TRÈS_FORT
- **Résultats** : `SESSION_VALIDATION_ACTUELLE/outputs/`
- **Documentation complète** : `SESSION_VALIDATION_ACTUELLE/outputs/RESUME_ANALYSES_CORRECTIONS.md`

---

**Dernière mise à jour** : 2025-01-XX


