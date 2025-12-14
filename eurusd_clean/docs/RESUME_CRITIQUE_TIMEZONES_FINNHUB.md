# Résumé Critique : Gestion des Timezones avec Finnhub

**Date** : 2025-01-XX  
**Priorité** : 🔴 CRITIQUE  
**Contexte** : Migration Dukascopy → Finnhub - Vérification cohérence timezones

---

## 🎯 OBJECTIF

**Vérifier et garantir** que les timezones des **événements** et des **prix** correspondent correctement dans toutes les formules du pipeline.

---

## 📋 SITUATION ACTUELLE IDENTIFIÉE

### Événements Finnhub (Table `events`)

**Source** : `scripts/finnhub_import.py`

**Comment c'est stocké** :
- ✅ API Finnhub retourne timestamps en **UTC**
- ✅ Parsé avec `pd.to_datetime(time_str, utc=True)` (ligne 125)
- ✅ Stocké dans DB avec `TIMESTAMP WITH TIME ZONE` en **UTC** (lignes 266-272)
- ✅ Colonne : `ts_utc` (nom correspond au contenu réel)

**Exemple** :
```python
# Event CPI US 11 sept 2025 12:30 UTC (14:30 Bern)
ts_utc: 2025-09-11 12:30:00+00:00  # UTC réel
```

### Prix Finnhub (Table `prices_finnhub_m1`)

**⚠️ NON VÉRIFIÉ** - Besoin de diagnostic :

**Questions critiques** :
1. Quelle timezone est stockée dans `prices_finnhub_m1.datetime` ?
   - UTC ?
   - Europe/Zurich ?
   - Autre ?

2. Comment sont-ils importés ?
   - Script d'import à trouver
   - Conversion timezone effectuée ?

**Documentation trouvée** :
- Structure : `datetime TIMESTAMP WITH TIME ZONE`
- Mais timezone réelle **non documentée**

---

## ⚠️ PROBLÈMES IDENTIFIÉS

### 1. Conversion Événements → Prix (Étape 6 Pipeline)

**Fichier** : `scripts/run_pipeline_complete.py` lignes 830-884

**Code actuel** :
```python
# Fallback vers prices_finnhub_m1
query = f"""
SELECT datetime, open, high, low, close
FROM prices_finnhub_m1
WHERE datetime >= '{event_datetime}'::TIMESTAMP - INTERVAL '5 minutes'
  AND datetime <= '{event_datetime}'::TIMESTAMP + INTERVAL '120 minutes'
"""
```

**⚠️ PROBLÈMES** :
- `event_datetime` vient de `anchor_time` (ligne 834)
- `anchor_time` vient de `ts_utc` des événements (UTC)
- **Mais** : Gestion timezone complexe (lignes 850-866)
- **Risque** : Si prix sont en UTC → OK, sinon → INCOHÉRENCE

### 2. Utilisation dans les Formules

**Étape 5** (Tendances) :
- Utilise `prices_finnhub_h1` (ligne 607)
- Conversion timezone ? À vérifier

**Étape 6** (Impacts) :
- Fallback `prices_finnhub_m1` avec conversion complexe
- Risque d'erreur si timezone incorrecte

**Étape 8** (Cluster cible) :
- Utilise `prices_finnhub_m30` (ligne 1065)
- Utilise `prices_finnhub_m1` pour patterns (ligne 1431)
- Conversions multiples → Risque d'incohérence

---

## 🔍 DIFFÉRENCE AVEC DUKASCOPY

### Ancien Système (Dukascopy)

| Élément | Timezone |
|---------|----------|
| Events `ts_utc` | ⚠️ Nom UTC mais stockait heure Bern affichée |
| Prix `prices_1m` | UTC réel |
| Vue `prices_bern` | Bern (+2h automatique) |
| **Règle** | Event 14:30 → Prix 14:30 (via vue) |

### Nouveau Système (Finnhub)

| Élément | Timezone |
|---------|----------|
| Events `ts_utc` | ✅ UTC réel (vérifié) |
| Prix `prices_finnhub_m1` | ⚠️ **INCONNU** |
| Vue équivalente ? | ❌ Pas de vue `prices_finnhub_bern` |
| **Règle** | ⚠️ **À DÉTERMINER** |

---

## 🎯 ACTIONS IMMÉDIATES REQUISES

### Action 1 : Diagnostic DB Réelle

