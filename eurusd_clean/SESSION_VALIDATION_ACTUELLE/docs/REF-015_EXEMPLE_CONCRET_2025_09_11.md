# REF-015 : Exemple Concret - Calcul Core Score CPI (US) avec 2025-09-11

**Date :** 2025-12-06  
**Exemple :** Comment 2025-09-11 contribue au score CPI (US) = 75.06

---

## 📊 DONNÉES RÉELLES DANS LA DB

**Score CPI (US) dans core_scores :**
- **Score empirique :** 75.06
- **Avg impact :** 59.83 pips
- **P80 impact :** 90.28 pips
- **Sample size :** 32 occurrences
- **Min :** 22.40 pips
- **Max :** 151.80 pips

---

## 🔍 CALCUL DÉTAILLÉ

### Formule Complète

```
base_score = (avg × 0.5 + p80 × 0.5)
           = (59.83 × 0.5 + 90.28 × 0.5)
           = 29.92 + 45.14
           = 75.06

robustness = 1.0 (car sample_size = 32 ≥ 20)

score_final = base_score × robustness
            = 75.06 × 1.0
            = 75.06
```

### Explication

1. **Moyenne (59.83 pips)** : Impact moyen des 32 mouvements CPI forts
2. **P80 (90.28 pips)** : 80% des mouvements sont < 90.28 pips
3. **Formule 50/50** : Combine moyenne (stabilité) et P80 (mouvements forts)
4. **Robustness 1.0** : Pas de pénalité (32 occurrences ≥ 20)

---

## 📅 CONTRIBUTION DE 2025-09-11

### Impact Réel Mesuré

**2025-09-11 :** 62.40 pips (UP)

### Position dans la Distribution

Sur les 32 occurrences CPI (US) :

| Position | Impact (pips) | Description |
|----------|---------------|-------------|
| Min | 22.40 | Plus faible mouvement |
| **2025-09-11** | **62.40** | **Au-dessus de la moyenne (59.83)** |
| Médiane | 51.25 | Milieu de distribution |
| P80 | 90.28 | 80ème percentile |
| Max | 151.80 | Plus fort mouvement |

### Contribution au Calcul

**Si 2025-09-11 est inclus :**

1. **À la moyenne :**
   - Impact : 62.40 pips
   - Contribution : +1.95 pips à la moyenne (62.40 / 32)
   - Nouvelle moyenne : ~59.83 pips (impact modeste car proche de la moyenne)

2. **Au P80 :**
   - 62.40 pips < 90.28 pips (P80 actuel)
   - N'affecte pas le P80 (car en dessous)

3. **Impact sur le score :**
   - Score reste ~75.06 (impact minimal car proche de la moyenne)

---

## 💡 POURQUOI LE SCORE EST-IL ÉLEVÉ (75.06) ?

### Analyse de la Distribution

**32 mouvements CPI (US) mesurés :**

- **Moyenne modérée :** 59.83 pips
- **P80 élevé :** 90.28 pips
- **Écart important :** P80 - Avg = 30.45 pips

**Interprétation :**
- La plupart des mouvements CPI sont modérés (~60 pips)
- Mais **20% des mouvements sont très forts** (≥ 90 pips)
- Ces mouvements forts "tirent" le P80 vers le haut

### Exemples de Mouvements Forts (Top 20%)

- **151.80 pips** (max) : Exceptionnel
- **109.30 pips** (2023-07-12) : Très fort
- **93.60 pips** (2023-10-12) : Fort
- **90.28 pips** (P80) : Seuil du top 20%

### Impact sur la Formule

**Formule :** `50% avg + 50% p80`

- **50% avg (59.83)** : Représente la tendance générale
- **50% p80 (90.28)** : Représente les mouvements forts
- **Résultat :** 75.06 (équilibre entre les deux)

**Si on utilisait seulement la moyenne :**
- Score = 59.83 (sous-estimerait les mouvements forts)

**Si on utilisait seulement le P80 :**
- Score = 90.28 (surestimerait la plupart des cas)

**Formule 50/50 :** Équilibre optimal ✅

---

## 🔄 COMPARAISON AVEC event_families

### Score event_families (exemple pour un événement CPI)

**Typiquement :** ~50-60 points

**Calcul :** Basé sur **tous les événements CPI** (toutes dates, tous contextes, mouvements faibles inclus)

### Score core_scores (CPI US)

**Valeur :** 75.06 points

**Calcul :** Basé sur **mouvements forts uniquement** (≥ 20 pips) avec CPI comme noyau dur

### Différence

**+15-25 points** entre core_scores et event_families

**Explication :**
- `event_families` : Inclut tous les CPI (même ceux sans mouvement)
- `core_scores` : Inclut uniquement les CPI qui ont généré un mouvement fort

**Conséquence :** `core_scores` est plus élevé car il ne considère que les cas "réussis".

---

## 🎯 UTILISATION DANS LE PIPELINE

### Problème si Utilisation Directe

**Score actuel (moyenne event_families) :** ~50.0  
**Score core_scores :** 75.06  
**Différence :** +50%

**Impact :**
- Impact base : +50% (surestimé)
- Prédiction : Surestimée

### Solution : Option C (Moyenne Pondérée)

```python
score_final = 0.7 × mean(event_families) + 0.3 × core_score
            = 0.7 × 50.0 + 0.3 × 75.06
            = 35.0 + 22.52
            = 57.52
```

**Résultat :** Score intermédiaire (+15% au lieu de +50%)

---

## 📋 RÉSUMÉ

### Pour 2025-09-11 Spécifiquement

1. **Impact réel :** 62.40 pips
2. **Position :** Au-dessus de la moyenne (59.83), en dessous du P80 (90.28)
3. **Contribution :** Modeste (proche de la moyenne)
4. **Score CPI (US) :** 75.06 (basé sur 32 occurrences, dont 2025-09-11)

### Pour le Score CPI (US) en Général

1. **32 mouvements forts** mesurés sur 3 ans
2. **Moyenne :** 59.83 pips (modérée)
3. **P80 :** 90.28 pips (élevé, car 20% des mouvements sont très forts)
4. **Score final :** 75.06 (équilibre 50/50 entre moyenne et P80)

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




