#!/usr/bin/env python3
"""
Construction V2 Scores & Composite Global

Objectif :
1. Macro V2 : Calculer surprise_z et créer events family_surp_pos/neg
2. Tech V2 : Filtrer events techniques selon régime TREND/RANGE
3. Scores empiriques : Calculer médiane pips et hit ratio (1h/4h/1j)
4. Composite global : Apprendre poids avec walk-forward ridge logistic

Date : 2025-12-08
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Config
BASE_DIR = Path(__file__).parent.parent / 'outputs'
PRICES_FILE = BASE_DIR / 'prices_ohlc_m1.csv'
EVENTS_FILE = BASE_DIR / 'events.csv'
EVENTS_TECH_FILE = BASE_DIR / 'events_tech_m1.csv'

OUTPUT_DIR = BASE_DIR
SCORES_V2_FILE = OUTPUT_DIR / 'scores_v2.csv'
ALPHA_WEIGHTS_FILE = OUTPUT_DIR / 'alpha_weights.csv'
WALKFORWARD_REPORT_FILE = OUTPUT_DIR / 'walkforward_report.csv'

# Paramètres
EMA_WINDOW_H1 = 200  # EMA 200 sur H1 pour régime
TREND_THRESHOLD = 0.0001  # Seuil pour TREND vs RANGE (en pips)
INTENSITY_THRESHOLD = 1.5  # Seuil pour return_* events

# Minimum événements pour calculer score empirique.
# 50 est trop strict pour les releases mensuelles/trimestrielles (NFP, ISM, etc.).
MIN_EVENTS_FOR_SCORE = 20

# Plancher sur l'écart-type des surprises pour éviter sur-normalisation
SIGMA_FLOOR = 0.1

# E2: Seuils minimum pour calculer z-score
MIN_Z_FOR_ZSCORE = 10  # Par défaut
MIN_Z_FOR_ZSCORE_EIA = 5  # Plus permissif pour EIA

# E3: Nombre de top Secondary event_keys à garder
TOP_SECONDARY_COUNT = 40

def load_data():
    """Charge tous les fichiers nécessaires"""
    print("="*80)
    print("📊 CHARGEMENT DONNÉES")
    print("="*80)
    print()
    
    # Prix OHLC
    print(f"Lecture : {PRICES_FILE}")
    df_prices = pd.read_csv(PRICES_FILE)
    df_prices['ts_utc'] = pd.to_datetime(df_prices['ts_utc'])
    df_prices = df_prices.sort_values('ts_utc').reset_index(drop=True)
    print(f"   ✅ {len(df_prices):,} lignes")
    
    # Événements macro
    print(f"Lecture : {EVENTS_FILE}")
    df_events = pd.read_csv(EVENTS_FILE)
    df_events['ts_utc'] = pd.to_datetime(df_events['ts_utc'])
    df_events = df_events.sort_values('ts_utc').reset_index(drop=True)
    print(f"   ✅ {len(df_events):,} lignes")
    
    # Événements techniques
    print(f"Lecture : {EVENTS_TECH_FILE}")
    df_tech = pd.read_csv(EVENTS_TECH_FILE)
    df_tech['ts_utc'] = pd.to_datetime(df_tech['ts_utc'])
    df_tech = df_tech.sort_values('ts_utc').reset_index(drop=True)
    print(f"   ✅ {len(df_tech):,} lignes")
    print()
    
    return df_prices, df_events, df_tech

def map_family_with_other_split(event_key: str, base_family: str) -> str:
    """
    D2: Splitter "Other" en 3 sous-familles (Bills, EIA, Secondary)
    pour éviter que les signaux non corrélés s'annulent.
    """
    if base_family != "Other":
        return base_family
    
    ek = (event_key or "").lower()
    
    # EIA / energy weekly data (vérifier EN PREMIER car plus spécifique)
    if (ek.startswith("eia ") or "eia " in ek or 
        "eia crude" in ek or "eia gasoline" in ek or "eia distillate" in ek or
        "eia natural gas" in ek or "eia heating oil" in ek or 
        "eia refinery" in ek or "eia cushing" in ek):
        return "EIA"
    
    # Bills / Treasury auctions (vérifier après EIA)
    if ("bill auction" in ek or "month bill" in ek or "week bill" in ek or 
        "btf auction" in ek or ("auction" in ek and ("bill" in ek or "btf" in ek))):
        return "Bills"
    
    # Reste des secondaires
    return "Secondary"

def build_macro_v2(df_events, df_prices=None):
    """
    Construit Macro V2 : surprise_z et events family_surp_pos/neg
    
    Args:
        df_events: DataFrame des événements
        df_prices: DataFrame des prix (optionnel, nécessaire pour E3)
    """
    print("="*80)
    print("📈 CONSTRUCTION MACRO V2")
    print("="*80)
    print()
    
    # Calculer surprise
    df_events['surprise'] = df_events['actual'] - df_events['estimate']
    
    # Filtrer uniquement estimate NaN.
    # On garde surprise == 0 (elle compte pour la fréquence, mais donnera surprise_z ~ 0).
    mask_valid = df_events['estimate'].notna()
    df_valid = df_events[mask_valid].copy()
    
    print(f"Événements valides (estimate non-NaN) : {len(df_valid):,} / {len(df_events):,}")
    
    # --- E1: Exclure Bills définitivement (pas d'estimate, pas prédictifs via surprise) ---
    n_before_bills = len(df_valid)
    df_valid = df_valid[~df_valid['event_key'].str.contains(r'bill auction|week bill|month bill|btf auction|auction', case=False, na=False, regex=True)].copy()
    n_after_bills = len(df_valid)
    print(f"⚠️  E1: Exclusion Bills : {n_before_bills:,} → {n_after_bills:,} événements ({n_before_bills - n_after_bills:,} exclus)")
    print()
    
    # Calculer surprise_z par event_key
    df_valid['surprise_z'] = np.nan
    
    for event_key in df_valid['event_key'].unique():
        mask = df_valid['event_key'] == event_key
        subset = df_valid[mask]['surprise']
        
        # --- E2: Seuil minimum adapté selon famille ---
        # Récupérer la famille pour cet event_key
        family_for_key = df_valid[mask]['family'].iloc[0] if len(df_valid[mask]) > 0 else None
        min_z = MIN_Z_FOR_ZSCORE_EIA if family_for_key == 'EIA' else MIN_Z_FOR_ZSCORE
        
        if len(subset) >= min_z:
            mean_surprise = subset.mean()
            std_surprise = subset.std()
            
            # Sigma floor pour éviter std trop petit (sur-normalisation)
            if pd.notna(std_surprise):
                std_surprise = max(std_surprise, SIGMA_FLOOR)
            
            if std_surprise and std_surprise > 0:
                df_valid.loc[mask, 'surprise_z'] = (subset - mean_surprise) / std_surprise
    
    print(f"Surprise_z calculé pour {df_valid['surprise_z'].notna().sum():,} événements")
    print()
    
    # --- D2: Splitter "Other" en Bills/EIA/Secondary ---
    if 'family' in df_valid.columns:
        df_valid['family'] = df_valid.apply(
            lambda r: map_family_with_other_split(r.get('event_key', ''), r.get('family', 'Other')),
            axis=1
        )
        # Afficher statistiques du split
        other_split_stats = df_valid[df_valid['family'].isin(['Bills', 'EIA', 'Secondary'])]['family'].value_counts()
        if len(other_split_stats) > 0:
            print(f"📊 D2: Split 'Other' → {len(other_split_stats)} sous-familles :")
            for family, count in other_split_stats.items():
                print(f"   {family}: {count:,} événements")
            print()
    
    # --- E3: Filtrer Secondary pour garder seulement top K par corrélation ---
    # (Si df_prices fourni, sinon on skip E3 et on le fera plus tard)
    if df_prices is not None and 'Secondary' in df_valid['family'].values:
        print(f"📊 E3: Calcul corrélations Secondary...")
        
        # Préparer prix avec mouvement futur 1h (horizon principal)
        df_prices_clean = df_prices.copy()
        df_prices_clean['ts_utc'] = pd.to_datetime(df_prices_clean['ts_utc'])
        if df_prices_clean['ts_utc'].dt.tz is None:
            df_prices_clean['ts_utc'] = pd.to_datetime(df_prices_clean['ts_utc'], utc=True)
        df_prices_clean = df_prices_clean.sort_values('ts_utc').reset_index(drop=True)
        
        # Calculer mouvement futur 1h
        df_prices_clean['future_close_1h'] = df_prices_clean['close'].shift(-60)
        df_prices_clean['movement_1h'] = df_prices_clean['future_close_1h'] - df_prices_clean['close']
        df_prices_clean['direction_1h'] = np.sign(df_prices_clean['movement_1h'])
        
        # Merger avec df_valid pour avoir les mouvements
        df_valid_merged = df_valid[df_valid['family'] == 'Secondary'].copy()
        df_valid_merged = df_valid_merged.merge(
            df_prices_clean[['ts_utc', 'direction_1h']],
            on='ts_utc',
            how='left'
        )
        df_valid_merged = df_valid_merged[df_valid_merged['direction_1h'].notna() & df_valid_merged['surprise_z'].notna()]
        
        if len(df_valid_merged) > 0:
            # Calculer corrélation par event_key
            corr_stats = []
            for event_key in df_valid_merged['event_key'].unique():
                subset = df_valid_merged[df_valid_merged['event_key'] == event_key]
                if len(subset) >= 5:  # Minimum pour corrélation
                    corr = subset['surprise_z'].corr(subset['direction_1h'])
                    if pd.notna(corr):
                        corr_stats.append({
                            'event_key': event_key,
                            'corr': abs(corr),  # Valeur absolue pour ranking
                            'corr_signed': corr
                        })
            
            if len(corr_stats) > 0:
                df_corr = pd.DataFrame(corr_stats)
                df_corr = df_corr.sort_values('corr', ascending=False)
                top_secondary = df_corr.head(TOP_SECONDARY_COUNT)['event_key'].tolist()
                
                n_before = len(df_valid[df_valid['family'] == 'Secondary'])
                df_valid = df_valid[
                    (df_valid['family'] != 'Secondary') | 
                    (df_valid['event_key'].isin(top_secondary))
                ].copy()
                n_after = len(df_valid[df_valid['family'] == 'Secondary'])
                
                print(f"   ✅ E3: Secondary filtré : {n_before:,} → {n_after:,} événements ({n_before - n_after:,} exclus)")
                print(f"   Top {len(top_secondary)} event_keys gardés (sur {len(df_corr)} avec corrélation)")
                print()
        else:
            print(f"   ⚠️  E3: Pas assez de données pour calculer corrélations, skip")
            print()
    
    # --- Étape A: Exclure complètement Secondary du directionnel ---
    # Secondary a weights=0.0 même après top-K, donc ne sert qu'à augmenter n_active et comprimer S
    n_before_exclude = len(df_valid)
    df_valid = df_valid[df_valid["family"] != "Secondary"].copy()
    n_after_exclude = len(df_valid)
    excluded = n_before_exclude - n_after_exclude
    if excluded > 0:
        print(f"⚠️  Étape A: Exclusion complète Secondary : {n_before_exclude:,} → {n_after_exclude:,} événements ({excluded:,} exclus)")
        print()
    
    # Créer events family_surp_pos et family_surp_neg
    events_v2 = []
    
    for _, row in df_valid.iterrows():
        if pd.notna(row['surprise_z']):
            # Positif
            if row['surprise'] > 0:
                events_v2.append({
                    'ts_utc': row['ts_utc'],
                    'event_key': f"{row['family']}_surp_pos",
                    'family': row['family'],
                    'type': 'macro',
                    'surprise_z': row['surprise_z'],
                    'intensity': abs(row['surprise_z']),
                    'is_active': 1
                })
            # Négatif
            else:
                events_v2.append({
                    'ts_utc': row['ts_utc'],
                    'event_key': f"{row['family']}_surp_neg",
                    'family': row['family'],
                    'type': 'macro',
                    'surprise_z': row['surprise_z'],
                    'intensity': abs(row['surprise_z']),
                    'is_active': 1
                })
    
    df_macro_v2 = pd.DataFrame(events_v2)
    print(f"✅ {len(df_macro_v2):,} événements Macro V2 créés")
    print()
    
    return df_macro_v2

def build_tech_v2(df_tech, df_prices):
    """Construit Tech V2 : filtre selon régime TREND/RANGE"""
    print("="*80)
    print("🔧 CONSTRUCTION TECH V2")
    print("="*80)
    print()
    
    # S'assurer que ts_utc est timezone-aware UTC
    if df_prices['ts_utc'].dt.tz is None:
        df_prices['ts_utc'] = pd.to_datetime(df_prices['ts_utc'], utc=True)
    else:
        df_prices['ts_utc'] = df_prices['ts_utc'].dt.tz_convert('UTC')
    
    if df_tech['ts_utc'].dt.tz is None:
        df_tech['ts_utc'] = pd.to_datetime(df_tech['ts_utc'], utc=True)
    else:
        df_tech['ts_utc'] = df_tech['ts_utc'].dt.tz_convert('UTC')
    
    # Créer série H1 (agrégation M1 → H1)
    df_prices['ts_h1'] = df_prices['ts_utc'].dt.floor('H')
    df_h1 = df_prices.groupby('ts_h1').agg({
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).reset_index()
    df_h1 = df_h1.sort_values('ts_h1').reset_index(drop=True)
    
    # Calculer EMA 200 sur H1
    df_h1['ema_200'] = df_h1['close'].ewm(span=EMA_WINDOW_H1, adjust=False).mean()
    
    # Calculer slope EMA (différence sur fenêtre glissante)
    window_slope = 20
    df_h1['ema_slope'] = df_h1['ema_200'].diff(window_slope) / window_slope
    
    # Déterminer régime
    df_h1['regime'] = 'RANGE'
    df_h1.loc[abs(df_h1['ema_slope']) > TREND_THRESHOLD, 'regime'] = 'TREND'
    
    # Mapper régime vers timestamps M1
    df_prices['ts_h1'] = df_prices['ts_utc'].dt.floor('H')
    df_prices = df_prices.merge(
        df_h1[['ts_h1', 'regime']],
        on='ts_h1',
        how='left'
    )
    df_prices['regime'] = df_prices['regime'].fillna('RANGE')
    
    print(f"Régime TREND : {(df_prices['regime'] == 'TREND').sum():,} minutes")
    print(f"Régime RANGE : {(df_prices['regime'] == 'RANGE').sum():,} minutes")
    print()
    
    # Mapper régime vers events techniques
    df_tech = df_tech.merge(
        df_prices[['ts_utc', 'regime']],
        on='ts_utc',
        how='left'
    )
    df_tech['regime'] = df_tech['regime'].fillna('RANGE')
    
    # Filtrer events techniques selon règles
    events_v2 = []
    
    for _, row in df_tech.iterrows():
        event_key = row['event_key']
        regime = row['regime']
        intensity = row['intensity']
        
        # Règle 1 : inside_bar_break_* uniquement en TREND
        if 'inside_bar_break' in event_key:
            if regime == 'TREND':
                events_v2.append({
                    'ts_utc': row['ts_utc'],
                    'event_key': event_key,
                    'family': row['family'],
                    'type': 'tech',
                    'intensity': intensity,
                    'is_active': 1
                })
        
        # Règle 2 : return_* uniquement si |intensity| > 1.5
        elif 'return_' in event_key:
            if abs(intensity) > INTENSITY_THRESHOLD:
                events_v2.append({
                    'ts_utc': row['ts_utc'],
                    'event_key': event_key,
                    'family': row['family'],
                    'type': 'tech',
                    'intensity': intensity,
                    'is_active': 1
                })
        
        # Autres events : garder tous
        else:
            events_v2.append({
                'ts_utc': row['ts_utc'],
                'event_key': event_key,
                'family': row['family'],
                'type': 'tech',
                'intensity': intensity,
                'is_active': 1
            })
    
    df_tech_v2 = pd.DataFrame(events_v2)
    print(f"✅ {len(df_tech_v2):,} événements Tech V2 créés (après filtrage)")
    print()
    
    return df_tech_v2

def calculate_empirical_scores(df_events_v2, df_prices):
    """Calcule scores empiriques : médiane pips et hit ratio (1h/4h/1j)"""
    print("="*80)
    print("📊 CALCUL SCORES EMPIRIQUES")
    print("="*80)
    print()
    
    # Préparer prix avec calculs de mouvement
    df_prices = df_prices.sort_values('ts_utc').reset_index(drop=True)
    
    # S'assurer que ts_utc est timezone-aware UTC
    if df_prices['ts_utc'].dt.tz is None:
        df_prices['ts_utc'] = pd.to_datetime(df_prices['ts_utc'], utc=True)
    else:
        df_prices['ts_utc'] = df_prices['ts_utc'].dt.tz_convert('UTC')
    
    # S'assurer que df_events_v2['ts_utc'] est aussi timezone-aware UTC
    if df_events_v2['ts_utc'].dt.tz is None:
        df_events_v2['ts_utc'] = pd.to_datetime(df_events_v2['ts_utc'], utc=True)
    else:
        df_events_v2['ts_utc'] = df_events_v2['ts_utc'].dt.tz_convert('UTC')
    
    df_prices['close_pips'] = df_prices['close'] * 10000  # Conversion en pips
    
    # Calculer mouvements futurs (1h, 4h, 1j)
    horizons = {
        '1h': 60,   # 60 minutes
        '4h': 240,  # 240 minutes
        '1j': 1440  # 1440 minutes (24h)
    }
    
    for horizon_name, horizon_minutes in horizons.items():
        df_prices[f'future_close_{horizon_name}'] = df_prices['close'].shift(-horizon_minutes)
        df_prices[f'movement_pips_{horizon_name}'] = (
            (df_prices[f'future_close_{horizon_name}'] - df_prices['close']) * 10000
        )
        df_prices[f'direction_{horizon_name}'] = np.sign(df_prices[f'movement_pips_{horizon_name}'])
    
    # Calculer scores par event_key
    scores = []
    
    # S'assurer que df_prices est trié et créer array numpy pour searchsorted (plus rapide)
    df_prices = df_prices.sort_values('ts_utc').reset_index(drop=True)
    prices_ts_array = df_prices['ts_utc'].values
    
    unique_event_keys = df_events_v2['event_key'].unique()
    total_keys = len(unique_event_keys)
    total_combinations = total_keys * 3  # 3 horizons par event_key
    print(f"Calcul des scores pour {total_keys} event_keys ({total_combinations} combinaisons event_key × horizon)...")
    print()
    
    processed_combinations = 0
    start_time = datetime.now()
    
    for idx_key, event_key in enumerate(unique_event_keys):
        mask = df_events_v2['event_key'] == event_key
        event_times = df_events_v2[mask]['ts_utc'].values  # Utiliser .values pour numpy array
        
        for horizon_idx, horizon_name in enumerate(['1h', '4h', '1j']):
            movements = []
            directions = []
            
            # Filtrer les event_times valides (non-NaN)
            valid_times = event_times[~pd.isna(event_times)]
            
            if len(valid_times) > 0:
                # Utiliser searchsorted vectorisé (beaucoup plus rapide)
                price_indices = np.searchsorted(prices_ts_array, valid_times, side='right')
                
                # Filtrer les indices valides
                valid_mask = (price_indices < len(df_prices)) & (price_indices + horizons[horizon_name] < len(df_prices))
                valid_price_indices = price_indices[valid_mask]
                
                if len(valid_price_indices) > 0:
                    # Extraire movements et directions en une seule opération
                    movements_array = df_prices.iloc[valid_price_indices][f'movement_pips_{horizon_name}'].values
                    directions_array = df_prices.iloc[valid_price_indices][f'direction_{horizon_name}'].values
                    
                    # Filtrer les valeurs non-NaN
                    valid_movements = movements_array[~pd.isna(movements_array) & ~pd.isna(directions_array)]
                    valid_directions = directions_array[~pd.isna(movements_array) & ~pd.isna(directions_array)]
                    
                    movements.extend(valid_movements.tolist())
                    directions.extend(valid_directions.tolist())
            
            processed_combinations += 1
            
            # Afficher progression toutes les 10 combinaisons ou tous les 5%
            if processed_combinations % 10 == 0 or processed_combinations % max(1, total_combinations // 20) == 0:
                pct = processed_combinations * 100 / total_combinations
                bar_length = 50
                filled = int(bar_length * pct / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = processed_combinations / elapsed if elapsed > 0 else 0
                remaining = (total_combinations - processed_combinations) / rate if rate > 0 else 0
                print(f"\r   [{bar}] {pct:5.1f}% ({processed_combinations}/{total_combinations}) | {event_key[:25]:25s} {horizon_name} | ETA: {remaining/60:.1f}min", end='', flush=True)
            
            if len(movements) >= MIN_EVENTS_FOR_SCORE:
                median_pips = np.median(movements)
                hit_ratio = (np.array(directions) == 1).mean() if len(directions) > 0 else 0.5
                
                scores.append({
                    'event_key': event_key,
                    'horizon': horizon_name,
                    'n_events': len(movements),
                    'median_pips': median_pips,
                    'hit_ratio': hit_ratio
                })
    
    print()  # Nouvelle ligne après la barre de progression
    
    df_scores = pd.DataFrame(scores)
    
    print(f"✅ {len(df_scores):,} scores calculés")
    print(f"   Event keys avec scores : {df_scores['event_key'].nunique()}")
    print()
    
    return df_scores

def build_composite_global(df_events_v2, df_scores, df_prices):
    """Construit composite global avec walk-forward ridge logistic"""
    print("="*80)
    print("🎯 CONSTRUCTION COMPOSITE GLOBAL")
    print("="*80)
    print()
    
    # S'assurer que ts_utc est timezone-aware UTC
    if df_prices['ts_utc'].dt.tz is None:
        df_prices['ts_utc'] = pd.to_datetime(df_prices['ts_utc'], utc=True)
    else:
        df_prices['ts_utc'] = df_prices['ts_utc'].dt.tz_convert('UTC')
    
    if df_events_v2['ts_utc'].dt.tz is None:
        df_events_v2['ts_utc'] = pd.to_datetime(df_events_v2['ts_utc'], utc=True)
    else:
        df_events_v2['ts_utc'] = df_events_v2['ts_utc'].dt.tz_convert('UTC')
    
    # Filtrer events avec scores valides
    valid_event_keys = df_scores[df_scores['n_events'] >= MIN_EVENTS_FOR_SCORE]['event_key'].unique()
    df_events_filtered = df_events_v2[df_events_v2['event_key'].isin(valid_event_keys)].copy()
    
    # --- D1: Exclusion temporaire de "Other" (et ses splits: Bills/EIA/Secondary) pour test directionnel ---
    # Après D2, Other est splité en Bills/EIA/Secondary, donc on filtre ces 4 familles
    # Les event_keys sont déjà transformés en "family_surp_pos/neg", donc on filtre par préfixe
    n_before = len(df_events_filtered)
    
    # Filtrer par event_key commençant par Other_/Bills_/EIA_/Secondary_
    mask_exclude = (
        df_events_filtered['event_key'].str.startswith('Other_', na=False) |
        df_events_filtered['event_key'].str.startswith('Bills_', na=False) |
        df_events_filtered['event_key'].str.startswith('EIA_', na=False) |
        df_events_filtered['event_key'].str.startswith('Secondary_', na=False)
    )
    df_events_filtered = df_events_filtered[~mask_exclude].copy()
    n_after = len(df_events_filtered)
    n_excluded = n_before - n_after
    print(f"⚠️  D1: Exclusion temporaire de 'Other/Bills/EIA/Secondary' : {n_before:,} → {n_after:,} événements ({n_excluded:,} exclus)")
    
    print(f"Événements avec scores valides (après exclusion Other) : {len(df_events_filtered):,}")
    print()
    
    # Créer matrice X(t) : events actifs pondérés
    # Macro : pondérés par surprise_z
    # Tech : pondérés par intensity
    
    # Préparer données pour chaque timestamp
    timestamps = sorted(df_events_filtered['ts_utc'].unique())
    
    # Créer features X(t)
    X_data = []
    y_data_1h = []
    y_data_4h = []
    y_data_1j = []
    timestamps_data = []
    
    # Préparer prix avec mouvements futurs
    df_prices = df_prices.sort_values('ts_utc').reset_index(drop=True)
    df_prices['close_pips'] = df_prices['close'] * 10000
    
    horizons = {'1h': 60, '4h': 240, '1j': 1440}
    for horizon_name, horizon_minutes in horizons.items():
        df_prices[f'future_close_{horizon_name}'] = df_prices['close'].shift(-horizon_minutes)
        df_prices[f'movement_pips_{horizon_name}'] = (
            (df_prices[f'future_close_{horizon_name}'] - df_prices['close']) * 10000
        )
        df_prices[f'direction_{horizon_name}'] = np.sign(df_prices[f'movement_pips_{horizon_name}'])
    
    # Créer mapping event_key -> feature index
    event_keys_sorted = sorted(valid_event_keys)
    event_key_to_idx = {ek: i for i, ek in enumerate(event_keys_sorted)}
    
    print(f"Features : {len(event_keys_sorted)} event_keys")
    print(f"Timestamps uniques : {len(timestamps):,}")
    print()
    
    # Optimiser : créer index de prix pour recherche rapide
    df_prices = df_prices.sort_values('ts_utc').reset_index(drop=True)
    
    # Convertir en numpy datetime64 pour compatibilité searchsorted
    prices_ts_array = pd.to_datetime(df_prices['ts_utc']).values.astype('datetime64[ns]')
    
    # Limiter le nombre de timestamps pour performance (peut être ajusté)
    max_timestamps = min(50000, len(timestamps))  # Limiter à 50k max
    timestamps = timestamps[:max_timestamps]
    
    print(f"Traitement de {len(timestamps):,} timestamps...")
    print()
    
    # Construire X(t) et y(t) pour chaque timestamp
    start_time = datetime.now()
    
    for idx_ts, ts in enumerate(timestamps):
        # Afficher progression toutes les 1000 timestamps ou tous les 5%
        if idx_ts % 1000 == 0 or idx_ts % max(1, len(timestamps) // 20) == 0:
            pct = idx_ts * 100 / len(timestamps)
            bar_length = 50
            filled = int(bar_length * pct / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = idx_ts / elapsed if elapsed > 0 else 0
            remaining = (len(timestamps) - idx_ts) / rate if rate > 0 else 0
            print(f"\r   [{bar}] {pct:5.1f}% ({idx_ts}/{len(timestamps)}) | ETA: {remaining/60:.1f}min", end='', flush=True)
        
        # Events actifs à ce timestamp (optimisé avec groupby)
        events_at_ts = df_events_filtered[df_events_filtered['ts_utc'] == ts]
        
        if len(events_at_ts) == 0:
            continue
        
        # Créer vecteur feature X(t)
        x_vec = np.zeros(len(event_keys_sorted))
        
        for _, event in events_at_ts.iterrows():
            event_key = event['event_key']
            if event_key in event_key_to_idx:
                idx = event_key_to_idx[event_key]
                
                if event['type'] == 'macro':
                    # Macro : pondéré par surprise_z
                    weight = event.get('surprise_z', 0)
                else:
                    # Tech : pondéré par intensity
                    weight = event.get('intensity', 0)
                
                x_vec[idx] += weight
        
        # Trouver prix correspondant avec searchsorted (rapide)
        # Convertir ts en datetime64 pour compatibilité
        ts_dt64 = pd.to_datetime(ts).to_numpy().astype('datetime64[ns]')
        price_idx = np.searchsorted(prices_ts_array, ts_dt64, side='right')
        
        if price_idx >= len(df_prices) or price_idx + horizons['1j'] >= len(df_prices):
            continue
        
        # Extraire directions futures
        y_1h = df_prices.iloc[price_idx]['direction_1h']
        y_4h = df_prices.iloc[price_idx]['direction_4h']
        y_1j = df_prices.iloc[price_idx]['direction_1j']
        
        if pd.notna(y_1h) and pd.notna(y_4h) and pd.notna(y_1j):
            X_data.append(x_vec)
            y_data_1h.append(int(y_1h > 0))  # 1 si UP, 0 si DOWN
            y_data_4h.append(int(y_4h > 0))
            y_data_1j.append(int(y_1j > 0))
            timestamps_data.append(ts)
    
    print()  # Nouvelle ligne après la barre de progression
    
    X = np.array(X_data)
    y_1h = np.array(y_data_1h)
    y_4h = np.array(y_data_4h)
    y_1j = np.array(y_data_1j)
    
    print(f"Matrice X : {X.shape}")
    print(f"Vecteurs y : {len(y_1h)} échantillons")
    print()
    
    # Walk-forward avec Ridge Logistic
    # Diviser en train/test (80/20)
    split_idx = int(len(X) * 0.8)
    
    X_train = X[:split_idx]
    X_test = X[split_idx:]
    y_train_1h = y_1h[:split_idx]
    y_test_1h = y_1h[split_idx:]
    y_train_4h = y_4h[:split_idx]
    y_test_4h = y_4h[split_idx:]
    y_train_1j = y_1j[:split_idx]
    y_test_1j = y_1j[split_idx:]
    
    # Normaliser (fit sur train seulement)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Entraîner modèles pour chaque horizon
    alphas = {}
    reports = []
    
    for horizon_name, y_train, y_test in [
        ('1h', y_train_1h, y_test_1h),
        ('4h', y_train_4h, y_test_4h),
        ('1j', y_train_1j, y_test_1j)
    ]:
        print(f"Entraînement modèle {horizon_name}...")
        
        # Ridge Logistic (C = 1/alpha)
        model = LogisticRegression(penalty='l2', C=1.0, max_iter=1000, solver='lbfgs')
        model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
        
        # Métriques
        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)
        test_prec = precision_score(y_test, y_pred_test, zero_division=0)
        test_rec = recall_score(y_test, y_pred_test, zero_division=0)
        test_f1 = f1_score(y_test, y_pred_test, zero_division=0)
        
        # Stocker poids
        alphas[horizon_name] = {
            'event_key': event_keys_sorted,
            'weight': model.coef_[0].tolist(),
            'intercept': model.intercept_[0]
        }
        
        # Rapport
        reports.append({
            'horizon': horizon_name,
            'train_samples': len(y_train),
            'test_samples': len(y_test),
            'train_accuracy': train_acc,
            'test_accuracy': test_acc,
            'test_precision': test_prec,
            'test_recall': test_rec,
            'test_f1': test_f1
        })
        
        print(f"   Test Accuracy : {test_acc:.3f}")
        print()
    
    # Exporter alpha weights
    alpha_rows = []
    for horizon_name, data in alphas.items():
        for event_key, weight in zip(data['event_key'], data['weight']):
            alpha_rows.append({
                'horizon': horizon_name,
                'event_key': event_key,
                'weight': weight,
                'intercept': data['intercept']
            })
    
    df_alpha = pd.DataFrame(alpha_rows)
    
    # Exporter rapport walk-forward
    df_report = pd.DataFrame(reports)
    
    return df_alpha, df_report

def main():
    print("="*80)
    print("CONSTRUCTION V2 SCORES & COMPOSITE GLOBAL")
    print("="*80)
    print()
    
    # 1. Charger données
    df_prices, df_events, df_tech = load_data()
    
    # 2. Construire Macro V2 (avec df_prices pour E3)
    df_macro_v2 = build_macro_v2(df_events, df_prices=df_prices)
    
    # 3. Construire Tech V2
    df_tech_v2 = build_tech_v2(df_tech, df_prices)
    
    # 4. Combiner events V2
    df_events_v2 = pd.concat([df_macro_v2, df_tech_v2], ignore_index=True)
    df_events_v2 = df_events_v2.sort_values('ts_utc').reset_index(drop=True)
    
    print(f"Total événements V2 : {len(df_events_v2):,}")
    print()
    
    # 5. Calculer scores empiriques
    df_scores = calculate_empirical_scores(df_events_v2, df_prices)
    
    # Exporter scores_v2.csv
    df_scores.to_csv(SCORES_V2_FILE, index=False)
    print(f"✅ Scores exportés : {SCORES_V2_FILE}")
    print()
    
    # 6. Construire composite global
    df_alpha, df_report = build_composite_global(df_events_v2, df_scores, df_prices)
    
    # Exporter alpha_weights.csv
    df_alpha.to_csv(ALPHA_WEIGHTS_FILE, index=False)
    print(f"✅ Alpha weights exportés : {ALPHA_WEIGHTS_FILE}")
    
    # Exporter walkforward_report.csv
    df_report.to_csv(WALKFORWARD_REPORT_FILE, index=False)
    print(f"✅ Walk-forward report exporté : {WALKFORWARD_REPORT_FILE}")
    print()
    
    print("="*80)
    print("✅ CONSTRUCTION TERMINÉE")
    print("="*80)
    print()
    print("📁 Fichiers générés :")
    print(f"   📊 {SCORES_V2_FILE}")
    print(f"   🎯 {ALPHA_WEIGHTS_FILE}")
    print(f"   📋 {WALKFORWARD_REPORT_FILE}")
    print()

if __name__ == '__main__':
    main()


