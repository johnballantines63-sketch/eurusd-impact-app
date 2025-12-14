# ⚠️ RAPPEL CRITIQUE POUR CLAUDE

## 📁 OÙ CRÉER LES FICHIERS DE DOCUMENTATION

### ✅ CHEMIN CORRECT

```python
BASE_PATH = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/"

# Tous fichiers de session vont ici :
filesystem.write_file(
    path=BASE_PATH + "SESSION_XX_RAPPORT_FINAL.md",
    content=...
)
```

### ❌ CHEMIN INCORRECT

```python
# NE JAMAIS faire ça :
filesystem.write_file(
    path="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/SESSION_XX.md",
    content=...
)
```

---

## 📋 RÈGLE SIMPLE

**TOUS les fichiers suivants vont dans `eurusd_clean/docs/` :**

- ✅ `MESSAGE_SESSION_XX_XX.md`
- ✅ `SESSION_XX_RAPPORT_FINAL.md`
- ✅ `SESSION_XX_CHECKPOINT.md`
- ✅ `SESSION_XX_SUMMARY.md`
- ✅ Tout fichier de documentation session

**SEULE EXCEPTION :**
- `eurusd_clean/PROJECT_STATE.md` (peut rester à cette racine)

---

## 🎯 TEMPLATE À COPIER-COLLER

```python
# Définir le chemin de base au début de la session
DOCS_PATH = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/"

# Utiliser pour TOUS les fichiers
filesystem.write_file(
    path=DOCS_PATH + "VOTRE_FICHIER.md",
    content=votre_contenu
)
```

---

## ⚡ VÉRIFICATION RAPIDE

Avant de terminer une session, vérifier :

```bash
# Liste fichiers .md à la racine projet
ls /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/*.md

# Devrait montrer SEULEMENT des scripts Python, CSV, etc.
# PAS de fichiers SESSION_XX.md ou MESSAGE_XX.md
```

---

**📌 Respecter cette règle = Projet organisé = Succès à long terme**

---

*Rappel créé - Session 48*
