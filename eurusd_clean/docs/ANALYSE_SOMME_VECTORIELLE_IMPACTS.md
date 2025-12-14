# Analyse : Somme Vectorielle pour Impacts vs Score Moyen

**Date** : Analyse méthodologique  
**Question** : Devrait-on appliquer une somme vectorielle des impacts plutôt qu'une addition ou une moyenne, comme pour le calcul des surprises ?

---

## 🔍 MÉTHODES IDENTIFIÉES

### Méthode 1 : Score Moyen + Formule D (Actuelle dans Pipeline)

**Localisation** : `src/core/cluster_impact_calculator.py` (ligne 107-205)

**Processus** :
1. Calculer score base **moyen** du cluster
2. Calculer surprise **nette** (somme vectorielle signée)
3. Ajuster score selon surprise
4. Appliquer Formule D avec score moyen ajusté

**Code** :
```python
# 1. Score moyen
base_score_mean = base_scores.mean()

# 2. Surprise nette (somme vectorielle)
surprise_net = sum(signed_surprises)  # Somme algébrique
max_surprise = abs(surprise_net)

# 3. Score ajusté
adjusted_score = calculate_adjusted_empirical_score(base_score_mean, max_surprise)

# 4. Impact avec Formule D
impact_pips = calculate_impact_d(adjusted_score, num_events, amplification)
```

**Avantage** :
- ✅ Simple et direct
- ✅ Utilise Formule D validée

**Inconvénient** :
- ❌ Ne tient pas compte des directions des événements
- ❌ Ne permet pas l'annulation entre impacts opposés

---

### Méthode 2 : Somme Vectorielle des Scores (Session 105)

**Localisation** : `scripts/session105/test_vectoriel_scores_FINAL.py`

**Processus** :
1. Calculer score ajusté pour chaque événement
2. Appliquer direction (+1 ou -1) selon famille et surprise
3. Score vectoriel = score ajusté × direction
4. **Somme vectorielle des scores**
5. Appliquer Formule D sur score vectoriel total

**Code** :
```python
scores_vectoriels = []
for event in events:
    score_adjusted = calculate_adjusted_empirical_score(base, surprise_pct)
    direction = get_event_direction(family, surprise)
    score_vectoriel = score_adjusted * direction  # Signé
    scores_vectoriels.append(score_vectoriel)

# Somme vectorielle
score_vectoriel_total = sum(scores_vectoriels)

# Formule D sur score vectoriel total (num_events=1 car déjà agrégé)
impact_base = -7.08 + 0.419 * score_vectoriel_total
```

**Avantage** :
- ✅ Tient compte des directions (comme les surprises)
- ✅ Permet annulation entre événements opposés
- ✅ Méthode cohérente avec somme vectorielle des surprises

**Inconvénient** :
- ⚠️ Utilise formule single event (num_events=1) même pour clusters

---

### Méthode 3 : Somme Vectorielle des Impacts (PredictionService)

**Localisation** : `app/services/prediction_service.py` (ligne 705-788)

**Processus** :
1. Calculer impact **absolu** pour chaque événement
2. Appliquer direction (+1 ou -1)
3. Contribution = impact × direction
4. **Somme algébrique** de toutes les contributions
5. Appliquer amplification
6. Appliquer correction 0.758

**Code** :
```python
contributions = []
for event in group:
    impact_abs = predict_impact_v9_clean(empirical_score, num_events)
    direction = get_event_direction(family, surprise)
    contribution = impact_abs * direction  # Signé
    contributions.append(contribution)

impact_brut = sum(contributions)  # Somme algébrique
impact_amplified = abs(impact_brut) * amplification_factor
impact_final = impact_amplified * 0.758
```

**Avantage** :
- ✅ Tient compte des directions
- ✅ Permet annulation entre impacts opposés
- ✅ Cohérent avec logique vectorielle

**Inconvénient** :
- ⚠️ Nécessite fonction `get_event_direction()` (pas dans pipeline actuel)

---

## 📊 COMPARAISON DÉTAILLÉE

### Pour les Surprises (Validé Session 113)

**Méthode** : **Somme vectorielle (somme algébrique signée)**

**Exemple** :
- Événement 1 : CPI +10% (inflation hausse)
- Événement 2 : Jobless Claims +12% (mauvaise nouvelle)
- Événement 3 : Other -3% (bonne nouvelle)
- **Surprise nette** : +10% + 12% - 3% = **+19%**

**Raison** :
- Les surprises opposées s'annulent
- Le marché réagit à la surprise **nette**, pas à chaque surprise individuellement

---

### Pour les Impacts (À Déterminer)

#### Option A : Score Moyen (Méthode Actuelle)

**Calcul** :
- Score moyen : (64.6 + 64.6 + 64.6) / 3 = 64.6
- Impact avec Formule D : ~19.99 pips par événement
- Total : 19.99 × 3 = 59.97 pips (ou 45.4 après correction 0.758)

**Problème** :
- Ne tient pas compte des directions
- Tous les événements contribuent positivement

#### Option B : Somme Vectorielle des Scores

**Calcul** :
- Score 1 ajusté : 122.8 × (+1) = +122.8
- Score 2 ajusté : 64.6 × (+1) = +64.6
- Score 3 ajusté : 64.6 × (-1) = -64.6 (si direction opposée)
- **Score vectoriel total** : +122.8 + 64.6 - 64.6 = **+122.8**
- Impact avec Formule D : -7.08 + 0.419 × 122.8 = **44.5 pips**

**Avantage** :
- ✅ Permet annulation si directions opposées
- ✅ Plus réaliste économiquement

