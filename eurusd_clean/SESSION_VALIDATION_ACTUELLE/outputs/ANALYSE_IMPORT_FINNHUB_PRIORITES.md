# 📊 ANALYSE : POSSIBILITÉS D'IMPORT DEPUIS FINNHUB

**Date** : 2025-12-09  
**Objectif** : Évaluer si Finnhub peut fournir les données manquantes pour les 5 priorités

---

## 📋 RÉSUMÉ EXÉCUTIF

### ✅ Disponible via Finnhub (structure actuelle)

1. **estimate** : ✅ Présent (champ `estimate`)
2. **previous** : ✅ Présent (champ `prev` dans Finnhub, mappé à `previous` en DB)
3. **actual** : ✅ Présent
4. **event, country, time** : ✅ Présents

### ⚠️ Partiellement disponible / À tester

1. **Forecast pour Bills** : `estimate` existe, mais peut être NULL pour Bills
2. **Historique EIA** : Disponible via import historique, mais limite de période à vérifier

### ❌ Non disponible (structure actuelle)

1. **forecast séparé** : Finnhub n'a pas de champ `forecast` distinct (seulement `estimate`)
2. **forecast_std / dispersion** : Non présent
3. **n_contributors** : Non présent
4. **revision / preliminary flag** : Non présent dans la structure

---

## 🔍 DÉTAIL PAR PRIORITÉ

### PRIORITÉ #1 : Forecast / Consensus pour Bill Auctions ⚠️

**Ce qui manque** : `estimate` est NULL pour la plupart des Bills actuels.

**Ce que Finnhub fournit** :
- ✅ Champ `estimate` dans la structure
- ✅ Champ `prev` (previous) toujours présent
- ❌ Pas de champ `forecast` séparé

**Analyse du code actuel** (`finnhub_import.py` ligne 145-163) :
```python
estimate = event.get('estimate')  # ✅ Récupéré
previous = event.get('prev')       # ✅ Récupéré
forecast = None                     # ❌ Toujours NULL (ligne 177)
```

**Recommandation** :
1. **Test sur historique** : Vérifier si `estimate` existe pour Bills dans les données historiques Finnhub
2. **Fallback previous** : Si `estimate` NULL mais `prev` présent, utiliser `previous` comme estimate pour Bills uniquement
3. **Limitation** : Si Finnhub ne fournit vraiment pas `estimate` pour Bills, il faudra :
   - Soit accepter que Bills ne peut pas utiliser surprise
   - Soit chercher une source alternative (TradingEconomics, Bloomberg API, etc.)

**Plan d'action** :
```python
# Modifier parse_finnhub_event pour Bills
if 'bill' in event_key.lower() or 'auction' in event_key.lower():
    if estimate is None and previous is not None:
        estimate = previous  # Utiliser previous comme estimate
```

---

### PRIORITÉ #2 : Historique plus long pour EIA ✅

**Ce qui manque** : Historique EIA insuffisant (< seuil MIN_EVENTS_FOR_SCORE=20).

**Ce que Finnhub fournit** :
- ✅ API supporte import historique (testé dans `finnhub_import_historical.py`)
- ✅ Pas de limite de période apparente (vérifier avec Finnhub Premium)

**Plan d'action** :
1. **Import historique 3+ ans** :
   ```bash
   python scripts/finnhub_import.py \
     --from-date 2022-01-01 \
     --to-date 2025-12-09
   ```
2. **Vérifier couverture EIA** :
   - Compter événements EIA après import
   - Vérifier si chaque event_key EIA dépasse MIN_EVENTS_FOR_SCORE=20

**Effort** : ⚠️ **Élevé** (import 3+ ans peut prendre du temps, vérifier limites API)

---

### PRIORITÉ #3 : Normalisation / Mapping propre des event_keys ✅

**Ce qui manque** : Doublons ("3 month bill" vs "3-month bill"), fragmentation Secondary.

