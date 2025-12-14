# 🚀 MESSAGE SESSION 31 - Démarrage URGENT

**Date :** Session 31  
**Session précédente :** Session 30 - Config + DataService (CORRECTIONS NÉCESSAIRES)  
**Tokens disponibles :** 190,000  
**Objectif :** CORRIGER DataService + intégrer table scores

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ PROBLÈME CRITIQUE DÉCOUVERT SESSION 30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔴 URGENCE : DataService ne fonctionne pas correctement

**Symptôme :** get_events() ne trouve AUCUN événement le 11 septembre 2025 alors qu'il y en a 69 !

**Cause racine :**
- `importance_n` est NULL pour 46/69 événements (67%)
- DataService filtre sur `importance_n >= 3` → trouve 0 résultats
- Table **`scores`** (991 lignes) existe mais N'EST PAS utilisée !

**Solution :** Intégrer table `scores` dans DataService.get_events()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ INSTRUCTIONS DÉMARRAGE (5 MINUTES MAX)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📖 Lecture Obligatoire

**1. Lire ce fichier EN ENTIER** (5 min)

**2. Consulter DATABASE_SCHEMAS.md**
```bash
cat docs/DATABASE_SCHEMAS.md
```
**Vérifier section table `scores`** (à ajouter si manquante)

**3. Voir scripts investigation Session 30**
```bash
ls scripts/*.py | grep -E "(check|find|list|debug)"
```

**4. Voir résultat problème**
```bash
cat << EOF
Total événements 11 sept : 69
importance_n = 1 : 23 événements
importance_n = NULL : 46 événements  ← PROBLÈME !
EOF
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RÉSUMÉ SESSION 30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Ce qui a été fait ✅

### 1. config.py migré et corrigé
✅ Fix dataclass → classe normale
✅ 500 lignes de configuration centralisée
✅ Validation au démarrage

### 2. DataService créé
✅ 650 lignes de code
✅ 9 méthodes principales
✅ Context manager
✅ **MAIS** : Ne fonctionne pas car table `scores` non intégrée

### 3. Investigation DB complète
✅ Scripts créés pour explorer schéma
✅ Découverte table `scores` (991 lignes)
✅ Identification problème `importance_n = NULL`

### 4. Documentation schémas
✅ DATABASE_SCHEMAS.md créé
✅ 4 tables documentées (events, event_families, prices_1m, event_impacts_v2)
✅ **MANQUE** : Table `scores` à documenter

## Statistiques

**Progression :** 30% → 50% (architecture créée)  
**Tokens Session 30 :** 120,000 / 190,000 (63%)  
**Fichiers créés :** 15+ (code + tests + doc + scripts)  
**Problèmes découverts :** 2 critiques

## Problèmes Critiques Découverts

### Problème #1 : importance_n = NULL
```
Table events :
- 69 événements le 11 septembre 2025
- 23 ont importance_n = 1
- 46 ont importance_n = NULL (67% !)
```

**Impact :** DataService.get_events() avec `min_importance=3` trouve 0 résultats

### Problème #2 : Table scores non utilisée
```
Table scores (991 lignes) :
- event_key
- score_impact_0_100      ← Score impact 0-100
- score_persist_0_100     ← Score persistance 0-100
- impact_median_1h_pips   ← Impact médian pips
- persistence_median_min  ← Persistance médiane min
```

**Impact :** Les scores créés par André ne sont PAS utilisés !

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 OBJECTIF SESSION 31 - CORRECTIONS URGENTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Mission Principale

**Corriger DataService pour utiliser table `scores`**

## Tâches Détaillées (PRIORITÉ 1)

### 1. Documenter table scores (15 min)

**Fichier :** `docs/DATABASE_SCHEMAS.md`

**Ajouter section :**
```markdown
## Table : scores (991 lignes)

**Clé primaire :** event_key

| Colonne | Type | Description |
|---------|------|-------------|
| event_key | VARCHAR | Clé événement |
| impact_median_1h_pips | DOUBLE | Impact médian 1h en pips |
| persistence_median_min | DOUBLE | Persistance médiane minutes |
| score_impact_0_100 | DOUBLE | Score impact 0-100 |
| score_persist_0_100 | DOUBLE | Score persistance 0-100 |
```

### 2. Corriger DataService.get_events() (1h)

**Fichier :** `app/services/data_service.py` ligne ~200

**AVANT (ne fonctionne pas) :**
```python
query = """
SELECT
    e.ts_utc,
    e.event_title,
    ...
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.importance_n >= 3  ← PROBLÈME : NULL !
"""
```

**APRÈS (corrigé) :**
```python
query = """
SELECT
    e.ts_utc,
    e.event_title,
    e.event_key,
    e.country,
    e.importance_n,
    e.actual,
    e.estimate,
    e.forecast,
    e.previous,
    e.unit,
    e.event_type,
    -- Colonnes SCORES (NOUVEAU)
    s.score_impact_0_100,
    s.score_persist_0_100,
    s.impact_median_1h_pips,
    s.persistence_median_min,
    -- Calcul surprise
    CASE ... END AS surprise_pct
"""

