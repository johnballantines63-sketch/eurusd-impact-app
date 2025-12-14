# ⚠️ ERREURS RÉCURRENTES - À NE JAMAIS REFAIRE

**Date création :** 21 octobre 2025  
**Dernière mise à jour :** Session 27  
**Type :** GARDE-FOUS CRITIQUES

---

## 🎯 OBJECTIF

Ce document liste les **erreurs récurrentes** qui ont été commises **multiple fois** et qui doivent être **systématiquement évitées**.

**Règle d'or :** Lire ce document AVANT d'écrire du code de calcul.

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
    Si forecast est NULL, la surprise est NULL (pas 0, pas avec previous).
    """
    if forecast is not None and forecast != 0:
        return abs((actual - forecast) / forecast) * 100
    else:
        return None
```

### 📊 IMPACT
Des événements majeurs (CPI, NFP) apparaissent avec surprise <10% alors qu'ils devraient être >30%.

---

## 🚨 ERREUR #2 : TIMEZONE CONVERSION

### ❌ FRÉQUENCE
Commise **4+ fois** (Sessions 23, 24, 25, 26)

### ❌ CODE INCORRECT
```python
# MAUVAIS
query = f"SELECT * FROM prices_1m WHERE datetime = '2025-09-11 14:30:00+02:00'"
# ❌ DuckDB cherche LITTÉRALEMENT '14:30:00+02:00'
```

### ✅ CODE CORRECT
```python
# BON - Conversion explicite en UTC
event_time = pd.to_datetime('2025-09-11 14:30:00+02:00', utc=True)
event_time_utc = event_time.strftime('%Y-%m-%d %H:%M:%S')
query = f"SELECT * FROM prices_1m WHERE datetime >= '{event_time_utc}'::timestamp"
```

### 📊 IMPACT
Lit les prix 2h après l'annonce réelle → Phase 1 calculée : 6.6 pips au lieu de 33.7 pips.

---

## 🚨 ERREUR #3 : UTILISER TABLES DÉRIVÉES SANS VALIDER

### ❌ FRÉQUENCE
Commise **2+ fois** (Sessions 25, 26)

### ✅ GARDE-FOU
Avant d'utiliser une table dérivée :
1. Vérifier cas référence 11 septembre
2. Si erreur > 10% → Table corrompue
3. Toujours inclure `source` et `created_at`

---

## 🚨 ERREUR #7 : FORECAST vs ESTIMATE dans EODHD API

### ❌ FRÉQUENCE
Commise **1 fois** (Session 27) - **IMPACT MAJEUR**

### 🔍 PROBLÈME

**L'API EODHD appelle le champ forecast `"estimate"` pas `"forecast"` !**

**Résultat :**
```
Total événements : 58,449
Avec forecast    : 11 (0.0%) ❌
Avec estimate    : 26,364 (45.1%) ✅
```

**99.98% des événements n'avaient PAS de forecast !**

### ❌ CODE INCORRECT

**Dans `eodhd_client.py` ligne 162-163 :**
```python
estimate = pd.to_numeric(_col(raw, "estimate", "estimated", "consensus"), ...)
forecast = pd.to_numeric(_col(raw, "forecast", "forecasted"), ...)  # ❌ Jamais rempli
```

**Exemple JSON EODHD :**
```json
{
  "type": "CPI",
  "actual": 323.98,
  "previous": 323.05,
  "estimate": 323.89,  ← ICI (pas "forecast")
  ...
}
```

### ✅ CODE CORRECT

**Solution temporaire (déjà appliquée) :**
```sql
-- Copier estimate → forecast dans la DB
UPDATE events
SET forecast = estimate
WHERE forecast IS NULL AND estimate IS NOT NULL
```

**Solution permanente (à faire) :**
```python
# Dans eodhd_client.py ligne 162
forecast = pd.to_numeric(
    _col(raw, "forecast", "forecasted", "estimate", "consensus"),  # ← Ajouter estimate
    errors="coerce"
)
```

### 📊 IMPACT

**AVANT correction :**
- Planificateur chargeait `forecast = NULL`
- Fallback implicite sur `previous`
- Surprises sous-estimées
- CPI : 0.4% au lieu de 33.3%

**APRÈS correction :**
```
Événements utilisables :
AVANT : 11 (0.02%)
APRÈS : 26,370 (45.1%)
= ×2,397 fois plus !
```

### 🔒 GARDE-FOU

**Avant tout calcul de surprise :**

1. ✅ Vérifier que forecast existe :
```sql
SELECT 
    COUNT(*) as total,
    COUNT(forecast) as with_forecast,
    ROUND(100.0 * COUNT(forecast) / COUNT(*), 1) as pct
FROM events
```

2. ✅ Si pct < 40% → Investiguer pourquoi

3. ✅ Valider sur cas référence 11 septembre

**Template obligatoire :**
```python
def validate_forecast_availability(con):
    """Vérifie que forecast est disponible"""
    stats = con.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(forecast) as with_forecast
        FROM events
        WHERE actual IS NOT NULL
    """).fetchone()
    
    pct = (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
    
    if pct < 40:
        raise ValueError(f"Seulement {pct:.1f}% des événements ont forecast !")
    
    return True
```

---

## 📋 CHECKLIST COMPLÈTE

Avant tout calcul d'impact :

- [ ] Surprise avec `forecast` UNIQUEMENT (pas previous)
- [ ] Vérifier que forecast existe (> 40% des événements)
- [ ] Timezone convertie en UTC explicite
- [ ] Validation 11 septembre effectuée
- [ ] Cas référence : 33-37 pips
- [ ] Tables dérivées validées avec source + created_at

**Si UN SEUL item échoue → STOP.**

---

## 🎓 LEÇONS GÉNÉRALES

### 1. Toujours vérifier les hypothèses

Ne jamais supposer qu'une colonne existe ou est remplie. **Compter avec SQL.**

### 2. Faire confiance aux observations terrain

Quand l'utilisateur (André) signale un problème, l'investiguer à fond au lieu de supposer que le code est correct.

### 3. Documenter immédiatement

Chaque erreur découverte doit être ajoutée ici **pendant la session**, pas après.

### 4. Nommer selon la réalité

Si l'API appelle un champ `"estimate"`, ne pas le mapper vers `"forecast"` sans fallback.

---

**FIN DU DOCUMENT**

**Dernière mise à jour :** 21 octobre 2025 - Session 27  
**Erreurs documentées :** 4 (#1, #2, #3, #7)  
**Prochaine mise à jour :** Quand une nouvelle erreur récurrente est identifiée
