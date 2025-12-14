# 📋 SESSION 18 → 19 - DOCUMENT DE CONTINUITÉ COMPLET

**Date Session 18 :** 19 octobre 2025  
**Tokens utilisés :** 119K / 190K (62.6%)  
**Statut :** ⏸️ PAUSE - À CONTINUER  
**Prochaine session :** 19

---

## 🎯 OBJECTIF INITIAL SESSION 18

**Mission :** Développer interface de correction des données historiques

**Contexte :**
- Session 17 : Formule V2 validée sur 120 groupes (-70.5% MAE)
- ⚠️ Problème découvert : Données `actual`/`estimate` incorrectes dans DB
- Exemple : 11 septembre → surprise 0% au lieu de 33%
- Impact : Validation biaisée, V2 pourrait être meilleure (13% vs 29% erreur)

---

## ✅ CE QUI A ÉTÉ FAIT (SESSION 18)

### VOLET 1 : Audit qualité données (TERMINÉ) ✅

**Scripts créés :**
1. `audit_data_quality_session18.py` - Audit complet
2. `reimport_eodhd_targeted_session18.py` - Re-import ciblé
3. `verify_reimport_impact_session18.py` - Vérification impact

**Résultats obtenus :**
- Complétude globale : 40.9% → 41.7% (+0.8 pts)
- **HIGH importance : 84.4%** ✅ (objectif dépassé)
- **Session 17 : 97.5%** des groupes ont estimate ✅
- **Session 15 : 100%** des événements ont estimate ✅
- Re-import : 343 estimates récupérés

**Fichiers générés :**
- Backups DB automatiques
- Logs d'import
- Statistiques qualité

---

## 🚨 PROBLÈME CRITIQUE IDENTIFIÉ

### Le cas du 11 septembre 2025

**Symptôme :**
- Planificateur affiche 2 événements Inflation Rate
- Les DEUX ont surprise = 0%
- MT5 montre pourtant 59 pips de mouvement

**Diagnostic (après investigation) :**

```
API EODHD retourne 3 ÉVÉNEMENTS US 14:30 :

1. Inflation Rate (MoM) :
   "comparison": "mom"
   actual: 0.4
   estimate: 0.3
   → Surprise: 33.3% 🔥 ← CELUI-CI EST IMPORTANT !

2. Inflation Rate (YoY) :
   "comparison": "yoy"  
   actual: 2.9
   estimate: 2.9
   → Surprise: 0%

3. Core Inflation Rate (MoM) :
   "comparison": "mom"
   actual: 0.3
   estimate: 0.3
   → Surprise: 0%
```

**CE QUI EST DANS LA DB :**
```sql
SELECT event_key, actual, estimate FROM events 
WHERE date = '2025-09-11' AND event_key = 'inflation rate'

inflation rate    2.9    2.9    ← MAUVAISE VERSION (YoY)
```

**CE QUI DEVRAIT ÊTRE :**
```
inflation_rate_mom    0.4    0.3    ← BONNE VERSION
inflation_rate_yoy    2.9    2.9    ← Version informative
```

---

## 🔑 CAUSE RACINE DU PROBLÈME

### Pourquoi la mauvaise version est stockée ?

**Fonction `upsert_events()` dans `eodhd_client.py` :**

```python
MERGE INTO events AS e
USING tmp_eodhd_events AS t
ON  e.ts_utc = t.ts_utc
AND e.country = t.country
AND e.event_key = t.event_key  ← PROBLÈME ICI
```

**Séquence d'import :**
1. API retourne Inflation Rate (MoM) : 0.4 vs 0.3
2. Normalisé → `event_key` = "inflation rate"
3. INSERT dans DB ✅

4. API retourne Inflation Rate (YoY) : 2.9 vs 2.9
5. Normalisé → `event_key` = "inflation rate" (MÊME CLÉ !)
6. MERGE trouve match → **UPDATE** (écrase MoM) ❌

**Résultat : On garde la dernière version traitée (aléatoire !)**

---

## ✅ SOLUTION TROUVÉE

### Utiliser le champ `comparison` de EODHD

**EODHD fournit :**
- `"comparison": "mom"` = Month-over-Month = MENSUEL
- `"comparison": "yoy"` = Year-over-Year = ANNUEL
- `"comparison": "qoq"` = Quarter-over-Quarter = TRIMESTRIEL

**Modification à faire dans `calendar_to_events_df()` :**

