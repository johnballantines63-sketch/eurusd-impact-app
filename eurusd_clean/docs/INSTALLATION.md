# 🎯 INSTALLATION EURUSD_CLEAN - Guide Rapide

**eurusd_clean/ doit être 100% autonome et isolé du projet legacy**

---

## ⚡ Installation Rapide (5 minutes)

### 1. Copier Base de Données

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC

# Option A : Script automatique (RECOMMANDÉ)
python3 eurusd_clean/scripts/migration/setup_clean.py

# Option B : Copie manuelle
cp fx_impact_app/data/warehouse.duckdb eurusd_clean/app/data/
```

### 2. Vérifier Installation

```bash
cd eurusd_clean
python3 app/config.py
```

**Sortie attendue :**
```
✅ Base de données:
   Taille: 205.0 MB
   Tables: 8
   Événements: 58,449
```

### 3. Lire Documentation

```bash
cat PROJECT_STATE.md        # État système (OBLIGATOIRE)
cat README.md               # Guide démarrage
cat MESSAGE_SESSION_29.md   # Prochaine session
```

---

## 🎯 Philosophie : Isolation Complète

### ✅ Ce qui est CORRECT

**eurusd_clean/ contient TOUT :**
- ✅ Code source (app/, ui/)
- ✅ Base de données (app/data/warehouse.duckdb)
- ✅ Scripts (scripts/)
- ✅ Tests (tests/)
- ✅ Documentation (docs/)

**Résultat :** Dossier autonome, prêt à déployer, aucune dépendance externe

### ❌ Ce qui serait INCORRECT

**Liens/références vers projet legacy :**
- ❌ Liens symboliques vers warehouse.duckdb
- ❌ Chemins relatifs vers ../fx_impact_app/
- ❌ Imports depuis projet legacy
- ❌ Dépendances croisées

**Problèmes :** Couplage, confusion, impossible à déployer seul

---

## 📁 Structure Après Installation

```
eurusd_clean/
├── app/
│   ├── data/
│   │   └── warehouse.duckdb     ✅ 205 MB (COPIÉ)
│   ├── core/                    🚧 À migrer
│   ├── services/                🚧 À créer
│   └── config.py                ✅ Pointe vers app/data/
│
├── ui/                          🚧 À créer
├── scripts/
│   └── migration/
│       └── setup_clean.py       ✅ Script installation
├── tests/                       🚧 À créer
└── docs/                        ✅ Structure créée
```

---

## 🧹 Nettoyage Futur

**Quand eurusd_clean/ sera 100% fonctionnel :**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC

# Supprimer projet legacy (libère ~500 MB)
rm -rf fx_impact_app/
rm -rf .venv/
rm -rf __pycache__/
rm -rf backups/
rm *.py  # Scripts racine
rm *.md  # Documentation legacy

# Garder uniquement eurusd_clean/
# Renommer si souhaité
mv eurusd_clean eurusd_impact_calculator
```

**Résultat :** Structure propre, un seul dossier, aucune confusion

---

## ✅ Checklist Installation

- [ ] warehouse.duckdb copié (205 MB)
- [ ] python3 app/config.py fonctionne
- [ ] Tables validées (8+)
- [ ] Événements validés (58,449)
- [ ] PROJECT_STATE.md lu
- [ ] Prêt pour Session 29

---

**Temps installation :** 5 minutes  
**Espace requis :** ~250 MB (code + DB)  
**Prêt pour développement !** 🚀
