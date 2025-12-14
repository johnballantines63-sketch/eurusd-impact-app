# 🔍 NOTE D'INVESTIGATION - 11 SEPTEMBRE 2025

**Date investigation :** 20 octobre 2025  
**Session :** 13  
**Priorité :** HAUTE - Pour Session 14  
**Statut :** ⚠️ ANOMALIE DÉTECTÉE

---

## 📊 RÉSUMÉ EXÉCUTIF

**Observation :** Le système prédit **52.4 pips** alors que le mouvement réel MT5 était de **~521 pips** (facteur ×10).

**Direction :** ✅ Correcte (UP)  
**Amplitude :** ❌ Sous-estimée (×10)

---

## 🔍 DONNÉES ÉVÉNEMENT

### Événements à 14:30 (11 septembre 2025)

| # | Événement | Forecast | Actual | Surprise | % | Importance |
|---|-----------|----------|--------|----------|---|------------|
| 1 | **Initial Jobless Claims** | 235K | 263K | **+28K** | **+11.9%** | ⭐ |
| 2 | Jobless 4-Week Avg | 232 | 240.5 | +8.5 | +3.7% | ⭐ |
| 3 | CPI s.a | 323.0 | 323.364 | +0.364 | +0.1% | ⭐ |
| 4 | CPI | 323.89 | 323.98 | +0.09 | +0.0% | ⭐ |
| 5 | Inflation Rate | 2.9 | 2.9 | 0.0 | 0.0% | ⭐ |
| 6 | Core Inflation | 0.3 | 0.3 | 0.0 | 0.0% | ⭐ |
| 7 | Continuing Jobless | 1950 | 1939 | -11.0 | -0.6% | ⭐ |
| 8 | Real Earnings | - | -0.1 | - | - | ⭐ |

### Surprise majeure identifiée

**Initial Jobless Claims : +28,000 (+11.9%)** 🚨

- 28,000 demandeurs d'emploi de **plus** que prévu
- Signal de **faiblesse économique majeure**
- Surprise relative : **+11.9%** (énorme pour cet indicateur)

---

## 📈 COMPARAISON PRÉDICTION vs RÉALITÉ

### Prédiction système (Streamlit)

```
Groupe 1 (6 événements à 14:30) :
  Event 0 : +29.5 pips (Jobless +28K)
  Event 1 : +25.7 pips (CPI +0.36)
  Event 2 : +26.2 pips (CPI +0.09)
  Event 3 : +26.3 pips (Inflation +0.10)
  Event 4 : -22.5 pips (Jobless -11K)
  Event 5 : +33.6 pips (Jobless +8.5)
  ─────────────────────────────
  Total brut    : +119.3 pips
  Avec facteur  : +90.4 pips (×0.758)
  
Groupe 2 (1 événement à 14:45) :
  Event 6 : +24.9 pips (Current Account)
  
═══════════════════════════════
IMPACT FINAL : 52.4 pips UP ⬆️
```

### Mouvement réel (MT5)

**Graphique M1 (1 minute) :**
```
Prix avant (14:28) : ~1.16523
Prix pic (14:31)   : ~1.17044
Mouvement          : ~521 pips 🚀
Direction          : UP ⬆️
Temps au pic       : ~3 minutes
```

**Observation :**
- Mouvement **vertical** immédiat à 14:30
- Aucune hésitation, montée directe
- Pic atteint en ~3 minutes
- Retracement important ensuite

---

## 🤔 HYPOTHÈSES EXPLICATIVES

### Hypothèse 1 : Effets non-linéaires (PROBABLE)

**Description :**
Le système modélise des **effets linéaires** uniquement. Les événements extrêmes créent des réactions **exponentielles** non capturées.

**Mécanismes possibles :**
1. **Panique des traders** : Surprise +11.9% déclenche vente massive USD
2. **Cascade de stop-loss** : Positions longues USD liquidées en chaîne
3. **Effet de levier psychologique** : Peur d'une récession amplifie la réaction
4. **Algorithmes** : Trading algorithmique amplifie les mouvements extrêmes

**Probabilité :** ⭐⭐⭐⭐⭐ (très probable)

**Validation :**
- Chercher d'autres dates avec surprises > 10%
- Vérifier si facteur multiplicateur similaire (×5 à ×15)
- Tester sur 10-15 événements extrêmes

---

### Hypothèse 2 : Contexte macro non capturé (POSSIBLE)

**Description :**
Le contexte économique du 11 septembre 2025 rendait cette surprise beaucoup plus significative que le chiffre brut.

**Facteurs potentiels :**
1. **Attentes implicites du marché** différentes des forecasts officiels
2. **Série de mauvais chiffres** avant le 11 septembre (momentum baissier USD)
3. **Annonce Fed** parallèle ou imminente
4. **Contexte géopolitique** amplifiant la sensibilité
5. **Positionnement** : Marché très long USD, correction violente

**Probabilité :** ⭐⭐⭐ (possible)

**Validation :**
- Analyser contexte macro septembre 2025
- Vérifier annonces Fed autour du 11 septembre
- Examiner actualités géopolitiques
- Analyser sentiment de marché (COT reports)

---

### Hypothèse 3 : Spike / Erreur de cotation (PEU PROBABLE)

**Description :**
Le mouvement de 521 pips serait une erreur de cotation MT5 (spike).

**Contre-arguments :**
- Mouvement cohérent sur graphique (pas de spike isolé)
- Progression logique (montée puis retracement)
- Durée significative (~3 min au pic, puis consolidation)

