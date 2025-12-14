# Analyse Mathématique et Statistique : Score Qualité

## Proposition de l'Utilisateur

**Formule proposée :**
```
1. Score individuel = importance_n × score_empirique
   - Pour HIGH (importance_n=3) : 3 × score_empirique
   - Pour MEDIUM (importance_n=2) : 2 × score_empirique
   - Pour LOW (importance_n=1) : 1 × score_empirique

2. Somme vectorielle des scores individuels (avec direction)

3. Ajustement avec le nombre d'événements
```

## Analyse Mathématique

### Validité de la Multiplication

**Avantage :**
- Combine deux dimensions indépendantes :
  - `importance_n` : Importance calendaire (1-3)
  - `score_empirique` : Impact historique mesuré (0-100)
- Multiplication = interaction entre les deux facteurs
- Échelle proportionnelle : HIGH (3) = 3× plus important que LOW (1)

**Exemple :**
- Événement HIGH (3) avec score 30 = **90 points**
- Événement MEDIUM (2) avec score 30 = **60 points**
- Événement LOW (1) avec score 30 = **30 points**

**Ratio :** HIGH/MEDIUM = 1.5x, HIGH/LOW = 3x ✅

### Validité Statistique

**Somme Vectorielle :**
- Permet neutralisation des événements opposés
- Reflète l'impact net réel (Session 105)
- Validé dans `cluster_impact_calculator.py`

**Ajustement par Nombre d'Événements :**
- Normalise pour éviter que le nombre domine
- Score qualité = score_global / n_events
- Privilégie la qualité individuelle

## Comparaison avec Approches Existantes

### Approche Actuelle (ScoringEngine)
```python
importance_score = (importance - 1) / 2  # Normalise à 0-1
composite_score = weights.impact * impact_score + 
                  weights.importance * importance_score
```
- **Problème** : Addition pondérée, pas multiplication
- **Limite** : Ne capture pas l'interaction importance × impact

### Approche Proposée
```python
score_individuel = importance_n × score_empirique
score_global = sum(score_individuel × direction)  # Vectoriel
score_qualite = abs(score_global) / n_events
```
- **Avantage** : Multiplication capture l'interaction
- **Avantage** : Plus simple et intuitif
- **Avantage** : Cohérent avec logique vectorielle validée

## Validation Mathématique

### Propriétés de la Multiplication

1. **Commutativité** : `importance_n × score_empirique = score_empirique × importance_n` ✅
2. **Distributivité** : `(a + b) × c = a×c + b×c` ✅
3. **Proportionnalité** : Si importance_n double, score double ✅

### Propriétés Statistiques

1. **Normalisation** : Division par n_events évite biais de taille ✅
2. **Neutralisation** : Somme vectorielle permet annulation ✅
3. **Robustesse** : Moins sensible aux outliers que somme simple ✅

## Conclusion

**✅ L'approche proposée est mathématiquement et statistiquement valide :**
- Multiplication capture l'interaction importance × impact
- Somme vectorielle permet neutralisation
- Normalisation par n_events évite biais de taille
- Plus simple que l'approche actuelle (addition pondérée)

**Recommandation :** Implémenter cette approche pour le calcul du score qualité.




