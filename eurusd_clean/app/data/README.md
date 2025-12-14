# Base de Données - warehouse.duckdb

## 🗄️ Emplacement

**Base de données DANS ce répertoire :**
```
eurusd_clean/app/data/warehouse.duckdb
```

**Taille :** ~205 MB  
**Tables :** 8 principales  
**Événements :** 58,449

## 📋 Installation

### Copier depuis Projet Legacy

```bash
# Depuis la racine du projet
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC

# Copier base de données
cp fx_impact_app/data/warehouse.duckdb eurusd_clean/app/data/

# Vérifier
ls -lh eurusd_clean/app/data/warehouse.duckdb
```

### Vérifier Installation

```bash
cd eurusd_clean
python3 app/config.py
```

**Sortie attendue :**
```
✅ Base de données:
   Taille: 205.0 MB
   Tables: 8
   Événements: 58,449
```

## 🎯 Philosophie

**eurusd_clean/ est 100% autonome**
- ✅ Toutes les données incluses
- ✅ Pas de dépendances externes
- ✅ Prêt à déployer
- ✅ Isolation complète du legacy

**Projet legacy = Référence temporaire**
- Consulter si besoin
- Supprimer quand nouveau opérationnel
- Pas de liens/dépendances croisées

## 📊 Structure Base de Données

```
warehouse.duckdb (205 MB)
├── events (58,449)              # Événements économiques US/EU/GB
│   ├── ts_utc                  # Timestamp UTC
│   ├── event_key               # Identifiant (ex: "cpi", "nfp")
│   ├── event_title             # Nom complet
│   ├── country                 # Pays (US, EU, GB)
│   ├── actual                  # Valeur réelle
│   ├── estimate                # Consensus (45% rempli)
│   ├── forecast                # Forecast (45% rempli - copié depuis estimate)
│   └── previous                # Valeur précédente (86% rempli)
│
├── event_families (747)         # Mappings familles événements
│   ├── event_key
│   ├── country
│   ├── family                  # Catégorie (Employment, Inflation, etc.)
│   ├── empirical_score         # Score empirique 0-100
│   └── avg_movement_pips       # Mouvement moyen historique
│
├── event_impacts_v2 (8,344)     # Impacts calculés
│   ├── time_group              # Timestamp groupe (arrondi minute)
│   ├── surprise_pct            # % surprise calculée
│   ├── phase1_pips             # Impact phase 1 (⚠️ NULL - à calculer)
│   ├── ttr_minutes             # Time to reversal (⚠️ NULL)
│   └── direction               # Direction mouvement (⚠️ NULL)
│
├── scores (991)                 # Scores empiriques familles
│   ├── event_key
│   ├── country
│   └── empirical_score
│
├── prices_1m (1,114,260)        # Prix EUR/USD minute
│   ├── ts_utc
│   ├── open, high, low, close
│   └── volume
│
├── prices_5m                    # Prix 5 minutes
├── prices_15m                   # Prix 15 minutes
└── prices_1h                    # Prix 1 heure
```

## 🔧 Utilisation dans Code

```python
# app/services/data_service.py
from app.config import get_db_path
import duckdb

class DataService:
    def __init__(self):
        self.db_path = get_db_path()  # app/data/warehouse.duckdb
        
    def get_events(self, start_date, end_date):
        conn = duckdb.connect(self.db_path)
        query = """
            SELECT * FROM events
            WHERE DATE(ts_utc) BETWEEN ? AND ?
        """
        events = conn.execute(query, [start_date, end_date]).fetchdf()
        conn.close()
        return events
```

## ⚠️ Important

**Base de données = Partie intégrante eurusd_clean/**

- Ne PAS créer liens symboliques vers legacy
- Ne PAS référencer chemin legacy
- Copier warehouse.duckdb directement ici

**Avantages :**
- Isolation complète
- Déploiement simple (un dossier)
- Suppression legacy sans impact
- Clarté architecture

## 🧹 Nettoyage Futur

**Quand eurusd_clean/ sera opérationnel :**

```bash
# Supprimer projet legacy (libère espace disque)
rm -rf fx_impact_app/
rm -rf scripts/
rm -rf tests/
rm *.py  # Tous scripts racine
rm *.md  # Anciens README

# Garder uniquement eurusd_clean/
```

**Résultat :** Structure propre, professionnelle, autonome.

---

**Créé :** Session 28 - 22 octobre 2025  
**Status :** 🚧 À installer - Copier warehouse.duckdb depuis legacy
