# 📋 RÈGLES D'ORGANISATION DES FICHIERS

**Créé :** Session 31 - 22 octobre 2025  
**Objectif :** Éviter la désorganisation qui a causé problèmes Sessions 1-27

---

## 🚨 RÈGLE ABSOLUE

**SEULS les fichiers de documentation PERMANENTS peuvent être à la racine de `eurusd_clean/`**

**TOUS les fichiers de session/rapport DOIVENT être dans `docs/`**

---

## ✅ FICHIERS AUTORISÉS À LA RACINE

```
eurusd_clean/
├── PROJECT_STATE.md          ⭐ Fichier maître (source unique vérité)
├── README.md                 📖 Guide démarrage rapide
├── STRUCTURE.md              🏗️  Documentation architecture
├── INSTALLATION.md           🚀 Guide installation
├── CHANGELOG.md              📋 Historique versions
├── requirements.txt          📦 Dépendances Python
├── .gitignore                🔒 Git ignore
└── .DS_Store                 ⚠️  Fichier système (ignorer)
```

**TOTAL : 6-7 fichiers permanents maximum**

---

## ❌ FICHIERS INTERDITS À LA RACINE

**Ces fichiers DOIVENT être dans `docs/` :**

```
❌ MESSAGE_SESSION_XX.md      → docs/MESSAGE_SESSION_XX.md
❌ SESSION_XX_SUMMARY.md       → docs/SESSION_XX_SUMMARY.md
❌ FIN_SESSION_XX.md           → docs/FIN_SESSION_XX.md
❌ SESSION_XX_HANDOFF.md       → docs/SESSION_XX_HANDOFF.md
❌ SESSION_XX_OVERVIEW.txt     → docs/SESSION_XX_OVERVIEW.txt
❌ SESSION_XX_TLDR.md          → docs/SESSION_XX_TLDR.md
❌ INDEX_SESSION_XX.md         → docs/INDEX_SESSION_XX.md
❌ SESSION_XX_FINAL.md         → docs/SESSION_XX_FINAL.md
❌ Tout fichier temporaire de session
```

---

## 📁 ORGANISATION DOCS/

```
docs/
├── MESSAGE_SESSION_XX.md     📬 Instructions démarrage session
├── SESSION_XX_SUMMARY.md     📊 Résumé complet session
├── FIN_SESSION_XX.md         🏁 Fin de session
│
├── DATABASE_SCHEMAS.md       🗄️  Schémas DB
│
├── api/                      📚 Documentation API
├── archives/                 📦 Archives anciennes sessions
└── guides/                   📖 Guides utilisateur
```

---

## 🔄 WORKFLOW CRÉATION FICHIERS

### Pendant une Session

**1. Créer MESSAGE_SESSION_XX.md**
```bash
# ✅ CORRECT
docs/MESSAGE_SESSION_XX.md

# ❌ INCORRECT
MESSAGE_SESSION_XX.md
```

**2. Créer SESSION_XX_SUMMARY.md**
```bash
# ✅ CORRECT
docs/SESSION_XX_SUMMARY.md

# ❌ INCORRECT
SESSION_XX_SUMMARY.md
```

**3. Mettre à jour PROJECT_STATE.md**
```bash
# ✅ CORRECT - C'est le SEUL fichier de session à la racine
PROJECT_STATE.md
```

### Fin de Session

**Vérifier qu'AUCUN fichier de session n'est à la racine :**

```bash
cd eurusd_clean
ls *.md

# Devrait afficher SEULEMENT :
# PROJECT_STATE.md
# README.md
# STRUCTURE.md
# INSTALLATION.md
# CHANGELOG.md
```

**Si d'autres fichiers .md apparaissent, les déplacer vers `docs/` :**

```bash
mv MESSAGE_SESSION_XX.md docs/
mv SESSION_XX_SUMMARY.md docs/
```

---

## 🎯 JUSTIFICATION

### Pourquoi cette règle ?

**Problème Sessions 1-27 :**
- 400+ fichiers Python à la racine
- Documentation fragmentée (10+ endroits)
- Impossible de trouver information
- Perte continuité entre sessions
- Dette technique accumulée

**Solution :**
- Racine CLEAN (6-7 fichiers permanents)
- Documentation session dans `docs/`
- PROJECT_STATE.md = source unique vérité
- Organisation claire et maintenable

### Bénéfices

✅ **Lisibilité :** Racine propre, facile à comprendre  
✅ **Maintenabilité :** Fichiers organisés logiquement  
✅ **Continuité :** Documentation centralisée dans docs/  
✅ **Professionnalisme :** Structure standard de projet  

---

## 📝 CHECKLIST AVANT COMMIT

Avant de terminer une session, vérifier :

- [ ] Tous fichiers MESSAGE_SESSION_XX.md dans docs/
- [ ] Tous fichiers SESSION_XX_SUMMARY.md dans docs/
- [ ] Tous fichiers FIN_SESSION_XX.md dans docs/
- [ ] PROJECT_STATE.md mis à jour à la racine
- [ ] Racine contient SEULEMENT 6-7 fichiers permanents
- [ ] Aucun fichier temporaire à la racine

---

## 🚨 ERREUR CORRIGÉE SESSION 31

**Problème détecté :**
```
eurusd_clean/
├── MESSAGE_SESSION_29.md     ❌ À la racine
├── MESSAGE_SESSION_30.md     ❌ À la racine
├── MESSAGE_SESSION_31.md     ❌ À la racine
└── FIN_SESSION_28.md         ❌ À la racine
```

**Correction appliquée :**
```bash
mv MESSAGE_SESSION_29.md docs/
mv MESSAGE_SESSION_30.md docs/
mv MESSAGE_SESSION_31.md docs/
mv FIN_SESSION_28.md docs/
```

**Résultat :**
```
eurusd_clean/
├── PROJECT_STATE.md          ✅ Racine
├── README.md                 ✅ Racine
├── STRUCTURE.md              ✅ Racine
├── INSTALLATION.md           ✅ Racine
├── CHANGELOG.md              ✅ Racine
└── requirements.txt          ✅ Racine

docs/
├── MESSAGE_SESSION_29.md     ✅ docs/
├── MESSAGE_SESSION_30.md     ✅ docs/
├── MESSAGE_SESSION_31.md     ✅ docs/
├── MESSAGE_SESSION_32.md     ✅ docs/
└── FIN_SESSION_28.md         ✅ docs/
```

---

## 💡 RAPPEL POUR FUTURES SESSIONS

**Chaque fois que Claude crée un fichier, se demander :**

1. ❓ Est-ce un fichier de session/rapport ?
   - **OUI** → `docs/SESSION_XX_XXXXX.md`

2. ❓ Est-ce un fichier de documentation permanente ?
   - **OUI** → Vérifier s'il fait partie des 6-7 autorisés à la racine
   - **NON** → `docs/` ou sous-dossier approprié

3. ❓ Est-ce du code ?
   - **OUI** → `app/`, `tests/`, `scripts/`, ou `ui/`

**En cas de doute : mettre dans `docs/` !**

---

**📌 Cette règle est CRITIQUE pour maintenir la qualité du projet et éviter de répéter les erreurs des 27 premières sessions.**

**🎯 Respecter cette organisation = Succès à long terme**