```python
def calendar_to_events_df(items: List[Dict[str, Any]]) -> pd.DataFrame:
    # ... code existant ...
    
    # ✅ NOUVEAU : Extraire comparison
    comparison = _col(raw, "comparison").astype("string")
    
    # ✅ NOUVEAU : Enrichir event_key avec comparison
    for idx, row in df.iterrows():
        if pd.notna(row['comparison']):
            comp = row['comparison'].lower()
            event_key = row['event_key'].lower()
            
            # Ajouter suffixe si pas déjà présent
            if comp == 'mom' and 'mom' not in event_key:
                df.at[idx, 'event_key'] = event_key + '_mom'
            elif comp == 'yoy' and 'yoy' not in event_key:
                df.at[idx, 'event_key'] = event_key + '_yoy'
            elif comp == 'qoq' and 'qoq' not in event_key:
                df.at[idx, 'event_key'] = event_key + '_qoq'
    
    return df
```

---

## 📋 CE QUI RESTE À FAIRE (SESSION 19)

### PRIORITÉ 1 : Appliquer le fix (30 min)

**Script à créer : `apply_comparison_fix_session19.py`**

Doit :
1. Faire backup de `eodhd_client.py`
2. Modifier `calendar_to_events_df()` pour :
   - Extraire le champ `comparison`
   - Enrichir `event_key` avec `_mom`, `_yoy`, `_qoq`
3. Tester sur 11 septembre
4. Vérifier que les 2 versions sont distinctes

**Test attendu :**
```python
from fx_impact_app.src.eodhd_client import fetch_calendar_json, calendar_to_events_df
data = fetch_calendar_json('2025-09-11', '2025-09-11', countries=['US'])
df = calendar_to_events_df(data)
inf = df[df['event_key'].str.contains('inflation', na=False)]
print(inf[['event_key', 'actual', 'estimate']])

# Résultat attendu :
# inflation_rate_mom    0.4    0.3  ✅
# inflation_rate_yoy    2.9    2.9
```

---

### PRIORITÉ 2 : Re-import complet (45 min)

**Une fois le fix appliqué :**

```bash
# Re-importer TOUTES les données depuis 2023
python fx_impact_app/scripts/ingest_eodhd_calendar.py \
  --from 2023-01-01 \
  --to 2025-10-19 \
  --countries US EU GB DE FR JP AU ES IT
```

**Attendu :**
- Doublons resolus (MoM et YoY séparés)
- Sessions 15 & 17 : toujours 97.5%+ mais avec vraies surprises
- Cas 11 septembre : surprise 33% détectée

---

### PRIORITÉ 3 : Mise à jour event_families (30 min)

**Problème :** Les nouveaux `event_key` n'existent pas dans `event_families`

**Solution :**

```sql
-- Dupliquer les entrées pour MoM et YoY
INSERT INTO event_families 
SELECT 
    event_key || '_mom' as event_key,
    country,
    family,
    empirical_score,
    avg_movement_pips,
    -- ... autres colonnes
FROM event_families
WHERE event_key IN (
    'inflation rate', 'cpi', 'core inflation rate', 
    'gdp growth rate', 'unemployment rate'
)

-- Idem pour _yoy
```

**Ou créer script :**
`create_comparison_variants_event_families.py`

---

### PRIORITÉ 4 : Re-validation (60 min)

**Scripts à relancer :**

1. **Vérifier 11 septembre :**
```bash
python verify_db_reality_sept11_session18.py
```

Attendu :
```
inflation_rate_mom    0.4    0.3    → Surprise 33% ✅
inflation_rate_yoy    2.9    2.9    → Surprise 0%
```

2. **Re-mesurer Session 17 :**
```bash
python measure_impacts_v1_v2_session17.py
```

Attendu :
- MAE V2 devrait s'améliorer (174.9% → ~140-150%)
- Plus de cas avec surprises élevées détectées

3. **Re-tester cas 11 septembre :**
```bash
python test_11sept_v872.py
```

Attendu :
- Erreur V2 : 29% → 13% ✅

---

## 📂 FICHIERS CRITIQUES CRÉÉS SESSION 18

### Scripts d'audit
```
audit_data_quality_session18.py
verify_reimport_impact_session18.py
verify_db_reality_sept11_session18.py
investigate_monthly_annual_session18.py
inspect_eodhd_full_fields_session18.py
```