if with_family:
    query += """,
    ef.family,
    ef.avg_movement_pips,
    ef.empirical_score
"""

query += """
FROM events e
LEFT JOIN scores s 
    ON e.event_key = s.event_key
"""

if with_family:
    query += """
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
"""
```

**Modifier filtre importance :**
```python
# OPTION 1 : Utiliser scores
if min_importance > 1:
    # Conversion : importance 3 = score >= 70
    min_score = min_importance * 25  # 3 * 25 = 75
    where_clauses.append(f"s.score_impact_0_100 >= {min_score}")

# OPTION 2 : Utiliser COALESCE
if min_importance > 1:
    where_clauses.append(
        f"COALESCE(e.importance_n, "
        f"CASE WHEN s.score_impact_0_100 >= 70 THEN 3 "
        f"     WHEN s.score_impact_0_100 >= 40 THEN 2 "
        f"     ELSE 1 END) >= {min_importance}"
    )
```

### 3. Créer get_scores() (30 min)

**Fichier :** `app/services/data_service.py`

**Ajouter méthode :**
```python
def get_scores(
    self,
    min_impact_score: Optional[int] = None,
    min_persist_score: Optional[int] = None
) -> pd.DataFrame:
    """
    Récupère les scores événements.
    
    Args:
        min_impact_score: Score impact minimum (0-100)
        min_persist_score: Score persistance minimum (0-100)
        
    Returns:
        DataFrame avec scores
        
    Examples:
        >>> data_service = DataService()
        >>> 
        >>> # Scores haute impact
        >>> scores = data_service.get_scores(min_impact_score=70)
    """
    query = """
    SELECT 
        s.*,
        ef.family,
        ef.country
    FROM scores s
    LEFT JOIN event_families ef ON s.event_key = ef.event_key
    """
    
    where_clauses = []
    
    if min_impact_score is not None:
        where_clauses.append(f"s.score_impact_0_100 >= {min_impact_score}")
    
    if min_persist_score is not None:
        where_clauses.append(f"s.score_persist_0_100 >= {min_persist_score}")
    
    if where_clauses:
        query += "\nWHERE " + " AND ".join(where_clauses)
    
    query += "\nORDER BY s.score_impact_0_100 DESC"
    
    with self.get_connection() as conn:
        df = conn.execute(query).fetchdf()
    
    return df
```

### 4. Tester corrections (30 min)

**Script :** `scripts/test_data_service.py`

**Modifier test pour utiliser scores :**
```python
# Test événements 11 septembre avec scores
events = data_service.get_events(
    start_date='2025-09-11',
    end_date='2025-09-11',
    countries=['US'],
    min_importance=3,  # Maintenant utilise scores !
    with_family=True
)

assert len(events) > 0, "Événements 11 sept trouvés"
assert 'score_impact_0_100' in events.columns
print(f"✅ {len(events)} événements trouvés")
```

### 5. Créer test_scores.py (30 min)

**Nouveau fichier :** `scripts/test_scores.py`

```python
#!/usr/bin/env python3
"""Test table scores"""

from app.services import DataService

data_service = DataService()

# Test 1 : Récupérer tous scores
scores = data_service.get_scores()
print(f"Total scores : {len(scores)}")

# Test 2 : Scores haute impact
high_impact = data_service.get_scores(min_impact_score=70)
print(f"Haute impact (>=70) : {len(high_impact)}")

