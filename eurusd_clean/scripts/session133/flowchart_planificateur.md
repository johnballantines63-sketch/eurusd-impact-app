# 📊 FLOWCHART PLANIFICATEUR V3.0 - SESSION 133

**Date :** 13 novembre 2025  
**Objectif :** Intégrer module DoubleWave dans Planificateur avec aiguillage intelligent par pattern

---

## 🎯 VUE D'ENSEMBLE

```
INPUT: Date + Timezone + Seuil Minimum (pips)
    ↓
[Charger Events + Prix]
    ↓
[Détecter Pattern]
    ↓
    ├─→ Double Wave → predict_doublewave_overlap()
    ├─→ Single Wave → Formule Universelle amp(R²)
    └─→ Pattern Inconnu → Message explicatif
    ↓
[Afficher Prédiction + Justification]
    ↓
OUTPUT: Impact prédit + Pattern + Raison
```

---

## 📋 FLOWCHART DÉTAILLÉ (11 ÉTAPES)

### **ÉTAPE 1 : Validation Entrée Utilisateur**

```
INPUT:
  - date_str: str (formats flexibles: "2025-09-11", "11.09.2025", "2025.09.11", etc.)
  - timezone: str (default "Europe/Zurich")
  - min_pips: float (default 35.0)  # Seuil minimum mouvement significatif

VALIDATION:
  ✓ Date valide ?
  ✓ Timezone supportée ?
  ✓ Date dans période données (2023-2025) ?

SI INVALIDE:
  → Afficher message erreur
  → STOP

SI VALIDE:
  → Continuer ÉTAPE 2
```

**Implémentation :**
```python
def parse_flexible_date(date_str: str) -> datetime:
    """
    Parse date avec formats multiples (flexible)
    
    Formats acceptés:
    - YYYY-MM-DD, YYYY.MM.DD (ISO)
    - DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY (Européen)
    
    Returns:
        datetime object
    
    Raises:
        ValueError si format non reconnu
    """
    from datetime import datetime
    
    # Liste formats à essayer (ordre important)
    formats = [
        '%Y-%m-%d',      # 2025-09-11
        '%Y.%m.%d',      # 2025.09.11
        '%d.%m.%Y',      # 11.09.2025
        '%d/%m/%Y',      # 11/09/2025
        '%d-%m-%d',      # 11-09-2025
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Aucun format matché
    raise ValueError(
        f"Format date non reconnu: '{date_str}'. "
        f"Formats acceptés: YYYY-MM-DD, YYYY.MM.DD, DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY"
    )

def validate_input(date_str: str, timezone: str = "Europe/Zurich", min_pips: float = 35.0) -> Dict:
    """
    Valide les entrées utilisateur avec parsing flexible
    
    Args:
        date_str: Date (formats: YYYY-MM-DD, YYYY.MM.DD, DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY)
        timezone: Timezone (défaut: Europe/Zurich)
        min_pips: Seuil minimum mouvement significatif (défaut: 35 pips)
    
    Returns:
        {
            'valid': bool,
            'date': datetime or None,
            'timezone': pytz.timezone or None,
            'error_message': str or None
        }
    """
    try:
        # Parser date (formats flexibles)
        date = parse_flexible_date(date_str)
        tz = pytz.timezone(timezone)
        
        # Vérifier période données
        if date < datetime(2023, 1, 1) or date > datetime(2025, 12, 31):
            return {
                'valid': False,
                'date': None,
                'timezone': None,
                'error_message': f"Date hors période données (2023-2025): {date_str}"
            }
        
        # Valider min_pips
        if min_pips <= 0:
            return {
                'valid': False,
                'date': None,
                'timezone': None,
                'error_message': f"min_pips doit être > 0 (reçu: {min_pips})"
            }
        
        return {
            'valid': True,
            'date': date,
            'timezone': tz,
            'min_pips': min_pips,
            'error_message': None
        }
    except ValueError as e:
        return {
            'valid': False,
            'date': None,
            'timezone': None,
            'error_message': str(e)
        }
    except Exception as e:
        return {
            'valid': False,
            'date': None,
            'timezone': None,
            'error_message': f"Erreur validation: {str(e)}"
        }
```

---

### **ÉTAPE 2 : Charger Events Date Donnée**

