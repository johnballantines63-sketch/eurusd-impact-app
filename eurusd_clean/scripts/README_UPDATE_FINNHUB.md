# Scripts de Mise à Jour Finnhub

## Scripts Existants

### 1. **`finnhub_import.py`** - Import Événements
Importe les événements économiques depuis l'API Finnhub.

**Usage :**
```bash
python3 scripts/finnhub_import.py --from-date 2025-10-21 --to-date 2025-12-07
```

**Options :**
- `--from-date` : Date début (YYYY-MM-DD) - **requis**
- `--to-date` : Date fin (YYYY-MM-DD) - **requis**
- `--countries` : Liste pays (ex: US DE FR) - optionnel
- `--no-replace` : Ne pas remplacer, juste ajouter - optionnel

### 2. **`finnhub_import_historical.py`** - Import Historique Complet
Importe l'historique complet des événements par mois.

**Usage :**
```bash
python3 scripts/finnhub_import_historical.py --start-year 2023 --end-year 2025
```

### 3. **`update_finnhub_prices_to_today.py`** - Mise à Jour Prix
Met à jour les prix EUR/USD M1 depuis la dernière date en DB jusqu'à aujourd'hui.

**Usage :**
```bash
python3 scripts/update_finnhub_prices_to_today.py
```

**Fonctionnalités :**
- Détecte automatiquement la dernière date en DB
- Importe seulement les données manquantes
- Gère les doublons automatiquement
- Rate limiting (30 calls/second)

## Script Unifié

### **`update_finnhub_data_to_today.py`** - Mise à Jour Complète
Met à jour automatiquement **prix ET événements** jusqu'à aujourd'hui.

**Usage :**
```bash
python3 scripts/update_finnhub_data_to_today.py
```

**Ce qu'il fait :**
1. ✅ Met à jour les prix depuis dernière date → aujourd'hui
2. ✅ Met à jour les événements (7 jours passés → 30 jours futurs)

**Prérequis :**
- Variable d'environnement `FINNHUB_API_KEY` configurée
- Base de données `warehouse.duckdb` accessible

## Exemple d'Utilisation

```bash
# Mise à jour complète (prix + événements)
python3 scripts/update_finnhub_data_to_today.py

# Ou séparément :
python3 scripts/update_finnhub_prices_to_today.py
python3 scripts/finnhub_import.py --from-date 2025-11-30 --to-date 2026-01-07
```

## Notes

- Les scripts gèrent automatiquement les doublons
- Les prix sont stockés dans `prices_1m` / `prices_1m_compat` (vue `prices_1m_v`)
- Les événements sont stockés dans la table `events`
- Timezone : Les prix et événements sont en UTC dans la DB


