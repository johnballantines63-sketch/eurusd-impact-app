# ⚡ COMMANDES ESSENTIELLES SESSION 113

**Copier-coller rapide pour démarrer**

---

## 🚀 DÉMARRAGE APPLICATION

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
source .venv/bin/activate
export EODHD_API_KEY="68ac152b303f79.26633922"
streamlit run streamlit_app/Home.py
```

**→ Ouvre http://localhost:8501**

---

## 🧪 TESTS & DIAGNOSTIC

### Test complet application
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/session112/TEST_FINAL_app_complete.py
```

### Diagnostic base de données
```bash
python scripts/session112/DIAGNOSTIC_db.py
```

### Test API EODHD
```bash
export EODHD_API_KEY="68ac152b303f79.26633922"
python test_eodhd_api.py
```

---

## 🔍 DEBUG CALENDRIER

### Chercher lignes problématiques
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
grep -n "\.fetchone()\[0\]" streamlit_app/pages/1_Calendrier_Trading.py
grep -n "\.fetchall()\[0\]" streamlit_app/pages/1_Calendrier_Trading.py
```

### Ouvrir fichier pour édition
```bash
code streamlit_app/pages/1_Calendrier_Trading.py
# ou
nano streamlit_app/pages/1_Calendrier_Trading.py
```

---

## 📊 VÉRIFICATIONS DB

### Connexion DB et structure
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python3 << 'EOF'
import duckdb
import sys
sys.path.insert(0, 'src')
import config

conn = duckdb.connect(str(config.DB_PATH), read_only=True)

# Colonnes events
print("Colonnes events:")
cols = conn.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'events'
""").fetchall()
for col in cols:
    print(f"  • {col[0]}")

# Stats
stats = conn.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN event_title IS NOT NULL AND event_title != '' THEN 1 END) as with_name
    FROM events
""").fetchone()
print(f"\nTotal events: {stats[0]:,}")
print(f"Avec nom: {stats[1]:,}")

# Vue prices_bern
vue = conn.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0]
print(f"Prix (vue): {vue:,}")

conn.close()
EOF
```

---

## 🔧 CORRECTIONS RAPIDES

### Fix variable dans fichier Python
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# Exemple: Remplacer variable mal nommée
python3 << 'EOF'
from pathlib import Path
file = Path("streamlit_app/pages/1_Calendrier_Trading.py")
content = file.read_text()
content = content.replace('OLD_NAME', 'NEW_NAME')
file.write_text(content)
print("✅ Correction appliquée")
EOF
```

### Vérifier imports Python
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
try:
    import config
    print(f"✅ config: {config.DB_PATH}")
    from core import impact_measurement
    print("✅ impact_measurement")
    from core import formulas_validated
    print("✅ formulas_validated")
except Exception as e:
    print(f"❌ Erreur: {e}")
EOF
```

---

## 📚 DOCUMENTATION RAPIDE

### Lire fichiers critiques
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# Guide Session 113 (3 min)
cat docs/__REFERENCE_CRITIQUE__/SESSION_113_DEMARRAGE_RAPIDE.md

# Rapport Session 112 (10 min)
cat docs/__REFERENCE_CRITIQUE__/SESSION_112_RAPPORT_FINAL.md

# Index fichiers (5 min)
cat docs/__REFERENCE_CRITIQUE__/FICHIERS_CLES_SESSION_112.md
```

---

## 🗄️ BACKUP AVANT MODIFICATIONS

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# Backup DB
cp data/warehouse.duckdb data/warehouse_backup_$(date +%Y%m%d_%H%M%S).duckdb

# Backup app
tar -czf streamlit_app_backup_$(date +%Y%m%d_%H%M%S).tar.gz streamlit_app/

# Backup config
cp src/config.py src/config_backup_$(date +%Y%m%d_%H%M%S).py

echo "✅ Backups créés"
```

---