```
ACTION:
  → Query DB events pour date donnée
  → Filtrer importance_n = 3 (HIGH)
  → Convertir timezone Bern

REQUÊTE DB:
  SELECT *
  FROM events
  WHERE DATE(ts_utc AT TIME ZONE 'Europe/Zurich') = ?
    AND importance_n = 3
  ORDER BY ts_utc

SI AUCUN EVENT:
  → Afficher "Aucun événement HIGH ce jour"
  → STOP

SI EVENTS TROUVÉS:
  → Continuer ÉTAPE 3
```

**Implémentation :**
```python
def load_events_for_date(date: datetime, db_path: str, timezone_str: str = "Europe/Zurich") -> pd.DataFrame:
    """
    Charge événements HIGH pour date donnée
    
    Returns:
        DataFrame avec colonnes: ts_utc, country, event_title, actual, estimate, forecast, previous
    """
    import duckdb
    
    conn = duckdb.connect(db_path, read_only=True)
    
    query = f"""
    SELECT 
        ts_utc,
        country,
        event_title,
        event_key,
        importance_n,
        actual,
        estimate,
        forecast,
        previous
    FROM events
    WHERE DATE(ts_utc AT TIME ZONE '{timezone_str}') = ?
      AND importance_n = 3
    ORDER BY ts_utc
    """
    
    df = conn.execute(query, [date.strftime('%Y-%m-%d')]).df()
    conn.close()
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # Convertir timezone
    df['ts_bern'] = pd.to_datetime(df['ts_utc']).dt.tz_convert(timezone_str)
    
    return df
```

---

### **ÉTAPE 3 : Charger Prix Date Donnée**

```
ACTION:
  → Charger prix 24h autour événement
  → Timezone Bern (prices_bern)
  → Fenêtre: [00:00 date - 23:59 date]

REQUÊTE DB:
  SELECT datetime, open, high, low, close
  FROM prices_bern
  WHERE DATE(datetime) = ?
  ORDER BY datetime

SI AUCUN PRIX:
  → Afficher "Pas de prix disponibles"
  → STOP

SI PRIX TROUVÉS:
  → Continuer ÉTAPE 4
```

**Implémentation :**
```python
def load_prices_for_date(date: datetime, db_path: str, timezone_str: str = "Europe/Zurich") -> pd.DataFrame:
    """
    Charge prix 1-minute pour date donnée
    
    Returns:
        DataFrame avec index datetime (timezone Bern) et colonnes: open, high, low, close
    """
    import duckdb
    
    conn = duckdb.connect(db_path, read_only=True)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE DATE(datetime) = ?
    ORDER BY datetime
    """
    
    df = conn.execute(query, [date.strftime('%Y-%m-%d')]).df()
    conn.close()
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # Convertir en timezone
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert(timezone_str)
    df = df.set_index('datetime')
    
    return df
```

---

### **ÉTAPE 4 : Enrichir Events avec Scores**

```
ACTION:
  → Pour chaque event, chercher score empirique
  → Utiliser event_families ou mapping variantes
  → Calculer surprise si Actual/Forecast présents

POUR CHAQUE EVENT:
  score = get_empirical_score(event_key, country)
  
  SI Actual ET Forecast présents:
    surprise = (Actual - Forecast) / Forecast * 100
  SINON:
    surprise = 0

SI AUCUN EVENT SCORÉ:
  → Marquer "Aucun événement scoré"
  → Pattern = "Inconnu"
  → Continuer ÉTAPE 5

SI EVENTS SCORÉS:
  → Continuer ÉTAPE 5
```

**Implémentation :**
```python
def enrich_events_with_scores(df_events: pd.DataFrame, df_scores: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichit événements avec scores empiriques et surprises
    
    Returns:
        DataFrame avec colonnes additionnelles: score, surprise, surprise_adjusted
    """
    from scripts.session127.utils_mapping_variants import get_empirical_score_with_variants
    
    df_enriched = df_events.copy()
    
    scores = []
    surprises = []
    
    for idx, row in df_enriched.iterrows():
        # Chercher score
        score, source = get_empirical_score_with_variants(
            event_key=row['event_key'],
            country_code=row['country'],
            df_scores=df_scores,
            df_mapping=None  # À charger si nécessaire
        )
        scores.append(score if score else 0.0)
        
        # Calculer surprise
        if pd.notna(row['actual']) and pd.notna(row['estimate']) and row['estimate'] != 0:
            surprise = (row['actual'] - row['estimate']) / abs(row['estimate']) * 100
            surprises.append(surprise)
        else:
            surprises.append(0.0)
    
    df_enriched['score'] = scores
    df_enriched['surprise'] = surprises
    df_enriched['score_adjusted'] = df_enriched['score'] * (1 + df_enriched['surprise'] / 100)
    
    return df_enriched
```

