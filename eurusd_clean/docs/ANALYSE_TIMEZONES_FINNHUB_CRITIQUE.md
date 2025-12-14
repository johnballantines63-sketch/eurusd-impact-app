# Analyse Critique : Gestion des Timezones avec Finnhub

**Date** : 2025-01-XX  
**Statut** : Analyse en cours - CRITIQUE  
**Contexte** : Migration Dukascopy → Finnhub - Vérification cohérence timezones

---

## 🚨 PROBLÈME HISTORIQUE

**Les timezones ont causé 20+ sessions de confusion** selon la documentation. Il est **CRITIQUE** de bien comprendre la situation actuelle avant toute modification.

---

## 📋 SITUATION AVEC DUKASCOPY (Ancien Système)

### Table `events` - Colonne `ts_utc`

**Structure** :
```sql
CREATE TABLE events (
    ts_utc TIMESTAMP WITH TIME ZONE,  -- ⚠️ Nom "ts_utc" mais...
    ...
)
```

**⚠️ CONFUSION MAJEURE** :
- Nom de colonne : `ts_utc` (suggère UTC)
- **RÉALITÉ** : Stocke l'heure **AFFICHÉE** en Bern (Europe/Zurich)
- Exemple : `2025-09-11 14:30:00+02:00` = 14:30 Bern (pas UTC !)

**Documentation trouvée** :
> "Table `events`: ts_utc: 2025-09-11 14:30:00+02:00 → Stocke l'heure **AFFICHÉE** de l'événement (14:30 Bern)"

### Vue `prices_bern` (Dukascopy)

**Structure** :
```sql
CREATE VIEW prices_bern AS
SELECT 
    datetime + INTERVAL '2 hours' as datetime,
    open, high, low, close
FROM prices_1m
```

**Logique** :
- Table source `prices_1m` : Prix stockés en UTC
- Vue `prices_bern` : Ajoute +2h automatiquement
- Résultat : Event 14:30 = Prix 14:30 (logique pure)

**Règle "définitive" Session 112** :
> "Pour un événement stocké à 14:30+02:00 dans la table `events`, chercher les prix à 12:30 dans la table `prices_1m` (soustraire 2 heures)."

**Mais avec vue `prices_bern`** :
> "Event 14:30 → Prix 14:30 (logique pure)"

---

## 🔍 SITUATION ACTUELLE AVEC FINNHUB

### Table `events` - Source Finnhub

**Question critique** : Comment sont stockés les événements Finnhub ?

**Hypothèses** :
1. Même structure que Dukascopy (`ts_utc` = heure Bern affichée) ?
2. Vraie heure UTC ?
3. Autre format ?

**⚠️ À VÉRIFIER** :
- Structure réelle de la table `events`
- Comment Finnhub fournit les timestamps
- Comment ils sont stockés dans la DB

### Tables Prix Finnhub

**Structure documentée** :
```sql
CREATE TABLE prices_finnhub_m1 (
    datetime TIMESTAMP WITH TIME ZONE PRIMARY KEY,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT
)
```

**⚠️ QUESTIONS CRITIQUES** :

1. **Quelle timezone est utilisée** pour `datetime` dans `prices_finnhub_m1` ?
   - UTC ?
   - Europe/Zurich (Bern) ?
   - Autre ?

2. **Y a-t-il une vue équivalente à `prices_bern`** pour Finnhub ?
   - Non mentionné dans la documentation
   - Faut-il en créer une ?

3. **Comment convertir entre événements et prix** ?
   - Même règle -2h que Dukascopy ?
   - Conversion différente ?
   - Logique pure (même heure) ?

---

## 🔎 ANALYSE DES FORMULES DU PIPELINE

### Dans `run_pipeline_complete.py`

**Ligne 207** : Conversion `ts_utc`
```python
df_events['ts_utc'] = pd.to_datetime(df_events['ts_utc'])
```

**Ligne 228** : Utilisation comme anchor_time
```python
anchor_time = cluster_events.iloc[0]['ts_utc']
```

**Lignes 769-772** : Gestion timezone pour anchor_time
```python
if anchor_time.tzinfo is None:
    import pytz
    tz_bern = pytz.timezone('Europe/Zurich')
    anchor_time = tz_bern.localize(anchor_time)
```

