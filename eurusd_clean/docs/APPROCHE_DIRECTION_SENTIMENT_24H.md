# 📋 APPROCHE DIRECTION_SENTIMENT - MÉTHODOLOGIE 24 HEURES

**Date :** 29 octobre 2025 - Session 92.7  
**Pour :** Session 92.8 - Investigation facteur manquant  
**Validé par :** André Valentin

---

## 🎯 CONTEXTE

### Problème Identifié Session 92.7

**Surprise nette V2 crée régressions sur surprises positives :**

| Date | Surprise Net | Impact Réel | Baseline | V2 | Régression |
|------|--------------|-------------|----------|-----|------------|
| 2025-09-11 | +33.6% | 51.7 pips | **4.5** ✅ | **8.3** ❌ | -3.8 pips |
| 2025-01-15 | +27.5% | 49.9 pips | **6.3** ✅ | **10.1** ❌ | -3.8 pips |

**Conclusion :** Surprise nette = facteur PARTIEL, pas complet.

**FACTEUR MANQUANT CRITIQUE identifié : DIRECTION_SENTIMENT**

---

## 🔬 MÉTHODOLOGIE DIRECTION_SENTIMENT

### Principe Fondamental

**ANALYSER 24 HEURES AVANT ANNONCE (PAS 2H)**

**Pourquoi 24h ?**
- 2h = Bruit de marché, pas de vraie tendance
- 24h = Tendance établie, conviction marché
- Dernier pic 24h = Point de référence critique

**Décision André (29 oct 2025) :**
> "Il faut analyser sur au moins 24 heures avant, idéalement dernier pic absolu dans la période de 24h avant l'annonce. C'est là qu'on déterminera une vraie tendance ou pas."

---

## 📊 ÉTAPES ANALYSE 24 HEURES

### Étape 1 : Charger Prix 24h Avant

```python
def load_prices_24h_before(event_time: datetime, conn) -> pd.DataFrame:
    """
    Charge prix EURUSD 24h avant événement
    
    Args:
        event_time: Timestamp événement (ex: 2025-09-11 14:30:00+02:00)
        conn: Connexion DuckDB
    
    Returns:
        DataFrame avec colonnes: datetime, open, high, low, close
    """
    # Période : [event_time - 24h, event_time]
    start_time = event_time - timedelta(hours=24)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= ?
      AND datetime < ?
    ORDER BY datetime ASC
    """
    
    return conn.execute(query, [start_time, event_time]).df()
```

---

### Étape 2 : Identifier Dernier Pic Absolu

```python
def find_last_absolute_peak(prices_df: pd.DataFrame, event_price: float) -> dict:
    """
    Identifie le dernier pic absolu dans période 24h
    
    DÉFINITION PIC ABSOLU:
    - High maximum dans période 24h
    - Ou Low minimum dans période 24h
    
    SÉLECTION:
    - Si prix actuel plus proche du high → Pic = high (tendance haussière)
    - Si prix actuel plus proche du low → Pic = low (tendance baissière)
    
    Args:
        prices_df: DataFrame prix 24h
        event_price: Prix au moment de l'événement
    
    Returns:
        dict: {
            'peak_price': float,
            'peak_time': datetime,
            'peak_type': 'HIGH' ou 'LOW',
            'distance_pips': float,
            'hours_since_peak': float
        }
    """
    # Identifier high/low absolus période 24h
    idx_high = prices_df['high'].idxmax()
    idx_low = prices_df['low'].idxmin()
    
    peak_high = prices_df.loc[idx_high, 'high']
    peak_low = prices_df.loc[idx_low, 'low']
    
    time_high = prices_df.loc[idx_high, 'datetime']
    time_low = prices_df.loc[idx_low, 'datetime']
    
    # Distance du prix actuel aux pics
    distance_to_high = abs(event_price - peak_high)
    distance_to_low = abs(event_price - peak_low)
    
    # Sélectionner pic le plus proche
    if distance_to_high < distance_to_low:
        # Prix proche du high → Tendance haussière possible
        peak_type = 'HIGH'
        peak_price = peak_high
        peak_time = time_high
        distance_pips = (event_price - peak_high) * 10000  # Négatif si en dessous
    else:
        # Prix proche du low → Tendance baissière possible
        peak_type = 'LOW'
        peak_price = peak_low
        peak_time = time_low
        distance_pips = (event_price - peak_low) * 10000  # Positif si au dessus
    
    return {
        'peak_price': peak_price,
        'peak_time': peak_time,
        'peak_type': peak_type,
        'distance_pips': distance_pips,
        'hours_since_peak': (event_time - peak_time).total_seconds() / 3600
    }
```