---

### **ÉTAPE 5 : Détecter Pattern (CRITIQUE)**

```
ACTION:
  → Scanner prix pour détecter spikes
  → Classifier pattern selon critères

ALGORITHME DÉTECTION:
  1. Scanner prix minute par minute
  2. Calculer baseline = close(t-1) avant premier event
  3. Détecter pic1 (>35 pips depuis baseline)
  4. Si pic1 trouvé:
     - Chercher pullback1 (creux après pic1)
     - Chercher pic2 (après pullback1)
  5. Classifier:
     - Si pic2 existe ET pullback significatif → DOUBLE_WAVE
     - Si pic1 > 40 pips ET pas de pic2 → SINGLE_WAVE_FORT
     - Si pic1 20-40 pips → SINGLE_WAVE_STANDARD
     - Sinon → INCONNU

RÉSULTAT:
  pattern_type: str
  metrics: Dict (impact, pullback ratio, extension, etc.)
```

**Implémentation :**
```python
def detect_pattern(df_prices: pd.DataFrame, df_events: pd.DataFrame, min_pips: float = 35.0, timezone_str: str = "Europe/Zurich") -> Dict:
    """
    Détecte pattern de mouvement (Double Wave vs Single Wave)
    
    Utilise DoubleWaveDetectorRev12 validé Session 120
    
    Args:
        min_pips: Seuil minimum (pips) pour considérer mouvement significatif
                  - Défaut: 35 pips (validé Sessions 117/120)
                  - Conservateur: 50+ pips (moins de faux positifs)
                  - Agressif: 20-30 pips (capture plus de mouvements)
    
    Logique:
        1. Filtre: impact < min_pips → INCONNU
        2. Classification fixe (basée MAE Session 132):
           - > 40 pips → SINGLE_WAVE_FORT (⚠️ MAE 39k pips)
           - ≥ 20 pips → SINGLE_WAVE_STANDARD (✅ MAE 9.99 pips)
    
    Returns:
        {
            'pattern_type': 'DOUBLE_WAVE' | 'SINGLE_WAVE_FORT' | 'SINGLE_WAVE_STANDARD' | 'INCONNU',
            'detection_confidence': float (0-1),
            'metrics': {
                'impact_pips': float,
                'wave1_pips': float or None,
                'wave2_pips': float or None,
                'pullback_ratio': float or None,
                'extension_factor': float or None,
                ...
            }
        }
    """
    from scripts.session120.double_wave_detector_rev12 import DoubleWaveDetectorRev12
    
    # 1. Obtenir baseline (close t-1 avant premier event)
    first_event_time = df_events['ts_bern'].min()
    baseline_time = first_event_time - pd.Timedelta(minutes=1)
    
    if baseline_time not in df_prices.index:
        # Trouver close le plus proche avant event
        valid_times = df_prices[df_prices.index < first_event_time].index
        if len(valid_times) == 0:
            return {
                'pattern_type': 'INCONNU',
                'detection_confidence': 0.0,
                'metrics': {},
                'error': 'Pas de prix avant événement'
            }
        baseline_time = valid_times[-1]
    
    baseline = df_prices.loc[baseline_time, 'close']
    
    # 2. Scanner prix après baseline
    df_after = df_prices[df_prices.index >= baseline_time].copy()
    
    # 3. Utiliser détecteur Rev12
    detector = DoubleWaveDetectorRev12(debug=False)
    result = detector.detect_double_wave(df_after, baseline, first_event_time)
    
    if result is None:
        # Pas de Double Wave détecté → tester Single Wave
        max_deviation = (df_after['close'] - baseline).abs().max()
        impact_pips = max_deviation * 10000
        
        # 1. Filtre minimum paramétrable
        if impact_pips < min_pips:
            return {
                'pattern_type': 'INCONNU',
                'detection_confidence': 0.0,
                'metrics': {
                    'impact_pips': impact_pips
                },
                'reason': f'Impact ({impact_pips:.1f} pips) < seuil minimum ({min_pips} pips)'
            }
        
        # 2. Classification fixe (basée MAE Session 132)
        if impact_pips > 40:
            return {
                'pattern_type': 'SINGLE_WAVE_FORT',
                'detection_confidence': 0.8,
                'metrics': {
                    'impact_pips': impact_pips,
                    'wave1_pips': None,
                    'wave2_pips': None,
                    'pullback_ratio': None,
                    'extension_factor': None
                }
            }
        elif impact_pips >= 20:
            return {
                'pattern_type': 'SINGLE_WAVE_STANDARD',
                'detection_confidence': 0.9,
                'metrics': {
                    'impact_pips': impact_pips,
                    'wave1_pips': None,
                    'wave2_pips': None,
                    'pullback_ratio': None,
                    'extension_factor': None
                }
            }
        else:
            return {
                'pattern_type': 'INCONNU',
                'detection_confidence': 0.5,
                'metrics': {
                    'impact_pips': impact_pips
                }
            }
    
    # Double Wave détecté
    return {
        'pattern_type': 'DOUBLE_WAVE',
        'detection_confidence': 0.95,
        'metrics': {
            'impact_pips': result['total_impact_pips'],
            'wave1_pips': result['wave1_pips'],
            'wave2_pips': result['wave2_pips'],
            'pullback_ratio': result['pullback1_ratio'],
            'extension_factor': result['wave2_pips'] / result['wave1_pips'] if result['wave1_pips'] > 0 else None
        }
    }
```

