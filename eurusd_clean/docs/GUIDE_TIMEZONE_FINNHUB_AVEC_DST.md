# Guide Timezone Finnhub avec Gestion DST (Heure Hiver/Été)

**Date** : 2025-01-XX  
**Priorité** : 🔴 CRITIQUE  
**Contexte** : Migration Dukascopy → Finnhub - Gestion correcte des timezones avec DST

---

## 🎯 PROBLÈME IDENTIFIÉ PAR L'UTILISATEUR

**Point critique** :
> "Dukascopy stockait en UTC+2h et pas Finnhub mais si on peut vérifier et éviter les erreurs et les conversions multiple c'est essentiel. Il faut aussi penser à gérer l'heure d'hiver et d'été. Par exemple on sait que le cluster d'event d'US du 11.09 démarre à 14h30 s'il est stocké à 13h30 et qu'on est à l'heure d'hiver ce qui est le cas aujourd'hui il faudra en tenir compte."

**⚠️ IMPORTANT** : L'utilisateur indique que tout est **À VÉRIFIER**, pas des faits établis.

---

## 📋 COMPRÉHENSION À VÉRIFIER

### Dukascopy (Ancien Système)

**Hypothèse à vérifier** :
- Stockait peut-être en **UTC+2h** (à confirmer par diagnostic)
- Vue `prices_bern` : Ajoutait +2h automatiquement (à vérifier)
- Résultat attendu : Event 14:30 = Prix 14:30 (logique pure)

### Finnhub (Nouveau Système)

**À vérifier** :
- Comment stocke-t-il réellement les prix ?
- Gestion DST différente de Dukascopy ?
- Quelle timezone est réellement stockée ?

### Gestion DST (Daylight Saving Time)

**Europe/Zurich (Bern)** :
- **ÉTÉ** (mars → octobre) : UTC+2
- **HIVER** (novembre → février) : UTC+1

**Exemple à vérifier** :
- **11 septembre 2025** : ÉTÉ (UTC+2)
  - Event CPI US : 14:30 Bern = 12:30 UTC (en théorie)
  - **À VÉRIFIER** : Comment est-il réellement stocké dans la DB ?

- **15 janvier 2025** : HIVER (UTC+1)
  - Event CPI US : 14:30 Bern = 13:30 UTC (en théorie)
  - **À VÉRIFIER** : Comment est-il réellement stocké dans la DB ?

**⚠️ À VÉRIFIER** : 
- Comment les données sont-elles réellement stockées ?
- Y a-t-il un offset fixe ou gestion DST automatique ?
- Quelles conversions sont nécessaires ?

---

## 🔍 DIAGNOSTIC REQUIS

### Script Créé

**Fichier** : `scripts/diagnostic_timezone_complet.py`

**Fonctionnalités** :
1. ✅ Analyse timezone réelle des événements (`events.ts_utc`)
2. ✅ Analyse timezone réelle des prix Dukascopy (`prices_1m`)
3. ✅ Analyse timezone réelle des prix Finnhub (`prices_finnhub_m1`)
4. ✅ Comparaison événements ↔ prix pour même moment
5. ✅ Détection automatique heure été/hiver (DST)
6. ✅ Test sur dates référence (été + hiver)

### Commandes de Diagnostic

```bash
# Lancer le diagnostic complet
python scripts/diagnostic_timezone_complet.py

# Le script va :
# - Analyser toutes les tables de prix
# - Comparer avec événements CPI US
# - Identifier les timezones réelles
# - Détecter les problèmes DST
```

---

## 📊 SCÉNARIOS DE TEST

### Scénario 1 : Date Été (11 septembre 2025)