#### Option C : Somme Vectorielle des Impacts

**Calcul** :
- Impact 1 : 44.36 pips × (+1) = +44.36
- Impact 2 : 19.99 pips × (+1) = +19.99
- Impact 3 : 19.99 pips × (-1) = -19.99 (si direction opposée)
- **Impact brut** : +44.36 + 19.99 - 19.99 = **+44.36**
- Après amplification et correction : ~33.7 pips

**Avantage** :
- ✅ Calcule directement les impacts avec directions
- ✅ Plus intuitif

---

## ✅ RECOMMANDATION

### Méthode Recommandée : **Somme Vectorielle des Scores (Option B)**

**Raisons** :

1. **Cohérence avec Surprises** :
   - Les surprises utilisent somme vectorielle
   - Les impacts devraient aussi utiliser somme vectorielle
   - Même logique : annulation entre événements opposés

2. **Réalité Économique** :
   - Si CPI +10% (inflation hausse → EUR/USD DOWN) et Jobless -5% (bonne nouvelle → EUR/USD UP)
   - Le marché réagit à la **surprise nette** et à l'**impact net**
   - Les effets opposés s'annulent partiellement

3. **Validation Session 105** :
   - La Session 105 a validé la méthode "somme vectorielle des scores"
   - Cette méthode donne de bons résultats

4. **Simplicité** :
   - Plus simple que somme vectorielle des impacts (Option C)
   - Utilise directement la Formule D validée

---

## 🔧 IMPLÉMENTATION RECOMMANDÉE

### Code à Implémenter dans Pipeline (Étape 8.1)

```python
# 8.1 : Calcul de l'Impact de Base (SOMME VECTORIELLE DES SCORES)
import numpy as np

num_events = len(cluster_events)
scores_vectoriels = []

# 1. Calculer score ajusté et direction pour chaque événement
for _, event in cluster_events.iterrows():
    base_score = event.get('empirical_score', 44.0)
    actual = event.get('actual')
    estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
    
    # Calculer surprise
    surprise_pct = 0.0
    if actual is not None and estimate is not None and estimate != 0:
        surprise_pct = abs(actual - estimate) / abs(estimate) * 100
    
    # Ajuster score selon surprise
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=base_score,
        surprise_pct=surprise_pct
    )
    
    # TODO: Obtenir direction (+1 ou -1) selon famille et surprise
    # direction = get_event_direction(family, surprise)
    # Pour l'instant, utiliser direction par défaut +1
    direction = 1  # À remplacer par get_event_direction()
    
    # Score vectoriel (signé)
    score_vectoriel = adjusted_score * direction
    scores_vectoriels.append(score_vectoriel)

# 2. Somme vectorielle des scores
score_vectoriel_total = sum(scores_vectoriels)

# 3. Calculer impact avec Formule D
# ⚠️ IMPORTANT : Utiliser num_events=1 car le score est déjà agrégé
impact_base = calculate_impact_d(
    empirical_score=abs(score_vectoriel_total),  # Valeur absolue
    num_events=1,  # Score déjà agrégé
    amplification=1.0,  # Pas d'amplification ici
    correction_factor=1.0  # Pas de correction supplémentaire
)

# 4. Appliquer direction finale
direction_finale = +1 if score_vectoriel_total >= 0 else -1
impact_base = impact_base * direction_finale
```

---

## ⚠️ PRÉREQUIS

### Fonction Nécessaire : `get_event_direction()`

**À créer ou adapter** :
```python
def get_event_direction(family: str, surprise: float) -> int:
    """
    Détermine la direction de l'impact d'un événement.
    
    Args:
        family: Famille de l'événement (ex: 'CPI', 'Jobless Claims')
        surprise: Surprise (actual - estimate)
    
    Returns:
        +1 si impact positif sur EUR/USD, -1 si négatif
    """
    # Déterminer sentiment de base selon famille
    family_sentiment = {
        'CPI': -1,  # Inflation hausse → EUR/USD DOWN
        'Jobless Claims': -1,  # Chômage hausse → EUR/USD DOWN
        # ... autres familles
    }
    
    sentiment = family_sentiment.get(family, 1)  # Défaut : +1
    
    # Direction = sentiment si surprise > 0, -sentiment sinon
    return sentiment if surprise > 0 else -sentiment
```

---

## 📋 COMPARAISON AVEC MÉTHODE ACTUELLE

### Méthode Actuelle (Score Moyen)

**Résultat pour 1er août 2025** :
- Score moyen : 95.87
- Impact base : 250.82 pips (après correction 0.758)
- **Problème** : Trop élevé (8.28x trop)

### Méthode Recommandée (Somme Vectorielle)

**Résultat attendu** :
- Score vectoriel total : Variable selon directions
- Impact base : ~30-50 pips
- **Avantage** : Plus réaliste et cohérent

---

## ✅ CONCLUSION

**Réponse** : **OUI**, on devrait appliquer une somme vectorielle des impacts (via scores vectoriels), comme pour les surprises.

**Raison** :
1. ✅ Cohérence méthodologique
2. ✅ Réalité économique (annulation entre effets opposés)
3. ✅ Validation Session 105
4. ✅ Réduction surestimation (problème actuel)

**Action** :
1. Implémenter `get_event_direction()` ou utiliser existante
2. Modifier étape 8.1 pour utiliser somme vectorielle des scores
3. Tester sur 1er août 2025

---

_Date création : Analyse méthodologique_  
_Conclusion : Utiliser somme vectorielle des scores (comme surprises)_




