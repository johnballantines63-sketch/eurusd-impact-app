# 📊 SESSION 106 - DOCUMENTATION ÉTAPE 2bis

**Date :** 2 novembre 2025  
**Étape :** Test formule Planificateur V2.4  
**Script :** `step2bis_test_planificateur_formula.py`

---

## 🎯 CONTEXTE

**Question André :** Si les événements sans estimate étaient présents en Session 103, le facteur amp=2.5 et le score_adjusted=84.2 doivent être cohérents.

**Découverte :** Le Planificateur utilise une formule validée en Session 55 avec 99.9% de précision !

---

## 📐 FORMULE PLANIFICATEUR V2.4 (SESSION 55)

### Fonction : calculate_adjusted_empirical_score()

```python
def calculate_adjusted_empirical_score(
    base_empirical_score: float,
    surprise_pct: float
) -> float:
    """
    Ajuste score selon surprise par zones
    Validée Session 55 - 99.9% précision
    """
    abs_surprise = abs(surprise_pct)
    
    # Zone 1 : < 5% → Pas d'amplification
    if abs_surprise < 5:
        factor = 1.0
    
    # Zone 2 : 5-15% → Amplification progressive 1.0 → 1.5
    elif abs_surprise < 15:
        factor = 1.0 + (abs_surprise - 5) / 10 * 0.5
    
    # Zone 3 : 15-30% → Amplification progressive 1.5 → 1.9
    elif abs_surprise < 30:
        factor = 1.5 + (abs_surprise - 15) / 15 * 0.4
    
    # Zone 4 : ≥ 30% → Plafond à 1.9
    else:
        factor = 1.9
    
    return base_empirical_score * factor
```

### Logique de gestion des NaN

**Événements sans estimate :**
```python
if pd.notna(estimate) and estimate != 0:
    surprise_pct = abs((actual - estimate) / estimate) * 100
else:
    surprise_pct = 0.0  # Pas de surprise
```

**Conséquence :**
- Événements sans estimate → surprise = 0% → factor = 1.0
- Événements avec estimate → surprise calculée → factor 1.0 à 1.9

---

## 🔬 CE QUE LE SCRIPT VA TESTER

### 1. Application formule par événement

Pour chaque événement 11.09 :
- Calcul surprise (0% si NaN)
- Détermination zone (1, 2, 3 ou 4)
- Calcul factor
- Calcul score_adjusted = empirical_score × factor

### 2. Test agrégations différentes

**Méthodes testées :**
1. **Moyenne tous événements** (11 événements)
2. **Moyenne excluant NaN** (9 événements avec estimate)
3. **Somme** des scores ajustés
4. **Maximum** des scores ajustés

**Objectif :** Trouver quelle méthode donne ~84.2

### 3. Validation cohérence impact

Si score_adjusted ≈ 84.2 :
```python
impact = (84.2 * 11 / 100) * 0.758 * 2.5
       = 9.262 * 0.758 * 2.5
       = 56.3 pips
```

Comparé à impact_real = 56.8 pips  
Erreur attendue : ~0.5 pips ✅

---

## 🎯 RÉSULTATS ATTENDUS

### Scénario A : Moyenne fonctionne

```
Moyenne scores ajustés : ~84.2
Impact prédit : ~56.3 pips
Impact réel : 56.8 pips
Erreur : ~0.5 pips ✅
```

→ **VALIDÉ** : On a la bonne formule !

### Scénario B : Autre agrégation nécessaire

```
Moyenne : 49.8 ❌
Somme : 84.0 ✅
```

→ Session 103 utilisait SOMME pas moyenne

### Scénario C : Aucune ne marche

```
Toutes méthodes : Écart > 2 pips
```

→ Investigation supplémentaire nécessaire

---

## 📊 ANALYSE PRÉVISIONNELLE

### Événement dominant : inflation_rate_mom

```
empirical_score : 45.7
surprise : 33.33%
→ Zone 4 (≥ 30%)
→ factor = 1.9
→ score_adjusted = 45.7 × 1.9 = 86.8
```

**Ce seul événement ≈ 84.2 !** 🎯

### Autres événements (surprise ~0%)

```
9 événements avec surprise ~0%
→ Zone 1 (< 5%)
→ factor = 1.0
→ score_adjusted ≈ empirical_score (~44.8 moyen)
```

### Prédiction

**Si moyenne :**
```
(86.8 + 9×44.8 + 2×42.0) / 11 = 548.4 / 11 = 49.9 ❌
```

**Si on ne garde que événements avec surprise significative :**
```
inflation_rate_mom seul : 86.8 ✅ proche de 84.2 !
```

**Hypothèse :** Session 103 utilisait peut-être score MAX plutôt que moyenne ?

---

## 🚀 PROCHAINE ÉTAPE SELON RÉSULTATS

### Si validation complète (erreur < 2 pips)

**Étape 3 :** Implémenter formule finale
- Créer fonction `calculate_adjusted_empirical_score()`
- Appliquer aux 6 dates Cluster #3
- Mettre à jour CSV avec scores ajustés
- Continuer Phase 3.3 (amp_optimal)

### Si investigation nécessaire

**Étape 2ter :** Analyser Session 103
- Chercher rapports Session 103
- Comprendre méthodologie exacte
- Reproduire calcul 84.2
- Valider cohérence

---

## 💡 INSIGHTS CLÉS

### 1. Formule par zones (non-linéaire)

La formule Planificateur utilise des **zones discrètes** :
- < 5% : Aucun effet
- 5-15% : Amplification modérée
- 15-30% : Amplification forte
- ≥ 30% : Plafond 1.9×

**Justification :** Marché réagit par paliers, pas linéairement

### 2. Gestion intelligente des NaN

Événements sans estimate → surprise = 0% → factor = 1.0
= Conservation du score empirique sans amplification
= **Aucune perte d'information** (événement reste dans le calcul)

### 3. Facteur 1.9 plafonné

Pour surprise ≥ 30%, factor = 1.9 (pas 2.0 ou plus)
= Protection contre over-amplification
= Cohérent avec données empiriques

---

## 📝 QUESTIONS À RÉSOUDRE

1. **Agrégation :** Moyenne, somme, max ou autre ?
2. **Filtrage :** Tous événements ou seulement ceux avec surprise > seuil ?
3. **Cohérence :** Le 84.2 vient-il vraiment de cette formule ?

**Le script va répondre à ces 3 questions !** 🎯

---

**Prêt pour lancement !** 🚀
