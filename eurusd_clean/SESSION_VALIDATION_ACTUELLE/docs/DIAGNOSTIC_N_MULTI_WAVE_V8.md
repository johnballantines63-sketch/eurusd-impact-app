# Diagnostic N Multi-Wave V8 - Blocage Identifié

## Problème

**N multi-wave uniques = 9** (identique à V7) malgré :
- ✅ MOVEMENTS_FILE historique généré (2022-2025, 4,448 mouvements)
- ✅ Events historiques présents dans DB (2022-2023 : 31+100 dates avec events core)
- ✅ Scan étendu lancé (2018-2025)

## Cause Racine

**Décalage temporel entre mouvements détectés et events économiques**

### Mécanisme

1. **Détection mouvements** (`detect_all_movements`) :
   - Utilise `day_start` (début journée) comme référence
   - Exemple : mouvement détecté à `2022-10-24 07:00 UTC`

2. **Matching events** (`identify_tradable_dates`) :
   - Fenêtre : `[movement_start - 4h, movement_start + 30min]`
   - Exemple : `[2022-10-24 03:00 UTC, 2022-10-24 07:30 UTC]`

3. **Events économiques** :
   - CPI US : ~14:30 UTC
   - NFP : ~13:30 UTC
   - Jobless Claims : ~13:30 UTC
   - **→ Aucun event dans la fenêtre [03:00, 07:30 UTC]**

### Preuve

```
Mouvement test: 2022-10-24 07:00:00+00:00
Fenêtre: 2022-10-24 03:00:00+00:00 → 2022-10-24 07:30:00+00:00
Events dans fenêtre: 0
Events le 2022-10-24 (toute la journée): 11
```

## Impact

- **Mouvements 2022-2023** : 1,112 mouvements ≥40 pips
- **Matching events** : ~0% (fenêtre trop étroite)
- **Dates tradables identifiées** : 565 (limitées à 2024-2025 où timing coïncide)

## Solutions Possibles

### Option 1 : Assouplir Fenêtre Matching (Recommandé)

**Modifier `identify_tradable_dates`** pour chercher events sur **toute la journée** au lieu de `[-4h, +30min]` :

```python
# Au lieu de :
window_start = movement_start + timedelta(hours=-4)
window_end = movement_start + timedelta(minutes=30)

# Utiliser :
day_start = movement_start.replace(hour=0, minute=0, second=0)
day_end = day_start + timedelta(days=1)
window_start = day_start
window_end = day_end
```

**Avantages** :
- ✅ Respecte logique V7 (mouvements détectés par jour)
- ✅ Capture events économiques réels
- ✅ Augmente N multi-wave uniques

**Inconvénients** :
- ⚠️ Peut créer des faux positifs (mouvement maté avec event non lié)

### Option 2 : Utiliser Events Réels comme Référence

**Modifier `detect_all_movements`** pour utiliser les events réels comme `event_time` au lieu de `day_start`.

**Avantages** :
- ✅ Matching précis mouvement ↔ event

**Inconvénients** :
- ⚠️ Change logique V7 (mouvements dépendent des events)
- ⚠️ Nécessite refactoring important

### Option 3 : Générer Mapping Movements → Events

**Créer un script** qui génère un mapping explicite :
- Pour chaque mouvement, trouver l'event le plus proche dans la journée
- Si distance < seuil (ex: 6h), créer une entrée tradable

**Avantages** :
- ✅ Contrôle explicite du matching
- ✅ Audit possible

**Inconvénients** :
- ⚠️ Ajoute une étape supplémentaire
- ⚠️ Nécessite définition de seuil

## Recommandation V8

**Option 1** (assouplir fenêtre) est la plus simple et respecte l'esprit V7 :
- Mouvements détectés par jour (logique V7)
- Events cherchés sur toute la journée (assouplissement minimal)
- Pas de changement structurel

## Prochaine Action

1. **Appliquer Option 1** dans `test_direction_router_batch.py` → `identify_tradable_dates`
2. **Re-lancer scan** 2018-2025
3. **Vérifier N multi-wave uniques** (devrait augmenter)
4. **Si N ≥ 30** → stratification V8
5. **Si N < 30** → documenter limitation et garder V7 comme baseline

---

**Version** : Diagnostic V8
**Date** : 2025-01-XX
**Status** : ✅ **CAUSE IDENTIFIÉE - SOLUTION PROPOSÉE**

