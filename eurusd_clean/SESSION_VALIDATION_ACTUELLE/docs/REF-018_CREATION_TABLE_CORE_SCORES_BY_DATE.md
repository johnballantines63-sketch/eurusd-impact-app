# REF-018 : Création Table core_scores_by_date

**Date :** 2025-12-06  
**Objectif :** Créer une table pour stocker les scores core_scores par date (pas agrégée) afin de calculer les ratios pour toutes les dates historiques

---

## 📊 PROBLÈME IDENTIFIÉ

### Problème Initial

La table `core_scores` actuelle est **agrégée** (pas de colonne `datetime`) :
- Clé primaire : `(core_type, country)`
- Contient les scores moyens calculés sur toutes les dates historiques
- **Impossible de calculer les ratios Impact/Score pour chaque date individuelle**

### Conséquence

- On ne peut pas valider les théories sur un large échantillon
- On ne peut pas identifier les outliers (dates avec ratio anormal)
- On ne peut pas intégrer le ratio dans le pipeline pour améliorer les prédictions

---

## ✅ SOLUTION IMPLÉMENTÉE

### Nouvelle Table : `core_scores_by_date`

**Structure :**
```sql
CREATE TABLE core_scores_by_date (
    date DATE,
    core_type VARCHAR,
    country VARCHAR,
    empirical_score DOUBLE,        -- Score depuis core_scores (agrégé)
    impact_real DOUBLE,            -- Impact réel mesuré depuis prix
    ratio DOUBLE,                  -- impact_real / empirical_score
    anchor_time TIMESTAMP,
    n_core_events INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, core_type, country)
)
```

### Avantages

1. **Stockage par date** : Permet d'analyser chaque date individuellement
2. **Calcul de ratios** : Ratio Impact/Score pour chaque date
3. **Identification outliers** : Dates avec ratio anormal (sous/sur-estimation)
4. **Validation théories** : Tester sur large échantillon (1000+ dates)
5. **Intégration pipeline** : Utiliser ratio moyen par core_type comme multiplicateur

---

## 🔧 SCRIPT CRÉÉ

### `creer_table_core_scores_by_date.py`

**Fonctionnalités :**

1. **`--create`** : Créer la table
2. **`--populate`** : Remplir la table
   - `--limit N` : Limiter à N dates (pour test)
   - `--quiet` : Mode silencieux
3. **`--stats`** : Calculer statistiques depuis la table

**Filtres appliqués :**
- Dates avec `actual` disponible (pas de dates futures)
- Dates avec données de prix disponibles
- Événements HIGH importance (importance_n = 3)
- Pays US ou EU
- Core type détecté (pas GENERIC)

---

## 📈 RÉSULTATS INITIAUX

### Test avec 3 dates

| Date | Core Type | Country | Score DB | Impact Réel | Ratio | Statut |
|------|-----------|---------|----------|-------------|-------|--------|
| 2025-11-28 | CPI | US | 75.06 | 41.00 | 0.546 | ✅ Succès |
| 2025-11-27 | GENERIC | - | - | - | - | ❌ Core type non détecté |
| 2025-11-26 | GENERIC | - | - | - | - | ❌ Core type non détecté |

**Observation :** Seulement les dates avec core type détecté (CPI, NFP, etc.) sont stockées.

---

## 🎯 UTILISATION

### 1. Créer la table

```bash
python creer_table_core_scores_by_date.py --create
```

### 2. Remplir la table (test avec 10 dates)

```bash
python creer_table_core_scores_by_date.py --populate --limit 10
```

### 3. Remplir la table (complet - peut prendre du temps)

```bash
python creer_table_core_scores_by_date.py --populate
```

### 4. Calculer statistiques

```bash
python creer_table_core_scores_by_date.py --stats
```

---

## 📊 STATISTIQUES ATTENDUES

Une fois la table remplie, on pourra calculer :

### Par Core Type

| Core Type | N Dates | Ratio Moyen | Ratio Médian | Ratio Std | Impact Moyen | Score Moyen |
|-----------|---------|-------------|-------------|-----------|--------------|-------------|
| CPI | ? | ? | ? | ? | ? | ? |
| NFP | ? | ? | ? | ? | ? | ? |
| JOBLESS_PCE | ? | ? | ? | ? | ? | ? |
| GDP | ? | ? | ? | ? | ? | ? |

### Utilisation dans Pipeline

**Ratio moyen par core_type** → Multiplicateur pour ajuster prédiction :

```python
# Exemple
ratio_cpi_mean = 0.831  # Depuis statistiques
impact_predicted = impact_base * amplification * ratio_cpi_mean
```

---

## 🔍 PROCHAINES ÉTAPES

### Étape 1 : Remplir la table complète ✅ (EN COURS)

- [ ] Lancer `--populate` sans `--limit` pour toutes les dates
- [ ] Monitorer les erreurs (dates sans core_type, etc.)
- [ ] Vérifier la qualité des données

### Étape 2 : Calculer statistiques

- [ ] Exécuter `--stats` pour obtenir ratios moyens
- [ ] Identifier outliers (ratio > 2.0 ou < 0.5)
- [ ] Analyser causes des outliers

### Étape 3 : Intégrer dans Pipeline

- [ ] Ajouter ratio moyen comme paramètre dans pipeline
- [ ] Utiliser comme multiplicateur pour ajuster prédiction
- [ ] Tester sur dates de validation

### Étape 4 : Valider Théories

- [ ] Tester relation Score → Impact sur large échantillon
- [ ] Identifier patterns récurrents
- [ ] Améliorer prédictions avec nouvelles données

---

## ⚠️ NOTES IMPORTANTES

1. **Dates futures** : Filtrées automatiquement (pas d'`actual` disponible)
2. **Core type GENERIC** : Exclu (pas de pattern détecté)
3. **Connexions DuckDB** : Gérées correctement (fermeture avant pipeline)
4. **Performance** : Peut prendre du temps pour 1000+ dates (exécuter en arrière-plan)

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06  
**Script :** `SESSION_VALIDATION_ACTUELLE/scripts/creer_table_core_scores_by_date.py`