**Ce que Finnhub fournit** :
- ✅ Champ `event` (event_name) standardisé
- ✅ Fonction `normalize_event_key` déjà présente (lignes 82-105)

**Analyse code actuel** :
```python
def normalize_event_key(event_name: str, country: str) -> str:
    # Retire préfixe pays
    # Normalise : minuscules, retirer ponctuation
    # Normalise espaces
```

**Problème identifié** :
- La normalisation actuelle peut créer des collisions :
  - "3 month bill auction" → "3 month bill auction"
  - "3-month bill auction" → "3 month bill auction" ✅ (bon)
  - Mais "3 month" vs "3-Month" peut créer des variantes si preprocessing différent

**Recommandation** :
1. **Améliorer normalisation** :
   ```python
   # Ajouter normalisation tirets/hyphens
   key = re.sub(r'[-–—]', ' ', key)  # Convertir tous types de tirets en espaces
   ```
2. **Créer table de mapping manuel** :
   - Identifier les variantes restantes après normalisation
   - Créer `event_key_mapping.csv` avec correspondances
   - Appliquer mapping avant insertion DB

**Effort** : ✅ **Faible-Moyen** (normalisation code simple, mapping manuel si nécessaire)

---

### PRIORITÉ #4 : Forecast Quality / Dispersion ❌

**Ce qui manque** : `forecast_std`, `survey_dispersion`, `n_contributors`.

**Ce que Finnhub fournit** :
- ❌ Aucun champ de dispersion dans la structure actuelle
- ❌ Pas de champ `forecast_std`
- ❌ Pas de champ `n_contributors`

**Alternatives possibles** :
1. **Calculer dispersion manuellement** :
   - Collecter plusieurs sources de forecast (si disponibles)
   - Calculer std manuellement
   - ⚠️ Nécessite sources multiples

2. **Utiliser autre source** :
   - TradingEconomics API (si premium)
   - Bloomberg API (très cher)
   - Consensus Economics (payant)

**Recommandation** :
- ⚠️ **Déprioriser** cette priorité pour l'instant
- Si vraiment nécessaire, explorer TradingEconomics ou accepter que `estimate` seul doit suffire

**Effort** : ❌ **Très élevé / Impossible via Finnhub seul**

---

### PRIORITÉ #5 : Révisions / Final vs Preliminary ❌

**Ce qui manque** : Flag `revision`, `preliminary` vs `final`.

**Ce que Finnhub fournit** :
- ❌ Aucun champ de révision dans la structure actuelle
- ❌ Pas de flag `preliminary`/`final`

**Alternatives possibles** :
1. **Détecter révisions via comparaison** :
   - Comparer `previous` actuel avec `previous` d'un événement précédent
   - Si différent → révision détectée
   - ⚠️ Complexe et peu fiable

2. **Utiliser autre source** :
   - TradingEconomics API
   - FRED API (gratuit, mais US seulement)

**Recommandation** :
- ⚠️ **Déprioriser** cette priorité pour l'instant
- Focus sur Priorités #1, #2, #3 d'abord

**Effort** : ❌ **Très élevé / Impossible via Finnhub seul**

---

## 📊 PLAN D'ACTION RECOMMANDÉ

### Phase 1 : Quick Wins (1-2 jours)

1. **P1.1 : Tester estimate pour Bills** ✅
   - Script pour vérifier % de Bills avec `estimate` dans historique
   - Si > 50% → pas de problème, juste besoin d'historique
   - Si < 50% → implémenter fallback `previous` comme `estimate`

2. **P1.2 : Améliorer normalisation event_keys** ✅
   - Ajouter normalisation tirets
   - Tester sur échantillon pour détecter collisions restantes

### Phase 2 : Import Historique (2-3 jours)

3. **P2.1 : Import historique EIA** ⚠️
   - Importer 3+ ans d'historique
   - Vérifier couverture EIA après import
   - Valider que event_keys EIA passent seuil MIN_EVENTS_FOR_SCORE

### Phase 3 : Fallback Bills (1 jour)

