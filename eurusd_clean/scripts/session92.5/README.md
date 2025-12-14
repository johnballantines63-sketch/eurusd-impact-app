# 📊 SESSION 92.5 - EXPORT DUKASCOPY 11 SEPTEMBRE 2025

## 🎯 Objectif

Exporter les prix EUR/USD minute par minute du 11 septembre 2025 de 14h20 à 15h30 (Bern time) pour comparaison avec les données MT5 Swissquote.

---

## 🚀 EXÉCUTION RAPIDE

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session92.5
python3 export_dukascopy_11sept_1m.py
```

**Fichier généré:** `export_dukascopy_11sept_14h20-15h30.csv`

---

## 📋 Détails Export

**Paramètres:**
- **Date:** 11 septembre 2025
- **Heure début:** 14h20 Bern (12:20:00+02:00)
- **Heure fin:** 15h30 Bern (13:30:00+02:00)
- **Durée:** 70 minutes (71 lignes avec début et fin inclus)

**Format CSV:**
```csv
datetime,open,high,low,close
2025-09-11 12:20:00+02:00,1.16850,1.16855,1.16840,1.16845
2025-09-11 12:21:00+02:00,1.16845,1.16850,1.16840,1.16848
...
2025-09-11 13:30:00+02:00,1.17350,1.17360,1.17340,1.17355
```

**Source:** Table `prices_1m` dans `warehouse.duckdb` (Provider: Dukascopy)

---

## 📊 Informations Affichées

Le script affiche:
- ✅ Validation connexion DB
- ✅ Nombre de lignes retournées
- ✅ Vérification valeurs NULL
- ✅ **Peak absolue** (timestamp, prix, impact pips)
- ✅ Preview 5 premières lignes (14h20-14h24)
- ✅ Preview 5 lignes autour CPI (14h28-14h32)
- ✅ Preview 5 lignes autour peak
- ✅ Preview 5 dernières lignes (15h26-15h30)
- ✅ Statistiques comparaison Session 92.4

---

## 🎯 Prochaine Étape

**André:**
1. Exécuter le script
2. Ouvrir le CSV dans Excel
3. Comparer point par point avec MT5 Swissquote
4. Identifier si la divergence est normale (< 5 pips) ou problématique (> 10 pips)

**Valeurs référence:**
- DB Dukascopy 60 min: **51.7 pips**
- MT5 Swissquote: **56.2 pips**
- Divergence actuelle: **4.5 pips (8%)**

---

## 📁 Fichiers

```
session92.5/
├── README.md                                    (Ce fichier)
├── export_dukascopy_11sept_1m.py               (Script export)
└── export_dukascopy_11sept_14h20-15h30.csv     (Sera généré)
```

---

_Session 92.5 - Export données Dukascopy pour validation divergence sources_
