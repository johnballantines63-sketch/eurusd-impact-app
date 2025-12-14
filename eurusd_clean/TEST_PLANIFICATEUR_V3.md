# 🧪 GUIDE DE TEST - PLANIFICATEUR V3.0

**Date :** 16 novembre 2025  
**Version :** 3.0 avec améliorations (Calendrier + Checkbox + DOUBLE_WAVE Ensemble)

---

## 🚀 COMMANDES DE LANCEMENT

### **1. Lancer l'application Streamlit**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
streamlit run streamlit_app/Home.py
```

**OU** si vous êtes déjà dans le répertoire :

```bash
streamlit run streamlit_app/Home.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse :
- **URL locale :** `http://localhost:8501`

---

## 📋 CHECKLIST DE TEST

### **✅ TEST 1 : Sélection Date depuis Calendrier**

1. **Accéder au Planificateur V3**
   - Dans la sidebar, cliquer sur **"3_Planificateur_V3"**

2. **Tester le mode "Depuis calendrier"**
   - Sélectionner **"📅 Depuis calendrier"** dans les options
   - Vérifier que la liste des dates avec événements HIGH s'affiche
   - Sélectionner une date dans la liste
   - Vérifier que la date est bien formatée (ex: "11/09/2025 (Thursday)")

3. **Tester le mode "Saisie manuelle"**
   - Sélectionner **"📝 Saisie manuelle"**
   - Tester différents formats :
     - `2025-09-11`
     - `11.09.2025`
     - `11/09/2025`
   - Vérifier que tous les formats sont acceptés

---

### **✅ TEST 2 : Affichage Événements avec Checkbox**

1. **Après avoir sélectionné une date et cliqué sur "🚀 Calculer Prédictions V3.0"**
   - Vérifier que la section **"📋 Événements du Cluster"** s'affiche
   - Vérifier que chaque événement a :
     - ✅ Checkbox (coché par défaut)
     - ✅ Titre événement
     - ✅ Pays (ex: US)
     - ✅ Heure (format HH:MM)
     - ✅ Score empirique

2. **Tester les checkboxes**
   - Décocher un événement
   - Vérifier qu'il disparaît de la liste sélectionnée
   - Re-cocher l'événement
   - Vérifier qu'il réapparaît

3. **Tester la saisie Actual**
   - Pour un événement sélectionné, modifier la valeur "Actual"
   - Vérifier que la valeur est bien prise en compte
   - Vérifier que "Estimate" est en lecture seule

---

### **✅ TEST 3 : Prédiction avec Événements Sélectionnés**

1. **Sélectionner plusieurs événements**
   - Cocher 3-5 événements
   - Cliquer sur "🚀 Calculer Prédictions V3.0"
   - Vérifier que seuls les événements sélectionnés sont utilisés

2. **Tester avec un seul événement**
   - Décocher tous sauf un
   - Vérifier que la prédiction fonctionne avec un seul événement

3. **Tester avec aucun événement**
   - Décocher tous les événements
   - Vérifier qu'un message d'erreur s'affiche : "⚠️ Aucun événement sélectionné"

---

### **✅ TEST 4 : Support DOUBLE_WAVE avec Ensemble Methods**

1. **Trouver une date avec pattern DOUBLE_WAVE**
   - Utiliser une date connue avec plusieurs événements (ex: 11 septembre 2025)
   - Vérifier que le pattern détecté est "DOUBLE_WAVE"

2. **Vérifier l'utilisation d'Ensemble Methods**
   - Dans les résultats, vérifier que la méthode est "ensemble"
   - Vérifier que les détails Ensemble s'affichent :
     - Poids optimaux
     - Prédictions individuelles
     - Nombre de cas historiques

3. **Vérifier le fallback**
   - Si Ensemble Methods échoue, vérifier que le fallback vers `doublewave_overlap` fonctionne

---

### **✅ TEST 5 : Amélioration Chargement Événements**

1. **Tester avec différentes dates**
   - Dates avec beaucoup d'événements HIGH
   - Dates avec peu d'événements HIGH (devrait charger aussi empirical_score > 40)

2. **Vérifier le matching d'event_keys**
   - Utiliser le test comparatif pour vérifier que les event_keys sont bien matchés
   - Vérifier que les variantes (_mom, _yoy) sont bien gérées

---

## 🐛 TESTS DE RÉGRESSION

### **Vérifier que les fonctionnalités existantes fonctionnent toujours :**

1. ✅ Détection pattern (SINGLE_WAVE_FORT, SINGLE_WAVE_STANDARD, DOUBLE_WAVE)
2. ✅ Prédiction Single Wave avec Ensemble Methods
3. ✅ Affichage résultats (impact, amplification, R²)
4. ✅ Export CSV

---

## 📊 RÉSULTATS ATTENDUS

### **Scénario 1 : Date avec événements HIGH**
- ✅ Événements chargés et affichés avec checkbox
- ✅ Prédiction calculée avec événements sélectionnés
- ✅ Résultats affichés correctement

### **Scénario 2 : Date avec peu d'événements HIGH**
- ✅ Événements avec empirical_score > 40 également chargés
- ✅ Prédiction fonctionne même avec moins d'événements

### **Scénario 3 : Pattern DOUBLE_WAVE**
- ✅ Ensemble Methods utilisé si disponible
- ✅ Fallback vers doublewave_overlap si nécessaire
- ✅ Détails Ensemble affichés

---

## 🔍 COMMANDES DE DEBUG

### **Vérifier les imports**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python -c "from src.core.event_utils import normalize_event_key_with_variants; print('✅ Import OK')"
```

### **Vérifier la base de données**

```bash
python -c "from src.core import config; import duckdb; conn = duckdb.connect(str(config.config.DB_PATH), read_only=True); print('✅ DB OK')"
```

### **Tester le chargement d'événements**

```python
from datetime import datetime
from pathlib import Path
from src.core import config
from streamlit_app.pages.3_Planificateur_V3 import load_events_for_date

date = datetime(2025, 9, 11)
df = load_events_for_date(date, config.DB_PATH, "Europe/Zurich")
print(f"✅ {len(df)} événements chargés")
```

---

## 📝 NOTES IMPORTANTES

1. **Premier lancement** : Streamlit peut prendre quelques secondes pour charger
2. **Base de données** : Vérifier que `warehouse.duckdb` existe et est accessible
3. **Erreurs** : Si erreur d'import, vérifier que tous les modules sont dans le PYTHONPATH

---

## 🆘 EN CAS DE PROBLÈME

### **Erreur : ModuleNotFoundError**
```bash
# Vérifier que vous êtes dans le bon répertoire
pwd
# Devrait afficher : /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
```

### **Erreur : Base de données introuvable**
```bash
# Vérifier que la DB existe
ls -lh data/warehouse.duckdb
# OU
ls -lh warehouse.duckdb
```

### **Erreur : Streamlit non trouvé**
```bash
# Installer Streamlit si nécessaire
pip install streamlit
```

---

**Bonne chance pour les tests ! 🚀**