---

### Étape 3 : Calculer Indicateurs 24h

```python
def calculate_24h_indicators(prices_df: pd.DataFrame, peak_info: dict, event_price: float) -> dict:
    """
    Calcule indicateurs techniques sur période 24h
    
    INDICATEURS:
    1. Range 24h : high - low (volatilité absolue)
    2. ATR 24h : Average True Range (volatilité moyenne)
    3. Momentum 24h : (prix actuel - prix T-24h) / prix T-24h
    4. Position dans range : (prix - low) / (high - low)
    5. Distance du pic : Calculée dans find_last_absolute_peak()
    
    Args:
        prices_df: DataFrame prix 24h
        peak_info: Dict depuis find_last_absolute_peak()
        event_price: Prix au moment événement
    
    Returns:
        dict: {
            'range_24h_pips': float,
            'atr_24h_pips': float,
            'momentum_24h_pct': float,
            'position_in_range': float (0 à 1),
            'distance_from_peak_pips': float,
            'hours_since_peak': float
        }
    """
    # Range 24h
    high_24h = prices_df['high'].max()
    low_24h = prices_df['low'].min()
    range_24h_pips = (high_24h - low_24h) * 10000
    
    # ATR 24h (simplifié : moyenne des true ranges)
    prices_df['true_range'] = prices_df.apply(
        lambda row: max(
            row['high'] - row['low'],
            abs(row['high'] - row['close'].shift(1)) if row.name > 0 else 0,
            abs(row['low'] - row['close'].shift(1)) if row.name > 0 else 0
        ),
        axis=1
    )
    atr_24h_pips = prices_df['true_range'].mean() * 10000
    
    # Momentum 24h
    price_start_24h = prices_df.iloc[0]['close']
    momentum_24h_pct = ((event_price - price_start_24h) / price_start_24h) * 100
    
    # Position dans range
    position_in_range = (event_price - low_24h) / (high_24h - low_24h) if (high_24h - low_24h) > 0 else 0.5
    
    return {
        'range_24h_pips': range_24h_pips,
        'atr_24h_pips': atr_24h_pips,
        'momentum_24h_pct': momentum_24h_pct,
        'position_in_range': position_in_range,
        'distance_from_peak_pips': peak_info['distance_pips'],
        'hours_since_peak': peak_info['hours_since_peak']
    }
```

---

### Étape 4 : Calculer Direction_Sentiment

