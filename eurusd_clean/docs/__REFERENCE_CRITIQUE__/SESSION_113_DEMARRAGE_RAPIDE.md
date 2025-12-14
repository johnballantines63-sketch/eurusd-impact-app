# 🚀 SESSION 113 - DÉMARRAGE RAPIDE

**Lire d'abord:** `SESSION_112_RAPPORT_FINAL.md` (contexte complet)

---

## ⚡ COMMANDES DÉMARRAGE

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
source .venv/bin/activate
streamlit run streamlit_app/Home.py
```

---

## 🎯 TODO SESSION 113

### 🔴 1. FIX CALENDRIER TRADING (PRIORITÉ 1)

**Problème:** `tuple index out of range`

**Fichier:** `streamlit_app/pages/1_Calendrier_Trading.py`

**Diagnostic rapide:**
```bash
# Chercher lignes problématiques
grep -n "\.fetchone()\[0\]" streamlit_app/pages/1_Calendrier_Trading.py
grep -n "\.fetchall()\[0\]" streamlit_app/pages/1_Calendrier_Trading.py
```

**Solution pattern:**
```python
# AVANT (dangereux)
result = conn.execute("SELECT ...").fetchone()[0]

# APRÈS (safe)
result_tuple = conn.execute("SELECT ...").fetchone()
result = result_tuple[0] if result_tuple else None
```

**Test après fix:**
```bash
streamlit run streamlit_app/Home.py
# → Aller page Calendrier Trading
# → Vérifier liste événements futurs
```

---

### 🟡 2. RÉACTIVER EODHD (PRIORITÉ 2)

**Fichier:** `streamlit_app/pages/3_API_Status.py`

**Code à ajouter:**
```python
import requests

url = 'https://eodhd.com/api/economic-events'
params = {
    'from': str(d1),
    'to': str(d2),
    'api_token': os.getenv("EODHD_API_KEY"),
    'fmt': 'json',
    'countries': ','.join(countries) if countries else 'US'
}

r = requests.get(url, params=params, timeout=10)
if r.status_code == 200:
    items = r.json()
    st.success(f"✅ {len(items)} événements EODHD")
    
    # Afficher dans dataframe
    df = pd.DataFrame(items)
    st.dataframe(df)
```

**Référence:** `test_eodhd_api.py` (fonctionne)

---

### 🟢 3. TESTS FINAUX

**Script de test:**
```bash
python scripts/session112/TEST_FINAL_app_complete.py
```

**Tests manuels dans app:**
1. **Home** → Stats affichées correctement
2. **Calendrier** → Liste événements futurs
3. **Planificateur V2** → Calcul impact (11 sept 2025)
4. **API Status** → Clés détectées + EODHD fonctionne
5. **Mise à jour DB** → Boutons présents

---

## ⚠️ RAPPELS CRITIQUES

### Colonnes DB
```python
✅ event_title  (pas "event")
✅ importance_n (pas "importance_eod")
```

### Table prix
```python
✅ prices_bern  (pas "prices_1m")
# Vue avec timezone correcte
```

### Chemins
```python
✅ config.DB_PATH  (pas chemin hardcodé)
```

---

## 📊 STATUS ACTUEL

```
✅ Home.py                 100%
✅ Planificateur_V2.py    100%
✅ API_Status.py          90% (EODHD à réactiver)
✅ Mise_a_jour_DB.py      100%
⚠️ Calendrier_Trading.py  80% (tuple index à fixer)
```

---

## 🗄️ BASE DE DONNÉES

```
DB: eurusd_clean/data/warehouse.duckdb
Events: 58,449 (10,781 avec nom)
Prix: 1,114,260 bougies 1min
Vue prices_bern: ✅ Active
```

**Structure events:**
- `event_title` VARCHAR (nom événement)
- `importance_n` BIGINT (1-3)
- `ts_utc` TIMESTAMP WITH TIME ZONE
- `country`, `forecast`, `previous`, `actual`

---

## 🔧 OUTILS DIAGNOSTIC

```bash
# Vérifier structure DB
python scripts/session112/DIAGNOSTIC_db.py

# Test complet app
python scripts/session112/TEST_FINAL_app_complete.py

# Test API EODHD
export EODHD_API_KEY="68ac152b303f79.26633922"
python test_eodhd_api.py
```

---

## 📚 FICHIERS IMPORTANTS

**Configuration:**
- `src/config.py` - Chemins centralisés

**Modules core:**
- `src/core/impact_measurement.py` (v4.0)
- `src/core/formulas_validated.py`

**Documentation:**
- `docs/SOLUTION_DEFINITIVE_TIMEZONE.md`
- `docs/__REFERENCE_CRITIQUE__/SESSION_112_RAPPORT_FINAL.md`

**Scripts:**
- `scripts/session112/` - 40+ scripts migration/fixes

---

## 🎯 OBJECTIF SESSION 113

**Rendre app 100% fonctionnelle en 80 minutes**

```
30 min → Fix Calendrier
20 min → Réactiver EODHD  
20 min → Tests complets
10 min → Documentation
```

**Après Session 113 → PRÊT PRODUCTION** 🚀

---

**BONNE SESSION ! 🎯**
