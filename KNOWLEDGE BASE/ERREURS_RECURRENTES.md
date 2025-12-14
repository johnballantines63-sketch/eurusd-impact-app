# ⚠️ ERREURS RÉCURRENTES - À NE JAMAIS REFAIRE

**Date création :** 21 octobre 2025  
**Session :** 26  
**Type :** GARDE-FOUS CRITIQUES

---

## 🎯 OBJECTIF DE CE DOCUMENT

Ce document liste les **erreurs récurrentes** qui ont été commises **multiple fois** dans le projet et qui doivent être **systématiquement évitées**.

**Règle d'or :** Avant d'écrire du code de calcul de surprise ou d'impact, **LIRE CE DOCUMENT**.

---

## 🚨 ERREUR #1 : CALCUL SURPRISE avec `previous` au lieu de `forecast`

### ❌ FRÉQUENCE
Commise **6+ fois** (Sessions 7, 11, 13, 18, 23, 26)

### ❌ CODE INCORRECT
```python
# MAUVAIS - Utilise previous par défaut
def calculate_surprise(actual, forecast, previous):
    if forecast is not None and forecast != 0:
        return abs((actual - forecast) / forecast) * 100
    elif previous is not None and previous != 0:  # ❌ ERREUR ICI
        return abs((actual - previous) / previous) * 100
    return None
```

### ✅ CODE CORRECT
```python
# BON - Utilise SEULEMENT forecast
def calculate_surprise(actual, forecast):
    """
    Calcule surprise UNIQUEMENT avec forecast.
    
    CRITIQUE : Ne jamais utiliser 'previous' pour la surprise.
    Previous est toujours proche de actual, donnant des surprises faibles.
    
    Si forecast est NULL, la surprise est NULL (pas 0, pas avec previous).
    """
    if forecast is not None and forecast != 0:
        return abs((actual - forecast) / forecast) * 100
    else:
        return None  # Pas de forecast = pas de surprise calculable
```

### 📊 IMPACT DE L'ERREUR

**Exemple 11 septembre 2025 CPI :**
```
Actual:   0.4%
Forecast: 0.3%
Previous: 0.3%

Surprise avec forecast: (0.4 - 0.3) / 0.3 = 33.3% ✅ BON
Surprise avec previous: (0.4 - 0.3) / 0.3 = 33.3% (dans ce cas égal mais PAS GÉNÉRAL)

Mais souvent :
Actual:   323.364
Forecast: 323.0
Previous: 323.0

Surprise avec forecast: 0.11% ✅ JUSTE
Surprise avec previous: 0.11% (même résultat PAR HASARD)

CAS PROBLÉMATIQUE :
Actual:   323.364
Forecast: NULL
Previous: 323.0

Surprise avec forecast: NULL ✅ BON (on ne peut pas calculer)
Surprise avec previous: 0.11% ❌ FAUX (donne une fausse surprise faible)
```

**Résultat :** Des événements majeurs (CPI, NFP) apparaissent avec surprise <10% alors qu'ils devraient être >30%.

### 🔒 GARDE-FOU

**Avant de calculer une surprise, TOUJOURS :**

1. ✅ Vérifier que `forecast` existe et n'est pas NULL
2. ✅ Si `forecast` est NULL → surprise = NULL (pas 0, pas avec previous)
3. ✅ Ne JAMAIS utiliser `previous` comme fallback

**Template obligatoire :**
```python
def calculate_surprise_SAFE(actual, forecast):
    """
    SAFE version - Ne tombe jamais dans le piège du previous
    """
    if actual is None or forecast is None:
        return None
    
    if forecast == 0:
        return None  # Division par zéro
    
    return abs((actual - forecast) / forecast) * 100
```

---

## 🚨 ERREUR #2 : TIMEZONE CONVERSION

### ❌ FRÉQUENCE
Commise **4+ fois** (Sessions 23, 24, 25, 26)

### ❌ CODE INCORRECT
```python
# MAUVAIS - Assume que DuckDB convertit les timezones
query = f"""
SELECT * FROM prices_1m
WHERE datetime = '2025-09-11 14:30:00+02:00'
"""
# ❌ DuckDB cherche LITTÉRALEMENT '14:30:00+02:00', pas l'équivalent UTC
```

### ✅ CODE CORRECT
```python
# BON - Conversion explicite en UTC
from datetime import datetime

event_time = pd.to_datetime('2025-09-11 14:30:00+02:00', utc=True)
event_time_utc = event_time.strftime('%Y-%m-%d %H:%M:%S')

query = f"""
SELECT * FROM prices_1m
WHERE datetime >= '{event_time_utc}'::timestamp
"""
# ✅ Cherche en UTC pur, DuckDB peut comparer
```

### 📊 IMPACT DE L'ERREUR

**Exemple :**
```
Événement : 14:30 Berne (CEST = UTC+2)
Équivalent UTC : 12:30 UTC

Mauvaise requête :
WHERE datetime = '14:30:00+02:00'
→ Trouve 14:30 LOCAL dans la DB (qui est déjà en +02:00)
→ Lit les prix à 14:30 LOCAL = 2h APRÈS l'annonce réelle

Résultat :
Prix de départ : 1.17321 (2h après l'annonce)
Attendu : 1.16874 (au moment de l'annonce)
Écart : 50 pips !
Phase 1 calculée : 6.6 pips (faux)
Phase 1 réelle : 33.7 pips
```

### 🔒 GARDE-FOU

**Avant de requêter prices_1m avec un datetime, TOUJOURS :**

1. ✅ Convertir le timestamp en UTC explicite
2. ✅ Enlever le timezone offset pour la requête DuckDB
3. ✅ Valider sur cas référence (11 septembre)