---

### **ÉTAPE 6 : Aiguillage Prédiction selon Pattern**

```
SI pattern_type == "DOUBLE_WAVE":
  → ÉTAPE 7 (predict_doublewave_overlap)

SI pattern_type == "SINGLE_WAVE_STANDARD":
  → ÉTAPE 8 (formule universelle amp(R²))

SI pattern_type == "SINGLE_WAVE_FORT":
  → ÉTAPE 8 (formule universelle amp(R²))
  → ⚠️ Note: MAE élevé Session 132 (39k pips)

SI pattern_type == "INCONNU":
  → ÉTAPE 9 (message explicatif)
```

---

### **ÉTAPE 7 : Prédiction Double Wave**

```
ACTION:
  → Appeler predict_doublewave_overlap()
  → Vérifier critères inclusion/exclusion
  → Retourner prédiction OU message exclusion

CODE:
  from src.core.doublewave_prediction import predict_doublewave_overlap
  
  result = predict_doublewave_overlap(
      events=df_events,
      debug=False
  )
  
  SI result['status'] == 'predicted':
    → prediction = result['prediction']
    → amplification = result['amplification']
    → raison = result['reason']
    → Continuer ÉTAPE 10
  
  SI result['status'] == 'excluded':
    → message = result['reason']
    → Afficher exclusion
    → STOP

CRITÈRES VÉRIFIÉS (automatique dans module):
  ✓ Score total 150-350 (ou >500 superposition)
  ✓ Events scorés 5-10 (ou >15 superposition)
  ✓ Pays majeurs (US, EU, UK, CA, JP, CH)
  ✓ Pattern NOT Cascade
```

**Implémentation :**
```python
def predict_double_wave(df_events: pd.DataFrame, pattern_metrics: Dict) -> Dict:
    """
    Prédiction pour pattern Double Wave
    
    Returns:
        {
            'prediction_pips': float or None,
            'amplification': float or None,
            'status': 'predicted' | 'excluded',
            'reason': str,
            'pattern_type': 'overlap_standard' | 'overlap_superposition' | 'cascade',
            'total_score': float
        }
    """
    from src.core.doublewave_prediction import predict_doublewave_overlap
    
    result = predict_doublewave_overlap(events=df_events, debug=False)
    
    return result
```

---

### **ÉTAPE 8 : Prédiction Single Wave (Pipeline LOO-CV Complet)**

