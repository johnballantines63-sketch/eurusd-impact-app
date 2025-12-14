# Scripts Finnhub - Résumé

## ✅ Scripts Trouvés

### 1. **`finnhub_import.py`**
- **Fonction** : Import événements économiques depuis Finnhub
- **Usage** : `python3 scripts/finnhub_import.py --from-date YYYY-MM-DD --to-date YYYY-MM-DD`

### 2. **`finnhub_import_historical.py`**
- **Fonction** : Import historique complet (par mois)
- **Usage** : `python3 scripts/finnhub_import_historical.py --start-year 2023 --end-year 2025`

### 3. **`update_finnhub_prices_to_today.py`**
- **Fonction** : Met à jour les prix EUR/USD M1 depuis dernière date jusqu'à aujourd'hui
- **Usage** : `python3 scripts/update_finnhub_prices_to_today.py`

### 4. **`update_finnhub_data_to_today.py`** (NOUVEAU)
- **Fonction** : Met à jour automatiquement **prix ET événements** jusqu'à aujourd'hui
- **Usage** : `python3 scripts/update_finnhub_data_to_today.py`

## 🔑 Configuration

La clé API Finnhub est configurée dans le fichier `.env` :
```
FINNHUB_API_KEY=d4f3bq1r01qkcvvgcavgd4f3bq1r01qkcvvgcb00
```

## 📊 Base de Données

- **Prix** : Tables `prices_1m` / `prices_1m_compat` (vue `prices_1m_v`)
- **Événements** : Table `events`
- **Chemin DB** : `../fx_impact_app/data/warehouse.duckdb`

## 🚀 Mise à Jour Rapide

Pour mettre à jour toutes les données jusqu'à aujourd'hui :

```bash
python3 scripts/update_finnhub_data_to_today.py
```

Ce script :
1. ✅ Met à jour les prix depuis dernière date → aujourd'hui
2. ✅ Met à jour les événements (7 jours passés → 30 jours futurs)

## 📝 Notes

- Les scripts gèrent automatiquement les doublons
- Rate limiting : 30 calls/second
- Timezone : UTC pour prix et événements dans la DB