### Scripts de fix (NON APPLIQUÉS)
```
apply_deduplication_fix_session18.py        ← NE PAS UTILISER
apply_monthly_annual_fix_session18.py       ← NE PAS UTILISER
fix_deduplication_monthly_annual_session18.py ← NE PAS UTILISER
```

**⚠️ CES SCRIPTS SONT OBSOLÈTES !**
Ils utilisent magnitude au lieu de `comparison`.

### Scripts de re-import (UTILISÉS)
```
reimport_eodhd_targeted_session18.py  ← Déjà exécuté (343 corrections)
```

---

## 🗂️ STRUCTURE FICHIERS PROJET

### Code source principal
```
fx_impact_app/
├── src/
│   ├── eodhd_client.py          ← À MODIFIER (priorité 1)
│   ├── config.py
│   └── ...
├── scripts/
│   ├── ingest_eodhd_calendar.py ← À UTILISER (priorité 2)
│   └── ...
└── data/
    └── warehouse.duckdb          ← DB principale
```

### Tables DB critiques
```sql
-- Table événements (32,024 lignes)
events (
    ts_utc TIMESTAMP WITH TIME ZONE,
    country VARCHAR,
    event_key VARCHAR,      ← Clé à enrichir
    event_title VARCHAR,
    actual DOUBLE,
    estimate DOUBLE,
    previous DOUBLE,
    ...
)

-- Table scores (241 types)
event_families (
    event_key VARCHAR,      ← À dupliquer pour MoM/YoY
    country VARCHAR,
    empirical_score DOUBLE,
    avg_movement_pips DOUBLE,
    ...
)

-- Table impacts calculés (2,089 groupes)
event_group_impacts (
    time_group VARCHAR,
    mfe_pips DOUBLE,
    num_events INTEGER,
    ...
)
```

---

## 📊 ÉTAT ACTUEL DU PROJET

### Formule V2 (validée mais avec données biaisées)

```python
# Base impact
impact_base = -7.08 + 0.419 × empirical_score

# Amplification V2
surprise_abs = min(surprise, 30)
if score < 40:
    amplification = 1.0
elif surprise < 5%:
    amplification = 1.0
elif surprise < 15%:
    amplification = 1.0 + (surprise - 5) × 0.15
else:
    amplification = 2.5  # Plafond

# Impact final
impact = abs(impact_base) × amplification × 0.758
```

**Méthode multi-événements :** MAX (prend le score max et surprise max)

**Performances actuelles (avec données biaisées) :**
- MAE V1 : 593.6%
- MAE V2 : 174.9% (-70.5%)
- Session 17 : 97.5% groupes couverts
- Session 15 : 100% événements couverts

**Performances attendues (avec fix) :**
- MAE V2 : ~140-150% (amélioration supplémentaire)
- Cas 11 sept : 29% → 13% ✅

---

## 🔧 MODIFICATIONS À FAIRE (DÉTAILS TECHNIQUES)

### Dans `fx_impact_app/src/eodhd_client.py`

**Ligne ~125 (dans `calendar_to_events_df()`) :**

AJOUTER après la ligne `unit = _col(raw, "unit", "unit_short", "units").astype("string")` :

```python
# ✅ SESSION 18 : Extraire comparison (mom, yoy, qoq)
comparison = _col(raw, "comparison").astype("string")
```

PUIS dans le DataFrame, AJOUTER la colonne :

```python
df = pd.DataFrame({
    "ts_utc": ts_utc,
    "country": country,
    "event_title": event_title.astype("string"),
    "event_key": event_key.astype("string"),
    "label": label.astype("string"),
    "type": typ.astype("string"),
    "estimate": estimate.astype("Float64"),
    "forecast": forecast.astype("Float64"),
    "previous": previous.astype("Float64"),
    "actual": actual.astype("Float64"),
    "unit": unit.astype("string"),
    "comparison": comparison,  # ← AJOUTER
    "importance_n": importance_n,
})
```

PUIS AVANT `return df.reset_index(drop=True)`, AJOUTER :

```python
# ✅ SESSION 18 : Enrichir event_key avec comparison
for idx, row in df.iterrows():
    if pd.notna(row.get('comparison')):
        comp = str(row['comparison']).lower()
        event_key_current = str(row['event_key']).lower()
        
        # Ne pas ajouter si déjà présent
        if comp in ['mom', 'yoy', 'qoq']:
            if comp not in event_key_current:
                df.at[idx, 'event_key'] = f"{event_key_current}_{comp}"

# Supprimer colonne temporaire comparison
df = df.drop(columns=['comparison'], errors='ignore')
```

