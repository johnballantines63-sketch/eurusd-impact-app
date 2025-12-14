# EUR/USD News Impact Calculator

Application Streamlit pour analyser l'impact des actualités économiques sur la paire EUR/USD.

## 🎯 Fonctionnalités

- **Calendrier Trading** : Visualisation des événements économiques à venir
- **Analyseur Surprise** : Prédiction d'impact basée sur écarts actual vs forecast
- **Backtest Stratégie** : Analyse historique de performance
- **Planificateur Multi-Événements** : Gestion des événements simultanés
- **Impact Planner** : Planification des trades autour des actualités

## 🏗️ Architecture

```
eurusd_news_impact_calculator/
├── fx_impact_app/
│   ├── src/                    # Modules Python
│   │   ├── config.py
│   │   ├── event_families.py   # 26 familles d'événements
│   │   ├── forecaster_mvp.py
│   │   ├── scoring_engine.py
│   │   └── download_database.py
│   ├── streamlit_app/
│   │   ├── Home.py             # Point d'entrée
│   │   └── pages/              # 5 pages
│   └── data/
│       └── warehouse.duckdb    # Base (téléchargée depuis Google Drive)
```

## 📊 Base de Données

- **31,988 événements économiques** (USA, Zone Euro)
- **0 doublons** (nettoyée)
- **26 familles** avec sensibilités calibrées
- Historique depuis 2015

## 🚀 Déploiement

Application déployée sur Streamlit Cloud avec base de données hébergée sur Google Drive.

### Variables d'environnement requises

```env
EODHD_API_KEY=votre_clé_eodhd
TE_API_KEY=votre_clé_trading_economics
GDRIVE_DB_FILE_ID=1Kr4t_X-D12rex48s-FfdxR4UhxR7h-g-
```

## 📱 Accès

- **Web** : [URL Streamlit Cloud]
- **iPhone** : Ajouter à l'écran d'accueil pour mode PWA

## 🔧 Technologies

- Streamlit 1.50.0
- DuckDB 1.4.0
- Pandas 2.3.3
- Python 3.x

## 📝 Notes

- Base de données téléchargée automatiquement au premier lancement
- Mode fallback sur `previous` si `forecast` NULL (99.9% des cas)
- Saisie manuelle disponible pour événements critiques

---

**Version** : 3.1  
**Dernière mise à jour** : Octobre 2025
