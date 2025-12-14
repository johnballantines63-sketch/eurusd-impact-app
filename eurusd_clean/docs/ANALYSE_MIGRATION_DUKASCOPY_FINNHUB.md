# Analyse : Migration Dukascopy → Finnhub pour Mesure d'Impact

**Date** : 2025-01-XX  
**Statut** : Analyse en cours

## 🎯 Problème Identifié

L'utilisateur confirme que **tous les prix viennent maintenant de Finnhub** et non plus de Dukascopy. Cependant, le pipeline utilise encore des fonctions qui référencent Dukascopy.

## 📍 Références à Dukascopy dans le Code

### 1. Module `src/core/impact_measurement.py`

**Fonction problématique** : `measure_impact_from_dukascopy()`

**Problèmes identifiés** :
- ✅ Utilise la table `prices_bern` (vue Dukascopy) - ligne 89
- ✅ Nom de fonction indique explicitement "dukascopy"
- ✅ Documentation mentionne "prix Dukascopy"

**Code actuel** (lignes 87-93) :
```python
query = f"""
SELECT datetime, open, high, low, close
FROM prices_bern
WHERE datetime >= '{event_datetime}'::TIMESTAMP - INTERVAL '{lookback_minutes} minutes'
  AND datetime <= '{event_datetime}'::TIMESTAMP + INTERVAL '{lookahead_minutes} minutes'
ORDER BY datetime ASC
"""
```

### 2. Pipeline `scripts/run_pipeline_complete.py`

**Étape 6** (lignes 817-884) :

**Stratégie actuelle** :
1. Essayer `measure_impact_from_dukascopy()` avec `prices_bern` (dates récentes)
2. Fallback vers `prices_finnhub_m1` directement (dates historiques)