## 🚦 STATUS PAGES

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# Vérifier syntaxe Python
python3 -m py_compile streamlit_app/Home.py && echo "✅ Home OK"
python3 -m py_compile streamlit_app/pages/1_Calendrier_Trading.py && echo "✅ Calendrier OK"
python3 -m py_compile streamlit_app/pages/2_Planificateur_V2.py && echo "✅ Planificateur OK"
python3 -m py_compile streamlit_app/pages/3_API_Status.py && echo "✅ API Status OK"
python3 -m py_compile streamlit_app/pages/4_Mise_a_jour_DB.py && echo "✅ Mise à jour OK"
```

---

## 🎯 WORKFLOW SESSION 113

### 1. Démarrer (2 min)
```bash
cd eurusd_clean
source .venv/bin/activate
export EODHD_API_KEY="68ac152b303f79.26633922"

# Lire guides
cat docs/__REFERENCE_CRITIQUE__/SESSION_113_DEMARRAGE_RAPIDE.md
```

### 2. Diagnostic (5 min)
```bash
# Test app
python scripts/session112/TEST_FINAL_app_complete.py

# Diagnostic DB
python scripts/session112/DIAGNOSTIC_db.py

# Lancer app
streamlit run streamlit_app/Home.py
# → Tester chaque page
```

### 3. Fix Calendrier (30 min)
```bash
# Chercher problème
grep -n "\.fetchone()\[0\]" streamlit_app/pages/1_Calendrier_Trading.py

# Éditer
nano streamlit_app/pages/1_Calendrier_Trading.py

# Tester
streamlit run streamlit_app/Home.py
```

### 4. Réactiver EODHD (20 min)
```bash
# Éditer API Status
nano streamlit_app/pages/3_API_Status.py

# Référence fonctionnelle
cat test_eodhd_api.py

# Tester
streamlit run streamlit_app/Home.py
```

### 5. Tests finaux (20 min)
```bash
# Test complet
python scripts/session112/TEST_FINAL_app_complete.py

# Test manuel toutes pages
streamlit run streamlit_app/Home.py
```

---

## 🔑 VARIABLES ENVIRONNEMENT

```bash
# Clé API EODHD
export EODHD_API_KEY="68ac152b303f79.26633922"

# Vérifier
echo $EODHD_API_KEY

# Rendre permanent (optionnel)
echo 'export EODHD_API_KEY="68ac152b303f79.26633922"' >> ~/.zshrc
source ~/.zshrc
```

---

## 📊 QUICK CHECKS

### DB accessible ?
```bash
python3 -c "import sys; sys.path.insert(0, 'src'); import config; print(f'DB: {config.DB_PATH}'); print(f'Existe: {config.DB_PATH.exists()}')"
```

### Vue prices_bern active ?
```bash
python3 -c "import duckdb; import sys; sys.path.insert(0, 'src'); import config; conn = duckdb.connect(str(config.DB_PATH), read_only=True); print(f'Prix: {conn.execute(\"SELECT COUNT(*) FROM prices_bern\").fetchone()[0]:,}'); conn.close()"
```

### Imports OK ?
```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from core import impact_measurement, formulas_validated; print('✅ Imports OK')"
```

---

## 🎯 RÉSUMÉ COMMANDES SESSION 113

```bash
# DÉMARRAGE
cd eurusd_clean && source .venv/bin/activate
streamlit run streamlit_app/Home.py

# DIAGNOSTIC
python scripts/session112/TEST_FINAL_app_complete.py
python scripts/session112/DIAGNOSTIC_db.py

# DEBUG CALENDRIER
grep -n "\.fetchone()\[0\]" streamlit_app/pages/1_Calendrier_Trading.py
nano streamlit_app/pages/1_Calendrier_Trading.py

# TEST API
export EODHD_API_KEY="68ac152b303f79.26633922"
python test_eodhd_api.py
```

---

**PRÊT POUR SESSION 113 !** 🚀