**Créer script** : `scripts/diagnostic_timezone_finnhub.py`

**Objectifs** :
1. Vérifier timezone réelle stockée dans `prices_finnhub_m1.datetime`
2. Comparer avec événements pour même moment
3. Identifier conversion nécessaire

**Requêtes SQL** :
```sql
-- 1. Structure table
DESCRIBE prices_finnhub_m1;

-- 2. Échantillon prix avec timezone
SELECT 
    datetime,
    EXTRACT(TIMEZONE_HOUR FROM datetime) as tz_hour,
    EXTRACT(HOUR FROM datetime) as hour,
    open, close
FROM prices_finnhub_m1 
WHERE DATE(datetime) = '2025-09-11'
LIMIT 10;

-- 3. Comparer event vs prix même moment
SELECT 
    e.ts_utc as event_utc,
    EXTRACT(HOUR FROM e.ts_utc) as event_hour,
    p.datetime as price_datetime,
    EXTRACT(HOUR FROM p.datetime) as price_hour,
    p.open, p.close
FROM events e
CROSS JOIN prices_finnhub_m1 p
WHERE DATE(e.ts_utc) = '2025-09-11'
  AND EXTRACT(HOUR FROM e.ts_utc) = 12  -- CPI US en UTC
  AND DATE(p.datetime) = '2025-09-11'
LIMIT 10;
```

### Action 2 : Tester Correspondance

**Scénario de test** :
- Date : 2025-09-11 (CPI US)
- Event : 12:30 UTC (14:30 Bern)
- Chercher prix correspondant dans `prices_finnhub_m1`

**Questions** :
- Prix à 12:30 UTC ?
- Prix à 14:30 UTC ?
- Conversion nécessaire ?

### Action 3 : Documenter Règle Claire

**Une fois diagnostic fait** :

1. **Si prix en UTC** :
   - ✅ Logique simple : Event UTC = Prix UTC
   - Pas de conversion nécessaire

2. **Si prix en autre timezone** :
   - Créer fonction de conversion standardisée
   - Documenter règle claire

3. **Créer vue équivalente** (si nécessaire) :
   - Vue `prices_finnhub_bern` ?
   - Pour logique pure comme Dukascopy

---

## 📝 RÈGLES À ÉTABLIR

### Règle 1 : Correspondance Événements ↔ Prix

**À définir après diagnostic** :
- Event à 12:30 UTC → Prix à ??? UTC (ou autre timezone)

### Règle 2 : Utilisation dans le Pipeline

**Standardiser** :
- Une seule fonction de conversion
- Utilisée partout dans le pipeline
- Tests de validation

### Règle 3 : Fonctions Utilitaires

**Créer** : `src/core/timezone_utils_finnhub.py`

```python
def convert_event_to_price_time(event_ts: datetime) -> datetime:
    """Convertit timestamp événement → timestamp prix Finnhub"""
    pass

def get_prices_at_event(event_ts: datetime) -> pd.DataFrame:
    """Charge prix correspondant à un événement"""
    pass
```

---

## ⚠️ AVERTISSEMENTS

### Ne PAS faire avant diagnostic :

1. ❌ Modifier conversions existantes
2. ❌ Créer nouvelles fonctions
3. ❌ Supposer timezone des prix

### Faire AVANT modifications :

1. ✅ Diagnostic DB réelle (script SQL)
2. ✅ Test correspondance sur date référence
3. ✅ Documentation claire
4. ✅ Validation avec utilisateur

---

## 📊 PROCHAINES ÉTAPES

1. **IMMÉDIAT** : Créer script diagnostic timezone
2. **IMMÉDIAT** : Exécuter diagnostic sur DB réelle
3. **ENSEMBLE** : Analyser résultats avec utilisateur
4. **ENSEMBLE** : Établir règle claire
5. **ENSUITE** : Mettre à jour pipeline si nécessaire

---

## 📚 RÉFÉRENCES

- `docs/ANALYSE_TIMEZONES_FINNHUB_CRITIQUE.md` - Analyse détaillée
- `docs/REGLE_TIMEZONE_DEFINITIVE.md` - Règle Dukascopy (Session 112)
- `scripts/finnhub_import.py` - Import événements
- `scripts/run_pipeline_complete.py` - Pipeline (étapes 5, 6, 8)

---

**Status** : ⚠️ EN ATTENTE DIAGNOSTIC - NE PAS MODIFIER AVANT VALIDATION