4. **P3.1 : Implémenter fallback previous pour Bills** (si nécessaire)
   - Modifier `parse_finnhub_event` pour utiliser `previous` si `estimate` NULL
   - Tester impact sur calcul surprise

### Phase 4 : Sources Alternatives (optionnel, si nécessaire)

5. **P4.1 : Explorer TradingEconomics API** (si Finnhub insuffisant)
   - Vérifier disponibilité forecast Bills
   - Comparer structure avec Finnhub
   - Déterminer effort d'intégration

---

## 🔧 MODIFICATIONS CODE PROPOSÉES

### Modification 1 : Fallback previous pour Bills

**Fichier** : `scripts/finnhub_import.py`

**Ligne** : ~163

**Avant** :
```python
actual = to_float(actual)
estimate = to_float(estimate)
previous = to_float(previous)
```

**Après** :
```python
actual = to_float(actual)
estimate = to_float(estimate)
previous = to_float(previous)

# Fallback : Pour Bills, utiliser previous comme estimate si estimate manquant
event_key_lower = normalize_event_key(event_name, country).lower()
if ('bill' in event_key_lower or 'auction' in event_key_lower) and estimate is None and previous is not None:
    estimate = previous
    print(f"   ⚠️  Bills: estimate manquant, utilisation previous={previous} comme estimate")
```

### Modification 2 : Amélioration normalisation

**Fichier** : `scripts/finnhub_import.py`

**Ligne** : ~100

**Avant** :
```python
key = re.sub(r'[^\w\s]', '', key)  # Retirer ponctuation
```

**Après** :
```python
# Normaliser tirets (tous types) en espaces
key = re.sub(r'[-–—]', ' ', key)
# Retirer ponctuation restante
key = re.sub(r'[^\w\s]', '', key)
```

---

## 📊 RÉSULTATS ATTENDUS

### Après Phase 1 + 2 + 3 :

1. **Bills** :
   - ✅ Estimate disponible (via fallback si nécessaire)
   - ✅ Surprise calculable
   - ✅ Bills réintégré dans le modèle

2. **EIA** :
   - ✅ Historique 3+ ans importé
   - ✅ Event_keys EIA passent seuil MIN_EVENTS_FOR_SCORE
   - ✅ EIA présent dans alpha_weights

3. **Event_keys** :
   - ✅ Normalisation améliorée
   - ✅ Moins de collisions/variantes

### Impact attendu sur signal directionnel :

- **Bills réintégré** : +5-10% événements utilisables (selon fréquence)
- **EIA réintégré** : +2-5% événements utilisables (hebdomadaire)
- **Normalisation** : Meilleure agrégation, moins de fragmentation

**Total estimé** : +7-15% événements avec surprise calculable, potentiellement meilleure corrélation S ↔ direction.

---

## ⚠️ LIMITATIONS CONNUES

1. **Finnhub ne fournit pas** :
   - Forecast séparé (seulement estimate)
   - Dispersion forecast
   - Flags révision/preliminary

2. **Si estimate manquant pour Bills même après historique** :
   - Fallback previous acceptable mais moins idéal
   - Alternative : chercher source complémentaire

3. **Limites API Finnhub** :
   - Vérifier limites de rate limiting pour import historique
   - Vérifier disponibilité historique selon plan (Free vs Premium)

---

## 📋 CONCLUSION

**✅ Réalisable via Finnhub** :
- Priorité #1 (Bills) : ⚠️ Partiellement (fallback possible)
- Priorité #2 (EIA) : ✅ Oui (import historique)
- Priorité #3 (Normalisation) : ✅ Oui (code)

**❌ Non réalisable via Finnhub** :
- Priorité #4 (Dispersion) : ❌ Non disponible
- Priorité #5 (Révisions) : ❌ Non disponible

**Recommandation finale** : **Implémenter Phases 1-3**, puis évaluer impact sur signal avant d'explorer sources alternatives pour #4/#5.

