# 📋 Résumé Session Calendrier Trading
**Date** : 10 octobre 2025  
**Fichier** : `fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py`  
**Status** : ✅ Restauré depuis Git, fonctionnel

---

## 🎯 Objectif Principal

Ajouter un **système de double classification** pour les événements économiques :
1. **Classification Calendrier** (a priori) - actuelle
2. **Classification Empirique** (historique) - à ajouter

---

## 📊 Structure de la Base de Données

### Table `events`
```sql
Colonnes utilisées :
- ts_utc (TIMESTAMP) → event_datetime
- country (VARCHAR) → currency  
- event_title (VARCHAR) → event_name
- event_key (VARCHAR)
- importance_n (BIGINT) → impact_calendar
- actual, estimate, previous, forecast (DOUBLE)
```

### Table `event_families`
```sql
Colonnes utilisées :
- event_key (VARCHAR) - jointure
- empirical_score (0-100)
- empirical_impact ('HIGH', 'MEDIUM', 'LOW')
- impact_level (VARCHAR) - théorique
```

### Mapping Importance

**IMPORTANT** : Le mapping est **inversé** par rapport à l'intuition !

```python
# importance_n → impact_calendar
{
    1: 'High',    # ← Priorité maximale
    2: 'Medium',
    3: 'Low'
}
```

### Codes Pays

**Dans la DB** :
- `'EU'` = Union Européenne
- `'US'` = États-Unis  
- `'EA'` = Eurozone

**PAS** `'EUR'` ni `'USD'` !

---

## ✅ Ce qui Fonctionne Actuellement

### Fonctionnalités Opérationnelles

1. **Cache intelligent** (< 20ms après 1er chargement)
2. **Requête SQL optimisée** avec LEFT JOIN sur event_families
3. **Graphiques** :
   - Timeline interactive (Plotly)
   - Distribution Impact par devise
   - Heatmap horaire
4. **Alertes** : Événements High Impact à venir (48h)
5. **Filtres avancés** :
   - Devise (EU/US/EA)
   - Impact (High/Medium/Low)
   - Avec estimate
   - Surprise minimale (%)
6. **3 modes d'affichage** :
   - Groupé par date
   - Liste complète
   - Tableau

### Code Existant Fonctionnel

```python
# Fonction de chargement AVEC scores empiriques
@st.cache_data(ttl=3600, show_spinner=False)
def load_all_events_cached(start_date: str, end_date: str) -> pd.DataFrame:
    query = f"""
    SELECT 
        e.ts_utc as event_datetime,
        e.country as currency,
        e.event_title as event_name,
        e.event_key,
        e.importance_n,
        e.actual, e.estimate, e.previous, e.forecast,
        ef.empirical_score,
        ef.empirical_impact,
        ef.impact_level as theoretical_impact
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key
    WHERE ts_utc::DATE >= '{start_date}'::DATE
      AND ts_utc::DATE <= '{end_date}'::DATE
      AND e.country IN ('EU', 'US', 'EA')  # ← Codes corrects !
      AND e.importance_n IS NOT NULL
    ORDER BY ts_utc ASC
    """
    # ...
    # Mapping importance
    df['impact_calendar'] = df['importance_n'].map({1:'High', 2:'Medium', 3:'Low'})
    df['impact_empirical'] = df['empirical_impact'].fillna('Unknown')
```

---

## 🚀 Améliorations à Apporter

### 1. Toggle Classification (PRIORITAIRE)

**Emplacement** : Sidebar, en haut

```python
# À ajouter dans with st.sidebar: après st.header("⚙️ Configuration")
st.subheader("📊 Classification")
classification_mode = st.radio(
    "Source d'importance",
    ["📅 Calendrier (a priori)", "📊 Empirique (historique)"],
    index=0,
    help=(
        "📅 **Calendrier** : Importance théorique selon économistes\n\n"
        "📊 **Empirique** : Impact réel observé sur EUR/USD"
    )
)

st.divider()
```

**Puis dans le code principal** (après chargement des données) :

```python
use_empirical = classification_mode == "📊 Empirique (historique)"

if use_empirical:
    df_all['impact'] = df_all['impact_empirical']
else:
    df_all['impact'] = df_all['impact_calendar']
```

### 2. Mode Date Unique / Période

**Emplacement** : Sidebar, après classification

```python
st.sidebar.subheader("📅 Période")
mode_date = st.sidebar.radio(
    "Mode de sélection",
    ["Date unique", "Période"],
    index=0
)

if mode_date == "Date unique":
    selected_date = st.sidebar.date_input("Date", datetime.now().date())
    date_from = datetime.combine(selected_date, datetime.min.time())
    date_to = datetime.combine(selected_date, datetime.max.time())
else:
    # Presets + 2 dates (code existant à déplacer)
    period_preset = st.sidebar.selectbox(...)
    # ...
```

### 3. Adaptations Statistiques

**Métriques à adapter selon le mode** :

```python
# High Impact
if use_empirical:
    high_impact = len(df_all[df_all['impact'] == 'HIGH'])  # Majuscules !
    st.caption(f"⚪ {unknown_count} Unknown")
else:
    high_impact = len(df_all[df_all['impact'] == 'High'])  # Normale !

# Filtres
if use_empirical:
    impact_options = ['HIGH', 'MEDIUM', 'LOW', 'Unknown']
else:
    impact_options = ['High', 'Medium', 'Low']
```

