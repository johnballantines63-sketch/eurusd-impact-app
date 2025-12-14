# Problème Détection Tendance - Pas Assez de Données

**Date** : 1er août 2025  
**Problème** : Tendance non détectée pour le cluster cible

---

## 🔍 PROBLÈME IDENTIFIÉ

### Erreur
```
error: Pas assez de données (476 < 1000)
```

### Cause

La fonction `detect_trend_by_inversion_s107` requiert **au moins 1000 barres** pour le timeframe M30, mais seulement **476 barres** sont disponibles dans la fenêtre analysée.

---

## 📊 ANALYSE

### Paramètres utilisés dans l'étape 8

```python
lookback_days = 14
segment_hours = 12
min_r2_for_trend = 0.15
min_hours_before_event = 12
timeframe = 'M30'
```

### Calcul de la fenêtre

1. **Anchor time** : 2025-08-01 14:30:00
2. **Query time** (event - 2h) : 2025-08-01 12:30:00
3. **Start time** (query - 14 jours) : 2025-07-18 12:30:00
4. **End time** : Query time (2025-08-01 12:30:00) - **AVANT l'événement**

### Nombre de barres disponibles

- **14 jours** à **M30** = 14 * 48 barres/jour = **672 barres théoriques**
- **Après filtrage par query_dt** : **476 barres disponibles**
- **Requirement** : **1000 barres minimum** ❌

---

## 🔧 CODE CONCERNÉ

**Fichier** : `src/core/trend_detection_pre_event_s107.py`  
**Ligne** : ~95-100

```python
# Ajuster seuil selon timeframe (H1 a moins de bougies que M1)
min_bars = 100 if timeframe == 'H1' else (500 if timeframe == 'M15' else 1000)

if len(df_window) < min_bars:
    return {
        'trend_exists': False,
        'error': f'Pas assez de données ({len(df_window)} < {min_bars})'
    }
```

**Problème** : Le seuil de 1000 barres est trop élevé pour M30 avec seulement 14 jours de lookback.

---

## ✅ SOLUTIONS POSSIBLES

### Solution 1 : Réduire le seuil minimum pour M30

**Modification** : Ajuster `min_bars` pour M30

```python
min_bars = 100 if timeframe == 'H1' else (500 if timeframe == 'M15' else (400 if timeframe == 'M30' else 1000))
```

**Avantages** :
- ✅ Permet la détection avec 14 jours de lookback
- ✅ 476 barres > 400 barres (ok)
- ✅ Conservateur (assez de données pour segments de 12h)

**Inconvénients** :
- ⚠️ Nécessite modification de la fonction core

---

### Solution 2 : Augmenter le lookback

**Modification** : Augmenter `lookback_days` de 14 à 21 jours

```python
lookback_days = 21  # Au lieu de 14
```

**Calcul** :
- 21 jours * 48 barres/jour = 1008 barres théoriques
- Après filtrage : ~714 barres disponibles

**Problème** : Toujours < 1000 barres requis ❌

**Nécessiterait** : 30 jours minimum pour atteindre 1000 barres

---

### Solution 3 : Utiliser un timeframe différent

**Option A** : Utiliser H1 au lieu de M30

**Avantages** :
- ✅ Seuil de seulement 100 barres
- ✅ 14 jours * 24 barres/jour = 336 barres disponibles > 100 barres ✅

**Inconvénients** :
- ⚠️ Moins de précision pour détection tendance
- ⚠️ Nécessite modification de l'étape 8

---

### Solution 4 : Adapter le seuil dynamiquement

**Modification** : Calculer `min_bars` en fonction de `lookback_days` et `timeframe`

```python
# Calculer nombre de barres théoriques
bars_per_day = 24 if timeframe == 'H1' else (48 if timeframe == 'M30' else 1440)
theoretical_bars = lookback_days * bars_per_day

# Seuil minimum = 50% des barres théoriques (ou minimum absolu)
min_bars = max(100, int(theoretical_bars * 0.5))
```

**Avantages** :
- ✅ Adaptatif selon timeframe et lookback
- ✅ Conservateur (50% des barres théoriques)

---

## 🎯 RECOMMANDATION

**Solution recommandée** : **Solution 1 + Solution 4 combinées**

1. **Ajuster le seuil pour M30** : 400 barres au lieu de 1000
2. **Rendre le seuil adaptatif** : Basé sur timeframe et lookback

**Justification** :
- 476 barres disponibles > 400 barres requis ✅
- 14 jours de lookback est suffisant pour détecter tendances
- Les segments de 12h nécessitent ~24 barres chacun → 14 jours = 28 segments possibles

---

## 📋 MODIFICATIONS À APPORTER

**Fichier** : `src/core/trend_detection_pre_event_s107.py`  
**Lignes** : ~94-100

**Avant** :
```python
min_bars = 100 if timeframe == 'H1' else (500 if timeframe == 'M15' else 1000)

if len(df_window) < min_bars:
    return {
        'trend_exists': False,
        'error': f'Pas assez de données ({len(df_window)} < {min_bars})'
    }
```

**Après** :
```python
# Calculer seuil minimum adaptatif selon timeframe
bars_per_day = 24 if timeframe == 'H1' else (48 if timeframe == 'M30' else (96 if timeframe == 'M15' else 1440))
theoretical_bars = lookback_days * bars_per_day

# Seuil minimum = 50% des barres théoriques (ou minimum absolu selon timeframe)
if timeframe == 'H1':
    min_bars = 100
elif timeframe == 'M30':
    min_bars = max(400, int(theoretical_bars * 0.5))  # Minimum 400 pour M30
elif timeframe == 'M15':
    min_bars = max(500, int(theoretical_bars * 0.5))
else:
    min_bars = 1000

if len(df_window) < min_bars:
    return {
        'trend_exists': False,
        'error': f'Pas assez de données ({len(df_window)} < {min_bars})'
    }
```

---

**Status** : ✅ Problème identifié - Solution proposée




