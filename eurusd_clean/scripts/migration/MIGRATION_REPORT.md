# 📊 Rapport d'Analyse - Migration eurusd_clean

**Date :** 22 octobre 2025
**Session :** 29

---

## 📈 Résumé

- **Fichiers analysés :** 148
- **Fichiers avec erreurs :** 1
- **Modules trouvés :** 12
- **Modules ESSENTIELS :** 11 ✅
- **Modules OBSOLÈTES :** 1 ❌

---

## ✅ Modules ESSENTIELS (à migrer)

Ces modules sont activement utilisés et doivent être migrés vers `eurusd_clean/`.

### fx_impact_app.src.config

**Utilisé par :** 27 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/audit_suite.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/audit_v2.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/check_and_backfill-window.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/check_and_backfill_window.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/check_price_coverage.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/ingest_eodhd_calendar.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/ingest_prices_csv.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/ingest_prices_eodhd.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src/db_init.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src/forecaster_mvp.backup_20251005_153128.py`
- ... et 17 autres

</details>

---

### fx_impact_app.src.regex_presets

**Utilisé par :** 11 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.1_Simultaneous-Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.2_Simultaneous-Screener.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.4_Forecaster-with-Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.5_Baskets-with-Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.6_Calendar-Sim-Baskets-Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/8a_Forecaster_Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_backup_20250928-123635/10a-Calendar_Sim_Baskets_Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_backup_20250928-123635/7a-Simultaneous_Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_backup_20250928-123635/7b-Simultaneous_Screener.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_backup_20250928-123635/8a-Forecaster_with_Presets.py`
- ... et 1 autres

</details>

---

### fx_impact_app.src.forecaster_mvp

**Utilisé par :** 10 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/audit_suite.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/audit_v2.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.3_Forecaster-CLEAN.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.4_Forecaster-with-Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/8_Forecaster_MVP_OLD.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/8a_Forecaster_Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/9_Backtest.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_backup_20250928-123635/0-Live_Calendar_Forecast.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_backup_20250928-123635/8-Forecaster_CLEAN.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_backup_20250928-123635/8a-Forecaster_with_Presets.py`

</details>

---

### fx_impact_app.streamlit_app._ui

**Utilisé par :** 8 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.10_Lexique.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.11_Glossary.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.1_Simultaneous-Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.2_Simultaneous-Screener.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.3_Forecaster-CLEAN.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.4_Forecaster-with-Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.5_Baskets-with-Presets.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.6_Calendar-Sim-Baskets-Presets.py`

</details>

---

### fx_impact_app.src.presets

**Utilisé par :** 5 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/10_Calendar_Sim_Backtest.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/6_Top_events.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/7_Simultaneous_events.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/8_Forecaster_MVP_OLD.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/9_Backtest.py`

</details>

---

### fx_impact_app.src.eodhd_client

**Utilisé par :** 4 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/audit_v2.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/ingest_eodhd_calendar.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.0_Live-Calendar-Forecast.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/99_API_Status.py`

</details>

---

### fx_impact_app.src.db_tuning

**Utilisé par :** 3 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/scripts/audit_suite.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/.2_Simultaneous-Screener.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_backup_20250928-123635/7b-Simultaneous_Screener.py`

</details>

---

### fx_impact_app.src._shared

**Utilisé par :** 2 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/10_Calendar_Sim_Backtest.py`
- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/_archive/6_Top_events.py`

</details>

---

### src.config

**Utilisé par :** 1 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py`

</details>

---

### src.event_families

**Utilisé par :** 1 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py`

</details>

---

### src.forecaster_mvp

**Utilisé par :** 1 fichiers
**Dépendances :** 0 modules

<details>
<summary>Fichiers utilisant ce module</summary>

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py`

</details>

---

## 🔄 Ordre de Migration Recommandé

Basé sur l'analyse des dépendances (modules sans dépendances d'abord) :


---

## ❌ Modules OBSOLÈTES (à ignorer)

Ces modules ne sont pas ou peu utilisés. Ils peuvent être ignorés lors de la migration.

- `fx_impact_app.streamlit_app.ui` (utilisé par 1 fichier)

---

## ⚠️ Erreurs de Parsing

1 fichiers n'ont pas pu être analysés :

- `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/Backups/4_Planificateur-Multi-Evenements_1.py`
  - Erreur : expected an indented block after 'with' statement on line 1346 (4_Planificateur-Multi-Evenements_1.py, line 1346)

---

## 🎯 Recommandations

### Priorité 1 (Session 29)
1. Migrer les 2-3 premiers modules de l'ordre recommandé
2. Créer les tests unitaires correspondants
3. Valider la migration

### Priorité 2 (Sessions suivantes)
4. Continuer la migration dans l'ordre recommandé
5. Créer la couche services (`data_service.py`, `prediction_service.py`)
6. Refactoriser l'UI Streamlit

---

**Généré par :** `analyze_current_usage.py`
