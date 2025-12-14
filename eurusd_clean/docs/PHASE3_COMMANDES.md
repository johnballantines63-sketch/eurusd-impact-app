# 🚀 PHASE 3 - MIGRATION APP STREAMLIT - GUIDE COMPLET

**Migrer toutes les pages vers nouvelle structure eurusd_clean**

---

## 📋 VUE D'ENSEMBLE

**5 scripts à exécuter dans l'ordre :**

```
1. phase3_1_migrate_home.py           → Home.py (stats améliorées)
2. phase3_2_migrate_calendrier.py     → 1_Calendrier_Trading.py
3. phase3_3_migrate_planificateur.py  → 2_Planificateur_V2.py (validé)
4. phase3_4_migrate_api_status.py     → 3_API_Status.py
5. phase3_5_create_update_db.py       → 4_Mise_a_jour_DB.py (nouveau)
```

**Chaque script demande confirmation avant exécution !**

---

## 🎯 EXÉCUTION

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# 1. HOME PAGE (30s)
python scripts/session112/phase3_1_migrate_home.py
# → Taper 'oui'

# 2. CALENDRIER (20s)
python scripts/session112/phase3_2_migrate_calendrier.py
# → Taper 'oui'

# 3. PLANIFICATEUR V2 VALIDÉ (30s)
python scripts/session112/phase3_3_migrate_planificateur.py
# → Taper 'oui'

# 4. API STATUS (20s)
python scripts/session112/phase3_4_migrate_api_status.py
# → Taper 'oui'

# 5. MISE À JOUR DB (20s)
python scripts/session112/phase3_5_create_update_db.py
# → Taper 'oui'
```

**Total: ~2 minutes**

---

## 📁 STRUCTURE CRÉÉE

```
eurusd_clean/streamlit_app/
├── Home.py                         ✅ Stats améliorées
├── pages/
│   ├── 1_Calendrier_Trading.py    ✅ Filtre events
│   ├── 2_Planificateur_V2.py      ✅ Validé Session 72
│   ├── 3_API_Status.py            ✅ Tests DB
│   └── 4_Mise_a_jour_DB.py        ✅ Màj Events + Prix
```

---

## 🔧 MODIFICATIONS APPLIQUÉES

**Dans toutes les pages :**

1. **Imports adaptés**
```python
# Nouvelle structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from core import formulas_validated, impact_measurement
import config
```

2. **Chemins DB**
```python
# Plus de chemins hardcodés
DB_PATH = config.DB_PATH  # → eurusd_clean/data/warehouse.duckdb
```

3. **Table prix**
```python
# Partout remplacé
FROM prices_1m  →  FROM prices_bern  # Vue timezone correcte
```

---

## 🎨 HOME PAGE - NOUVELLES STATS

**Stats existantes (conservées) :**
- Total Événements
- Avec Forecast
- Cette Semaine
- Aujourd'hui

**Nouvelles stats (ajoutées) :**
- Dernière màj Events (jours depuis)
- Dernière màj Prix (jours depuis)
- Nombre prix disponibles
- Statut vue prices_bern (✅ Active)

---

## 📋 PAGE MISE À JOUR DB (NOUVEAU)

**Fonctionnalités :**
1. Bouton "Mettre à jour Events"
   - Lance `eodhd_client_FULL_IMPORT_20251019_135735.py`
   - Applique `fix_eodhd_estimate_session28.py`
   - Logs en temps réel

2. Bouton "Mettre à jour Prix"
   - Lance `dukascopy_eurusd_m1_3y.py`
   - Logs en temps réel
   - Vue prices_bern se met à jour auto

3. Statut DB actuel
   - Nombre events
   - Nombre prix
   - Âge dernière màj

---

## 🚀 TEST APRÈS MIGRATION

```bash
cd eurusd_clean

# Créer/activer venv (si pas déjà fait)
python3 -m venv .venv
source .venv/bin/activate

# Installer dépendances
pip install streamlit pandas plotly duckdb numpy requests

# Lancer app
streamlit run streamlit_app/Home.py
```

**Devrait ouvrir sur http://localhost:8501**

---

## ✅ VÉRIFICATIONS

**Dans le navigateur :**

1. **Home** : 
   - ✅ 8 métriques affichées
   - ✅ Pas d'erreurs
   - ✅ Stats cohérentes

2. **Calendrier Trading** :
   - ✅ Events chargés
   - ✅ Filtres fonctionnels

3. **Planificateur V2** :
   - ✅ Interface chargée
   - ✅ Calculs fonctionnels

4. **API Status** :
   - ✅ DB accessible
   - ✅ Tests passent

5. **Mise à jour DB** :
   - ✅ Boutons présents
   - ✅ Stats affichées

---

## 🔥 SI ERREUR "Module not found"

```bash
# Depuis eurusd_clean/
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
streamlit run streamlit_app/Home.py
```

---

## 📊 RÉSULTAT ATTENDU

```
✅ 5 pages migrées
✅ Structure propre
✅ Imports fonctionnels
✅ Vue prices_bern utilisée
✅ Config centralisé
✅ Nouvelle page Mise à jour DB
```

---

## 🎯 APRÈS SUCCÈS

**Phase 3 TERMINÉE !**

```
✅ Home avec stats améliorées
✅ 4 pages fonctionnelles
✅ App complète dans eurusd_clean/
✅ Prêt pour production
```

**Prochaine session : Archiver anciennes versions**

---

**LANCE LES 5 SCRIPTS !** 🚀🚀🚀
