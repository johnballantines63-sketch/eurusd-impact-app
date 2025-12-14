# 📋 GUIDE : AJOUTER DES DATES DE TEST

**Objectif :** Enrichir `test_vectorial_multi_dates.py` avec plus de dates pour valider le facteur de correction.

---

## 🎯 ÉTAPES POUR AJOUTER UNE DATE

### 1️⃣ Identifier une date avec événements importants

**Critères :**
- Plusieurs événements simultanés (≥2)
- Événements à impact élevé (CPI, NFP, Jobless Claims, etc.)
- Heure : généralement 14:30 (US) ou 14:15 (ECB)

**Sources :**
- MyFxBook calendar
- ForexFactory
- TradingEconomics

---

### 2️⃣ Mesurer l'impact réel sur MT5

**Méthode :**

1. Ouvrir MT5 sur EUR/USD, timeframe M1
2. Identifier l'heure de l'événement (ex: 14:30)
3. Mesurer le mouvement :
   - **Prix avant** : Prix de la bougie juste avant l'événement
   - **Prix pic** : Prix maximum/minimum atteint dans les 5-10 minutes
   - **Impact = |Prix pic - Prix avant|** en pips

**Exemple :**
```
11 septembre 2025, 14:30
Prix avant : 1.17000
Prix pic   : 1.17442 (5 min après)
Impact = (1.17442 - 1.17000) × 10000 = 44.2 pips
```

---

### 3️⃣ Ajouter dans TEST_DATES

Ouvrir `test_vectorial_multi_dates.py` et ajouter la date :

```python
TEST_DATES = [
    # Format : (date, heure, impact_réel_mt5)
    ('2025-09-11', '14:30:00', 43.4),   # Référence
    
    # NOUVELLES DATES À AJOUTER ICI
    ('2025-08-01', '14:30:00', 85.2),   # NFP (exemple)
    ('2025-07-11', '14:30:00', 32.1),   # CPI (exemple)
    # ... ajouter autant que nécessaire
]
```

---

### 4️⃣ Exécuter le test

```bash
python3 test_vectorial_multi_dates.py
```

Le script va :
- Charger automatiquement les événements depuis la DB
- Calculer la somme vectorielle
- Comparer avec l'impact MT5
- Afficher l'erreur

---

## 📊 DATES SUGGÉRÉES À TESTER

### Dates importantes 2025

| Date | Heure | Événements | Impact MT5 | Statut |
|------|-------|------------|------------|--------|
| 2025-09-11 | 14:30 | CPI + Jobless (6 evt) | 43.4 pips | ✅ Testé |
| 2025-08-01 | 14:30 | NFP + Emploi | ? pips | ⏳ À mesurer |
| 2025-07-11 | 14:30 | CPI | ? pips | ⏳ À mesurer |
| 2025-06-12 | 14:30 | CPI | ? pips | ⏳ À mesurer |
| 2025-05-02 | 14:30 | NFP | ? pips | ⏳ À mesurer |

**Action :** Ouvre MT5 et mesure les impacts pour ces dates.

---

### Dates importantes 2024

| Date | Heure | Événements | Impact MT5 | Statut |
|------|-------|------------|------------|--------|
| 2024-12-06 | 14:30 | NFP | ? pips | ⏳ À mesurer |
| 2024-11-13 | 14:30 | CPI | ? pips | ⏳ À mesurer |
| 2024-10-10 | 14:30 | CPI | ? pips | ⏳ À mesurer |

---

## 🔍 COMMENT TROUVER LES BONNES DATES

### Méthode 1 : Requête SQL

```sql
-- Trouver les dates avec plusieurs événements à impact élevé
SELECT 
    date(ts_utc) as date,
    time(ts_utc) as time,
    COUNT(*) as num_events,
    STRING_AGG(event_key, ', ') as events
FROM events
WHERE empirical_score > 70
AND impact_level IN ('HIGH', 'MEDIUM')
GROUP BY date(ts_utc), time(ts_utc)
HAVING COUNT(*) >= 2
ORDER BY date DESC
LIMIT 20
```

### Méthode 2 : MyFxBook Calendar

1. Aller sur https://www.myfxbook.com/forex-economic-calendar
2. Filtrer par importance : HIGH
3. Identifier les dates avec plusieurs événements
4. Noter les dates

---

## 🎯 OBJECTIF

**Minimum recommandé :** 10 dates testées

**Pourquoi ?**
- 1 date = validation initiale (fait ✅)
- 5-10 dates = validation du facteur de correction
- 20+ dates = robustesse statistique confirmée

---

## 📊 INTERPRÉTATION DES RÉSULTATS

Après avoir testé plusieurs dates, le script affichera :

```
📊 ANALYSE GLOBALE
Erreur moyenne (corrigé)  : XX.X%
Directions correctes      : X/X (XX%)
```

**Critères de succès :**
- ✅ Erreur moyenne < 30%
- ✅ Directions correctes > 80%
- ✅ Facteur 0.758 stable (±0.05)

---

## 🔧 AJUSTER LE FACTEUR SI NÉCESSAIRE

Si l'erreur moyenne est > 30%, le script proposera un facteur optimal :

```
💡 Facteur optimal suggéré : 0.XXX
```

**Action :**
1. Noter le nouveau facteur
2. Mettre à jour dans `sequence_multi_event_timeline_v87.py`
3. Re-tester

---

## 📝 EXEMPLE COMPLET

### Ajouter la date du 1er août 2025 (NFP)

1. **Mesurer sur MT5 :**
   ```
   Date : 2025-08-01
   Heure : 14:30
   Prix avant : 1.08500
   Prix pic : 1.09352
   Impact = 85.2 pips
   ```

2. **Ajouter dans le script :**
   ```python
   TEST_DATES = [
       ('2025-09-11', '14:30:00', 43.4),
       ('2025-08-01', '14:30:00', 85.2),  # ← NOUVELLE LIGNE
   ]
   ```

3. **Exécuter :**
   ```bash
   python3 test_vectorial_multi_dates.py
   ```

4. **Analyser les résultats**

---

## 🚀 PROCHAINES ACTIONS

1. ⏳ Mesurer les impacts MT5 pour 5-10 dates importantes
2. ⏳ Ajouter dans TEST_DATES
3. ⏳ Exécuter test_vectorial_multi_dates.py
4. ⏳ Analyser l'erreur moyenne
5. ⏳ Ajuster le facteur si nécessaire
6. ✅ Implémenter dans sequence_multi_event_timeline_v87.py

---

**Version :** 1.0  
**Date :** 18 octobre 2025  
**Tokens :** 105K / 190K