```
ACTION:
  → Identifier type événement principal
  → Appeler pipeline LOO-CV (Sessions 125-126 + Flowchart 132)
  → Calibrer amplification spécifique au type événement
  → Valider avec MAE < 10 pips
  → Calculer impact prédit

ALGORITHME (Pipeline 6 Étapes):
  
  PHASE 1 : IDENTIFICATION CLUSTERS
  1. Identifier type événement principal (CPI, NFP, Fed, etc.)
  2. Définir signature cluster (composition, pays, scores)
  3. Rechercher clusters identiques historiques (même signature ±5 min)
  4. Si < 3 clusters → Fallback fonction universelle
  
  PHASE 2 : VÉRIFICATION PATTERNS (CRITIQUE)
  5. Pour CHAQUE cluster trouvé:
     - Charger prix avant/après
     - Mesurer pattern réel (Single Wave? Double Wave? Timing?)
     - Vérifier cohérence pattern avec date actuelle
  6. Regrouper par pattern identique
  7. Si groupe < 3 dates → Fallback fonction universelle
  
  PHASE 3 : VALIDATION LOO-CV
  8. Pour chaque date du groupe (Leave-One-Out):
     - Date i = étalon de référence
     - Calculer R²_i, impact_réel_i, amp_idéal_i
     - Pour chaque autre date j:
       * Calculer R²_j
       * Prédire amp_j via corrélation avec étalon i
       * Prédire impact_j
       * Calculer erreur_j = |prédit - réel|
     - MAE_itération_i = moyenne erreurs
  9. MAE_global = moyenne toutes itérations
  10. Détecter outliers (MAE_i > 2× moyenne)
  
  PHASE 4 : DÉCISION
  11. Si MAE_global < 10 pips:
      → Utiliser amplification calibrée LOO-CV ✅
  12. Si MAE_global >= 10 pips:
      → Fallback fonction universelle (Sessions 125-126)
  
  PHASE 5 : PRÉDICTION
  13. Calculer R² tendance date actuelle (60 min avant event)
  14. Appliquer amp(R²) calibrée ou universelle
  15. impact_pips = score_adjusted * amp

FORMULE FALLBACK (Fonction Universelle):
  a, b, c = 0.040833, 0.050220, -0.006553
  r2 = max(0.0, min(1.0, r2_trend))
  amp = max(0.01, min(0.20, a + b*r2 + c*r2²))

RÉSULTATS VALIDATION (Sessions 125-126):
  - CPI→NFP : +88.3% amélioration vs baseline
  - Fed→CPI : +52.3% amélioration
  - Fed→NFP : +60.0% amélioration
  - Moyenne : +71.6% amélioration

⚠️ ATTENTION MAE SESSION 132:
  - Single_Wave_Standard: MAE 9.99 pips ✅ EXCELLENT
  - Single_Wave_Fort: MAE 39k pips ❌ À AMÉLIORER
  → Afficher warning approprié selon pattern
```

