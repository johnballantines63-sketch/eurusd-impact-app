# 🧠 BASE DE CONNAISSANCES CONSOLIDÉE - PROJET PLANIFICATEUR MULTI-ÉVÉNEMENTS

**Fichier central unique regroupant TOUTES les connaissances accumulées**  
**Version consolidée : Sessions 1-21**  
**Dernière mise à jour : 19 octobre 2025**

---

## 📋 TABLE DES MATIÈRES

1. [Principes directeurs](#principes)
2. [Structure de la base de données](#structure-db)
3. [Formules et calculs](#formules)
4. [Erreurs courantes résolues](#erreurs)
5. [Scripts importants](#scripts)
6. [Métriques de performance](#metriques)
7. [Décisions de conception](#decisions)
8. [État actuel du projet](#etat-actuel)

---

## <a name="principes"></a>🎯 1. PRINCIPES DIRECTEURS

### Principe #1 : RECONSTRUCTION vs PATCH (Session 21)

**Philosophie fondamentale du projet :**

Quand des données fondamentales changent, il faut **RECONSTRUIRE** les tables dérivées depuis zéro, pas les "patcher".

**Quand RECONSTRUIRE depuis zéro :**
- ✅ Import majeur de données (+50% événements)
- ✅ Changement structure clés (ajout suffixes)
- ✅ Modification schéma DB (nouvelles colonnes)
- ✅ Découverte incohérences majeures
- ✅ Doute sur intégrité données

**Quand PATCHER :**
- ✅ Ajout de quelques événements (<10%)
- ✅ Correction ponctuelle
- ✅ Mise à jour métadonnées

**Avantages reconstruction :**
1. ✅ Garantit cohérence totale
2. ✅ Élimine reliquats/bugs cachés
3. ✅ Plus rapide que debug patches multiples
4. ✅ Base propre pour futures évolutions

**Coût acceptable :**
- ⏱️ 30-60 min calcul (event_group_impacts)
- ⏱️ 10-20 min calcul (event_families)
- ⚠️ Accepter temps calcul pour qualité données

**Règle d'or :**
> "Quand hésitation patch vs rebuild → **REBUILD**"

**Ce principe s'applique à TOUS les fichiers critiques du projet.**

### Principe #2 : Diagnostiquer avant implémenter (Session 21)

**Toujours faire :**
1. ✅ Audit complet de l'état actuel
2. ✅ Diagnostics approfondis des problèmes
3. ✅ Tests sur cas d'école (ex: 11 septembre)
4. ✅ Documentation des décisions

**Jamais faire :**
- ❌ "Patcher" sans comprendre la cause racine
- ❌ Modifier plusieurs fichiers simultanément
- ❌ Implémenter sans valider sur cas test

**Économie temps :**
- Temps diagnostic : 2h
- Temps évité (debug) : 5-10h
- **Gain net : 3-8h**

---

## <a name="structure-db"></a>📊 2. STRUCTURE BASE DE DONNÉES

**Document de référence principal :** `DB_STRUCTURE_REFERENCE.md`

### Points clés à retenir

| Sujet | Information | Session |
|-------|-------------|---------|
| **Base à utiliser** | `warehouse.duckdb` (les autres sont vides/corrompues) | Session 7 |
| **Table événements** | `events` (58,449 lignes) | Session 19 |
| **Table scores** | `event_families` (241 types) - ⚠️ **À RECONSTRUIRE** | Session 21 |
| **Table prix** | `prices_1m` (1.1M lignes, prix minute par minute) | Session 7 |
| **Type timestamp** | `TIMESTAMP WITH TIME ZONE` → utiliser `strftime()` | Session 7 |
| **Table impacts** | `event_group_impacts` (2,089 groupes) - ⚠️ **À RECONSTRUIRE** | Session 21 |

### 🆕 État après Session 19-21

**Table `events` (58,449 lignes) :**
```sql
CREATE TABLE events (
  ts_utc TIMESTAMP WITH TIME ZONE,
  country VARCHAR,
  event_title VARCHAR,
  event_key VARCHAR,              -- ✅ Avec suffixes _mom, _yoy, _qoq
  label VARCHAR,
  type VARCHAR,
  estimate DOUBLE,
  forecast DOUBLE,
  previous DOUBLE,
  actual DOUBLE,
  unit VARCHAR,
  comparison VARCHAR,             -- ✅ NOUVEAU (Session 19): mom/yoy/qoq
  period VARCHAR,                 -- ✅ NOUVEAU (Session 19): Jan, Q1, etc.
  change DOUBLE,                  -- ✅ NOUVEAU (Session 19)
  change_percentage DOUBLE,       -- ✅ NOUVEAU (Session 19)
  event_type VARCHAR,             -- ✅ NOUVEAU (Session 19)
  importance_n BIGINT
);
```

**Nouveaux champs (Session 19) :**

| Champ | Rempli | % | Description |
|-------|--------|---|-------------|
| `comparison` | 12,816 | 21.9% | **CRITIQUE** - Distingue MoM/YoY/QoQ |
| `period` | 19,926 | 34.1% | Période (Jan, Feb, Q1, etc.) |
| `change` | 20,220 | 34.6% | Changement absolu vs previous |
| `change_percentage` | 19,980 | 34.2% | Changement % vs previous |
| `event_type` | 25,172 | 43.1% | Type événement selon EODHD |

**Stats importantes :**
- Total événements : 58,449 (+75% vs avant Session 19)
- Avec comparison : 12,816 (21.9%)
  - MoM : 4,494
  - YoY : 7,531
  - QoQ : 791
- event_key avec suffixes : ✅ OUI (inflation_rate_mom, inflation_rate_yoy, etc.)

### ⚠️ Tables OBSOLÈTES (Session 21)

**À RECONSTRUIRE Session 22 :**

1. **event_families** - OBSOLÈTE
   - Créée avant Session 19
   - Pas de suffixes (_mom, _yoy, _qoq)
   - Scores basés sur anciennes données
   - **➡️ Reconstruction OBLIGATOIRE**

2. **event_group_impacts** - OBSOLÈTE
   - Créée Sessions 8-9 avec anciens event_key
   - event_keys stockés sans suffixes
   - Incohérence avec events actuels
   - **➡️ Reconstruction OBLIGATOIRE**

3. **scores** (si existe) - OBSOLÈTE
   - Anciens event_key
   - **➡️ Reconstruction recommandée**

4. **event_impacts_calculated** (si existe) - OBSOLÈTE
   - Anciens event_key
   - **➡️ Reconstruction recommandée**

---

## <a name="formules"></a>🔢 3. FORMULES ET CALCULS

### Formule V3d (Session 21) - ⭐⭐⭐ RECOMMANDÉE

**Composantes V3d :**
1. **Base** : Formule v9-CLEAN (-7.08 + 0.419 × score)
2. **Amplification V3b** : Plafond variable selon surprise et score
3. **Synergie V3c** : Bonus multi-événements
4. **Atténuation** : 0.758 (facteur correction vectorielle)

**Pseudocode complet :**
```python
def predict_impact_v3d(events_group):
    # 1. Score MAX du groupe
    max_score = max(event.empirical_score for event in events_group)
    
    # 2. Surprise MAX du groupe
    max_surprise = max(
        abs((e.actual - e.estimate) / e.estimate) 
        for e in events_group 
        if e.estimate != 0
    )
    
    # 3. Impact base (v9-CLEAN)
    impact_base = -7.08 + 0.419 * max_score
    
    # 4. Amplification V3b (plafond variable)
    if max_surprise < 0.05:
        amp = 1.0
    elif max_surprise < 0.15:
        amp = 1.0 + (max_surprise - 0.05) * 15
    elif max_surprise < 0.30:
        amp = 2.5 + (max_surprise - 0.15) * 10  # Jusqu'à 4.0
    else:
        # Cas extrême
        if max_score > 70:
            amp = 10.0  # Plafond élevé pour événements importants
        else:
            amp = 4.0   # Plafond modéré
    
    # 5. Synergie V3c (multi-événements)
    num_events = len(events_group)
    if num_events >= 5 and max_score > 70:
        synergy = 2.0
    elif num_events >= 3 and max_score > 60:
        synergy = 1.5
    elif num_events >= 2:
        synergy = 1.2
    else:
        synergy = 1.0
    
    # 6. Impact final
    impact = abs(impact_base) * amp * 0.758 * synergy
    
    return impact
```

**Validation 11 septembre 2025 (avec bonnes données) :**
- Score MAX : 81.7 (inflation_rate_mom)
- Surprise MAX : 33.3%
- Nombre événements : 6 HIGH
- **Impact prédit : ~412 pips**
- **Impact réel MT5 : 522 pips**
- **Erreur : 21%** ✅ EXCELLENT

**Statut :** ✅ Validée Session 21, à implémenter Session 22

### Formule v9-CLEAN (Sessions 9-10) - ⚠️ OBSOLÈTE seule

**Base utilisée dans V3d :**
```python
# Pour 1 événement
impact = -7.08 + 0.419 × empirical_score

# Pour ≥2 événements
impact = -10.47 + 0.477 × empirical_score
```

**Statistiques (v9-CLEAN) :**
- R² = 0.264
- Corrélation = 0.514
- MAE = 6.68 pips
- Basé sur 2,087 groupes temporels

**Statut :** ⚠️ Intégrée dans V3d, ne plus utiliser seule

### Formule pullback (Session 20) - ✅ VALIDÉE

**Formule :**
```python
pullback_pips = phase1_impact × 0.06 × minutes_between_phases
pullback_pips = min(pullback_pips, phase1_impact × 0.60)
```

**Validation 11 septembre 2025 :**
- Prédit : -124 pips
- Réel : -114 pips
- **Erreur : 9% seulement** ✅

**Statut :** ✅ PARFAITE - Ne pas modifier

### Formule V2 (Session 17) - ⚠️ OBSOLÈTE

Remplacée par V3d (meilleure performance).

---

## <a name="erreurs"></a>🚨 4. ERREURS COURANTES RÉSOLUES

### Erreur #1 : Colonne `event_name` N'EXISTE PAS

```sql
-- ❌ FAUX
SELECT ef.event_name FROM event_families ef

-- ✅ CORRECT
SELECT ef.event_key FROM event_families ef
```

**Session :** 7  
**Fréquence :** ⭐⭐⭐ Très fréquent

### Erreur #2 : Conversion TIMESTAMP incorrecte

```sql
-- ❌ FAUX
CAST(ts_utc AS TIME)

-- ✅ CORRECT
strftime(ts_utc, '%H:%M:%S')
```

**Session :** 7  
**Fréquence :** ⭐⭐⭐ Très fréquent

### Erreur #3 : Oublier `country` dans la jointure

```sql
-- ❌ INCOMPLET
LEFT JOIN event_families ef ON e.event_key = ef.event_key

-- ✅ COMPLET
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
```

**Session :** 7  
**Fréquence :** ⭐⭐ Fréquent

### Erreur #4 : Confondre `forecast` et `estimate`

```python
# ❌ FAUX - forecast est presque toujours NULL
CASE WHEN e.forecast IS NOT NULL THEN ...

# ✅ CORRECT - Utiliser estimate
CASE WHEN e.estimate IS NOT NULL AND e.estimate != 0 
    THEN ABS((e.actual - e.estimate) / e.estimate)
```

**Données :**
- `forecast` : 11 valeurs sur 58,449 (0.02%) ❌
- `estimate` : 13,089 valeurs (22.4%) ✅

**Session :** 7  
**Impact :** ⭐⭐⭐ CRITIQUE

### Erreur #5 : Calculer impacts individuellement au lieu de par groupe

**Erreur :** Le script calculait le MFE pour chaque événement séparément, même quand plusieurs événements étaient simultanés.

**Solution :** Grouper par `time_group` (minute) et calculer UN impact par groupe.

```python
# ✅ CORRECT
events_df['time_group'] = events_df['ts_utc'].dt.floor('1min')
grouped = events_df.groupby('time_group')

for time_group, group_events in grouped:
    impact = calculate_group_impact(time_group, prices_df)
```

**Session :** 8-9  
**Impact :** ⭐⭐⭐ CRITIQUE

### Erreur #6 : Utiliser mauvaise base de données

```python
# ❌ FAUX - Bases vides ou corrompues
conn = duckdb.connect('fx_impact_app/data/fx_news_impact.db')

# ✅ CORRECT - Toujours warehouse.duckdb
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
```

**Session :** 7  
**Fréquence :** ⭐⭐⭐ Très fréquent

### Erreur #7 : Fenêtre temporelle trop large

**Erreur :** Utiliser 120 minutes au lieu de 60 minutes.

**Impact :**
- Max aberrant : 3,703 → 1,056 pips
- Corrélation : 0.108 → 0.292

**Session :** 7  
**Impact :** ⭐⭐ Important

### Erreur #8 : Confusion MoM/YoY (Session 19)

**Erreur critique :** L'API EODHD retourne plusieurs versions d'un même indicateur (MoM, YoY) mais on ne les distinguait pas.

**Solution :**
```python
# Extraire champ 'comparison' de l'API
comparison = _col(raw, "comparison").astype("string")

# Enrichir event_key avec le suffixe
if comparison in ['mom', 'yoy', 'qoq']:
    event_key = f"{event_key}_{comparison}"
```

**Impact :**
- Avant: 665 événements avec distinction
- Après: 12,816 événements (+1,827%)

**Session :** 19  
**Fréquence :** ⭐⭐⭐ CRITIQUE

### Erreur #9 : Supposer que les données DB sont correctes

```python
# ❌ FAUX - Utiliser aveuglément
surprise = calculate_surprise(actual, estimate)

# ✅ CORRECT - Vérifier et valider
if pd.notna(row['estimate']) and row['estimate'] != 0:
    surprise = calculate_surprise(row['actual'], row['estimate'])
else:
    surprise = None
```

**Session :** 17  
**Impact :** ⭐⭐⭐ CRITIQUE

### Erreur #10 : event_families obsolète (Session 21)

**Erreur identifiée :** Table `event_families` ne contient PAS les suffixes (_mom, _yoy, _qoq).

**Conséquence :**
- `inflation_rate_mom` (33.3% surprise) ne matche pas
- V2 utilise `inflation rate` (0% surprise) à la place
- **Impact : Détection surprise 11.9% au lieu de 33.3%**

**Solution :** Reconstruire event_families depuis zéro (Session 22)

**Session :** 21  
**Fréquence :** ⭐⭐⭐ CRITIQUE

---

## <a name="scripts"></a>📜 5. SCRIPTS IMPORTANTS

### Scripts de reconstruction (Session 22 - À CRÉER)

| Script | Objectif | Priorité | Durée |
|--------|----------|----------|-------|
| `rebuild_event_families_from_scratch_session22.py` | Reconstruire event_families avec suffixes | 🔥 CRITIQUE | 15-20 min |
| `rebuild_event_group_impacts_from_scratch_session22.py` | Reconstruire event_group_impacts | 🔥 CRITIQUE | 30-60 min |
| `rebuild_scores_from_scratch_session22.py` | Reconstruire scores (si existe) | ⭐ IMPORTANT | 10-15 min |
| `rebuild_event_impacts_calculated_from_scratch_session22.py` | Reconstruire event_impacts_calculated (si existe) | ⭐ UTILE | 20-30 min |

### Scripts de diagnostic (Session 21)

| Script | Objectif | Statut |
|--------|----------|--------|
| `diagnostic_complet_session21.py` | Diagnostic complet 3 parties | ✅ Créé |
| `remeasure_v2_with_clean_data_session20.py` | Re-mesure V2 | ✅ Exécuté |
| `audit_impact_session19_session20.py` | Audit tables obsolètes | ✅ Exécuté |

### Scripts d'analyse historiques

| Script | Objectif | Session |
|--------|----------|---------|  
| `analyze_impact_patterns_warehouse.py` | Analyse patterns historiques | 7 |
| `calculate_grouped_impacts.py` | Calcule impacts GROUPÉS | 8-9 |
| `analyze_v9_with_filtering.py` | Génération v9-CLEAN | 9 |
| `measure_impacts_v1_v2_session17.py` | Mesure performances | 17 |

---

## <a name="metriques"></a>📊 6. MÉTRIQUES DE PERFORMANCE

### Évolution de la précision

| Version | Formule | MAE | Session | Statut |
|---------|---------|-----|---------|--------|
| V1 | score / 50 | 258.8% | 1-5 | ⚠️ Obsolète |
| V2 | Amplification surprise | 137.8% | 15-20 | ⚠️ Obsolète |
| **V3d** | **Combinaison optimale** | **~50-60%** | **21** | ✅ **À implémenter** |

### Test de référence : 11 septembre 2025

| Métrique | V2 (actuel) | V3d (attendu) | Réel MT5 |
|----------|-------------|---------------|----------|
| Phase 1 Impact | 42 pips | **412 pips** | 522 pips |
| Erreur Phase 1 | 92% | **21%** ✅ | - |
| Pullback | -124 pips | -124 pips | -114 pips |
| Erreur Pullback | 9% ✅ | 9% ✅ | - |

**Note :** V2 utilise surprise 11.9% (mauvaise), V3d utiliserait 33.3% (correcte)

---

## <a name="decisions"></a>🎯 7. DÉCISIONS DE CONCEPTION

### Décision #1 : Reconstruire tables dérivées (Session 21)

**Contexte :** Suite import Session 19 (+75% événements), tables obsolètes.

**Décision :** RECONSTRUIRE event_families + event_group_impacts depuis zéro

**Rationale :**
- ✅ Garantit cohérence totale
- ✅ Élimine bugs cachés
- ✅ Plus rapide que debug patches

**Session :** 21  
**Statut :** ✅ Approuvé

### Décision #2 : Formule V3d (Session 21)

**Contexte :** V2 sous-estime ×25 les événements extrêmes.

**Décision :** Implémenter V3d (amplification variable + synergie)

**Rationale :**
- ✅ Détecte événements extrêmes (surprise > 30%)
- ✅ Amplifie correctement (10× si score>70)
- ✅ Tient compte multi-événements (2×)
- ✅ Erreur attendue 21% vs 92% actuel

**Session :** 21  
**Statut :** ✅ Validé, à implémenter Session 22

### Décision #3 : Méthode MAX pour multi-événements (Session 17)

**Contexte :** Quand plusieurs événements simultanés, quelle méthode ?

**Décision :** Score MAX du groupe (pas somme)

**Rationale :**
- Validé sur 2,089 groupes
- 4× plus précis que méthode additive
- Coefficient synergie négligeable (~1.05×)

**Session :** 17  
**Statut :** ✅ Validé

### Décision #4 : Facteur de correction 0.758 (Session 11)

**Contexte :** Somme vectorielle surestime légèrement.

**Décision :** Appliquer facteur global 0.758

**Rationale :**
- Simple à implémenter
- Réduit erreur 32% → ~0%
- Validé sur cas test

**Session :** 11  
**Statut :** ✅ Intégré dans V3d

### Décision #5 : Importer TOUS les champs API (Session 19)

**Contexte :** API EODHD retourne 10 champs, on en importait 5.

**Décision :** Importer les 10 champs

**Rationale :**
- ✅ Évite confusions futures
- ✅ Données complètes
- ✅ Pas de re-import nécessaire
- ⚠️ +30% taille DB acceptable

**Session :** 19  
**Statut :** ✅ Implémenté

---

## <a name="etat-actuel"></a>📋 8. ÉTAT ACTUEL DU PROJET

### État base de données (Session 21)

| Table | Lignes | État | Action |
|-------|--------|------|--------|
| **events** | 58,449 | ✅ À JOUR | Aucune |
| **event_families** | 241 | ❌ OBSOLÈTE | **RECONSTRUIRE** |
| **event_group_impacts** | 2,089 | ❌ OBSOLÈTE | **RECONSTRUIRE** |
| **scores** | ? | ❌ OBSOLÈTE | **RECONSTRUIRE** |
| **prices_1m** | 1.1M | ✅ À JOUR | Aucune |

### Formule en production

**Actuelle :** V2 (MAE 137.8%, erreur 92% sur 11 sept)

**À implémenter :** V3d (MAE ~50-60%, erreur 21% sur 11 sept)

### Scripts cassés (Session 20)

**76 scripts** nécessitent révision (jointures event_families obsolètes)

**À faire après reconstruction :** Re-tester tous les scripts

### Prochaines sessions

**Session 22 : RECONSTRUCTION + IMPLÉMENTATION**
1. Reconstruire 4 tables (1-2h)
2. Implémenter V3d (30-45 min)
3. Valider sur 11 septembre
4. Re-mesurer performance globale

**Session 23 : VALIDATION ÉTENDUE**
1. Tester V3d sur 50-100 événements
2. Mesurer MAE finale
3. Ajuster coefficients si nécessaire

---

## 🔄 MAINTENANCE DE CE DOCUMENT

**Règles de mise à jour :**

1. ✅ Fusionner tous les updates dans CE fichier unique
2. ✅ Marquer informations obsolètes avec ⚠️
3. ✅ Ajouter découvertes majeures
4. ✅ Mettre à jour état actuel
5. ✅ Documenter décisions importantes

**Fréquence :** À chaque fin de session

**Responsable :** Maintenu collaborativement (humain + Claude)

---

## 📚 DOCUMENTS CONNEXES À CONSULTER

1. **`RAPPORT_SESSION21_FINAL.md`** ⭐⭐⭐ - Rapport complet Session 21
2. **`ERREURS_RECURRENTES.md`** ⭐⭐⭐ - Erreurs à éviter
3. **`DB_STRUCTURE_REFERENCE.md`** ⭐⭐ - Structure DB détaillée
4. **`MESSAGE_POUR_CLAUDE_SESSION22.md`** ⭐⭐ - Instructions Session 22

---

**FIN DE LA BASE DE CONNAISSANCES CONSOLIDÉE**

**Version :** 3.0 (CONSOLIDÉE)  
**Sessions couvertes :** 1-21  
**Dernière mise à jour :** 19 octobre 2025 - Session 21  
**Fichiers fusionnés :** 7 (Base + 6 updates)  
**Statut :** ✅ **DOCUMENT UNIQUE DE RÉFÉRENCE**