```python
def calculate_direction_sentiment(indicators: dict, peak_info: dict) -> float:
    """
    Calcule score direction_sentiment basé sur analyse 24h
    
    LOGIQUE:
    1. Tendance depuis pic (poids 40%)
       - Si proche high + momentum positif → Haussier
       - Si proche low + momentum négatif → Baissier
    
    2. Momentum 24h (poids 30%)
       - Momentum > 0 → Haussier
       - Momentum < 0 → Baissier
    
    3. Position dans range (poids 20%)
       - > 0.7 → Haussier (sommet range)
       - < 0.3 → Baissier (bas range)
    
    4. Volatilité (poids 10%)
       - ATR faible + tendance claire → Amplifier sentiment
       - ATR forte → Atténuer sentiment (incertitude)
    
    Args:
        indicators: Dict depuis calculate_24h_indicators()
        peak_info: Dict depuis find_last_absolute_peak()
    
    Returns:
        float: Score -1 (baissier fort) à +1 (haussier fort)
    """
    score = 0.0
    
    # 1. Tendance depuis pic (40%)
    if peak_info['peak_type'] == 'HIGH':
        # Proche du high
        if indicators['distance_from_peak_pips'] > -10:  # Moins de 10 pips sous high
            score += 0.4  # Très haussier
        elif indicators['distance_from_peak_pips'] > -30:
            score += 0.2  # Modérément haussier
        else:
            score -= 0.2  # Correction depuis high
    else:  # peak_type == 'LOW'
        # Proche du low
        if indicators['distance_from_peak_pips'] < 10:  # Moins de 10 pips au dessus low
            score -= 0.4  # Très baissier
        elif indicators['distance_from_peak_pips'] < 30:
            score -= 0.2  # Modérément baissier
        else:
            score += 0.2  # Rebond depuis low
    
    # 2. Momentum 24h (30%)
    momentum = indicators['momentum_24h_pct']
    if momentum > 0.2:
        score += 0.3
    elif momentum > 0.05:
        score += 0.15
    elif momentum < -0.2:
        score -= 0.3
    elif momentum < -0.05:
        score -= 0.15
    
    # 3. Position dans range (20%)
    position = indicators['position_in_range']
    if position > 0.7:
        score += 0.2  # Sommet range
    elif position > 0.5:
        score += 0.1
    elif position < 0.3:
        score -= 0.2  # Bas range
    elif position < 0.5:
        score -= 0.1
    
    # 4. Volatilité (10%)
    # Si ATR faible (<30 pips) + tendance claire → Amplifier
    # Si ATR forte (>60 pips) → Atténuer (incertitude)
    atr = indicators['atr_24h_pips']
    if atr < 30 and abs(score) > 0.3:
        score *= 1.1  # Amplifier conviction
    elif atr > 60:
        score *= 0.9  # Atténuer conviction
    
    # Borner entre -1 et +1
    return max(-1.0, min(1.0, score))
```

---

## 🧪 INTÉGRATION AVEC SURPRISE NETTE

### Formule Combinée

```python
def calculate_combined_factor(surprise_net: float, direction_sentiment: float) -> float:
    """
    Combine surprise nette ET direction_sentiment
    
    HYPOTHÈSE:
    - Si surprise nette positive + marché haussier → Amplification
    - Si surprise nette positive + marché baissier → Atténuation
    - Si surprise nette négative + marché baissier → Amplification
    - Si surprise nette négative + marché haussier → Atténuation
    
    FORMULE:
    combined_factor = direction_factor_v2 × (1 + direction_sentiment × 0.1)
    
    EXEMPLE:
    - direction_factor = 1.05 (surprise nette +33%)
    - direction_sentiment = +0.5 (marché haussier)
    - combined = 1.05 × (1 + 0.5 × 0.1) = 1.05 × 1.05 = 1.1025
    
    Args:
        surprise_net: Surprise nette en %
        direction_sentiment: Score -1 à +1
    
    Returns:
        float: Facteur combiné (0.65 à 1.15 environ)
    """
    # Facteur direction depuis surprise nette (V2)
    if surprise_net > 30:
        direction_factor = 1.05
    elif surprise_net > 0:
        direction_factor = min(1.0 + (surprise_net / 200), 1.05)
    elif surprise_net >= -30:
        direction_factor = max(1.0 + (surprise_net / 100), 0.7)
    else:
        direction_factor = 0.7
    
    # Ajustement par direction_sentiment (±10% max)
    combined_factor = direction_factor * (1 + direction_sentiment * 0.1)
    
    return combined_factor
```

---

## 📋 TESTS ATTENDUS SESSION 92.8

### Test 1 : Analyse 4 Dates CPI avec Direction_Sentiment

**Objectif :** Comprendre POURQUOI régressions sur 09-11 et 01-15

**Pour chaque date :**
1. Charger prix 24h avant
2. Identifier dernier pic absolu
3. Calculer indicateurs 24h
4. Calculer direction_sentiment
5. Combiner avec surprise nette
6. Comparer prédiction vs réel

**Résultat attendu :**
```
Date: 2025-09-11
  Surprise nette: +33.6%
  Dernier pic: HIGH à 1.1750 (T-8h)
  Distance pic: -15 pips
  Momentum 24h: +0.15%
  Direction_sentiment: +0.4 (haussier)
  
  Factor surprise seule: 1.05
  Factor combiné: 1.05 × 1.04 = 1.092
  
  Impact prédit: 58.0 pips
  Impact réel: 51.7 pips
  Erreur: 6.3 pips (vs 8.3 pips V2 seule)
```

**Critère succès :**
- 4/4 dates < 5 pips erreur ✅
- Aucune régression vs baseline ✅

