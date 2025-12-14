# Briefing - Déploiement Application EUR/USD Impact

**Contexte** : Suite de la session du 6 octobre 2025  
**Objectif** : Déployer l'application pour accès Mac + iPhone  
**Référence** : Lire d'abord `resume_final_oct6.md` pour contexte complet

---

## ÉTAT ACTUEL DU PROJET

### Application 100% Fonctionnelle
- **5 pages Streamlit** opérationnelles
- **Base de données** : 31,988 événements, 0 doublons, 85 MB
- **Analyseur Surprise** : Mode hybride testé et validé
  - Fallback automatique sur `previous` si forecast NULL
  - Saisie manuelle pour événements critiques
- **26 familles d'événements** avec sensibilités calibrées
- **Localisation** : `/Users/andrevalentin/Projects/eurusd_news_impact_calculator`

### Stack Technique
- **Framework** : Streamlit (Python)
- **Base de données** : DuckDB (warehouse.duckdb, 85 MB)
- **Dépendances** : pandas, duckdb, requests, python-dotenv
- **APIs** : EODHD (clé disponible dans .env)

---

## OBJECTIF NOUVEAU : DÉPLOIEMENT

### Besoin Utilisateur
Créer une version accessible facilement sur :
1. **Mac** (application ou web)
2. **iPhone** (application ou web)

Sans nécessiter :
- Terminal ou commandes techniques
- Installation Python/dépendances
- Lancement manuel `streamlit run`

### Contraintes
- Budget limité (privilégier solutions gratuites)
- Maintenance minimale
- Mise à jour simple
- Accès offline souhaitable mais pas critique

---

## OPTIONS DE DÉPLOIEMENT

### Option 1 : Streamlit Cloud (Web App)
**Recommandation principale** - Gratuit, rapide, universel

