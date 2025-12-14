# 📚 KNOWLEDGE BASE UPDATE - SESSION 24

**Date :** 20 octobre 2025  
**Session :** 24  
**Type :** Mise à jour majeure - Approche trading + Sources données

---

## 🎯 NOUVELLES CONNAISSANCES CRITIQUES

### 1. APPROCHE TRADING D'ANDRÉ (NOUVEAU) 🔥

#### Principe fondamental

**André NE trade PAS pendant la minute d'annonce.**

**Pourquoi :**
- Volatilité extrême (400-600 pips en 1 minute)
- Mouvements émotionnels qui se corrigent
- Impossible d'entrer/sortir proprement
- Spreads élargis, slippage élevé

#### Ce qu'André trade

**Il observe et entre APRÈS :**

1. **Phase 1 terminée** (TTR atteint)
   - Le pic du mouvement initial est identifié
   - Exemple : 14:35 (5 min après l'annonce)

2. **Pullback identifié**
   - Correction après le pic
   - Exemple : 14:35 → 14:45

3. **Direction stabilisée**
   - Nouveau niveau d'équilibre
   - Confirmation de la tendance

#### Métriques qui comptent pour trader

**✅ IMPORTANTES :**
- **Phase 1 globale** : Mouvement total jusqu'au TTR (5-15 min)
- **TTR** : Temps jusqu'au pic
- **Pullback** : Amplitude et durée de la correction
- **Phase 2** : Continuation ou stabilisation

**❌ PAS IMPORTANTES pour trader :**
- Volatilité de la minute exacte d'annonce
- Range de la 1ère minute (info académique seulement)
- Mouvements qui se corrigent immédiatement

#### Avertissements statistiques (NOUVEAU)

**Le système doit pouvoir alerter :**

> "⚠️ Attention : mouvement >400 pips probable dans la 1ère minute, mais statistiquement ce mouvement se corrige après 3-5 minutes. Attendre TTR (5 min) avant d'entrer."

**Utilité :**
- **Académique** : Comprendre le pattern
- **Psychologique** : Ne pas paniquer face à la volatilité
- **Tactique** : Savoir QUAND entrer

**Ce n'est PAS pour trader cette minute**, c'est pour **éviter d'entrer trop tôt**.

---

### 2. SOURCES DE DONNÉES VALIDÉES (NOUVEAU)

#### Sources ABANDONNÉES ❌

**EODHD :**
- Sous-estime mouvements **×10**
- 11 septembre : 36 pips (vs 600 réels)
- API gratuite mais qualité insuffisante
- **Statut : Ne plus utiliser**

**HistData.com :**
- Sous-estime mouvements **×100 à ×300**
- 11 septembre : 1.8 pips (vs 600 réels)
- Données tick manquantes
- **Statut : Ne plus utiliser**

#### Source ADOPTÉE ✅

**Dukascopy :**
- Source **institutionnelle** (banque suisse)
- Données **tick par tick**
- Agrégation M1 par nous (contrôle qualité)
- API gratuite
- **Statut : Source officielle du projet**

**URL API :**
```
https://datafeed.dukascopy.com/datafeed/{SYMBOL}/{YYYY}/{MM-1}/{DD}/{HH}h_ticks.bi5
```

**Script d'import :**
```bash
python3 import_dukascopy_session24.py
```

#### Source de RÉFÉRENCE ✅

**MT5 d'André :**
- Broker personnel d'André
- Données de trading réelles
- **Utilisé pour VALIDATION** des autres sources
- **Ne peut pas être automatisé** (export manuel)

---

### 3. CAS DE RÉFÉRENCE : 11 SEPTEMBRE 2025

#### Données validées (MT5 André)

**Événement :**
- Date : 11 septembre 2025
- Heure : **14:30 Berne (CEST) = 12:30 UTC**
- Type : Inflation MoM + 14 autres événements simultanés
- Surprise : 33.3% (0.4% vs 0.3% attendu)
- Score : ~46

#### Mouvements observés

**Minute 14:30 Berne (12:30 UTC) :**
- Prix avant : ~1.16800
- Low : 1.16583
- High : 1.17011
- **Range 1 minute : 428 pips** 🚀
- Direction : UP

**Phase 1 (14:30 → 14:35 Berne) :**
- Départ : 1.16583
- TTR atteint : 1.17200
- **Mouvement total : 617 pips**
- Durée : **5 minutes**

**Pullback (14:35 → 14:45 Berne) :**
- Départ : 1.17200
- Minimum : 1.16930
- **Pullback : 270 pips** (43% de Phase 1)
- Durée : **10 minutes**

**Phase 2 (14:45+ Berne) :**
- Événement 14:45 : Nouvel événement économique
- Résultat : Continuation haussière
- Suppression du pullback + momentum

#### Métriques calculées

```python
{
    'phase1': {
        'pips': 617,
        'ttr_minutes': 5,
        'direction': 'UP'
    },
    'pullback': {
        'pips': 270,
        'ratio': 0.43,  # 43% de Phase 1
        'duration_minutes': 10
    },
    'phase2': {
        'continuation': True,
        'reason': 'Nouvel événement 14:45'
    },
    'first_minute_volatility': {
        'range': 428,
        'ratio_to_phase1': 0.69  # 69% du mouvement Phase 1 en 1 min
    }
}
```

---

### 4. MÉTRIQUES À CALCULER (MISE À JOUR)

#### Anciennes métriques (V2)

```python
# V2 calculait seulement
impact_pips = base_formula(score) * amplification
ttr = 3 + (score/100) * 5
pullback = impact × 0.06 × minutes
```

#### Nouvelles métriques (V4)

**Phase 1 globale :**
```python
# Mouvement total jusqu'au TTR
# Calculé sur plusieurs minutes (pas 1 seule)
phase1_pips = calculate_phase1_global(
    score=score,
    surprise=surprise,
    num_events=num_events,
    duration_minutes=5-15  # Variable
)
```

**TTR (Time To Return) :**
```python
# Temps jusqu'au pic du mouvement
# Dépend de score et surprise
ttr_minutes = calculate_ttr(
    score=score,
    surprise=surprise
)
# Exemple : 5 min pour surprise 33% et score 46
```

**Pullback :**
```python
# Correction après le TTR
# En pips ET en ratio de Phase 1
pullback_pips = calculate_pullback(
    phase1_pips=phase1_pips,
    score=score,
    surprise=surprise
)
# Ratio typique : 20-50% de Phase 1
# Durée typique : 5-15 minutes
```

**Phase 2 :**
```python
# Continuation ou stabilisation
# Dépend des événements suivants
phase2_pips = calculate_phase2(
    phase1_pips=phase1_pips,
    pullback_pips=pullback_pips,
    has_following_events=bool,
    momentum_strength=float
)
```

**Avertissement volatilité :**
```python
# Pour la 1ère minute
if surprise > 20 and score > 40:
    warning = {
        'extreme_movement': phase1_pips * 0.7,  # 70% en 1 min
        'correction_after': 3-5,  # minutes
        'advice': 'Attendre TTR avant entrée'
    }
```

---

### 5. FORMULE V4 (STRUCTURE)

#### Principes directeurs

1. **Focus phases exploitables** : Pas la minute unique
2. **Basé sur données empiriques** : Dukascopy + MT5 validé
3. **Avertissements intégrés** : Volatilité 1ère minute
4. **Prédictions réalistes** : Pas de plafonds arbitraires

#### Structure proposée

```python
def predict_impact_v4(score, surprise, num_events):
    """
    Prédit l'impact d'un événement économique
    Focus sur phases de trading exploitables
    """
    
    # 1. Calculer Phase 1 (mouvement jusqu'au TTR)
    phase1 = {
        'pips': calculate_phase1_pips(score, surprise, num_events),
        'ttr_minutes': calculate_ttr(score, surprise),
        'direction': determine_direction(sentiment, actual_vs_forecast)
    }
    
    # 2. Calculer Pullback
    pullback = {
        'pips': phase1['pips'] * calculate_pullback_ratio(score, surprise),
        'duration_minutes': calculate_pullback_duration(score),
        'probability': calculate_pullback_probability(surprise, num_events)
    }
    
    # 3. Calculer Phase 2
    phase2 = {
        'pips': calculate_phase2_pips(phase1, pullback, num_events),
        'type': 'continuation' if has_momentum else 'stabilization'
    }
    
    # 4. Avertissement volatilité 1ère minute
    warning = None
    if surprise > 20 and score > 40:
        warning = {
            'type': 'extreme_volatility',
            'first_minute_range': phase1['pips'] * 0.7,
            'correction_after_minutes': 3-5,
            'recommendation': 'wait_for_ttr'
        }
    
    return {
        'phase1': phase1,
        'pullback': pullback,
        'phase2': phase2,
        'warning': warning,
        'confidence': calculate_confidence(score, surprise, num_events)
    }
```

---

### 6. DÉCALAGE HORAIRE (IMPORTANT)

#### Problème identifié Session 24

**Graphiques MT5 d'André :**
- Affichés en **heure de Berne (CEST)**
- CEST = UTC + 2 heures (en été)
- CET = UTC + 1 heure (en hiver)

**Base de données :**
- Stockée en **UTC**
- Toujours UTC, pas de DST

#### Conversion

**Septembre (été) :**
```python
# 14:30 Berne (CEST) = 12:30 UTC
berne_time = "14:30"
utc_time = "12:30"  # -2 heures
```

**Décembre (hiver) :**
```python
# 14:30 Berne (CET) = 13:30 UTC
berne_time = "14:30"
utc_time = "13:30"  # -1 heure
```

#### Validation

**Toujours vérifier :**
- Quelle timezone affiche MT5 ?
- Convertir en UTC pour requêtes DB
- Reconvertir en heure locale pour affichage

---

### 7. PATTERNS MULTI-ÉVÉNEMENTS

#### Synergie vs Dilution

**Synergie (amplification) :**
- Événements de **même nature**
- Surprises dans **même direction**
- **Timing rapproché** (<5 min)
- Exemple : CPI + Core CPI hausse simultanée

**Dilution (atténuation) :**
- Événements de **nature différente**
- Surprises dans **directions opposées**
- Timing plus **espacé** (>10 min)

#### Calcul V4

```python
def calculate_multi_event_factor(events):
    if len(events) == 1:
        return 1.0
    
    # Analyser cohérence
    same_direction = all_surprises_same_direction(events)
    timing_gap = max_gap_minutes(events)
    
    if same_direction and timing_gap < 5:
        # Synergie forte
        return 1.0 + (len(events) - 1) * 0.15  # +15% par événement
    elif timing_gap > 10:
        # Dilution
        return 1.0 + (len(events) - 1) * 0.05  # +5% seulement
    else:
        # Neutre
        return 1.0 + (len(events) - 1) * 0.10  # +10% par événement
```

---

### 8. VALIDATION ET TESTS

#### Tests obligatoires

**1. Cas de référence (11 septembre) :**
```python
# Doit donner :
# Phase 1 : 600 ± 100 pips
# TTR : 5 ± 2 minutes
# Pullback : 250 ± 50 pips
# Erreur globale : < 30%
```

**2. 944 cas extrêmes (surprise > 30%) :**
```python
# Moyenne erreur : < 40%
# Amélioration vs V2 : +20 points minimum
```

**3. Cas normaux (surprise < 15%) :**
```python
# Pas de régression vs V2
# Prédictions cohérentes
```

#### Métriques de validation

```python
def validate_v4(predictions, actuals):
    metrics = {
        'mape': mean_absolute_percentage_error,
        'rmse': root_mean_squared_error,
        'bias': mean_error,
        'cases_within_30pct': percentage_within_threshold
    }
    
    # Par catégorie
    for category in ['low_surprise', 'medium', 'high', 'extreme']:
        metrics[category] = calculate_metrics(
            predictions[category],
            actuals[category]
        )
    
    return metrics
```

---

## 📋 CHECKLIST UTILISATION KNOWLEDGE BASE

Avant d'analyser un événement :

- [ ] Données depuis Dukascopy ? (pas EODHD/HistData)
- [ ] Focus sur Phase 1 globale ? (pas 1 minute)
- [ ] TTR calculé ?
- [ ] Pullback prédit ?
- [ ] Avertissement volatilité si surprise > 20% ?
- [ ] Multi-événements analysés ?
- [ ] Validation sur cas référence ?

---

**FIN UPDATE KNOWLEDGE BASE SESSION 24**

**Date :** 20 octobre 2025  
**Session :** 24  
**Type :** Mise à jour majeure  
**Impact :** Changement complet approche prédiction
