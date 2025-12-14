# 🕒 TIMEZONE NOTE — events.ts_utc et prices_finnhub_m1.datetime

**Date** : 2025-12-12

## Constat empirique (ground-truth)

Tests réalisés sur deux dates repères :
- **2025-08-01** (release 14:30 Europe/Zurich): événements US à 14:30+02:00 + bougie M1 très active à 14:30+02:00
- **2024-09-11** (release 14:30 Europe/Zurich): événements US à 14:30+02:00 + bougie M1 très active à 14:30+02:00

Les checks ±1h / ±2h ne montrent pas de bougies comparables.

## Conclusion

- `events.ts_utc` est **déjà stocké en heure Europe/Zurich (avec offset)** malgré son nom.
- `prices_finnhub_m1.datetime` est aussi en Europe/Zurich.
- **Aucune conversion timezone n'est appliquée** dans les vues/jointures.

## Règle de sécurité

Toute modification future introduisant une conversion timezone doit :
1. être justifiée par un nouveau test ground-truth,
2. mettre à jour ce document,
3. passer le guardrail automatique (`scripts/check_timezone_guardrail.py`).

## Script de vérification

Pour vérifier l'alignement timezone :
```bash
python3 scripts/check_timezone_guardrail.py
```

Pour une analyse détaillée sur une date spécifique :
```bash
python3 scripts/check_events_prices_timezone_alignment.py --date 2025-08-01 --hhmm 14:30 --window-min 8
```

---

**Fin de TIMEZONE_NOTE**