**Ligne 811-884** : Mesure d'impact - Fallback Finnhub
```python
# Essayer d'abord avec prices_bern (pour dates récentes)
impact_reel_result = measure_impact_from_dukascopy(...)

# Fallback : mesurer directement depuis prices_finnhub_m1
query = f"""
SELECT datetime, open, high, low, close
FROM prices_finnhub_m1
WHERE datetime >= '{event_datetime}'::TIMESTAMP - INTERVAL '5 minutes'
  AND datetime <= '{event_datetime}'::TIMESTAMP + INTERVAL '120 minutes'
"""
```

**⚠️ PROBLÈMES IDENTIFIÉS** :

1. **`event_datetime` est en quelle timezone ?**
   - Si `anchor_time` vient de `ts_utc` (heure Bern affichée)
   - Comment le convertir pour Finnhub ?

2. **Requête SQL directe sur `prices_finnhub_m1`**
   - Pas de conversion timezone explicite
   - Risque d'incohérence si timezones différentes

3. **Gestion timezone complexe (lignes 850-866)**
   - Beaucoup de code pour normaliser timezones
   - Suggère des problèmes sous-jacents

---

## 📊 COMPARAISON : DUKASCOPY vs FINNHUB

### Scénario : Événement CPI US à 14:30 Bern

**Avec Dukascopy (ancien)** :

1. **Event dans DB** :
   ```sql
   ts_utc: 2025-09-11 14:30:00+02:00  -- Heure affichée Bern
   ```

2. **Prix dans DB** :
   ```sql
   -- Table prices_1m (UTC)
   datetime: 2025-09-11 12:30:00+00:00
   
   -- Vue prices_bern (automatique +2h)
   datetime: 2025-09-11 14:30:00+02:00
   ```

3. **Requête** :
   ```sql
   SELECT * FROM prices_bern 
   WHERE datetime = '2025-09-11 14:30:00'
   -- ✅ Match direct (logique pure)
   ```

**Avec Finnhub (nouveau)** :

1. **Event dans DB** : (⚠️ À vérifier)
   ```sql
   ts_utc: 2025-09-11 14:30:00+02:00  -- Toujours heure Bern ?
   ```

2. **Prix dans DB** : (⚠️ À vérifier)
   ```sql
   -- Table prices_finnhub_m1
   datetime: ???  -- Quelle timezone ?
   ```

3. **Requête actuelle** :
   ```sql
   SELECT * FROM prices_finnhub_m1
   WHERE datetime >= '2025-09-11 14:30:00'::TIMESTAMP - INTERVAL '5 minutes'
   -- ⚠️ Risque : timezone non spécifiée
   ```

---

## ⚠️ QUESTIONS CRITIQUES À RÉSOUDRE

### 1. Structure Réelle de la Base de Données

**Actions requises** :
- ✅ Vérifier structure exacte de `events.ts_utc`
- ✅ Vérifier timezone réelle stockée dans `prices_finnhub_m1.datetime`
- ✅ Tester avec requête SQL directe

**Requêtes de diagnostic** :
```sql
-- 1. Vérifier structure events
DESCRIBE events;

-- 2. Échantillon events
SELECT ts_utc, event_title 
FROM events 
WHERE event_key LIKE '%CPI%' 
LIMIT 5;

-- 3. Vérifier timezone prices_finnhub_m1
SELECT datetime, EXTRACT(TIMEZONE_HOUR FROM datetime) as tz_hour
FROM prices_finnhub_m1 
LIMIT 5;

-- 4. Comparer même moment
SELECT 
    e.ts_utc as event_time,
    p.datetime as price_time,
    EXTRACT(HOUR FROM e.ts_utc) as event_hour,
    EXTRACT(HOUR FROM p.datetime) as price_hour
FROM events e
CROSS JOIN prices_finnhub_m1 p
WHERE DATE(e.ts_utc) = '2025-09-11'
  AND EXTRACT(HOUR FROM e.ts_utc) = 14
  AND DATE(p.datetime) = '2025-09-11'
LIMIT 10;
```

### 2. Correspondance Événements ↔ Prix

**Test nécessaire** :
- Prendre un événement connu (ex: 11 sept 2025 14:30)
- Vérifier quel prix correspond dans `prices_finnhub_m1`
- Déterminer la conversion correcte

**Scénario de test** :
```python
# Événement CPI US 11 sept 2025
event_time = "2025-09-11 14:30:00"  # Heure Bern ?

# Chercher prix correspondant
# Option A : Même heure (14:30)
# Option B : Moins 2h (12:30)
# Option C : Autre conversion

# Vérifier prix réel à 14:30 vs 12:30
```

