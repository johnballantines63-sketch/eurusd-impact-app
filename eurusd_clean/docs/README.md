# 📊 EUR/USD Impact Calculator - Clean Architecture

> Application professionnelle d'analyse d'impact des événements économiques sur EUR/USD

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Migration](https://img.shields.io/badge/migration-50%25-yellow.svg)](PROJECT_STATE.md)

---

## 🎯 Vue d'Ensemble

Ce projet fournit une analyse quantitative de l'impact des événements économiques (CPI, NFP, décisions banques centrales, etc.) sur la paire EUR/USD.

**Fonctionnalités principales :**
- 📈 Prédiction d'impact en pips
- ⏱️ Calcul latence et time-to-revert
- 🎲 Analyse surprise vs prévision
- 📊 Score composite de "tradabilité"
- 🔄 Gestion multi-événements simultanés

**Données :**
- 58,449 événements économiques (US, EU, GB)
- 1.1M+ bougies 1-minute EUR/USD
- 747 familles d'événements calibrées
- 3 ans d'historique (2022-2025)

---

## 🏗️ Architecture

```
eurusd_clean/
│
├── app/                          # Application principale
│   ├── config.py                 # Configuration centralisée ✅
│   │
│   ├── core/                     # Logique métier pure
│   │   ├── calculations.py       # Calculs impacts/latence/TTR ✅
│   │   ├── models.py             # Data models (EventFamily) ✅
│   │   └── formulas.py           # Formules v9-clean, v87 (à créer)
│   │
│   ├── services/                 # Couche services
│   │   ├── data_service.py       # Interface unique DB ✅
│   │   ├── prediction_service.py # Prédictions (Session 31)
│   │   └── scoring_service.py    # Scores composite (Session 32)
│   │
│   └── data/
│       └── warehouse.duckdb      # Base de données (205 MB)
│
├── tests/                        # Tests automatisés
│   ├── test_core/                # Tests logique métier ✅
│   ├── test_services/            # Tests services ✅
│   └── test_integration/         # Tests intégration (à créer)
│
├── scripts/                      # Scripts utilitaires
│   ├── migration/                # Scripts migration legacy
│   └── test_data_service.py      # Validation rapide ✅
│
└── docs/                         # Documentation
    ├── SESSION_30_SUMMARY.md     # Résumé dernière session
    └── archives/                 # Historique sessions
```

---

## 🚀 Démarrage Rapide

### Prérequis

```bash
Python 3.9+
DuckDB
Pandas, Pytest
```

### Installation

```bash
# Cloner le repository
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt
```

### Configuration

```bash
# (Optionnel) Créer fichier .env à la racine
cat > .env << EOF
EODHD_API_KEY=your_key_here
TE_API_KEY=your_key_here
EOF
```

### Validation

```bash
# Tester DataService
python3 scripts/test_data_service.py

# Lancer tous les tests
pytest tests/ -v
```

---

## 📚 Utilisation

### Exemple 1 : Récupérer Événements

```python
from app.services import DataService

# Initialiser service
data_service = DataService()

# Récupérer événements US septembre 2025
events = data_service.get_events(
    start_date='2025-09-01',
    end_date='2025-09-30',
    countries=['US'],
    min_importance=3,
    with_family=True
)

print(f"Trouvé {len(events)} événements haute importance")
print(events[['event_title', 'family', 'avg_movement_pips']].head())
```

### Exemple 2 : Récupérer Prix

```python
# Prix EUR/USD autour CPI US (11 sept 2025, 14:30)
prices = data_service.get_prices(
    start_time='2025-09-11 14:00:00',
    end_time='2025-09-11 15:00:00',
    timeframe='1m'
)

print(f"Récupéré {len(prices)} bougies 1-minute")
```

### Exemple 3 : Statistiques DB

```python
# Diagnostics base de données
stats = data_service.get_db_stats()

print(f"Événements : {stats['events_count']:,}")
print(f"Prix 1m : {stats['prices_count']:,}")
print(f"Période : {stats['first_event']} → {stats['last_event']}")
```

### Exemple 4 : Context Manager

```python
# Gestion automatique connexion
with DataService() as service:
    events = service.get_events(
        start_date='2025-09-11',
        end_date='2025-09-11'
    )
    # Connexion fermée automatiquement
```

---

## 🧪 Tests

### Lancer Tests

```bash
# Tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/test_services/test_data_service.py -v

# Tests avec coverage
pytest tests/ --cov=app --cov-report=html
```

### Tests Critiques

Le projet inclut des tests spécifiques pour **prévenir les erreurs récurrentes** :

✅ **Test jointure event_families** : Vérifie jointure sur event_key ET country  
✅ **Test surprise fallback** : Vérifie calcul avec estimate/previous  
✅ **Test validation données** : Vérifie cohérence DB

Ces tests garantissent que les 9 erreurs documentées dans `PROJECT_STATE.md` sont évitées.

---

## 📖 Documentation

### Fichiers Essentiels

| Fichier | Description |
|---------|-------------|
| [PROJECT_STATE.md](PROJECT_STATE.md) | 📄 **Fichier maître** - Source unique de vérité |
| [CHANGELOG.md](CHANGELOG.md) | 📋 Historique des versions |
| [STRUCTURE.md](STRUCTURE.md) | 🏗️ Arborescence détaillée |
| [docs/SESSION_30_SUMMARY.md](docs/SESSION_30_SUMMARY.md) | 📊 Résumé dernière session |

### Sections Critiques PROJECT_STATE.md

- **Section 1** : État actuel (À LIRE EN PREMIER)
- **Section 2** : Architecture système
- **Section 3** : ⚠️ Erreurs à ne jamais répéter (CRITIQUE)
- **Section 7** : Résumés sessions récentes

---

## 🔬 Méthodologie

### Formule Active : v9-clean

**Somme vectorielle avec correction empirique**

```python
# Pour multi-événements
vectorial_sum = sum(impact_i * direction_i for each event)
corrected_impact = vectorial_sum * 0.758  # Facteur validé empiriquement

# Direction : +1 (positif) ou -1 (négatif) selon surprise
```

**Performances :**
- R² : 0.292 (avec correction 0.758)
- R² : 0.264 (sans correction)

### Données Validées

✅ **events** : 58,449 événements (2022-2025)  
✅ **event_families** : 747 familles calibrées  
✅ **prices_1m** : 1,114,260 bougies Dukascopy  
⚠️ **event_impacts_v2** : 8,344 événements (phase1 à calculer)

---

## 🚧 État du Projet

### Progression Migration : 50%

**Modules migrés :**
- ✅ config.py (Session 30)
- ✅ forecaster_mvp.py → calculations.py (Session 29)
- ✅ event_families.py → models.py (Session 29)

**Services créés :**
- ✅ DataService (Session 30)
- ⏳ PredictionService (Session 31)
- ⏳ ScoringService (Session 32)

**Tests :**
- ✅ 30+ tests DataService
- ✅ 20+ tests calculations/models
- ⏳ Tests intégration (Session 31+)

### Prochaines Sessions

**Session 31 (Prévue) :**
- Créer PredictionService
- Migrer sequence_multi_event_timeline_v87.py
- Tests prédiction multi-événements

**Session 32 (Prévue) :**
- Créer ScoringService
- Refactoriser UI Streamlit
- Tests intégration complets

---

## ⚠️ Points d'Attention

### Erreurs à Éviter

Le projet documente **9 erreurs récurrentes critiques** identifiées sur 27 sessions :

1. ❌ Utiliser `ef.event_name` (n'existe pas)
2. ❌ Oublier fallback `estimate`/`previous` pour surprise
3. ❌ Jointure sans `country`
4. ❌ `CAST AS TIME` au lieu de `strftime()`
5. ❌ Calculer impacts individuellement (doublons)
6. ❌ Utiliser mauvaise base de données
7. ❌ Confondre `avg_movement_pips` avec impact réel
8. ❌ NULL dans agrégations texte
9. ❌ Fenêtre temporelle trop large

**→ Voir PROJECT_STATE.md Section 3 pour détails**

### Checklist Avant Requête SQL

- [ ] J'utilise `warehouse.duckdb`
- [ ] Je N'utilise PAS `ef.event_name`
- [ ] Je joins sur `event_key` ET `country`
- [ ] J'utilise `strftime()` pour timestamps
- [ ] J'ai un fallback `estimate`/`previous`
- [ ] Je groupe par minute pour multi-événements

---

## 🤝 Contribution

### Standards Qualité

- ✅ Type hints obligatoires
- ✅ Docstrings avec exemples
- ✅ Tests unitaires pour nouveau code
- ✅ Respect erreurs récurrentes documentées
- ✅ Ratio tests/code > 50%

### Workflow

1. Lire `PROJECT_STATE.md` Section 1-3
2. Consulter `MIGRATION_REPORT.md` pour priorités
3. Créer branche feature
4. Implémenter avec tests
5. Valider checklist qualité
6. Mettre à jour `PROJECT_STATE.md` et `CHANGELOG.md`

---

## 📊 Statistiques

### Métriques Code

- **Lignes production** : ~1,600
- **Lignes tests** : ~1,200
- **Ratio tests/code** : 75%
- **Coverage** : ~65%

### Base de Données

- **Taille** : 205 MB
- **Événements** : 58,449
- **Prix 1m** : 1,114,260
- **Familles** : 747
- **Période** : 2022-01 → 2025-09

### Performance

- **Requête événements** : ~50ms (1 mois)
- **Requête prix** : ~100ms (1h)
- **Calcul impact** : ~20ms
- **Stats DB** : ~200ms

---

## 📝 Licence

Projet privé - Développement interne

---

## 📞 Support

Pour questions ou problèmes :

1. Consulter `PROJECT_STATE.md` Section 1
2. Vérifier `CHANGELOG.md` pour changements récents
3. Lire documentation sessions (`docs/`)

---

## 🏆 Remerciements

**Sessions de développement :**
- Session 28 : Analyse & décision migration
- Session 29 : Migration core (calculations, models)
- Session 30 : Config + DataService

**Outils utilisés :**
- DuckDB (base de données analytique)
- Pandas (manipulation données)
- Pytest (tests automatisés)
- Python 3.9+

---

**Version :** 0.3.0  
**Dernière mise à jour :** 22 octobre 2025 - Session 30  
**Statut :** 🚧 Migration en cours (50%)  
**Prochain jalon :** PredictionService (Session 31)