**Événement attendu** :
- CPI US à **14:30 Bern** (heure d'été UTC+2)
- En UTC : **12:30 UTC**

**Questions à vérifier** :
1. Comment est stocké dans `events.ts_utc` ?
   - 12:30 UTC ✅ ?
   - 13:30 UTC ❌ ?
   - 14:30 UTC+2 ❌ ?

2. Comment sont stockés les prix ?
   - Dukascopy : À quelle heure pour ce moment ?
   - Finnhub : À quelle heure pour ce moment ?

3. Correspondance :
   - Event 12:30 UTC → Prix 12:30 UTC ✅ ?
   - Ou conversion nécessaire ?

### Scénario 2 : Date Hiver (15 janvier 2025)

**Événement attendu** :
- CPI US à **14:30 Bern** (heure d'hiver UTC+1)
- En UTC : **13:30 UTC**

**Questions à vérifier** :
1. Même que scénario 1 mais avec offset différent
2. Vérifier que DST est bien géré

---

## ⚠️ PROBLÈMES POTENTIELS IDENTIFIÉS

### Problème 1 : Stockage avec Offset Fixe

**Si prix stockés en UTC+2 fixe** :
- ✅ Correct en été
- ❌ Incorrect en hiver (devrait être UTC+1)

**Solution** :
- Utiliser `TIMESTAMP WITH TIME ZONE` correctement
- Laisser DuckDB gérer DST automatiquement

### Problème 2 : Conversions Multiples

**Si plusieurs conversions** :
- Event → Conversion 1 → Conversion 2 → Prix
- Risque d'erreurs cumulées

**Solution** :
- Une seule source de vérité
- Fonction de conversion standardisée

### Problème 3 : Incohérence DST

**Si DST mal géré** :
- Même événement (14:30 Bern) → Heures UTC différentes selon saison
- Risque d'utiliser mauvaise heure

**Solution** :
- Toujours convertir via `pytz.timezone('Europe/Zurich')`
- Utiliser `.astimezone()` pour conversions

---

## ✅ SOLUTIONS PROPOSÉES

### Solution 1 : Fonction de Conversion Standardisée

**Créer** : `src/core/timezone_utils_finnhub.py`

```python
import pytz
from datetime import datetime

TZ_BERN = pytz.timezone('Europe/Zurich')
TZ_UTC = pytz.UTC

def convert_bern_to_utc(bern_time: datetime, is_dst: bool = None) -> datetime:
    """
    Convertit une heure Bern en UTC en gérant DST automatiquement.
    
    Args:
        bern_time: Datetime en heure Bern (peut être naive ou aware)
        is_dst: Si None, détecte automatiquement via pytz
    
    Returns:
        Datetime en UTC (timezone-aware)
    """
    # Si naive, localiser en Bern
    if bern_time.tzinfo is None:
        bern_time = TZ_BERN.localize(bern_time)
    
    # Convertir en UTC (pytz gère DST automatiquement)
    return bern_time.astimezone(TZ_UTC)

def get_price_time_from_event(event_ts_utc: datetime) -> datetime:
    """
    Obtient le timestamp prix correspondant à un événement.
    
    Si événements et prix sont tous les deux en UTC, retourne tel quel.
    Sinon, applique conversion nécessaire.
    
    Args:
        event_ts_utc: Timestamp événement (en UTC)
    
    Returns:
        Timestamp pour requête prix (même timezone que prix dans DB)
    """
    # À déterminer après diagnostic
    # Si prix en UTC : retourner tel quel
    # Si prix en autre timezone : convertir
    pass
```

### Solution 2 : Vue Finnhub avec Conversion Automatique

**Créer vue équivalente à `prices_bern`** :

```sql
-- Vue pour prix Finnhub en heure Bern (gère DST automatiquement)
CREATE VIEW prices_finnhub_bern AS
SELECT 
    datetime AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich' as datetime,
    open, high, low, close, volume
FROM prices_finnhub_m1
```

**Avantages** :
- Conversion automatique (pas de risque d'oubli)
- Gestion DST automatique
- Logique pure : Event 14:30 = Prix 14:30

### Solution 3 : Tests de Validation

**Créer** : `tests/test_timezone_dst.py`

```python
def test_summer_event():
    """Test événement en été"""
    # Date été (11 sept 2025)
    # Event 14:30 Bern = 12:30 UTC
    # Vérifier correspondance prix

def test_winter_event():
    """Test événement en hiver"""
    # Date hiver (15 jan 2025)
    # Event 14:30 Bern = 13:30 UTC
    # Vérifier correspondance prix

def test_dst_transition():
    """Test transition DST"""
    # Avant/après changement heure
    # Vérifier que conversion est correcte
```

---

## 🎯 PLAN D'ACTION

### Phase 1 : Diagnostic (IMMÉDIAT)

1. ✅ **Script créé** : `scripts/diagnostic_timezone_complet.py`
2. ⏳ **Lancer diagnostic** :
   ```bash
   python scripts/diagnostic_timezone_complet.py
   ```
3. ⏳ **Analyser résultats** :
   - Identifier timezones réelles
   - Détecter problèmes DST
   - Comparer Dukascopy vs Finnhub

### Phase 2 : Analyse des Résultats (ENSEMBLE)

1. ⏳ Examiner sortie du diagnostic
2. ⏳ Identifier conversions nécessaires
3. ⏳ Déterminer règle claire (comme Session 112)

### Phase 3 : Mise en Place (ENSUITE)

1. ⏳ Créer fonctions utilitaires standardisées
2. ⏳ Créer vue Finnhub si nécessaire
3. ⏳ Mettre à jour pipeline avec conversions correctes
4. ⏳ Tests de validation

---

## 📝 EXEMPLES À VÉRIFIER

### Cas : CPI US 11 septembre 2025 (ÉTÉ)

**Événement réel** :
- Heure publication : **14:30 Europe/Zurich**
- En UTC (été) : **12:30 UTC** (14:30 - 2h) - **en théorie**

**⚠️ À VÉRIFIER DANS LA DB** :

1. **Comment est réellement stocké events.ts_utc ?**
   - 12:30 UTC ? ✅ (si UTC)
   - 13:30 UTC ? ⚠️ (si autre système)
   - 14:30 avec offset ? ⚠️ (si stocké en heure Bern)

2. **Pour trouver prix correspondant** :
   - **À VÉRIFIER** : Comment sont stockés les prix ?
   - Quelle conversion est nécessaire ?

3. **Résultat diagnostic déterminera** :
   - Si vue `prices_finnhub_bern` est nécessaire
   - Quelle conversion appliquer

### Cas : CPI US 15 janvier 2025 (HIVER)

**Événement réel** :
- Heure publication : **14:30 Europe/Zurich**
- En UTC (hiver) : **13:30 UTC** (14:30 - 1h) - **en théorie**

**⚠️ DIFFÉRENCE POTENTIELLE** : Offset change selon saison !

**À VÉRIFIER DANS LA DB** :

1. **Comment est réellement stocké events.ts_utc en hiver ?**
   - 13:30 UTC ? ✅ (si UTC avec DST)
   - 12:30 UTC ? ❌ (si offset fixe)
   - Autre ?

2. **Comparer avec été** :
   - Même système de stockage ?
   - DST bien géré ?

---

## 🚀 PROCHAINE ÉTAPE IMMÉDIATE

**Lancer le diagnostic** :

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/diagnostic_timezone_complet.py
```

**Résultats attendus** :
- Analyse complète des timezones
- Identification problèmes DST
- Comparaison Dukascopy vs Finnhub
- Recommandations pour corrections

---

## 📚 RÉFÉRENCES

- `scripts/diagnostic_timezone_complet.py` - Script diagnostic
- `docs/ANALYSE_TIMEZONES_FINNHUB_CRITIQUE.md` - Analyse détaillée
- `docs/RESUME_CRITIQUE_TIMEZONES_FINNHUB.md` - Résumé exécutif
- `docs/REGLE_TIMEZONE_DEFINITIVE.md` - Règle Dukascopy (Session 112)

---

**Status** : ⏳ EN ATTENTE DIAGNOSTIC - Script prêt à lancer