---

### Test 2 : Comparaison Baseline / V2 / Combined

**Tableau comparatif attendu :**

| Date | Réel | Baseline | V2 Seule | Combined | Meilleure |
|------|------|----------|----------|----------|-----------|
| 2025-09-11 | 51.7 | **4.5** | 8.3 | **?** | ? |
| 2025-01-15 | 49.9 | **6.3** | 10.1 | **?** | ? |
| 2025-05-13 | 34.0 | 22.2 | **0.6** | **?** | ? |
| 2025-07-15 | 24.6 | 31.6 | **8.8** | **?** | ? |

**Objectif :** Combined MEILLEURE ou ÉGALE baseline sur TOUTES dates

---

## 🎯 CRITÈRES VALIDATION SESSION 92.8

### Critères Obligatoires

1. ✅ **MAE 4 dates < 5 pips** (strict)
2. ✅ **AUCUNE régression vs baseline** (0/4 dates)
3. ✅ **Explication claire pourquoi ça marche** (pas juste "ça marche")
4. ✅ **Direction_sentiment cohérent économiquement** (pas facteur magique)

### Si Échec

**Si MAE > 5 pips OU régressions persistent :**

**Investiguer Hypothèses B ou D :**
- Hypothèse B : Contexte inflation (niveau CPI tendance)
- Hypothèse D : Cycle Fed (phase hawkish/dovish)

**OU combiner plusieurs facteurs :**
- Surprise nette × Direction_sentiment × Contexte_inflation

---

## 🚫 PIÈGES À ÉVITER

### Piège #1 : Analyser seulement 2h avant

**❌ ERREUR :** 2h = bruit de marché, pas vraie tendance  
**✅ CORRECT :** 24h = tendance établie

### Piège #2 : Ignorer dernier pic absolu

**❌ ERREUR :** Calculer tendance depuis T-24h arbitraire  
**✅ CORRECT :** Calculer depuis dernier high/low (point de référence)

### Piège #3 : Se contenter d'amélioration partielle

**❌ ERREUR :** "MAE 7 pips c'est acceptable"  
**✅ CORRECT :** "Toutes dates < 5 pips ou je continue"

### Piège #4 : Facteur magique sans explication

**❌ ERREUR :** "Direction_sentiment = 0.437, ça marche"  
**✅ CORRECT :** "Direction_sentiment positif car prix proche high 24h"

---

## 📚 RÉFÉRENCES

**Documents à lire AVANT Session 92.8 :**

1. `MANDATORY_SESSION_RULES.md` (règles tokens, rigueur)
2. `PROJECT_STATE.md` (état projet complet)
3. `ANALYSE_CLUSTERS_HYPOTHESES.md` (hypothèses B, C, D)
4. `SESSION92.7_RAPPORT_COMPLET.md` (résultats V2)
5. `APPROCHE_DIRECTION_SENTIMENT_24H.md` (ce document)

**Charte Scientifique :**
- Article 1 : Rigueur scientifique absolue
- Article 6 : "€100,000 réels avec ce code ?"
- Ne JAMAIS se contenter d'approximations

---

## ✅ CHECKLIST SESSION 92.8

**AVANT tout code :**
- [ ] Lire APPROCHE_DIRECTION_SENTIMENT_24H.md ENTIÈREMENT
- [ ] Comprendre pourquoi 24h (pas 2h)
- [ ] Comprendre logique dernier pic absolu
- [ ] Valider méthodologie avec André si doute

**Pendant investigation :**
- [ ] Charger prix 24h pour 4 dates CPI
- [ ] Identifier dernier pic absolu (HIGH ou LOW)
- [ ] Calculer indicateurs 24h (range, ATR, momentum, position)
- [ ] Calculer direction_sentiment selon formule
- [ ] Tester formule combinée
- [ ] Comparer baseline / V2 / combined

**Critères succès :**
- [ ] MAE 4 dates < 5 pips
- [ ] 0 régressions vs baseline
- [ ] Explication claire facteurs
- [ ] Code documenté et testé

---

_Approche Direction_Sentiment 24h - Session 92.7 - 29 octobre 2025_  
_"Analyser 24h, identifier pic absolu, déterminer vraie tendance" - Validé André Valentin_
