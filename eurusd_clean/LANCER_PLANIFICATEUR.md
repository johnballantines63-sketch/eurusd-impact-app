# 🚀 GUIDE DE LANCEMENT - PLANIFICATEUR V3.0

**Date :** 16 novembre 2025  
**Shell :** zsh (macOS)  
**Python :** 3.13

---

## ✅ VÉRIFICATIONS PRÉALABLES

### **1. Vérifier que Python3 est installé**

```bash
python3 --version
```

**Résultat attendu :** `Python 3.13.x` (ou version similaire)

---

### **2. Vérifier que Streamlit est installé**

```bash
streamlit --version
```

**Résultat attendu :** `Streamlit, version 1.28.0` (ou supérieur)

**Si Streamlit n'est pas installé :**

```bash
pip3 install streamlit
```

---

### **3. Vérifier que vous êtes dans le bon répertoire**

```bash
pwd
```

**Résultat attendu :** `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean`

**Si vous n'y êtes pas :**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
```

---

## 🎯 COMMANDES DE LANCEMENT

### **MÉTHODE 1 : Lancement Direct (Recommandé)**

**Dans zsh (terminal macOS) :**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean && streamlit run streamlit_app/Home.py
```

**OU si vous êtes déjà dans le répertoire :**

```bash
streamlit run streamlit_app/Home.py
```

---

### **MÉTHODE 2 : Avec Python explicite**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean && python3 -m streamlit run streamlit_app/Home.py
```

---

### **MÉTHODE 3 : Avec port personnalisé**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean && streamlit run streamlit_app/Home.py --server.port 8501
```

---

## 📋 RÉPONSES AUX QUESTIONS

### **Q1 : Doit-on utiliser zsh ?**

**Réponse :** Oui, sur macOS, zsh est le shell par défaut. Les commandes fonctionnent dans zsh.

**Alternative :** Si vous préférez bash, les commandes sont identiques.

---

### **Q2 : Doit-on activer un venv (environnement virtuel) ?**

**Réponse :** **NON**, d'après la vérification :
- Python3 est installé globalement : `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`
- Streamlit est installé globalement : `/Library/Frameworks/Python.framework/Versions/3.13/bin/streamlit`
- **Aucun venv n'est présent dans le projet**

**Vous pouvez lancer directement sans activer de venv.**

---

### **Q3 : Quelle est la commande bash exacte ?**

**Commande complète (copier-coller) :**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean && streamlit run streamlit_app/Home.py
```

**OU en deux étapes :**

```bash
# Étape 1 : Aller dans le répertoire
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

# Étape 2 : Lancer Streamlit
streamlit run streamlit_app/Home.py
```

---

## 🌐 ACCÈS À L'APPLICATION

Après avoir lancé la commande, vous verrez :

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

**Cliquez sur le lien ou ouvrez manuellement :** `http://localhost:8501`

---

## 📱 NAVIGATION DANS L'APPLICATION

1. **Page d'accueil** : Statistiques générales
2. **Sidebar** : Menu avec pages disponibles
3. **Planificateur V3** : Cliquer sur **"3_Planificateur_V3"** dans la sidebar

---

## 🛑 ARRÊTER L'APPLICATION

Dans le terminal où Streamlit tourne :
- Appuyer sur **`Ctrl + C`** (ou **`Cmd + C`** sur Mac)

---

## 🔧 EN CAS DE PROBLÈME

### **Erreur : "streamlit: command not found"**

```bash
# Installer Streamlit
pip3 install streamlit

# OU avec python3 -m
python3 -m pip install streamlit
```

---

### **Erreur : "ModuleNotFoundError"**

```bash
# Installer les dépendances
pip3 install -r requirements.txt
```

---

### **Erreur : "Base de données introuvable"**

```bash
# Vérifier que la DB existe
ls -lh data/warehouse.duckdb

# OU
ls -lh warehouse.duckdb
```

---

### **Port déjà utilisé**

```bash
# Utiliser un autre port
streamlit run streamlit_app/Home.py --server.port 8502
```

---

## ✅ CHECKLIST RAPIDE

- [ ] Terminal ouvert (zsh ou bash)
- [ ] Dans le bon répertoire (`eurusd_clean`)
- [ ] Python3 installé (`python3 --version`)
- [ ] Streamlit installé (`streamlit --version`)
- [ ] Commande lancée : `streamlit run streamlit_app/Home.py`
- [ ] Navigateur ouvert sur `http://localhost:8501`
- [ ] Page "3_Planificateur_V3" accessible dans la sidebar

---

## 🎯 COMMANDE FINALE (COPIER-COLLER)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean && streamlit run streamlit_app/Home.py
```

**C'est tout ! Pas besoin de venv, pas besoin de configuration supplémentaire.** 🚀

---

**Bonne utilisation !**