**Avantages** :
- Déploiement en 15-30 minutes
- Accès depuis n'importe quel navigateur (Mac Safari, iPhone)
- Aucune installation requise
- Mises à jour automatiques via Git
- URL personnalisée type `eurusd-impact.streamlit.app`
- Raccourci iPhone possible (icône écran d'accueil)

**Limitations** :
- Base DuckDB à héberger (85 MB) - possibilité cloud
- Pas d'accès offline
- Limites ressources plan gratuit (mais suffisant)
- Public ou privé (authentification basique)

**Étapes** :
1. Push projet sur GitHub (repo privé ou public)
2. Inscription Streamlit Cloud (gratuit)
3. Connexion repo GitHub
4. Configuration secrets (.env)
5. Deploy automatique

### Option 2 : Application Mac Native
**Complexe** - Nécessite rebuild complet UI

**Approches possibles** :
1. **PyInstaller** : Ne fonctionne pas bien avec Streamlit (serveur web intégré)
2. **Electron + Python** : Complexe, ~1-2 semaines dev
3. **Rebuild PyQt6/Tkinter** : Plusieurs jours travail, perte UX Streamlit

**Recommandation** : Éviter sauf besoin critique offline

### Option 3 : Application iPhone Native
**Très complexe** - Rebuild complet nécessaire

- Python non supporté nativement iOS
- Streamlit incompatible mobile natif
- Nécessite Swift/React Native (~1+ mois dev)
- Distribution TestFlight puis App Store

**Alternative simple** : PWA (Progressive Web App) depuis Streamlit Cloud
- Raccourci écran d'accueil iPhone
- S'ouvre en plein écran comme app native
- Pas de passage par App Store

---

## RECOMMANDATION IMMÉDIATE

**Déployer sur Streamlit Cloud** + PWA iPhone

### Avantages décisifs
- **Temps** : 30 minutes vs plusieurs semaines
- **Coût** : Gratuit vs potentiellement $99+/an (Apple Developer)
- **Maintenance** : Automatique via Git
- **Universel** : Fonctionne Mac, iPhone, iPad, PC, Android

### Workflow final utilisateur
1. **Mac** : Ouvrir `https://eurusd-impact.streamlit.app` dans Chrome/Safari
2. **iPhone** : 
   - Ouvrir URL dans Safari
   - Partager → "Sur l'écran d'accueil"
   - Icône apparaît comme app native
   - Ouvre en plein écran sans barre de navigation

---

## FICHIERS NÉCESSAIRES POUR DEPLOY

### À créer avant déploiement

**1. requirements.txt** (dépendances Python)
```
streamlit==1.28.0
duckdb==0.9.0
pandas==2.1.0
requests==2.31.0
python-dotenv==1.0.0
```

**2. .streamlit/config.toml** (configuration UI)
```toml
[theme]
primaryColor = "#0066CC"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
```

**3. .gitignore** (ne pas commit secrets)
```
.env
*.duckdb
__pycache__/
venv/
.DS_Store
```

**4. README.md** (documentation)
- Description projet
- Instructions utilisation
- Architecture

### Gestion Base de Données (85 MB)

**Problème** : GitHub limite à 100 MB, base fait 85 MB

**Solutions** :
1. **Git LFS** (Large File Storage) - Gratuit jusqu'à 1 GB
2. **Cloud séparé** : 
   - Upload base sur Google Drive/Dropbox
   - Script download au démarrage app
3. **Base cloud** : Migrer vers PostgreSQL/SQLite cloud

---

## SECRETS ET SÉCURITÉ

### Variables d'environnement (.env)
Ne jamais commit dans Git :
```
EODHD_API_KEY=68ac152b303f79.26633922
TE_API_KEY=44A37FA8426849F:4EFC3C6F76B1451
```

### Configuration Streamlit Cloud
Ajouter dans interface web :
- Settings → Secrets
- Copier contenu .env
- Variables disponibles via `st.secrets`

---

## PLAN D'ACTION SUGGÉRÉ

### Phase 1 : Préparation (15 min)
1. Créer `requirements.txt`
2. Créer `.streamlit/config.toml`
3. Mettre à jour `.gitignore`
4. Créer README.md basique

### Phase 2 : GitHub (10 min)
1. Créer repo GitHub (privé recommandé)
2. Push code (sans .env et warehouse.duckdb)
3. Configurer Git LFS pour .duckdb (ou solution cloud)

### Phase 3 : Streamlit Cloud (15 min)
1. Créer compte sur https://share.streamlit.io
2. Connecter repo GitHub
3. Configurer secrets (EODHD_API_KEY, TE_API_KEY)
4. Deploy automatique
5. Tester URL publique

### Phase 4 : Configuration iPhone (5 min)
1. Ouvrir URL dans Safari iPhone
2. Partager → "Sur l'écran d'accueil"
3. Renommer "EUR/USD Impact"
4. Ajouter icône personnalisée (optionnel)

**Total estimé** : 45 minutes

---

## QUESTIONS À RÉSOUDRE

1. **Base de données** : Git LFS, cloud externe, ou migration DB cloud ?
2. **Accès** : Public (avec authentification basique) ou privé (login requis) ?
3. **Domaine** : Garder `.streamlit.app` ou acheter domaine personnalisé ?
4. **Updates données** : Comment rafraîchir la base régulièrement ?

---

## ALTERNATIVES SI STREAMLIT CLOUD INSUFFISANT

### Si besoin accès offline strict
**Docker Desktop Mac** :
- Containeriser l'app complète
- Un seul fichier .dmg à distribuer
- Complexité moyenne, ~2-3 jours

### Si besoin app iPhone vraiment native
**React Native** + Backend API :
- Frontend : React Native (iOS + Android)
- Backend : FastAPI Python (API REST)
- Base hébergée cloud
- Temps : 3-4 semaines dev minimum

---

## FICHIERS DE RÉFÉRENCE

### Depuis session précédente
- `resume_final_oct6.md` - État complet projet
- `audit_results.json` - Diagnostic base de données
- `fx_impact_app/src/event_families.py` - 26 familles configurées
- `fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py` - Testé et validé

### Structure projet actuelle
```
eurusd_news_impact_calculator/
├── fx_impact_app/
│   ├── src/
│   │   ├── config.py
│   │   ├── forecaster_mvp.py
│   │   ├── scoring_engine.py
│   │   ├── event_families.py
│   │   └── eodhd_client.py
│   ├── scripts/
│   │   └── ingest_*.py
│   ├── streamlit_app/
│   │   └── pages/
│   │       ├── 0b_Impact-Planner.py
│   │       ├── 1_Calendrier-Trading.py
│   │       ├── 2_Backtest-Strategie.py
│   │       ├── 3_Analyseur-Surprise.py
│   │       └── 4_Planificateur-Multi-Evenements.py
│   └── data/
│       └── warehouse.duckdb (85 MB)
├── .env (secrets)
└── venv/
```

---

## POUR DÉMARRER LA NOUVELLE CONVERSATION

**Contexte à fournir** :
```
Bonjour, je souhaite déployer mon application Streamlit EUR/USD Impact 
pour qu'elle soit accessible facilement sur Mac et iPhone, sans nécessiter 
d'installation Python ou de commandes terminal.

L'application est 100% fonctionnelle en local :
- 5 pages Streamlit opérationnelles
- Base DuckDB de 85 MB (31,988 événements)
- Localisation : /Users/andrevalentin/Projects/eurusd_news_impact_calculator

J'ai préparé un briefing détaillé de déploiement. Ma préférence va vers 
Streamlit Cloud (gratuit, web app universelle) mais je suis ouvert à 
d'autres solutions si mieux adaptées.

Peux-tu me guider étape par étape pour :
1. Préparer les fichiers nécessaires (requirements.txt, config, etc.)
2. Gérer la base de 85 MB (Git LFS ou cloud)
3. Déployer sur Streamlit Cloud
4. Configurer l'accès iPhone (PWA)

[Coller ici le contenu du briefing ci-dessus si nécessaire]
```

---

**Préparé le** : 06 octobre 2025 - 04:45 UTC  
**État projet** : 100% fonctionnel, prêt pour déploiement  
**Prochaine étape** : Créer requirements.txt et préparer repo GitHub