# Streamlit App — EURUSD Trading Assistant

## Installation

```bash
# Installer les dépendances
pip install streamlit plotly duckdb pandas numpy

# Ou via requirements.txt (si disponible)
pip install -r requirements.txt
```

## Lancement

```bash
# Depuis la racine du projet
streamlit run app/streamlit_app.py

# Ou avec un port spécifique
streamlit run app/streamlit_app.py --server.port 8501
```

## Configuration

L'app lit par défaut `data/warehouse.duckdb`.

Vous pouvez modifier le chemin dans la sidebar de l'interface.

## Fonctionnalités V1

- ✅ Calendar : liste des dates avec prédictions
- ✅ Day Detail : détails d'une journée sélectionnée
- ✅ Events timeline : affichage des événements (core/non-core)
- ✅ Formulaire Actuals : saisie des valeurs réelles
- ✅ Trading Plan : gates + targets + fenêtres
- ✅ Graphique : pattern attendu (placeholder)

## Notes

- V1 utilise un **placeholder** pour pattern/direction
- Les actuals sont stockés en session (pas d'écriture DB)
- À brancher au moteur réel (contracts + cluster/pattern) dans V2

