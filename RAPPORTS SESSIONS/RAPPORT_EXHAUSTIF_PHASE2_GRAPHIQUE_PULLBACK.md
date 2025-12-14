# RAPPORT EXHAUSTIF - PHASE 2 : INTÉGRATION GRAPHIQUE PULLBACK
## Session du 14 octobre 2025 - Version 8.6.2

**Date :** 14 octobre 2025  
**Durée :** ~2h  
**Tokens utilisés :** ~100,000 / 190,000 (52%)  
**Status :** ✅ Code créé, ⏳ Test final requis  

---

## 📋 TABLE DES MATIÈRES

1. [Contexte et Objectifs](#contexte)
2. [Architecture Découverte](#architecture)
3. [Modifications Appliquées](#modifications)
4. [Fonctions Créées](#fonctions)
5. [Modification Restante](#modification-restante)
6. [Instructions de Test](#test)
7. [Résolution de Problèmes](#troubleshooting)
8. [Annexes Techniques](#annexes)

---

## 1. CONTEXTE ET OBJECTIFS {#contexte}

### 1.1 Situation initiale

**Phase 1 (COMPLÉTÉE)** - Rapport : `RAPPORT_INTERMEDIAIRE_14OCT2025_PULLBACK_CALCUL.md`
- ✅ Module `sequence_multi_event_timeline_v86.py` v8.6.2 opérationnel
- ✅ Calcul pullback : 82.8 pips (11 sept 2025)
- ✅ Affichage texte : "🔄 Pullback détecté : -82.8 pips"
- ❌ **PROBLÈME :** Graphique ne montre pas le pullback visuellement

### 1.2 Objectif Phase 2

Intégrer le pullback **visuellement** dans le graphique avec :
- Zone ORANGE pour le pullback entre phases rapprochées
- Courbe générée depuis les phases (pas vectorielle)
- Stats détaillées (durée, amplitude)

### 1.3 Résultat attendu

```
Prix EUR/USD
    ^
    │ 
    │     ╱╲  Phase 1 (+207 pips vert)
    │    ╱  ╲
    │   ╱    ╲___  ← PULLBACK (-82.8 pips ORANGE)
    │  ╱         ╲
    │ ╱           ╲__ Phase 2 (+16.4 pips vert)
    └──────────────────────────→ Temps
   14:30  14:35   14:45   15:00
```

---

## 2. ARCHITECTURE DÉCOUVERTE {#architecture}

### 2.1 Structure des fichiers

```
eurusd_news_impact_calculator_MPC/
├── fx_impact_app/
│   ├── src/
│   │   ├── sequence_multi_event_timeline_v86.py      # v8.6.2 (Phase 1)
│   │   └── price_curve_generator.py                  # ✅ MODIFIÉ
│   └── streamlit_app/
│       ├── components/
│       │   └── streamlit_sequential_ui.py            # ✅ MODIFIÉ
│       └── pages/
│           └── 4_Planificateur-Multi-Evenements.py   # ⏳ À MODIFIER
├── RAPPORT_INTERMEDIAIRE_14OCT2025_PULLBACK_CALCUL.md  # Phase 1
├── test_pullback_graph.py                              # ✅ CRÉÉ
├── apply_pullback_graph_patch.py                       # ✅ CRÉÉ
└── MODIFICATION_GRAPHIQUE_PULLBACK.py                  # ✅ CRÉÉ
```

### 2.2 Flux de données découvert

**ANCIEN (avant Phase 2) :**
```
sequence_multi_event_timeline_v86.py (calcule phases)
    ↓
Planificateur affiche phases en mode texte
    ↓
Graphique généré par generate_candlestick_curve_multi_events()
    ↓ (vectoriel, pas de phases)
❌ Pullback calculé mais PAS affiché graphiquement
```

**NOUVEAU (après Phase 2) :**
```
sequence_multi_event_timeline_v86.py (calcule phases avec pullback_pips)
    ↓
generate_candlestick_curve_from_phases() lit les phases
    ↓ détecte zones pullback
    ↓ génère descente progressive
create_sequential_phases_chart() affiche avec couleurs
    ↓ ORANGE pour pullback
✅ Pullback visuellement intégré
```

### 2.3 Découverte clé : Graphique actuel dans le planificateur

**Localisation exacte :**
- Fichier : `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`
- Autour ligne ~700-850 (variable selon version)
- Bloc identifié par :
  ```python
  if st.button("🎨 Générer Graphique de Prédiction", type="primary", ...):
  ```

**Code actuel identifié :**
```python
# Utilise generate_candlestick_curve_multi_events()
# Génère graphique vectoriel SANS phases
# ❌ Ne lit pas les métadonnées pullback_pips
```

---

## 3. MODIFICATIONS APPLIQUÉES {#modifications}

### 3.1 Fichier : `price_curve_generator.py`

**Chemin :** `fx_impact_app/src/price_curve_generator.py`

**Modifications :**

#### a) Nouvelle fonction `generate_candlestick_curve_from_phases()`

**Position :** Insérée avant `calculate_fibonacci_price_levels()` (ligne ~220)

**Signature :**
```python
def generate_candlestick_curve_from_phases(
    start_price: float,
    phases: List[Dict],
    base_time: datetime,
    duration_minutes: int = 120,
    volatility_factor: float = 0.3,
    spread_pips: float = 0.0
) -> pd.DataFrame
```

**Paramètres phases attendus :**
```python
phases = [
    {
        'phase_num': 1,
        'start_time': datetime,           # ou str ISO
        'peak_time': datetime,             # Temps du pic
        'cumulative_price': 1.17196,       # Prix au pic
        'impact_combined': 207.0,          # Impact vectoriel (avec direction)
        'pullback_pips': 0.0,              # Pullback depuis phase précédente
        'minutes_since_prev_phase': 0,
        'latency_minutes': 1.0,
        'ttr_predicted': 41.0,
        'duration_minutes': 41.0,
        'direction': 'UP',
        'events': [{'family': '...', ...}]
    },
    {
        'phase_num': 2,
        'start_time': datetime,
        'peak_time': datetime,
        'cumulative_price': 1.17142,
        'impact_combined': 16.4,
        'pullback_pips': 82.8,             # ← PULLBACK DÉTECTÉ
        'minutes_since_prev_phase': 15.0,
        ...
    }
]
```

**Logique implémentée :**
```python
Pour chaque minute :
    Si dans zone pullback (entre pic N-1 et début N) :
        Descente progressive linéaire
        Prix = pic_precedent - (pullback_pips × progress)
        Phase marquée "pullback"
    
    Sinon si dans phase :
        Si latence : prix stable
        Si mouvement : montée sigmoid
        Si retracement : descente Fibonacci 38.2%
```

**Colonnes DataFrame retourné :**
- `time` : datetime
- `open`, `high`, `low`, `close` : float (prix OHLC)
- `bid`, `ask` : float (avec spread)
- `phase` : str ("pre_event", "latence", "mouvement", "pullback", "retracement", "post_event")
- `phase_num` : int
- `minute_offset` : int

---

#### b) Nouvelle fonction `create_sequential_phases_chart()`

**Position :** Insérée après `generate_candlestick_curve_from_phases()` (ligne ~420)

**Signature :**
```python
def create_sequential_phases_chart(
    price_df: pd.DataFrame,
    phases: List[Dict],
    start_price: float,
    title: str = "📊 Timeline Séquentielle Multi-Événements avec Pullback"
) -> go.Figure
```

**Paramètre price_df :** DataFrame retourné par `generate_candlestick_curve_from_phases()`

**Couleurs implémentées :**
```python
phase_colors = {
    'pre_event': {'increasing': 'lightgray', 'decreasing': 'darkgray'},
    'latence': {'increasing': 'lightyellow', 'decreasing': 'khaki'},
    'mouvement': {'increasing': 'green', 'decreasing': 'red'},
    'pullback': {'increasing': 'orange', 'decreasing': 'darkorange'},  # ← CLEF
    'retracement': {'increasing': 'lightcoral', 'decreasing': 'indianred'},
    'post_event': {'increasing': 'lightgray', 'decreasing': 'darkgray'}
}
```

**Légende graphique :**
- 🟢 Vert : Phases de mouvement haussier
- 🔴 Rouge : Phases de mouvement baissier
- 🟠 **Orange : Zone de pullback** ← NOUVEAU
- 🟡 Jaune pâle : Latence
- 🔴 Rouge pâle : Retracement

**Annotations :**
- Ligne horizontale : Prix de départ (bleu)
- Lignes verticales : Début de chaque phase
- Labels : Phase N avec pullback/impact

---

#### c) Fonction helper `plt_to_rgb()`

**Position :** Juste après `create_sequential_phases_chart()`

**Signature :**
```python
def plt_to_rgb(color_name: str) -> Tuple[float, float, float]
```

**Mapping couleurs :**
```python
{
    'green': (0, 1, 0),
    'red': (1, 0, 0),
    'orange': (1, 0.647, 0),
    'darkorange': (1, 0.549, 0),
    'lightgray': (0.827, 0.827, 0.827),
    'darkgray': (0.663, 0.663, 0.663),
    'lightyellow': (1, 1, 0.878),
    'khaki': (0.941, 0.902, 0.549),
    'lightcoral': (0.941, 0.502, 0.502),
    'indianred': (0.804, 0.361, 0.361)
}
```

---

### 3.2 Fichier : `streamlit_sequential_ui.py`

**Chemin :** `fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py`

**Modifications :**

#### a) Imports ajoutés (lignes 13-23)

**Code inséré :**
```python
# Import du générateur de courbe avec pullback
try:
    from price_curve_generator import (
        generate_candlestick_curve_from_phases,
        create_sequential_phases_chart
    )
    PRICE_CURVE_AVAILABLE = True
except ImportError:
    PRICE_CURVE_AVAILABLE = False
    print("⚠️ Import price_curve_generator échoué - graphique prix non disponible")
```

---

#### b) Nouvelle fonction `display_price_chart_with_pullback()`

**Position :** Insérée avant `display_timeline_gantt_chart()` (ligne ~335)

**Signature :**
```python
def display_price_chart_with_pullback(
    phases: List[Dict[str, Any]],
    start_price: float = 1.17000,
    duration_minutes: int = 120
)
```

**Logique :**
1. Vérifie `PRICE_CURVE_AVAILABLE`
2. Parse timestamps des phases
3. Appelle `generate_candlestick_curve_from_phases()`
4. Appelle `create_sequential_phases_chart()`
5. Affiche graphique Plotly
6. Calcule et affiche statistiques pullback :
   - Durée pullback (minutes)
   - Amplitude pullback (pips)
   - Impact total (pips)

**Métriques affichées :**
```python
col1: "🔄 Durée Pullback" (minutes)
col2: "📉 Amplitude Pullback" (pips, avec delta négatif)
col3: "📈 Impact Total" (pic max en pips)
```

---

#### c) Modification `display_sequential_timeline()`

**Position :** Fin de la fonction (après graphique Gantt, ligne ~174)

**Code ajouté :**
```python
# ✨ NOUVEAU : Graphique de prix avec pullback
st.markdown("---")
if st.checkbox("📈 Afficher évolution des prix avec pullback", value=True, key="show_price_chart"):
    # Déterminer prix de départ et durée
    start_price = 1.17000  # Valeur par défaut
    
    # Calculer durée totale
    first_time = pd.to_datetime(phases[0]['start_time'])
    last_time = pd.to_datetime(phases[-1]['start_time']) + pd.Timedelta(minutes=phases[-1]['duration_minutes'])
    duration_minutes = int((last_time - first_time).total_seconds() / 60) + 30  # +30 min buffer
    
    display_price_chart_with_pullback(
        phases=phases,
        start_price=start_price,
        duration_minutes=duration_minutes
    )
```

**Effet :**
- Checkbox cochée par défaut
- Affiche automatiquement le graphique avec pullback
- Calcul automatique de la durée

---

### 3.3 Fichier : `4_Planificateur-Multi-Evenements.py`

**Chemin :** `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`

**Modification appliquée :**

#### Imports ajoutés (ligne ~40-48)

**Code inséré :**
```python
from price_curve_generator import (
    generate_candlestick_curve_multi_events,
    calculate_fibonacci_price_levels,
    create_candlestick_prediction_chart,
    # ✨ NOUVEAU v8.6.2 : Fonctions avec pullback
    generate_candlestick_curve_from_phases,
    create_sequential_phases_chart
)
```

**Status :** ✅ Appliqué

---

## 4. FONCTIONS CRÉÉES - RÉFÉRENCE RAPIDE {#fonctions}

### 4.1 Signatures complètes

```python
# === GÉNÉRATEUR DE COURBE ===
def generate_candlestick_curve_from_phases(
    start_price: float,              # Prix de départ (ex: 1.17000)
    phases: List[Dict],              # Phases de sequence_multi_event_timeline
    base_time: datetime,             # Timestamp début timeline
    duration_minutes: int = 120,     # Durée totale simulation
    volatility_factor: float = 0.3,  # Volatilité (0.1=calme, 1.0=fort)
    spread_pips: float = 0.0         # Spread bid/ask en pips
) -> pd.DataFrame                    # Colonnes: time, ohlc, bid, ask, phase, phase_num

# === VISUALISATION ===
def create_sequential_phases_chart(
    price_df: pd.DataFrame,          # DataFrame de generate_candlestick_curve_from_phases
    phases: List[Dict],              # Phases (pour annotations)
    start_price: float,              # Prix de départ
    title: str = "..."               # Titre du graphique
) -> go.Figure                       # Figure Plotly interactive

# === UI STREAMLIT ===
def display_price_chart_with_pullback(
    phases: List[Dict[str, Any]],    # Phases
    start_price: float = 1.17000,    # Prix départ
    duration_minutes: int = 120      # Durée
) -> None                            # Affiche dans Streamlit

# === HELPER ===
def plt_to_rgb(color_name: str) -> Tuple[float, float, float]
```

---

### 4.2 Exemple d'utilisation

```python
# Dans un contexte où 'phases' est disponible
import pandas as pd
from datetime import datetime
from price_curve_generator import (
    generate_candlestick_curve_from_phases,
    create_sequential_phases_chart
)

# Phases calculées par sequence_multi_event_timeline_v86
phases = [...]  # Voir structure section 3.1

# Générer courbe
price_df = generate_candlestick_curve_from_phases(
    start_price=1.17000,
    phases=phases,
    base_time=datetime(2025, 9, 11, 14, 30),
    duration_minutes=60
)

# Créer graphique
fig = create_sequential_phases_chart(
    price_df=price_df,
    phases=phases,
    start_price=1.17000
)

# Afficher (Streamlit)
import streamlit as st
st.plotly_chart(fig, use_container_width=True)

# Vérifier pullback
pullback_rows = price_df[price_df['phase'] == 'pullback']
if len(pullback_rows) > 0:
    print(f"✅ Pullback détecté : {len(pullback_rows)} minutes")
    print(f"   Amplitude : {(pullback_rows.iloc[0]['close'] - pullback_rows.iloc[-1]['close']) * 10000:.1f} pips")
```

---

## 5. MODIFICATION RESTANTE {#modification-restante}

### 5.1 Localisation exacte

**Fichier :** `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`

**Chercher le bloc :** (autour ligne 700-850, variable)
```python
if st.button("🎨 Générer Graphique de Prédiction", type="primary", use_container_width=True, key="minute_chart_generate_155755_6050"):
```

**Dans ce bloc, chercher :** (autour ligne 750-850)
```python
# ✅ Générer la courbe avec la bonne signature de fonction
# La fonction attend une liste de predictions, pas total_impact_pips
price_df = generate_candlestick_curve_multi_events(
```

---

### 5.2 Code à remplacer

**ANCIEN CODE :**
```python
# ✅ Générer la courbe avec la bonne signature de fonction
# La fonction attend une liste de predictions, pas total_impact_pips
price_df = generate_candlestick_curve_multi_events(
    start_price=start_price_input,
    predictions=events_for_generator,
    base_time=min(pred["event_time"] for pred in events_for_generator),
    duration_minutes=duration_minutes,
    volatility_factor=volatility_factor,
    spread_pips=spread_pips
)

if price_df is not None and len(price_df) > 0:
    # ✅ Calculer mouvement dominant depuis les données générées (UNIQUE calcul)
    max_movement = (price_df['high'].max() - start_price_input) * 10000
    min_movement = (price_df['low'].min() - start_price_input) * 10000
    observed_movement = max_movement if abs(max_movement) > abs(min_movement) else min_movement

    # Calculer Fibonacci si demandé
    fib_levels = None
    if show_fibonacci:
        fib_levels = calculate_fibonacci_price_levels(
            start_price=start_price_input,
            impact_pips=abs(observed_movement),
            direction=1 if observed_movement > 0 else -1
        )
    
    # Créer graphique avec le mouvement observé
    fig = create_candlestick_prediction_chart(
        price_df=price_df,
        total_impact_pips=abs(observed_movement),
        direction=1 if observed_movement > 0 else -1,
        event_markers=[],
        start_price=start_price_input,
        fib_levels=fib_levels,
        show_spread=show_bid_ask
    )
    
    # Afficher
    st.plotly_chart(fig, use_container_width=True, key="minute_prediction_chart_155755_6050")
```

---

**NOUVEAU CODE :**
```python
# ✅ NOUVEAU v8.6.2 : Générer courbe AVEC PULLBACK VISUEL
# Vérifier si phases disponibles pour nouveau générateur
if 'phases' in locals() and phases and len(phases) > 0:
    # 🆕 UTILISER LE NOUVEAU GÉNÉRATEUR AVEC PHASES
    st.info("✨ Utilisation du nouveau générateur avec pullback visuel")
    
    price_df = generate_candlestick_curve_from_phases(
        start_price=start_price_input,
        phases=phases,
        base_time=min(pd.to_datetime(p['start_time']) for p in phases),
        duration_minutes=duration_minutes,
        volatility_factor=volatility_factor,
        spread_pips=spread_pips
    )
    
    if price_df is not None and len(price_df) > 0:
        # Créer graphique avec zones de pullback colorées
        fig = create_sequential_phases_chart(
            price_df=price_df,
            phases=phases,
            start_price=start_price_input,
            title="📊 Évolution Prédite EUR/USD avec Pullback"
        )
        
        # Afficher
        st.plotly_chart(fig, use_container_width=True, key="minute_prediction_chart_155755_6050")
        
        # Stats supplémentaires sur pullback
        pullback_rows = price_df[price_df['phase'] == 'pullback']
        if len(pullback_rows) > 0:
            st.success(f"🔄 Pullback détecté : {len(pullback_rows)} minutes de descente entre phases")

else:
    # FALLBACK : Ancien système si pas de phases
    st.warning("⚠️ Phases non disponibles, utilisation ancien système vectoriel")
    
    price_df = generate_candlestick_curve_multi_events(
        start_price=start_price_input,
        predictions=events_for_generator,
        base_time=min(pred["event_time"] for pred in events_for_generator),
        duration_minutes=duration_minutes,
        volatility_factor=volatility_factor,
        spread_pips=spread_pips
    )
    
    if price_df is not None and len(price_df) > 0:
        # Calculs pour ancien système
        max_movement = (price_df['high'].max() - start_price_input) * 10000
        min_movement = (price_df['low'].min() - start_price_input) * 10000
        observed_movement = max_movement if abs(max_movement) > abs(min_movement) else min_movement

        fib_levels = None
        if show_fibonacci:
            fib_levels = calculate_fibonacci_price_levels(
                start_price=start_price_input,
                impact_pips=abs(observed_movement),
                direction=1 if observed_movement > 0 else -1
            )
        
        fig = create_candlestick_prediction_chart(
            price_df=price_df,
            total_impact_pips=abs(observed_movement),
            direction=1 if observed_movement > 0 else -1,
            event_markers=[],
            start_price=start_price_input,
            fib_levels=fib_levels,
            show_spread=show_bid_ask
        )
        
        st.plotly_chart(fig, use_container_width=True, key="minute_prediction_chart_155755_6050")
```

---

### 5.3 Méthodes d'application

#### Option A - Script automatique

**Fichier :** `apply_pullback_graph_patch.py`

**Commande :**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
python3 apply_pullback_graph_patch.py
```

**Comportement :**
- Recherche le pattern exact à remplacer
- Crée backup : `4_Planificateur-Multi-Evenements.py.backup_before_pullback_graph`
- Applique le remplacement
- Affiche status

**Limitations :**
- Le pattern doit matcher EXACTEMENT (sensible espaces/retours ligne)
- Si code modifié depuis, peut échouer

---

#### Option B - Modification manuelle

**Fichier guide :** `MODIFICATION_GRAPHIQUE_PULLBACK.py`

**Étapes :**
1. Ouvrir `4_Planificateur-Multi-Evenements.py`
2. Chercher `if st.button("🎨 Générer Graphique de Prédiction"`
3. Dans ce bloc, chercher `price_df = generate_candlestick_curve_multi_events(`
4. Remplacer tout le bloc (voir section 5.2)
5. Sauvegarder

---

## 6. INSTRUCTIONS DE TEST {#test}

### 6.1 Script de validation

**Fichier :** `test_pullback_graph.py`

**Commande :**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
python3 test_pullback_graph.py
```

**Tests effectués :**
1. Import `price_curve_generator` (3 fonctions)
2. Import `streamlit_sequential_ui` (2 fonctions)
3. Import `sequence_multi_event_timeline_v86` (2 fonctions)
4. Vérification signatures
5. Simulation données phases
6. Génération courbe avec pullback
7. Calcul pullback (validation 82.8 pips)

**Résultat attendu :**
```
======================================================================
TEST INTÉGRATION GRAPHIQUE PULLBACK - VERSION 8.6.2
======================================================================

📦 Test 1 : Import price_curve_generator...
   ✅ Import réussi : generate_candlestick_curve_from_phases
   ✅ Import réussi : create_sequential_phases_chart
   ✅ Import réussi : plt_to_rgb

...

✅ TOUS LES TESTS PASSÉS !
======================================================================
```

---

### 6.2 Test Streamlit complet

**Commande :**
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
streamlit run fx_impact_app/streamlit_app/Home.py
```

**Procédure :**

1. **Navigation :**
   - Page : "📅 Planificateur Multi-Événements"

2. **Paramètres :**
   - Date : 11 septembre 2025
   - Événements : Sélectionner tous les événements de 14:30 et 14:45
   - ☑️ Cocher "Mode séquentiel" (si option disponible)

3. **Génération graphique :**
   - Cliquer "🎨 Générer Graphique de Prédiction"
   - Attendre génération (~2-5 secondes)

4. **Vérifications visuelles :**

   **a) Message informatif :**
   ```
   ✨ Utilisation du nouveau générateur avec pullback visuel
   ```

   **b) Graphique :**
   - ✅ Phase 1 (14:30) en **VERT** montant jusqu'à ~14:35
   - ✅ Zone **ORANGE** descendante entre 14:35 et 14:45
   - ✅ Phase 2 (14:45) en **VERT** depuis prix après pullback
   - ✅ Légende avec "🔄 Pullback (descente)"

   **c) Stats pullback :**
   ```
   🔄 Pullback détecté : 10 minutes de descente entre phases
   ```

   **d) Lignes verticales :**
   - Phase 1 : label "📍 Phase 1\nImpact: +207.0 pips"
   - Phase 2 : label "🔄 Phase 2\nPullback: -82.8 pips\nImpact: +16.4 pips"

---

### 6.3 Critères de validation

| Critère | Attendu | Comment vérifier |
|---------|---------|------------------|
| Import réussi | Pas d'erreur console | Voir terminal Streamlit |
| Phases calculées | 2 phases détectées | Affichage texte avant graphique |
| Pullback calculé | 82.8 pips | Message texte "🔄 Pullback détecté : -82.8 pips" |
| Zone orange visible | Oui | Visuel graphique entre 14:35 et 14:45 |
| Durée pullback | 10 minutes | Nombre de chandeliers orange |
| Prix cohérent | Descend de ~82.8 pips | Prix au début vs fin de zone orange |
| Légende complète | 5-6 types de phases | Voir légende à droite |
| Stats affichées | 3 métriques | Durée / Amplitude / Impact |

---

## 7. RÉSOLUTION DE PROBLÈMES {#troubleshooting}

### 7.1 Erreurs d'import

**Symptôme :**
```
ImportError: cannot import name 'generate_candlestick_curve_from_phases'
```

**Causes possibles :**
1. Modification non sauvegardée dans `price_curve_generator.py`
2. Cache Python (.pyc) périmé
3. Fichier corrompu

**Solutions :**
```bash
# Vérifier le fichier contient bien la fonction
grep "def generate_candlestick_curve_from_phases" fx_impact_app/src/price_curve_generator.py

# Nettoyer caches
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
rm -rf ~/.streamlit/cache

# Relancer
streamlit run fx_impact_app/streamlit_app/Home.py
```

---

### 7.2 Phases non détectées

**Symptôme :**
```
⚠️ Phases non disponibles, utilisation ancien système vectoriel
```

**Causes possibles :**
1. Mode séquentiel non activé
2. Variable `phases` non définie dans scope
3. Phases vides ou None

**Solutions :**
1. Vérifier checkbox "Mode séquentiel" est cochée
2. Vérifier dans terminal si message :
   ```
   🚀 [4_Planificateur] Module v8.6.2 (avec pullback FIX v2) importé avec succès !
   ```
3. Si non présent, problème avec `sequence_multi_event_timeline_v86`

**Debug :**
```python
# Ajouter dans le code juste avant génération graphique :
print(f"DEBUG: 'phases' in locals() = {'phases' in locals()}")
if 'phases' in locals():
    print(f"DEBUG: len(phases) = {len(phases)}")
    print(f"DEBUG: phases[0] keys = {phases[0].keys()}")
```

---

### 7.3 Pullback non visible graphiquement

**Symptôme :**
- Graphique s'affiche
- Stats "Pullback détecté" apparaissent
- Mais zone orange absente

**Causes possibles :**
1. Données pullback = 0
2. Temps pullback trop court (< 1 minute)
3. Couleur mal configurée

**Debug :**
```python
# Après génération price_df, ajouter :
pullback_rows = price_df[price_df['phase'] == 'pullback']
print(f"DEBUG: Pullback rows = {len(pullback_rows)}")
print(f"DEBUG: Pullback times = {pullback_rows['time'].tolist()}")
print(f"DEBUG: Pullback prices = {pullback_rows['close'].tolist()}")
```

**Solutions :**
- Si `len(pullback_rows) == 0` : Problème dans logique de génération
- Vérifier `phase.get('pullback_pips', 0) > 0` pour Phase 2
- Vérifier timestamps cohérents (peak_time < start_time phase suivante)

---

### 7.4 Erreur "KeyError: 'cumulative_price'"

**Symptôme :**
```
KeyError: 'cumulative_price'
```

**Cause :**
Phase manque la clé `cumulative_price`

**Solution :**
Vérifier que `sequence_multi_event_timeline_v86` version 8.6.2 sauvegarde bien :
```python
phase['cumulative_price'] = ttr_result['cumulative_price']
```

Si absente, utiliser fallback :
```python
prev_cumulative = prev_phase.get('cumulative_price', start_price)
```

---

### 7.5 Graphique trop court ou trop long

**Symptôme :**
Graphique ne couvre pas toute la période ou dépasse largement

**Cause :**
Paramètre `duration_minutes` mal calculé

**Solution :**
Ajuster dans l'appel :
```python
# Calculer durée dynamiquement
first_time = min(pd.to_datetime(p['start_time']) for p in phases)
last_phase = max(phases, key=lambda p: pd.to_datetime(p['start_time']))
last_time = pd.to_datetime(last_phase['start_time']) + pd.Timedelta(minutes=last_phase['duration_minutes'])
duration_minutes = int((last_time - first_time).total_seconds() / 60) + 30  # +30 buffer

price_df = generate_candlestick_curve_from_phases(
    ...
    duration_minutes=duration_minutes
)
```

---

## 8. ANNEXES TECHNIQUES {#annexes}

### 8.1 Structure complète phase

```python
phase = {
    # Identifiants
    'phase_num': 1,                          # Numéro séquentiel
    
    # Timing
    'start_time': '2025-09-11 14:30:00+02:00',  # ou datetime
    'peak_time': '2025-09-11 14:35:00+02:00',   # Temps du pic observé
    'predicted_end': '...',                      # Fin prédite
    
    # Prix
    'cumulative_price': 1.17196,             # Prix au pic (cumulatif)
    
    # Impacts
    'impact_combined': 207.0,                # Impact vectoriel (avec direction)
    'impact_brut': 207.0,                    # Impact brut
    'pullback_pips': 0.0,                    # Pullback depuis phase précédente
    'minutes_since_prev_phase': 0.0,         # Minutes depuis début phase précédente
    
    # Timings
    'latency_minutes': 1.0,                  # Latence moyenne
    'ttr_predicted': 41.0,                   # TTR prédit (minutes)
    'ttr_real': 41.0,                        # TTR réel observé (si dispo)
    'duration_minutes': 41.0,                # Durée totale phase
    
    # Direction
    'direction': 'UP',                       # 'UP' ou 'DOWN'
    
    # Métadonnées
    'num_events': 6,                         # Nombre événements dans phase
    'events': [                              # Liste événements
        {
            'family': 'CPI',
            'country': 'US',
            'ts_utc': '...',
            ...
        }
    ],
    
    # Facteurs
    'attenuation_factor': 1.0,               # Facteur d'atténuation (si applicable)
    'attenuation_reason': '',                # Raison atténuation
    
    # Notes
    'note': '🔄 Pullback détecté : -82.8 pips...',  # Note affichée UI
    
    # Status
    'is_complete': True,                     # Phase complète ou interrompue
}
```

---

### 8.2 Formule pullback (rappel Phase 1)

**Référence :** `RAPPORT_INTERMEDIAIRE_14OCT2025_PULLBACK_CALCUL.md`

```python
def calculate_pullback(
    phase1_impact: float,
    minutes_since_peak: float,
    minutes_to_next_phase: float
) -> float:
    """
    Calcule pullback entre deux phases rapprochées
    
    Règles :
    - Si intervalle > 30 min : pas de pullback (retourne 0)
    - Si intervalle < 30 min : pullback proportionnel
    - Formule : ~4% par minute
    - Plafond : 50% (Fibonacci)
    
    Exemple 11 sept 2025 :
    - phase1_impact = 207.0 pips
    - minutes_since_peak = 10.0 (entre 14:35 et 14:45)
    - minutes_to_next_phase = 15.0
    
    → pullback = 207.0 × 0.04 × 10 = 82.8 pips
    """
    
    if minutes_to_next_phase > 30:
        return 0.0
    
    pullback_rate_per_minute = 0.04
    max_pullback_pct = 0.50
    
    pullback_pct = min(
        pullback_rate_per_minute * minutes_since_peak,
        max_pullback_pct
    )
    
    return abs(phase1_impact) * pullback_pct
```

---

### 8.3 Mapping phases → DataFrame

**Input (phases) :**
```python
[
    {'phase_num': 1, 'start_time': '14:30', 'duration': 41, ...},
    {'phase_num': 2, 'start_time': '14:45', 'pullback_pips': 82.8, ...}
]
```

**Output (price_df) :**
```
   time                open     high     low      close    phase       phase_num
0  2025-09-11 14:30   1.17000  1.17001  1.16999  1.17000  pre_event   0
1  2025-09-11 14:31   1.17000  1.17001  1.16999  1.17000  latence     1
...
5  2025-09-11 14:35   1.17195  1.17197  1.17194  1.17196  mouvement   1
6  2025-09-11 14:36   1.17196  1.17196  1.17188  1.17190  pullback    2  ← ORANGE
7  2025-09-11 14:37   1.17190  1.17190  1.17182  1.17184  pullback    2  ← ORANGE
...
15 2025-09-11 14:44   1.17118  1.17118  1.17116  1.17117  pullback    2  ← ORANGE
16 2025-09-11 14:45   1.17117  1.17118  1.17116  1.17117  latence     2
17 2025-09-11 14:46   1.17117  1.17120  1.17116  1.17119  mouvement   2
...
```

---

### 8.4 Commandes utiles

```bash
# Naviguer au projet
cd ~/Desktop/eurusd_news_impact_calculator_MPC

# Lister fichiers modifiés (git)
git status

# Voir différences
git diff fx_impact_app/src/price_curve_generator.py

# Test Python
python3 test_pullback_graph.py

# Appliquer patch
python3 apply_pullback_graph_patch.py

# Nettoyer caches
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Lancer Streamlit
streamlit run fx_impact_app/streamlit_app/Home.py

# Vérifier version module
python3 -c "import sys; sys.path.insert(0, 'fx_impact_app/src'); from sequence_multi_event_timeline_v86 import __doc__; print(__doc__)"

# Chercher fonction dans fichier
grep -n "def generate_candlestick_curve_from_phases" fx_impact_app/src/price_curve_generator.py
```

---

### 8.5 Fichiers de référence

**Phase 1 (complétée) :**
- `RAPPORT_INTERMEDIAIRE_14OCT2025_PULLBACK_CALCUL.md` - Rapport complet Phase 1
- `RESUME_SESSION_14OCT2025_V4_PULLBACK_FIX_V2.md` - Résumé fix v8.6.2

**Phase 2 (actuelle) :**
- `RAPPORT_EXHAUSTIF_PHASE2_GRAPHIQUE_PULLBACK.md` - **CE FICHIER**
- `test_pullback_graph.py` - Script validation
- `apply_pullback_graph_patch.py` - Script patch automatique
- `MODIFICATION_GRAPHIQUE_PULLBACK.py` - Instructions manuelles

**Code :**
- `fx_impact_app/src/price_curve_generator.py` - Générateur courbe
- `fx_impact_app/src/sequence_multi_event_timeline_v86.py` - Calcul phases
- `fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py` - UI
- `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py` - Page principale

---

## 9. CHECKLIST REPRISE SESSION

Pour reprendre cette session dans un nouveau contexte Claude :

### ☐ Lecture rapide
1. Lire sections 1 (Contexte) et 2 (Architecture)
2. Comprendre flux de données section 2.2
3. Noter fichiers modifiés section 3

### ☐ Vérification état
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC

# Vérifier fonctions créées
grep -c "def generate_candlestick_curve_from_phases" fx_impact_app/src/price_curve_generator.py
# Doit retourner : 1

grep -c "def display_price_chart_with_pullback" fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py
# Doit retourner : 1

# Vérifier imports planificateur
grep "generate_candlestick_curve_from_phases" fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py
# Doit avoir un résultat
```

### ☐ Si fonctions manquantes
Relire sections 3.1, 3.2, 3.3 pour savoir quoi créer

### ☐ Action suivante
1. **Si modification restante pas appliquée :**
   - Lire section 5 (Modification restante)
   - Appliquer via script ou manuellement
   
2. **Si tout appliqué :**
   - Lire section 6 (Test)
   - Exécuter tests

### ☐ En cas d'erreur
Consulter section 7 (Troubleshooting)

---

## 10. RÉSUMÉ ÉTAT ACTUEL

**✅ COMPLÉTÉ :**
- [x] Fonction `generate_candlestick_curve_from_phases()` créée
- [x] Fonction `create_sequential_phases_chart()` créée
- [x] Fonction `plt_to_rgb()` créée
- [x] Fonction `display_price_chart_with_pullback()` créée
- [x] Import ajouté dans `streamlit_sequential_ui.py`
- [x] Import ajouté dans planificateur
- [x] Scripts de test créés
- [x] Scripts de patch créés
- [x] Documentation exhaustive créée

**⏳ EN ATTENTE :**
- [ ] Modification bloc génération graphique dans planificateur (section 5)
- [ ] Test validation Python (section 6.1)
- [ ] Test Streamlit complet (section 6.2)
- [ ] Vérification visuelle pullback orange (section 6.2)
- [ ] Documentation finale après validation

**🎯 OBJECTIF SUIVANT :**
Appliquer modification restante puis tester sur 11 septembre 2025

---

## MÉTA-INFORMATIONS

**Fichier :** `RAPPORT_EXHAUSTIF_PHASE2_GRAPHIQUE_PULLBACK.md`  
**Auteur :** Claude (Anthropic)  
**Session :** 14 octobre 2025  
**Version :** 1.0  
**Tokens :** ~15,000 (ce rapport)  
**Temps lecture estimé :** 30-45 minutes  
**Niveau détail :** EXHAUSTIF  

**Utilisation recommandée :**
- Lecture section 1-2 : Vue d'ensemble (5 min)
- Section 3 : Modifications détaillées (10 min)
- Section 5 : Action immédiate (5 min)
- Section 6 : Tests (10 min)
- Sections 7-8 : Référence au besoin

**Mots-clés :**
pullback, graphique, phase, orange, sequence_multi_event_timeline, price_curve_generator, streamlit, plotly, EUR/USD, 11 septembre 2025, v8.6.2

---

**FIN DU RAPPORT**