### 3. Utilisation dans les Formules

**À vérifier** :

1. **Étape 2** : Détection clusters
   - Utilise `ts_utc` directement
   - Pas de conversion explicite

2. **Étape 5** : Calcul tendances
   - Charge prix avec `prices_finnhub_h1`
   - Conversion timezone ? (lignes 607-672)

3. **Étape 6** : Mesure impact
   - Fallback vers `prices_finnhub_m1`
   - Conversion complexe (lignes 850-866)

4. **Étape 8** : Application cluster cible
   - Détection tendance avec `prices_finnhub_m30`
   - Pattern detection avec `prices_finnhub_m1`

**⚠️ PROBLÈME** : Incohérence possible entre les timezones utilisées dans chaque étape

---

## 🎯 PLAN D'ACTION IMMÉDIAT

### Phase 1 : Diagnostic

1. **Analyser structure DB réelle**
   ```bash
   python scripts/diagnostic_timezone_finnhub.py
   ```

2. **Tester correspondance événements/prix**
   - Prendre 3-5 dates de référence
   - Vérifier timezone de chaque table
   - Comparer avec prix réels

3. **Documenter findings**
   - Créer document référence timezone Finnhub
   - Lister tous les cas d'usage

### Phase 2 : Validation

1. **Créer script de test**
   - Test sur date référence (11 sept 2025)
   - Vérifier impact mesuré vs réel
   - Valider conversion timezone

2. **Comparer avec Dukascopy**
   - Même événement avec Dukascopy vs Finnhub
   - Vérifier cohérence résultats

### Phase 3 : Correction (si nécessaire)

1. **Standardiser timezones**
   - Une seule règle claire
   - Fonctions utilitaires

2. **Créer vue équivalente** (si nécessaire)
   - Vue `prices_finnhub_bern` ?
   - Pour logique pure

3. **Mettre à jour pipeline**
   - Utiliser conversion correcte partout
   - Supprimer code redondant

---

## 📝 DOCUMENTATION À CRÉER

### 1. Guide Timezone Finnhub

**Contenu** :
- Structure exacte des tables
- Timezone réelle stockée
- Règle de conversion événements → prix
- Exemples concrets

### 2. Fonctions Utilitaires

**Créer** : `src/core/timezone_utils_finnhub.py`

```python
def convert_event_time_to_price_time(event_timestamp: datetime) -> datetime:
    """Convertit timestamp événement → timestamp prix Finnhub"""
    pass

def ensure_timezone_consistency(ts: datetime, target_tz: str) -> datetime:
    """S'assure qu'un timestamp a la bonne timezone"""
    pass

def query_prices_at_event_time(event_timestamp: datetime) -> pd.DataFrame:
    """Charge prix correspondant à un événement (conversion automatique)"""
    pass
```

### 3. Tests de Validation

**Créer** : `tests/test_timezone_finnhub.py`

```python
def test_event_price_correspondence():
    """Vérifie qu'un événement correspond au bon prix"""
    pass

def test_impact_measurement_timezone():
    """Vérifie que la mesure d'impact utilise les bonnes timezones"""
    pass

def test_pipeline_timezone_consistency():
    """Vérifie cohérence timezone dans tout le pipeline"""
    pass
```

---

## ⚠️ AVERTISSEMENTS

### Ne PAS modifier sans comprendre :

1. ❌ **Ne PAS changer les conversions** sans valider la structure réelle
2. ❌ **Ne PAS supposer** que Finnhub = Dukascopy
3. ❌ **Ne PAS créer de nouvelles règles** sans documentation

### Faire AVANT modifications :

1. ✅ **Analyser la DB réelle** (requêtes SQL)
2. ✅ **Tester sur dates de référence**
3. ✅ **Documenter chaque découverte**
4. ✅ **Valider avec utilisateur**

---

## 📚 RÉFÉRENCES

- `docs/REGLE_TIMEZONE_DEFINITIVE.md` - Règle Session 112 (Dukascopy)
- `docs/SOLUTION_DEFINITIVE_TIMEZONE.md` - Vue prices_bern
- `docs/ARCHITECTURE_FINNHUB.md` - Structure Finnhub
- `scripts/audit_timezone_sources.py` - Audit timezones sources

---

**Status** : ⚠️ ANALYSE EN COURS - NE PAS MODIFIER AVANT VALIDATION