**Implémentation :**
```python
def predict_single_wave(df_events: pd.DataFrame, df_prices: pd.DataFrame, pattern_type: str, db_path: str) -> Dict:
    """
    Prédiction pour pattern Single Wave avec Pipeline LOO-CV complet
    
    Utilise méthodologie Flowchart Session 132 + Pipeline Sessions 125-126:
    - Phase 1: Identification clusters identiques historiques
    - Phase 2: Vérification patterns (CRITIQUE)
    - Phase 3: Validation LOO-CV (Leave-One-Out Cross-Validation)
    - Phase 4: Décision (MAE < 10 pips ?)
    - Phase 5: Prédiction avec amplification calibrée ou fallback
    
    Args:
        df_events: Events enrichis avec scores
        df_prices: Prix 1-minute
        pattern_type: Type pattern détecté (SINGLE_WAVE_STANDARD / SINGLE_WAVE_FORT)
        db_path: Chemin vers warehouse.duckdb
    
    Returns:
        {
            'prediction_pips': float,
            'amplification': float,
            'r2_trend': float,
            'score_adjusted_total': float,
            'status': 'predicted',
            'reason': str,
            'method': 'loo_cv_calibrated' | 'universal_fallback',
            'mae_global': float or None,
            'warning': str or None
        }
    """
    # PHASE 1 : IDENTIFICATION TYPE ÉVÉNEMENT
    main_event_type = identify_main_event_type(df_events)
    
    # PHASE 2-4 : PIPELINE LOO-CV
    try:
        from scripts.session126.calibrate_universal_amplification import calibrate_for_event_type
        
        # Appeler pipeline complet (6 étapes)
        calibration = calibrate_for_event_type(
            event_type=main_event_type,
            db_path=db_path,
            method='loo_cv',  # Leave-One-Out Cross-Validation
            min_clusters=3,   # Minimum 3 clusters identiques
            pattern_filter=pattern_type  # Vérifier pattern cohérence
        )
        
        # Vérifier MAE < 10 pips
        if calibration['mae_global'] < 10.0 and calibration['status'] == 'EXCELLENT':
            method = 'loo_cv_calibrated'
            amp_function = calibration['amp_function']
            mae_global = calibration['mae_global']
            reason = f"Pipeline LOO-CV calibré (MAE {mae_global:.1f} pips, {calibration['n_clusters']} clusters)"
        else:
            # Fallback fonction universelle
            method = 'universal_fallback'
            amp_function = calculate_amplification_from_r2_universal
            mae_global = None
            reason = f"Fallback fonction universelle (MAE pipeline {calibration['mae_global']:.1f} pips >= 10)"
    
    except Exception as e:
        # Fallback si pipeline échoue
        method = 'universal_fallback'
        amp_function = calculate_amplification_from_r2_universal
        mae_global = None
        reason = f"Fallback fonction universelle (pipeline unavailable: {str(e)})"
    
    # PHASE 5 : PRÉDICTION
    
    # 1. Calculer R² tendance (60 min avant premier event)
    first_event_time = df_events['ts_bern'].min()
    window_start = first_event_time - pd.Timedelta(minutes=60)
    window_end = first_event_time - pd.Timedelta(minutes=1)
    
    df_window = df_prices[(df_prices.index >= window_start) & (df_prices.index <= window_end)]
    
    if len(df_window) < 10:
        return {
            'prediction_pips': None,
            'amplification': None,
            'r2_trend': None,
            'score_adjusted_total': None,
            'status': 'excluded',
            'reason': 'Fenêtre pré-événement insuffisante (< 10 minutes données)',
            'method': None,
            'mae_global': None,
            'warning': None
        }
    
    # Régression linéaire
    from sklearn.linear_model import LinearRegression
    import numpy as np
    
    X = np.arange(len(df_window)).reshape(-1, 1)
    y = df_window['close'].values
    
    model = LinearRegression()
    model.fit(X, y)
    r2_trend = model.score(X, y)
    
    # 2. Appliquer amplification (calibrée ou universelle)
    amp = amp_function(r2_trend)
    
    # 3. Calculer score_adjusted total
    score_adjusted_total = df_events['score_adjusted'].sum()
    
    # 4. Prédiction
    prediction_pips = score_adjusted_total * amp
    
    # Warning si Single_Wave_Fort (MAE élevé Session 132)
    warning = None
    if pattern_type == 'SINGLE_WAVE_FORT':
        warning = (
            "⚠️ Pattern Single_Wave_Fort: MAE élevé (39k pips Session 132). "
            "Prédiction indicative - Utiliser avec prudence."
        )
    
    return {
        'prediction_pips': prediction_pips,
        'amplification': amp,
        'r2_trend': r2_trend,
        'score_adjusted_total': score_adjusted_total,
        'status': 'predicted',
        'reason': reason,
        'method': method,
        'mae_global': mae_global,
        'warning': warning
    }

def identify_main_event_type(df_events: pd.DataFrame) -> str:
    """
    Identifie le type d'événement principal dans le cluster
    
    Priorité:
    1. Event avec score le plus élevé
    2. Si égalité : US > EU > UK > CA > JP
    3. Si toujours égalité : Premier chronologiquement
    
    Returns:
        Type événement (ex: "CPI", "NFP", "Fed Decision")
    """
    # Trouver event avec score max
    max_score_idx = df_events['score'].idxmax()
    main_event = df_events.loc[max_score_idx]
    
    # Normaliser nom événement
    event_key = main_event['event_key'].lower()
    
    # Mapping vers types standards
    if 'cpi' in event_key or 'inflation' in event_key:
        return 'CPI'
    elif 'nonfarm' in event_key or 'payroll' in event_key:
        return 'NFP'
    elif 'fed' in event_key or 'fomc' in event_key or 'interest rate' in event_key:
        return 'Fed Decision'
    elif 'gdp' in event_key:
        return 'GDP'
    elif 'retail' in event_key:
        return 'Retail Sales'
    elif 'pmi' in event_key:
        return 'PMI'
    elif 'unemployment' in event_key:
        return 'Unemployment'
    else:
        # Retourner event_key original si pas reconnu
        return main_event['event_key']

def calculate_amplification_from_r2_universal(r2_trend: float) -> float:
    """
    Fonction universelle fallback (Sessions 125-126)
    
    Formule validée sur 5 tests / 3 familles:
    - CPI→NFP : +88.3% amélioration
    - Fed→CPI : +52.3% amélioration
    - Fed→NFP : +60.0% amélioration
    - Moyenne : +71.6% amélioration
    
    Args:
        r2_trend: R² régression linéaire (0-1)
    
    Returns:
        Amplification (0.01-0.20)
    """
    a, b, c = 0.040833, 0.050220, -0.006553
    r2_clipped = max(0.0, min(1.0, r2_trend))
    amp = max(0.01, min(0.20, a + b*r2_clipped + c*r2_clipped**2))
    return amp
```

