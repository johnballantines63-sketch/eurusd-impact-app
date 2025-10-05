
# FX Impact — V5 full (light)
- Chemins DB robustes via `src/config.py` (utilise env `FX_DB_PATH` si défini).
- Pages incluses (certaines en mode *stub* pour sécuriser le démarrage) :
  1. Ingestion, 2. Discovery, 3. Scanner Q1, 4. Linked news q2, 5. Planner
  6. Top events (filtrage + affichage), 7. Simultaneous events (groupes +/- X min)
  8. Forecaster MVP (API stable), 9. Backtest (simplifié), 10. Calendar Sim Backtest
- **Placement conseillé de la DB** : `fx_impact_app/data/warehouse.duckdb`, sinon définir :
  ```bash
  export FX_DB_PATH="$(pwd)/fx_impact_app/data/warehouse.duckdb"
  ```
- Lancement :
  ```bash
  export PYTHONPATH="$(pwd)"
  streamlit run fx_impact_app/streamlit_app/Home.py
  ```
