# Notebooks de Validation

## Validation Empirique — Events vs Prix Réels

Notebook pour valider empiriquement les événements et les patterns de prix réels.

### Lancer le notebook

```bash
jupyter notebook notebooks/validate_events_vs_price_patterns.ipynb
```

Ou avec JupyterLab :

```bash
jupyter lab notebooks/validate_events_vs_price_patterns.ipynb
```

### Notes importantes

Le notebook utilise les colonnes suivantes des tables DB :
- `events_with_ts_local_v1` : utilise `ts_utc`, `ts_local`, `actual`, `estimate`, `previous` (pas `prev`)
- `economic_events` : utilise `datetime_utc` (renommé en `ts_utc`), `event_name` (renommé en `event`), `forecast` (renommé en `estimate`), `previous` (renommé en `prev`)
- `prices_finnhub_m5` : utilise `datetime` (renommé en `ts_utc`)

Les fonctions `load_consensus()` et `load_prices_full_day()` effectuent ces renommages automatiquement pour uniformiser les noms de colonnes dans le notebook.