**Template obligatoire :**
```python
def query_prices_SAFE(event_timestamp):
    """
    SAFE version - Conversion timezone explicite
    """
    # Convertir en UTC
    if hasattr(event_timestamp, 'tz_convert'):
        utc_time = event_timestamp.tz_convert('UTC')
    else:
        utc_time = pd.to_datetime(event_timestamp, utc=True)
    
    # Format sans timezone pour DuckDB
    time_str = utc_time.strftime('%Y-%m-%d %H:%M:%S')
    
    query = f"""
    SELECT * FROM prices_1m
    WHERE datetime >= '{time_str}'::timestamp
    """
    
    return query
```

---

## 🚨 ERREUR #3 : FILTRER TROP TÔT (surprise > 30%)

### ❌ FRÉQUENCE
Commise **3+ fois** (Sessions 18, 23, 26)

### ❌ CODE INCORRECT
```python
# MAUVAIS - Filtre surprise > 30% AVANT d'avoir tous les événements
events_df = get_all_events()
events_df['surprise'] = calculate_surprise(...)
filtered = events_df[events_df['surprise'] > 30]  # ❌ Perd des événements

# Puis calcule Phase 1 seulement sur filtered
for event in filtered:
    calculate_phase1(event)
```

**Problème :** Si on veut analyser TOUS les événements (pas juste surprise > 30%), on doit recommencer.

### ✅ CODE CORRECT
```python
# BON - Calcule Phase 1 pour TOUS, filtre APRÈS
events_df = get_all_events()
events_df['surprise'] = calculate_surprise(...)

# Calcule Phase 1 pour TOUS
for event in events_df:
    event['phase1'] = calculate_phase1(event)

# Filtre APRÈS si besoin
high_surprise = events_df[events_df['surprise'] > 30]
medium_surprise = events_df[(events_df['surprise'] >= 10) & (events_df['surprise'] < 30)]
```

### 🔒 GARDE-FOU

**Toujours calculer les métriques (Phase 1, TTR, etc.) sur TOUS les événements, filtrer après.**

---

## 🚨 ERREUR #4 : UTILISER TABLES DÉRIVÉES SANS VALIDER

### ❌ FRÉQUENCE
Commise **2+ fois** (Sessions 25, 26)

### ❌ APPROCHE INCORRECTE
```python
# MAUVAIS - Utilise event_group_impacts sans vérifier
df = query("SELECT * FROM event_group_impacts")
# ❌ Cette table peut être corrompue (calculée avec anciennes sources)
```

### ✅ APPROCHE CORRECTE
```python
# BON - Valide TOUJOURS avec cas référence
df = query("SELECT * FROM event_group_impacts")

# Validation obligatoire
sept11 = df[df['date'] == '2025-09-11']
if sept11['mfe_pips'].iloc[0] < 30 or sept11['mfe_pips'].iloc[0] > 40:
    raise ValueError("Table corrompue - MFE 11 sept incorrect")

# Sinon, utilise la table primaire
df = calculate_from_scratch(events, prices_1m)
```

### 🔒 GARDE-FOU

**Avant d'utiliser une table dérivée (event_impacts, event_groups, etc.) :**

1. ✅ Vérifier cas référence 11 septembre
2. ✅ Si erreur > 10% → Table corrompue, recalculer
3. ✅ Toujours inclure colonne `source` et `created_at` dans tables dérivées

---

## 🚨 ERREUR #5 : SOUS-ESTIMER L'IMPORTANCE DU CAS RÉFÉRENCE

### ❌ FRÉQUENCE
Commise **constamment**

### ❌ APPROCHE INCORRECTE
```python
# MAUVAIS - Génère des résultats sans valider
results = calculate_all_impacts(events)
save_to_csv(results)  # ❌ Pas de validation
```

### ✅ APPROCHE CORRECTE
```python
# BON - Valide AVANT de sauvegarder
results = calculate_all_impacts(events)

# Validation obligatoire
sept11 = results[results['date'] == '2025-09-11 12:30']
assert 30 <= sept11['phase1_pips'] <= 40, "STOP - Cas référence invalide"

save_to_csv(results)  # ✅ Sûr de sauvegarder
```

### 🔒 GARDE-FOU

**TOUJOURS valider sur 11 septembre 2025 12:30 UTC :**
- Phase 1 : 33-37 pips (tolérance ±5 pips)
- Prix départ : ~1.16874
- Direction : UP

**Si cette validation échoue, NE PAS continuer.**

---

## 📋 CHECKLIST AVANT TOUT CALCUL D'IMPACT

Avant de calculer des impacts ou générer des prédictions, vérifier :

- [ ] Surprise calculée avec `forecast` UNIQUEMENT (pas previous)
- [ ] Timezone convertie explicitement en UTC
- [ ] Validation 11 septembre effectuée
- [ ] Tables sources validées (pas corrompues)
- [ ] Cas référence passe les critères

**Si UN SEUL item échoue → STOP et corriger.**

---

## 🎓 POURQUOI CES ERREURS SE RÉPÈTENT

1. **Knowledge Base trop longue** : L'info est perdue dans 100 pages
2. **Pas de checklist systématique** : On oublie les validations
3. **Pas de garde-fous dans le code** : Rien ne force la validation
4. **Contexte perdu entre sessions** : Claude redécouvre les mêmes problèmes

---

## ✅ SOLUTION

**Ce document doit être :**
1. ✅ Lu AU DÉBUT de chaque session
2. ✅ Référencé dans chaque script de calcul
3. ✅ Mis à jour quand une nouvelle erreur récurrente apparaît

---

**FIN DU DOCUMENT**

**Dernière mise à jour :** 21 octobre 2025 - Session 26  
**Erreurs documentées :** 5  
**Prochaine mise à jour :** Quand une 6ème erreur récurrente est identifiée
