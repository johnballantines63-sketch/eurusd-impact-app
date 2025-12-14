# 🔧 GUIDE DÉPANNAGE - ModuleNotFoundError

## 🚨 Problème

```
ModuleNotFoundError: No module named 'formulas_validated'
```

## 🔍 Cause

Le problème vient du **répertoire de lancement** de Streamlit.

### ❌ Mauvaise méthode (erreur)

```bash
cd fx_impact_app/streamlit_app
streamlit run pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

**Pourquoi ça ne marche pas :**
- Streamlit lance depuis `streamlit_app/`
- Le code fait : `Path(__file__).parent.parent.parent / "src"`
- Résultat : cherche dans `streamlit_app/../../src` (n'existe pas)

### ✅ Bonne méthode

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app
streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

**Pourquoi ça marche :**
- Streamlit lance depuis `fx_impact_app/`
- Le code fait : `Path(__file__).parent.parent.parent / "src"`
- Depuis `pages/` : `parent` = `streamlit_app/`, `parent.parent` = `fx_impact_app/`, `parent.parent.parent` = racine
- Mais en fait avec le bon lancement, le path relatif fonctionne
- Résultat : trouve `fx_impact_app/src/` ✅

---

## 🚀 SOLUTIONS

### Solution 1 : Script Automatique (RECOMMANDÉ)

```bash
# Rendre exécutable
chmod +x /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/launch_planificateur_correct.sh

# Lancer
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/launch_planificateur_correct.sh
```

---

### Solution 2 : Manuel

```bash
# 1. Aller dans fx_impact_app (pas streamlit_app !)
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app

# 2. Vérifier que src/ existe
ls src/formulas_validated.py
# Doit afficher : src/formulas_validated.py

# 3. Lancer Streamlit
streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

---

### Solution 3 : Diagnostic

Si ça ne marche toujours pas, lancer le diagnostic :

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app
python streamlit_app/pages/diagnostic_imports.py
```

Cela affichera :
- Path actuel
- Path vers src/
- Test des imports
- Localisation des modules

---

## 🔍 Vérification Structure

Votre structure doit être :

```
fx_impact_app/
├── src/
│   ├── __init__.py
│   ├── formulas_validated.py    ✅
│   ├── double_wave.py             ✅
│   ├── single_wave_strong.py      ✅
│   └── config.py
│
└── streamlit_app/
    └── pages/
        └── 5_Planificateur_V2_FORMULES_VALIDEES.py
```

**Commande vérification :**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app
ls -la src/*.py | grep -E "(formulas|double|single)"
```

Doit afficher :
```
src/formulas_validated.py
src/double_wave.py
src/single_wave_strong.py
```

---

## 💡 Explication Technique

### Code dans le Planificateur

```python
# Ligne 34-36
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))
```

### Analyse Path

```
__file__ = .../fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py

Path(__file__) 
= .../fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py

.parent 
= .../fx_impact_app/streamlit_app/pages/

.parent.parent 
= .../fx_impact_app/streamlit_app/

.parent.parent.parent 
= .../fx_impact_app/

.parent.parent.parent / "src"
= .../fx_impact_app/src/  ✅ CORRECT
```

**Le code est correct !** C'est juste le lancement qui doit être depuis `fx_impact_app/`.

---

## 🎯 Commande Finale

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app && streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

Ou utilisez le script :

```bash
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/launch_planificateur_correct.sh
```

---

## ✅ Test Réussi

Quand ça fonctionne, vous devriez voir :

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Et l'interface devrait afficher :
```
🎯 Planificateur V2 - Formules Validées
Version 2.4 - Méthode Session 55 + détection automatique type mouvement
```

---

## 🐛 Si Toujours Pas de Solution

Essayez d'ajouter le path de manière absolue :

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app
export PYTHONPATH="${PYTHONPATH}:/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src"
streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py
```

Ou créez un alias :

```bash
# Dans ~/.zshrc ou ~/.bashrc
alias plani='cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app && streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py'

# Puis simplement :
plani
```

---

**Résumé : Lancer depuis `fx_impact_app/`, pas `streamlit_app/` !** ✅