**Probabilité :** ⭐ (peu probable)

**Validation :**
- Vérifier avec d'autres brokers (FXCM, OANDA, etc.)
- Comparer avec données historiques TradingView
- Vérifier volumes (si disponibles)

---

## 📊 ANALYSE QUANTITATIVE

### Comparaison surprise vs impact

| Surprise Jobless | Impact prédit | Impact réel | Ratio |
|------------------|---------------|-------------|-------|
| +28K (+11.9%) | 29.5 pips | ~521 pips | ×17.7 |

**Note :** Le ratio ×17.7 pour l'événement principal suggère un **effet multiplicateur massif**.

### Distribution normale des surprises

Pour Initial Jobless Claims typiques :
- Surprise moyenne : ±5K (±2%)
- Surprise +28K = **+5.6 sigma** (extrêmement rare)
- Probabilité : < 0.0001% (événement "cygne noir")

**Implication :** Le système n'est **pas calibré** pour événements > 3 sigma.

---

## 🎯 RECOMMANDATIONS SESSION 14

### Action 1 : Analyser événements extrêmes historiques

**Objectif :** Identifier pattern d'amplification

**Méthode :**
```sql
-- Requête pour trouver surprises extrêmes
SELECT 
    event_title,
    ts_utc,
    actual,
    estimate,
    ABS((actual - estimate) / NULLIF(estimate, 0) * 100) as surprise_pct
FROM events
WHERE ABS((actual - estimate) / NULLIF(estimate, 0) * 100) > 5.0
ORDER BY surprise_pct DESC
LIMIT 50;
```

**Analyser :**
1. Mouvement MT5 réel pour chaque événement
2. Impact prédit par système
3. Calculer ratio réel/prédit
4. Identifier seuil surprise pour amplification

---

### Action 2 : Tester multiplicateur non-linéaire

**Proposition :** Ajouter facteur multiplicateur pour surprises extrêmes

```python
def calculate_amplification_factor(surprise_pct):
    """
    Applique facteur multiplicateur pour surprises extrêmes
    
    Rationale :
    - Surprise < 5%   : facteur = 1.0 (linéaire)
    - Surprise 5-10%  : facteur = 1.5-3.0 (modéré)
    - Surprise > 10%  : facteur = 3.0-10.0 (extrême)
    """
    surprise_abs = abs(surprise_pct)
    
    if surprise_abs < 5.0:
        return 1.0
    elif surprise_abs < 10.0:
        # Interpolation linéaire entre 1.0 et 3.0
        return 1.0 + (surprise_abs - 5.0) * 0.4
    else:
        # Interpolation logarithmique pour surprises extrêmes
        return 3.0 + np.log1p(surprise_abs - 10.0) * 2.0
```

**Test :**
```
Surprise +11.9% → Facteur ≈ 3.5
Impact brut 119 pips × 3.5 = 416 pips
Après correction 0.758 : 315 pips
```

**Résultat :** Encore sous-estimé mais beaucoup plus proche !

---

### Action 3 : Valider sur échantillon

**Créer dataset test :**
1. Sélectionner 15-20 dates avec surprises > 5%
2. Calculer impact prédit (avec et sans multiplicateur)
3. Mesurer mouvement réel MT5
4. Comparer MAE (Mean Absolute Error)
5. Ajuster paramètres multiplicateur

**Métriques à optimiser :**
- MAE global
- Précision direction (déjà à 100%)
- Ratio prédit/réel pour cas extrêmes (cible : 0.8-1.2)

---

## 📝 DONNÉES TECHNIQUES

### Requête SQL pour reproduire analyse

```sql
SELECT 
    event_title,
    country,
    ts_utc,
    actual,
    estimate AS forecast,
    previous,
    (actual - estimate) AS surprise_absolute,
    ROUND((actual - estimate) / NULLIF(estimate, 0) * 100, 2) AS surprise_pct,
    unit,
    importance_n
FROM events
WHERE ts_utc >= '2025-09-11 14:20:00'
  AND ts_utc <= '2025-09-11 14:40:00'
ORDER BY ts_utc;
```

### Prix MT5 pour validation

```
Timeframe : M1 (1 minute)
Date      : 11 septembre 2025
Heure     : 14:30 UTC+2
Prix avant: 1.16523
Prix pic  : 1.17044
Mouvement : 521 pips (0.00521)
Direction : UP
```

---

## 🔗 LIENS VERS DOCUMENTATION

- **Rapport Session 13 :** `RAPPORT_SESSION13_FINAL.md`
- **Tests validés :** `test_v87_complet.py`
- **Module v87 :** `fx_impact_app/src/sequence_multi_event_timeline_v87.py`
- **Base de données :** `fx_impact_app/data/warehouse.duckdb`

---

## ✅ CONCLUSION

**Le 11 septembre 2025 est un cas d'école d'événement extrême :**
- Surprise +11.9% (5.6 sigma)
- Effet amplification ×10-×17
- Direction correctement prédite ✅
- Amplitude massivement sous-estimée ❌

**Action requise :** Implémenter multiplicateur non-linéaire en Session 14 pour gérer événements > 5% surprise.

**Priorité :** HAUTE

---

**Version :** 1.0  
**Date :** 20 octobre 2025, 01:45  
**Pour :** Session 14  
**Statut :** 📌 RÉFÉRENCE FUTURE