**Problèmes** :
- ⚠️ Logique redondante (mesure d'impact dupliquée dans le fallback)
- ⚠️ Dépendance à `prices_bern` qui peut ne plus exister
- ⚠️ Double code pour la même fonctionnalité

**Code actuel** (lignes 817-824) :
```python
# Essayer d'abord avec prices_bern (pour dates récentes)
impact_reel_result = measure_impact_from_dukascopy(
    db_path=self.db_path,
    event_timestamp=anchor_time,
    lookback_minutes=5,
    lookahead_minutes=120,
    debug=False
)
```

**Fallback** (lignes 830-884) :
- Logique complète de mesure d'impact directement avec `prices_finnhub_m1`
- Gestion des timezones manuelle

## 🔍 Différences Clés : Dukascopy vs Finnhub

### Tables de Prix

| Dukascopy | Finnhub |
|-----------|---------|
| `prices_bern` (vue) | `prices_finnhub_m1` |
| `prices_1m` | `prices_finnhub_m1` |
| `prices_1h` | `prices_finnhub_h1` |

### Timezone

- **Dukascopy** : `prices_bern` = vue avec datetime en heure Bern (Europe/Zurich)
- **Finnhub** : Tables `prices_finnhub_*` avec `datetime TIMESTAMP WITH TIME ZONE`

**Note** : La vue `prices_bern` était créée pour simplifier (datetime + 2h), mais avec Finnhub, les timezones sont gérées différemment.

## ✅ Solution Proposée

### Option 1 : Créer une Nouvelle Fonction Finnhub (RECOMMANDÉ)

**Avantages** :
- ✅ Séparation claire des responsabilités
- ✅ Pas de risque de casser le code existant
- ✅ Facilite la transition progressive
- ✅ Nom explicite

**Fonction proposée** : `measure_impact_from_finnhub()`

**Fichier** : `src/core/impact_measurement.py` (ajouter)

**Logique** :
- Utiliser `prices_finnhub_m1` directement
- Gérer les timezones correctement (Finnhub stocke en UTC avec timezone)
- Conserver la même interface que `measure_impact_from_dukascopy()` pour compatibilité

### Option 2 : Adapter la Fonction Existante

**Avantages** :
- ✅ Une seule fonction à maintenir
- ✅ Moins de duplication

**Inconvénients** :
- ⚠️ Nom ambigu si on garde "dukascopy"
- ⚠️ Risque de régression si code existant dépend de `prices_bern`
- ⚠️ Besoin de paramètre pour choisir la source

**Fonction adaptée** : `measure_impact_from_prices()`

## 📝 Plan d'Action Recommandé

### Étape 1 : Créer Fonction Finnhub

Créer `measure_impact_from_finnhub()` dans `src/core/impact_measurement.py` :

```python
def measure_impact_from_finnhub(
    db_path: Path,
    event_timestamp: datetime,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120,
    debug: bool = False
) -> Dict:
    """
    Mesure l'impact réel EUR/USD depuis prix Finnhub.
    
    VERSION 1.0 - FINNHUB NATIF:
    - Utilise prices_finnhub_m1 directement
    - Gère timezones UTC correctement
    
    Args:
        db_path: Chemin vers warehouse.duckdb
        event_timestamp: Timestamp événement (peut être avec timezone)
        lookback_minutes: Minutes avant (défaut 5)
        lookahead_minutes: Minutes après (défaut 120)
        debug: Afficher infos debug
    
    Returns:
        dict avec impact_pips, direction, etc. ou None si échec
    """
```

**Logique** :
- Convertir `event_timestamp` en UTC si nécessaire
- Requête directe sur `prices_finnhub_m1`
- Même calcul d'impact que la fonction Dukascopy

### Étape 2 : Mettre à Jour le Pipeline

**Dans `scripts/run_pipeline_complete.py`** :

**Changement** :
- Remplacer `measure_impact_from_dukascopy()` par `measure_impact_from_finnhub()`
- Supprimer le fallback redondant (lignes 830-884)
- Simplifier la logique

**Code proposé** :
```python
# === MESURE IMPACT RÉEL ===
# Utiliser directement prices_finnhub_m1
impact_reel = 0.0
direction = 0

try:
    from core.impact_measurement import measure_impact_from_finnhub
    
    impact_reel_result = measure_impact_from_finnhub(
        db_path=self.db_path,
        event_timestamp=anchor_time,
        lookback_minutes=5,
        lookahead_minutes=120,
        debug=False
    )
    
    if impact_reel_result:
        impact_reel = impact_reel_result['impact_pips']
        direction = impact_reel_result['direction']
except Exception as e:
    self._log(f"   ⚠️ Erreur mesure impact réel pour {cluster_date}: {e}", "WARNING")
```

### Étape 3 : Vérifier Autres Références

**Fichiers à vérifier** :
- ✅ `src/config.py` : Vérifier `DB_TABLE_PRICES`
- ✅ Autres scripts qui utilisent `measure_impact_from_dukascopy()`
- ✅ Documentation

## 🔧 Détails Techniques

### Gestion des Timezones

**Finnhub** :
- Stocke `datetime` en UTC avec timezone
- Format : `TIMESTAMP WITH TIME ZONE`

**Conversion nécessaire** :
```python
# Si event_timestamp n'a pas de timezone, localiser en Europe/Zurich
if event_timestamp.tzinfo is None:
    tz_bern = pytz.timezone('Europe/Zurich')
    event_timestamp = tz_bern.localize(event_timestamp)

# Convertir en UTC pour requête
event_timestamp_utc = event_timestamp.astimezone(pytz.UTC)
```

### Table Finnhub à Utiliser

**Recommandation** : `prices_finnhub_m1`
- ✅ Résolution 1 minute = précision maximale
- ✅ Données historiques complètes (10 ans)
- ✅ Cohérent avec logique actuelle (M1 pour mesure d'impact)

## ⚠️ Points d'Attention

1. **Compatibilité** : Vérifier que toutes les dates historiques ont des données dans `prices_finnhub_m1`

2. **Performance** : Vérifier que les requêtes sur `prices_finnhub_m1` sont performantes (index sur `datetime`)

3. **Timezone** : S'assurer que la conversion timezone est correcte pour tous les cas

4. **Tests** : Valider avec quelques dates de référence connues

## 📊 Validation

**Cas de test recommandés** :
- Date récente avec données : 2025-09-11 (CPI US)
- Date historique : 2024-09-11 (comparaison)
- Vérifier que les impacts mesurés sont cohérents

## 🚀 Actions Immédiates

1. ✅ **ANALYSE COMPLÈTE** (ce document)
2. ⏳ **CRÉER FONCTION** `measure_impact_from_finnhub()`
3. ⏳ **METTRE À JOUR PIPELINE** pour utiliser Finnhub uniquement
4. ⏳ **TESTS** sur dates de référence
5. ⏳ **VALIDATION** avec utilisateur

---

**Note** : L'utilisateur a demandé de ne rien modifier sans accord explicite. Ce document est une proposition d'analyse et de solution.