---

## ⚠️ PIÈGES À ÉVITER

### Erreur #1 : Oublier country dans les jointures
```sql
-- ❌ FAUX
LEFT JOIN event_families ef ON e.event_key = ef.event_key

-- ✅ CORRECT
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
```

### Erreur #2 : Utiliser forecast au lieu d'estimate
```python
# ❌ FAUX - forecast est NULL 99% du temps
if row['forecast'] is not None:

# ✅ CORRECT
if row['estimate'] is not None:
```

### Erreur #3 : Ne pas vérifier les nouveaux event_key dans event_families

Après le fix, `inflation_rate_mom` n'existe pas dans `event_families`.

Il faut soit :
- Dupliquer les entrées
- Ou faire une jointure flexible (strip suffix)

---

## 📖 DOCUMENTS À LIRE (NOUVEAU CLAUDE)

**OBLIGATOIRE (lecture complète) :**
1. `ERREURS_RECURRENTES.md` ⭐⭐⭐
2. `KNOWLEDGE_BASE.md` ⭐⭐⭐
3. `KNOWLEDGE_BASE_UPDATE_SESSION17.md` ⭐⭐⭐
4. Ce document (SESSION 18 continuité)

**Contexte (lecture rapide) :**
5. `RAPPORT_SESSION17_FINAL.md`
6. `RAPPORT_SESSION15_FINAL.md`
7. `DB_STRUCTURE_REFERENCE.md`

---

## 🎯 PLAN SESSION 19

### Phase 1 : Application du fix (30-45 min)
1. ✅ Créer script `apply_comparison_fix_session19.py`
2. ✅ Appliquer modification `eodhd_client.py`
3. ✅ Tester sur 11 septembre
4. ✅ Vérifier résultat attendu

### Phase 2 : Re-import (45-60 min)
1. ✅ Re-importer 2023-2025 avec nouveau code
2. ✅ Vérifier DB (doit avoir _mom et _yoy)
3. ✅ Compter nouvelles lignes

### Phase 3 : Mise à jour event_families (30 min)
1. ✅ Créer variantes MoM/YoY dans event_families
2. ✅ Ou modifier code pour jointure flexible

### Phase 4 : Re-validation (60 min)
1. ✅ Re-tester 11 septembre (erreur 29% → 13%)
2. ✅ Re-mesurer Session 17 (MAE devrait s'améliorer)
3. ✅ Générer rapport final

**Temps total estimé : 3-4 heures**

---

## 💾 BACKUPS IMPORTANTS

Avant toute modification :
```bash
# Backup DB
cp fx_impact_app/data/warehouse.duckdb \
   fx_impact_app/data/warehouse_backup_session18.duckdb

# Backup code
cp fx_impact_app/src/eodhd_client.py \
   fx_impact_app/src/eodhd_client_backup_session18.py
```

---

## ✅ CHECKLIST SESSION 19

- [ ] Lire ce document EN ENTIER
- [ ] Lire `ERREURS_RECURRENTES.md`
- [ ] Créer backup DB et code
- [ ] Créer `apply_comparison_fix_session19.py`
- [ ] Tester fix sur 11 septembre
- [ ] Re-import complet 2023-2025
- [ ] Vérifier DB contient _mom et _yoy
- [ ] Mettre à jour event_families
- [ ] Re-valider Session 17
- [ ] Re-tester cas 11 septembre
- [ ] Générer rapport final Session 18-19

---

## 🔗 LIENS RAPIDES

**Base de données :**
`fx_impact_app/data/warehouse.duckdb`

**Code à modifier :**
`fx_impact_app/src/eodhd_client.py` (fonction `calendar_to_events_df()`)

**Script d'import :**
`fx_impact_app/scripts/ingest_eodhd_calendar.py`

**Environnement virtuel :**
`source .venv/bin/activate`

---

**FIN DU DOCUMENT DE CONTINUITÉ SESSION 18 → 19**

**Date de création :** 19 octobre 2025  
**Tokens finaux Session 18 :** 119K / 190K (62.6%)  
**Statut :** ✅ DOCUMENT COMPLET - PRÊT POUR SESSION 19  
**Priorité Session 19 :** Appliquer fix comparison (30 min), puis re-import complet
