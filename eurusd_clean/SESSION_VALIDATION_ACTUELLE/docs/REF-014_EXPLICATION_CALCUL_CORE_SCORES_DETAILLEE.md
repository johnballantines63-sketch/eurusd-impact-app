# REF-014 : Explication Détaillée du Calcul des Core Scores

**Date :** 2025-12-06  
**Exemple :** CPI (US) = 75.06

---

## 🎯 PROCESSUS COMPLET

### Étape 1 : Identifier Toutes les Dates avec CPI (US)

**Période :** 2023-01-01 à 2025-12-06 (3 ans)

**Requête :**
```sql
SELECT DISTINCT DATE(e.ts_utc) as date
FROM events e
WHERE e.country = 'US'
  AND (LOWER(e.event_key) LIKE '%cpi%' OR LOWER(e.event_title) LIKE '%cpi%')
  AND DATE(e.ts_utc) >= '2023-01-01'
  AND DATE(e.ts_utc) <= '2025-12-06'
  AND e.importance_n >= 2
```

**Résultat :** 37 dates identifiées avec CPI (US)

---

### Étape 2 : Détecter Mouvements Forts et Mesurer Impacts Réels

**Pour chaque date :**

1. **Charger prix** : Fenêtre 14:00-20:00
2. **Baseline** : OPEN première bougie à 14:30
3. **Détecter mouvement** : Pic maximum après 14:30
4. **Mesurer impact** : `(pic_price - baseline) × 10000` (en pips)
5. **Filtrer** : Garder uniquement mouvements ≥ 20 pips

**Résultat pour CPI (US) :** 34 mouvements forts détectés (sur 37 dates)

**Exemples d'impacts mesurés :**
- 2023-01-12 : 42.60 pips (DOWN)
- 2023-02-14 : 50.90 pips (DOWN)
- 2023-04-12 : 76.40 pips (UP)
- 2023-07-12 : 109.30 pips (UP)
- 2023-10-12 : 93.60 pips (DOWN)
- ... et 29 autres

---

### Étape 3 : Calculer Statistiques

**Sur les 34 impacts mesurés :**

| Statistique | Valeur |
|-------------|--------|
| **Moyenne (avg)** | 59.09 pips |
| **Médiane** | 51.25 pips |
| **P80 (80ème percentile)** | 87.64 pips |
| **Écart-type** | 33.39 pips |
| **Min** | 22.40 pips |
| **Max** | 151.80 pips |
| **Sample size** | 34 |

---

### Étape 4 : Calculer Score Empirique

**Formule :**

```
base_score = (avg × 0.5 + p80 × 0.5)
           = (59.09 × 0.5 + 87.64 × 0.5)
           = 29.54 + 43.82
           = 73.36
```

**Facteur de robustesse :**

| Sample Size | Robustness |
|-------------|------------|
| ≥ 20 | 1.0 |
| 10-19 | 0.9 |
| 5-9 | 0.8 |
| < 5 | 0.7 |

**Pour CPI (US) :** Sample size = 34 → Robustness = 1.0

**Score empirique :**

```
score_empirical = base_score × robustness
                = 73.36 × 1.0
                = 73.36
```

**Normalisation (max 100) :**

```
score_normalized = min(100.0, score_empirical)
                 = min(100.0, 73.36)
                 = 73.36
```

---

### Étape 5 : Vérification avec Score dans DB

**Score dans DB :** 75.06

**Différence :** 1.70 points

**Causes possibles :**
- Dates légèrement différentes (32 vs 34 occurrences)
- Recalcul avec données mises à jour
- Arrondis dans les calculs

---

## 📊 EXEMPLE CONCRET : 2025-09-11

### Situation

**Date :** 2025-09-11  
**Événement :** CPI (US) à 14:30  
**Impact réel mesuré :** 62.40 pips (UP)

### Contribution au Score CPI (US)

**Si 2025-09-11 est inclus dans le calcul :**

1. **Impact mesuré :** 62.40 pips
2. **Position dans distribution :** 
   - Rang : ~20/34 (environ 60ème percentile)
   - Entre moyenne (59.09) et P80 (87.64)
3. **Contribution :**
   - À la moyenne : +1.84 pips (62.40 / 34)
   - Au P80 : Influence le 80ème percentile si dans le top 20%

### Calcul Final

**Avec 2025-09-11 inclus :**

- **Nouvelle moyenne :** ~59.09 pips (impact modeste)
- **Nouveau P80 :** ~87.64 pips (peut augmenter si 62.40 > ancien P80)
- **Score final :** ~73-75 (selon recalcul exact)

---

## 🔍 POURQUOI LE SCORE EST-IL ÉLEVÉ (75.06) ?

### Analyse

Le score CPI (US) = 75.06 est élevé car :

1. **P80 élevé (90.28 pips)** : 80% des mouvements CPI sont < 90.28 pips
   - Indique que CPI génère souvent des mouvements importants
   - Exemples : 109.30 pips (2023-07-12), 151.80 pips (max)

2. **Moyenne modérée (59.83 pips)** : Mais combinée avec P80 élevé
   - Formule : 50% avg + 50% p80
   - = 0.5 × 59.83 + 0.5 × 90.28
   - = 29.92 + 45.14 = 75.06

3. **Sample size robuste (32)** : Robustness = 1.0
   - Pas de pénalité pour faible échantillon

---

## 💡 COMPARAISON AVEC SCORES event_families

### Pour un événement CPI individuel

**Score event_families (exemple) :** ~50-60

**Score core_scores (CPI US) :** 75.06

**Différence :** +15-25 points

**Explication :**
- `event_families` : Score basé sur **tous les événements CPI** (toutes dates, tous contextes)
- `core_scores` : Score basé sur **mouvements forts uniquement** (≥ 20 pips) avec CPI comme noyau dur

**Conséquence :** `core_scores` est plus élevé car il ne considère que les cas où CPI a généré un mouvement fort.

---

## 🎯 UTILISATION DANS LE PIPELINE

### Problème Actuel

Si on utilise directement `core_score = 75.06` au lieu de `mean(event_families) = ~50` :

- **Impact base** : Plus élevé (score × 1.5)
- **Prédiction** : Surestimée

### Solution Proposée

**Option C (Moyenne Pondérée) :**

```python
score_final = 0.7 × mean(event_families) + 0.3 × core_score
            = 0.7 × 50.0 + 0.3 × 75.06
            = 35.0 + 22.52
            = 57.52
```

**Résultat :** Score intermédiaire qui intègre l'information supplémentaire sans surestimer.

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




