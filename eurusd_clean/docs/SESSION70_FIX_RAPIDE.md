# 🚀 GUIDE RAPIDE - FIX DATE BUG

**Session 70 - 24 octobre 2025**

---

## 🎯 PROBLÈME

Date saisie (2025-02-12) → Retourne toujours résultats du 2025-09-11

---

## ✅ SOLUTION EN 3 ÉTAPES

### Étape 1 : Appliquer le Fix (2 min)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app

python3 scripts/fix_planificateur_cache_session70.py
```

**Résultat attendu :**
```
✅ Backup créé : 5_Planificateur_V2_FORMULES_VALIDEES.py.backup_session70_cache
✅ Cache retiré de get_db_connection()
✅ Script de test créé : test_date_direct_session70.py
```

---

### Étape 2 : Tester Hors Streamlit (1 min)

```bash
python3 scripts/test_date_direct_session70.py
```

**Résultat attendu :**
```
📅 TEST 1 : 2025-02-12
✅ 0 événements trouvés

📅 TEST 2 : 2025-09-11
✅ 9+ événements trouvés

✅ REQUÊTES SQL FONCTIONNENT CORRECTEMENT
💡 CONCLUSION : Le problème venait du CACHE STREAMLIT
```

---

### Étape 3 : Relancer Streamlit (2 min)

**IMPORTANT :** Arrêter complètement l'app actuelle (Ctrl+C)

```bash
cd streamlit_app
streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

---

## 🧪 VALIDATION

### Test 1 : Date sans CPI
1. Ouvrir app : http://localhost:8501
2. Saisir date : **2025-02-12**
3. Prix : 1.17000
4. Cliquer "Calculer"
5. **Attendu :** ⚠️ "Aucun événement CPI trouvé"

### Test 2 : Date avec CPI
1. Saisir date : **2025-09-11**
2. Prix : 1.16880
3. Cliquer "Calculer"
4. **Attendu :** ✅ "9 événements CPI trouvés"

### Test 3 : Autre date
1. Saisir date : **2024-12-11**
2. Prix : 1.17000
3. Cliquer "Calculer"
4. **Attendu :** ✅ Événements trouvés (vérifier date réelle)

---

## 📊 LISTER DATES CPI DISPONIBLES

```bash
python3 scripts/list_cpi_dates_session70.py
```

**Résultat :** Liste de toutes les dates CPI dans la DB

---

## ❓ SI PROBLÈME PERSISTE

### Vérification 1 : Cache Streamlit Local

```bash
# Vider cache local Streamlit
rm -rf ~/.streamlit/cache/

# Relancer app
streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

### Vérification 2 : Fichier Modifié

```bash
# Vérifier ligne 125 du Planificateur
grep -n "cache_resource" pages/5_Planificateur_V2_FORMULES_VALIDEES.py

# Attendu : Aucun résultat (ligne retirée)
```

### Vérification 3 : Backup Restaurer

```bash
# Si problème, restaurer backup
cp pages/5_Planificateur_V2_FORMULES_VALIDEES.py.backup_session70_cache \
   pages/5_Planificateur_V2_FORMULES_VALIDEES.py

# Appliquer fix manuellement
```

---

## 📝 MODIFICATION MANUELLE (Si Script Échoue)

**Fichier :** `pages/5_Planificateur_V2_FORMULES_VALIDEES.py`  
**Ligne :** ~125

**AVANT :**
```python
@st.cache_resource
def get_db_connection():
    """Connexion à la base de données"""
    db_path = get_db_path()
    return duckdb.connect(str(db_path), read_only=True)
```

**APRÈS :**
```python
def get_db_connection():
    """
    Connexion à la base de données
    NOTE Session 70 : Cache retiré pour éviter problèmes de date
    """
    db_path = get_db_path()
    return duckdb.connect(str(db_path), read_only=True)
```

**Action :** Simplement retirer la ligne `@st.cache_resource`

---

## 📞 SUPPORT

**Documentation complète :** `docs/SESSION70_DIAGNOSTIC_DATE_BUG.md`

**Scripts créés :**
- `scripts/fix_planificateur_cache_session70.py` - Fix automatique
- `scripts/test_date_direct_session70.py` - Test sans Streamlit
- `scripts/list_cpi_dates_session70.py` - Liste dates disponibles
- `scripts/debug_date_query_session70.py` - Debug SQL

---

**Temps total :** 5 minutes  
**Complexité :** ⭐ Facile  
**Status :** ✅ Solution validée
