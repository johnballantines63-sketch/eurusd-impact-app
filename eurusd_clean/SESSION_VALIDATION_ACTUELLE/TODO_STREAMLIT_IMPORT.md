# TODO : Fonction Streamlit Import Automatique

## 📋 Objectif

Créer une fonction Streamlit pour l'import automatique des prix et événements Finnhub afin de toujours être à jour lors de l'intégration Streamlit.

## 🎯 Fonctionnalités Requises

### 1. Import Prix Finnhub
- Vérifier dernière date en DB
- Importer prix manquants depuis dernière date → aujourd'hui
- Afficher progression
- Gérer erreurs API

### 2. Import Événements Finnhub  
- Importer événements depuis 7 jours passés → 30 jours futurs
- Mettre à jour événements existants
- Afficher statistiques

### 3. Interface Streamlit
- Bouton "Mettre à jour les données"
- Indicateur de progression
- Messages de statut
- Affichage statistiques après import

## 📝 Notes Techniques

- Utiliser les scripts existants :
  - `scripts/update_finnhub_prices_to_today.py`
  - `scripts/finnhub_import.py`
  
- Placer dans un module dédié :
  - `streamlit_app/utils/data_refresh.py` ou
  - `streamlit_app/pages/DataRefresh.py`

- Déclencher automatiquement au démarrage de l'app (optionnel)
- Ou via bouton manuel dans une page dédiée

## 🔧 Structure Suggérée

```python
# streamlit_app/utils/data_refresh.py

def check_data_freshness():
    """Vérifie si les données sont à jour"""
    pass

def refresh_prices():
    """Met à jour les prix Finnhub"""
    pass

def refresh_events():
    """Met à jour les événements Finnhub"""
    pass

def refresh_all_data():
    """Met à jour prix + événements"""
    pass
```

## 📅 Priorité

- À faire lors de l'intégration Streamlit
- Utiliser les scripts existants comme base

## ✅ Scripts de Base Disponibles

- ✅ `scripts/update_finnhub_prices_to_today.py`
- ✅ `scripts/finnhub_import.py`
- ✅ `scripts/update_finnhub_data_to_today.py` (script unifié)

---

**Note** : Cette tâche est à réaliser lors de l'intégration Streamlit pour garantir que les données sont toujours à jour.