---

### **ÉTAPE 9 : Gestion Pattern Inconnu**

```
SI pattern_type == "INCONNU":
  
  MESSAGE:
    "Pattern non identifié pour cette date.
    
    Possible raisons:
    - Impact trop faible (< 20 pips)
    - Volatilité diffuse (pas de pic net)
    - Données prix incomplètes
    
    Suggestion: Vérifier manuellement les graphiques de prix."
  
  → Afficher message
  → STOP
```

---

### **ÉTAPE 10 : Affichage Résultats**

```
AFFICHER:
  
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 PRÉDICTION EUR/USD - {date}
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  🔍 PARAMÈTRES DÉTECTION:
  - Seuil minimum: {min_pips} pips
  - Timezone: {timezone}
  
  🎯 PATTERN DÉTECTÉ: {pattern_type}
  Confiance: {detection_confidence * 100}%
  
  📈 IMPACT PRÉDIT: {prediction_pips:.1f} pips
  
  🔧 MÉTHODOLOGIE:
  - Amplification: {amplification:.4f}
  - {raison}
  
  📊 MÉTRIQUES PATTERN:
  {afficher metrics selon pattern}
  
  ⚙️ ÉVÉNEMENTS ANALYSÉS:
  {liste events avec scores}
  
  {warning si présent}
  
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Implémentation :**
```python
def display_results(
    date: datetime,
    min_pips: float,
    timezone_str: str,
    pattern_type: str,
    detection_confidence: float,
    prediction_result: Dict,
    pattern_metrics: Dict,
    df_events: pd.DataFrame
) -> None:
    """
    Affiche résultats de manière formatée
    """
    print("=" * 80)
    print(f"📊 PRÉDICTION EUR/USD - {date.strftime('%Y-%m-%d')}")
    print("=" * 80)
    print()
    
    print("🔍 PARAMÈTRES DÉTECTION:")
    print(f"- Seuil minimum: {min_pips} pips")
    print(f"- Timezone: {timezone_str}")
    print()
    
    print(f"🎯 PATTERN DÉTECTÉ: {pattern_type}")
    print(f"Confiance: {detection_confidence * 100:.1f}%")
    print()
    
    if prediction_result['status'] == 'predicted':
        print(f"📈 IMPACT PRÉDIT: {prediction_result['prediction_pips']:.1f} pips")
        print()
        
        print("🔧 MÉTHODOLOGIE:")
        print(f"- Amplification: {prediction_result['amplification']:.4f}")
        print(f"- {prediction_result['reason']}")
        
        # Afficher méthode utilisée (LOO-CV vs Fallback)
        if 'method' in prediction_result and prediction_result['method']:
            if prediction_result['method'] == 'loo_cv_calibrated':
                print(f"✅ Méthode: Pipeline LOO-CV calibré (MAE {prediction_result['mae_global']:.1f} pips)")
            elif prediction_result['method'] == 'universal_fallback':
                print("🔄 Méthode: Fonction universelle (fallback)")
        print()
        
        print("📊 MÉTRIQUES PATTERN:")
        for key, value in pattern_metrics.items():
            if value is not None:
                if isinstance(value, float):
                    print(f"  - {key}: {value:.2f}")
                else:
                    print(f"  - {key}: {value}")
        print()
        
        if prediction_result.get('warning'):
            print(prediction_result['warning'])
            print()
    
    elif prediction_result['status'] == 'excluded':
        print(f"❌ PRÉDICTION NON DISPONIBLE")
        print(f"Raison: {prediction_result['reason']}")
        print()
    
    print("⚙️ ÉVÉNEMENTS ANALYSÉS:")
    for idx, row in df_events.iterrows():
        score_str = f"{row['score']:.1f}" if row['score'] > 0 else "N/A"
        surprise_str = f"{row['surprise']:+.1f}%" if row['surprise'] != 0 else "N/A"
        print(f"  - {row['ts_bern'].strftime('%H:%M')} {row['country']} {row['event_title']}")
        print(f"    Score: {score_str} | Surprise: {surprise_str}")
    
    print()
    print("=" * 80)
```

---

### **ÉTAPE 11 : Export Résultats (Optionnel)**

```
SI utilisateur demande export:
  
  CRÉER FICHIER JSON:
    {
      "date": "2025-09-11",
      "pattern_type": "DOUBLE_WAVE",
      "detection_confidence": 0.95,
      "prediction_pips": 56.2,
      "amplification": 0.1201,
      "methodology": "Overlap standard",
      "metrics": {...},
      "events": [...]
    }
  
  SAUVEGARDER:
    results/{date}_prediction.json