# Test 3 : Vérifier CPI US
cpi_scores = scores[scores['event_key'].str.contains('cpi', case=False, na=False)]
print(f"\nScores CPI : {len(cpi_scores)}")
print(cpi_scores[['event_key', 'score_impact_0_100', 'impact_median_1h_pips']])
```

## Critères de Succès

- [ ] Table scores documentée dans DATABASE_SCHEMAS.md
- [ ] DataService.get_events() intègre table scores
- [ ] DataService.get_scores() créé
- [ ] Tests passent avec événements 11 septembre
- [ ] script test_scores.py créé et fonctionne
- [ ] Documentation mise à jour
- [ ] Tokens < 115k

## Temps Estimé

⏱️ **Total :** 3-4 heures

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ POINTS D'ATTENTION CRITIQUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚨 TOUJOURS vérifier schéma AVANT d'écrire SQL !

**Leçon Session 30 :** Ne JAMAIS supposer les noms de colonnes

**Process obligatoire :**
1. Créer script `check_schema.py`
2. Exécuter pour voir colonnes réelles
3. PUIS écrire requêtes SQL

## 🚨 Table scores = SOURCE VÉRITÉ pour importance

- ❌ `importance_n` : 67% NULL
- ✅ `scores.score_impact_0_100` : Toujours renseigné

**Utiliser scores en priorité !**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 GESTION TOKENS SESSION 31
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Instructions pour Claude

**À chaque étape importante :**

1. **Indiquer tokens utilisés**
   ```
   📊 Tokens : X / 190,000 (Y%)
   ```

2. **Fréquence :** Tous les 15-20k tokens

3. **Alerte à 115k tokens :**
   ```
   ⚠️ ALERTE TOKENS : 115k atteints
   
   Actions immédiates :
   1. 🛑 STOP développement
   2. 📝 Sauvegarder progression
   3. 🔄 Mettre à jour docs/SESSION_31_CORRECTIONS.md
   4. ✉️ Créer MESSAGE_SESSION_32.md
   5. 🏁 Terminer proprement
   ```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 WORKFLOW SESSION 31
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Ordre d'Exécution Recommandé

### Phase 1 : Préparation (10 min)
1. Lire ce MESSAGE_SESSION_31.md
2. Consulter docs/DATABASE_SCHEMAS.md
3. Voir scripts investigation Session 30

### Phase 2 : Documentation (15 min)
1. Ajouter table scores dans DATABASE_SCHEMAS.md
2. Mettre à jour exemples

### Phase 3 : Corrections DataService (1.5h)
1. Modifier get_events() - intégrer scores
2. Créer get_scores()
3. Mettre à jour documentation inline

### Phase 4 : Tests (1h)
1. Modifier test_data_service.py
2. Créer test_scores.py
3. Exécuter tests
4. Vérifier événements 11 septembre trouvés

### Phase 5 : Documentation (30 min)
1. Créer docs/SESSION_31_CORRECTIONS.md
2. Mettre à jour CHANGELOG.md
3. Créer MESSAGE_SESSION_32.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CHECKLIST SESSION 31
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Avant de Commencer
- [ ] MESSAGE_SESSION_31.md lu
- [ ] DATABASE_SCHEMAS.md consulté
- [ ] Scripts investigation vus

## Pendant la Session
- [ ] Table scores documentée
- [ ] DataService.get_events() corrigé (scores intégrés)
- [ ] DataService.get_scores() créé
- [ ] Tests modifiés
- [ ] test_scores.py créé
- [ ] Tokens surveillés (<115k)

## Avant de Terminer
- [ ] Tests passent (événements 11 sept trouvés)
- [ ] SESSION_31_CORRECTIONS.md créé
- [ ] CHANGELOG.md mis à jour
- [ ] MESSAGE_SESSION_32.md créé

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 RÉFÉRENCES RAPIDES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Fichiers Importants

| Fichier | Description | Action |
|---------|-------------|--------|
| MESSAGE_SESSION_31.md | Ce fichier | LIRE EN ENTIER |
| docs/DATABASE_SCHEMAS.md | Schémas DB | Ajouter scores |
| app/services/data_service.py | À corriger | Intégrer scores |
| scripts/check_sept11_final.py | Preuve problème | Référence |
| scripts/list_all_tables.py | Liste tables | Référence |

## Commandes Utiles

```bash
# Voir table scores
python3 -c "
import duckdb
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
print(conn.execute('SELECT * FROM scores LIMIT 5').fetchdf())
"

# Tester DataService
cd eurusd_clean
python3 scripts/test_data_service.py

# Vérifier événements 11 sept
python3 scripts/check_sept11_final.py
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 RAPPEL OBJECTIF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Session 31 :** CORRIGER DataService pour qu'il fonctionne vraiment

**Problème :** DataService ne trouve pas les événements car `importance_n = NULL`

**Solution :** Utiliser table `scores` avec `score_impact_0_100`

**Validation :** Trouver événements 11 septembre 2025 (CPI, NFP, etc.)

**Temps estimé :** 3-4 heures

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🚀 Session 31 : CORRECTIONS URGENTES - DataService + scores**

**Tokens Session 30 :** 120,000 (63%)  
**Tokens disponibles Session 31 :** 190,000

**Let's fix the DataService! 🔧**