### 4. Affichage Score Empirique

**Dans display_event_card()** :

```python
# Ajouter score si disponible ET en mode empirique
if use_empirical and pd.notna(event.get('empirical_score')):
    score = event['empirical_score']
    event_display += f" (Score: {score:.0f})"
```

---

## ⚠️ Pièges à Éviter

### 1. Codes Pays
```python
# ❌ FAUX
country IN ('EUR', 'USD')

# ✅ CORRECT
country IN ('EU', 'US', 'EA')
```

### 2. Mapping Impact
```python
# ❌ FAUX (intuition)
{3: 'High', 2: 'Medium', 1: 'Low'}

# ✅ CORRECT
{1: 'High', 2: 'Medium', 3: 'Low'}
```

### 3. Format Impact
```python
# Calendrier : 'High', 'Medium', 'Low' (capitalize)
# Empirique : 'HIGH', 'MEDIUM', 'LOW' (uppercase)
# Toujours adapter les comparaisons !
```

### 4. Variable classification_mode
```python
# ❌ Utiliser AVANT définition
use_empirical = classification_mode == "..."  # Ligne 700
# ... mais classification_mode défini après !

# ✅ Ordre correct :
# 1. Sidebar (définir classification_mode)
# 2. Chargement données
# 3. Utiliser classification_mode
```

---

## 🔧 Stratégie pour Demain

### Option 1 : Script Shell Chirurgical (RECOMMANDÉ)

Créer un script qui :
1. Trouve la ligne `st.header("⚙️ Configuration")`
2. Insère le toggle juste après
3. Trouve la ligne où utiliser `classification_mode`
4. Insère la logique de switch

**Avantages** :
- ✅ Modifications minimales
- ✅ Pas de risque de casser le reste
- ✅ Backup automatique

### Option 2 : Réécrire la fonction main()

Recréer toute la fonction avec :
- Sidebar complète en premier
- Tout le reste après

**Avantages** :
- ✅ Structure propre
- ✅ Plus maintenable

**Inconvénients** :
- ⚠️ Plus long
- ⚠️ Risque de bugs

---

## 📁 Fichiers Importants

```
fx_impact_app/
├── data/
│   └── warehouse.duckdb          # Base de données
├── streamlit_app/
│   └── pages/
│       ├── 1_Calendrier-Trading.py    # ← Fichier à modifier
│       └── 4_Planificateur-Multi-Evenements.py  # Référence
└── src/
    ├── config.py
    └── ...
```

---

## 🎯 Checklist Pour Demain

### Préparation
- [ ] Ouvrir nouvelle session Claude
- [ ] Copier ce résumé
- [ ] Vérifier Git : `git status`
- [ ] Confirmer que le calendrier fonctionne : `streamlit run streamlit_app/Home.py`

### Développement
- [ ] Créer script d'ajout du toggle
- [ ] Tester en local
- [ ] Vérifier les deux modes (Calendrier / Empirique)
- [ ] Tester avec différentes périodes
- [ ] Vérifier les statistiques s'adaptent

### Validation
- [ ] Toggle visible dans sidebar ✓
- [ ] Bascule entre modes fonctionne ✓
- [ ] Statistiques correctes (High/Medium/Low) ✓
- [ ] Graphiques s'adaptent ✓
- [ ] Alertes fonctionnent ✓
- [ ] Export CSV OK ✓

---

## 💡 Pour Démarrer Demain

**Message d'ouverture suggéré** :

```
Bonjour ! Je continue l'optimisation du Calendrier Trading.

CONTEXTE :
- Fichier : fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py
- Status : Restauré depuis Git, fonctionnel
- Objectif : Ajouter toggle Classification (Calendrier/Empirique)

INFOS DB CRITIQUES :
- Pays : 'EU', 'US', 'EA' (pas EUR/USD !)
- Mapping : {1:'High', 2:'Medium', 3:'Low'} (inversé !)
- Scores empiriques : 'HIGH'/'MEDIUM'/'LOW' (uppercase)

J'ai un résumé complet en artifact avec toutes les infos.
Quelle approche recommandes-tu : script chirurgical ou réécriture ?
```

---

## 📊 Résultats Attendus

### Avant (Actuel)
- 1 seule classification (Calendrier)
- 10 oct 2025 : 7 événements "High Impact"

### Après (Objectif)
- 2 classifications au choix
- **Mode Calendrier** : 7 événements High (importance_n=1)
- **Mode Empirique** : 2 événements MEDIUM (score 55-63), autres Unknown

### Bénéfice Utilisateur
- Vision **théorique** (calendrier économique)
- Vision **pratique** (impact trading réel)
- Meilleure prise de décision

---

## 🔗 Références

- Résumé session v8.4 : `session_summary_oct9_v84_final.md`
- Planificateur (référence) : `pages/4_Planificateur-Multi-Evenements.py` (lignes 553-564)
- Documentation DuckDB : https://duckdb.org/docs/

---

**Tokens utilisés aujourd'hui** : 130k / 190k (68%)  
**Tokens restants pour demain** : ~60k - suffisant ! ✅

**Prêt pour une session productive demain ! 🚀**