```

---

## 🎯 CRITÈRES VALIDATION FLOWCHART

### **Complétude**
- ✅ Toutes étapes définies (1-11)
- ✅ Gestion erreurs spécifiée
- ✅ Cas limites couverts

### **Clarté**
- ✅ Actions explicites pour chaque étape
- ✅ Pseudo-code inclus
- ✅ Diagrammes ASCII

### **Intégration**
- ✅ Module DoubleWave utilisé
- ✅ Fonction universelle utilisée
- ✅ Détecteur Rev12 utilisé

### **Décisions**
- ✅ Aiguillage pattern explicite
- ✅ Critères inclusion/exclusion respectés
- ✅ Warnings pour cas limites

---

## ⚠️ POINTS D'ATTENTION

### **1. Timezone CRITIQUE**
- Toujours utiliser `tz='Europe/Zurich'` pour prix
- Convertir events UTC → Bern avant analyse
- Vérifier cohérence timestamps events/prix

### **2. Baseline Précis**
- Utiliser close(t-1) avant premier event
- PAS low(t0) qui peut être spike anormal
- Impact erreur baseline: 5 pips → 20+ pips finale

### **3. Pattern Detection**
- Utiliser DoubleWaveDetectorRev12 (validé MAE 4.5 pips)
- Seuil détection: 35 pips (capture Double Wave)
- Garde temporelle: 3 bars minimum avant pullback

### **4. Amplifications Fixes**
- Overlap standard: 0.1201
- Overlap superposition: 0.0128
- NE PAS mélanger avec fonction universelle

### **5. MAE Par Pattern (Session 132)**
- Single_Wave_Standard: 9.99 pips ✅
- Double_Wave: 957.97 pips ⚠️
- Single_Wave_Fort: 39k pips ❌
→ Afficher warnings appropriés

---

## 🧪 TESTS VALIDATION FLOWCHART

### **Test 1 : Date avec Double Wave (2025-09-11)**
```
ENTRÉE:
  date = "2025-09-11"
  timezone = "Europe/Zurich"

ATTENDU:
  ✓ Events chargés (20+ events ECB+US)
  ✓ Prix chargés
  ✓ Pattern = DOUBLE_WAVE
  ✓ Appel predict_doublewave_overlap()
  ✓ Status = 'excluded' OU 'predicted' (superposition)
  ✓ Affichage résultats
```

### **Test 2 : Date avec Single Wave (2024-12-18)**
```
ENTRÉE:
  date = "2024-12-18"
  timezone = "Europe/Zurich"

ATTENDU:
  ✓ Events chargés (Fed Decision)
  ✓ Prix chargés
  ✓ Pattern = SINGLE_WAVE_STANDARD ou SINGLE_WAVE_FORT
  ✓ Appel formule universelle amp(R²)
  ✓ Prédiction calculée
  ✓ Affichage résultats
```

### **Test 3 : Date sans events (2025-01-15)**
```
ENTRÉE:
  date = "2025-01-15"
  timezone = "Europe/Zurich"

ATTENDU:
  ✓ Query DB
  ✓ Aucun event HIGH
  ✓ Message "Aucun événement HIGH ce jour"
  ✓ STOP proprement
```

---

## 📊 MÉTRIQUES SUCCÈS

### **Fonctionnel**
- [ ] Flowchart implémente 100% étapes (11/11)
- [ ] Tous cas tests passent (3/3)
- [ ] Gestion erreurs complète

### **Performance**
- [ ] Temps exécution < 5 secondes par date
- [ ] Pas d'erreur timezone
- [ ] Prédictions cohérentes avec Session 132

### **UX**
- [ ] Affichage clair et informatif
- [ ] Warnings appropriés (Single_Wave_Fort)
- [ ] Messages erreurs explicites

---

## 🚀 PROCHAINES ÉTAPES

### **Après Validation Flowchart**
1. ✅ Valider flowchart avec André
2. ⏳ Implémenter dans Planificateur V3.0
3. ⏳ Créer interface Streamlit
4. ⏳ Tester sur 3+ dates (Overlap, Superposition, Single)
5. ⏳ Documentation utilisateur

---

**Auteur :** André Valentin avec Claude  
**Session :** 133  
**Date :** 13 novembre 2025  
**Statut :** ✅ FLOWCHART COMPLET - PRÊT VALIDATION
