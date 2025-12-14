#!/usr/bin/env python3
"""
Génération d'Événements Techniques M1

Objectif :
- Détecter patterns techniques depuis prices_ohlc_m1.csv
- Générer events_tech_m1.csv au format LONG
- Format : ts_utc, event_key, family, is_active, intensity

Date : 2025-12-08
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Config
INPUT_FILE = Path(__file__).parent.parent / 'outputs' / 'prices_ohlc_m1.csv'
OUTPUT_FILE = Path(__file__).parent.parent / 'outputs' / 'events_tech_m1.csv'

def load_ohlc_data():
    """Charge les données OHLC"""
    print("="*80)
    print("📊 CHARGEMENT DONNÉES OHLC")
    print("="*80)
    print()
    
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Fichier introuvable : {INPUT_FILE}")
    
    print(f"Lecture : {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    # Convertir ts_utc en datetime
    df['ts_utc'] = pd.to_datetime(df['ts_utc'])
    
    # S'assurer que les colonnes OHLC sont numériques
    for col in ['open', 'high', 'low', 'close', 'volume', 'spread']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Trier par timestamp
    df = df.sort_values('ts_utc').reset_index(drop=True)
    
    print(f"✅ {len(df):,} lignes chargées")
    print(f"   Période : {df['ts_utc'].min()} → {df['ts_utc'].max()}")
    print()
    
    return df

def detect_candlestick_patterns(df):
    """Détecte les patterns de chandeliers"""
    print("🕯️  Détection patterns chandeliers...")
    
    events = []
    
    # Calculer body, upper shadow, lower shadow
    df['body'] = abs(df['close'] - df['open'])
    df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
    df['range'] = df['high'] - df['low']
    
    # Body ratio pour normalisation
    df['body_ratio'] = df['body'] / (df['range'] + 1e-10)
    
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        
        # 1. BULLISH ENGULFING
        if (prev['close'] < prev['open'] and  # Candle précédent bearish
            curr['close'] > curr['open'] and  # Candle actuel bullish
            curr['open'] < prev['close'] and    # Gap down
            curr['close'] > prev['open']):      # Engulfing complet
            intensity = (curr['body'] - prev['body']) / (prev['range'] + 1e-10)
            events.append({
                'ts_utc': curr['ts_utc'],
                'event_key': 'bullish_engulfing',
                'family': 'Candlestick',
                'is_active': 1,
                'intensity': intensity
            })
        
        # 2. BEARISH ENGULFING
        if (prev['close'] > prev['open'] and  # Candle précédent bullish
            curr['close'] < curr['open'] and  # Candle actuel bearish
            curr['open'] > prev['close'] and   # Gap up
            curr['close'] < prev['open']):      # Engulfing complet
            intensity = (curr['body'] - prev['body']) / (prev['range'] + 1e-10)
            events.append({
                'ts_utc': curr['ts_utc'],
                'event_key': 'bearish_engulfing',
                'family': 'Candlestick',
                'is_active': 1,
                'intensity': intensity
            })
        
        # 3. PIN BAR BULL (long lower shadow, small body)
        if (curr['lower_shadow'] > 2 * curr['body'] and
            curr['lower_shadow'] > curr['upper_shadow'] * 2 and
            curr['close'] > curr['open']):  # Bullish body
            intensity = curr['lower_shadow'] / (curr['range'] + 1e-10)
            events.append({
                'ts_utc': curr['ts_utc'],
                'event_key': 'pin_bar_bull',
                'family': 'Candlestick',
                'is_active': 1,
                'intensity': intensity
            })
        
        # 4. PIN BAR BEAR (long upper shadow, small body)
        if (curr['upper_shadow'] > 2 * curr['body'] and
            curr['upper_shadow'] > curr['lower_shadow'] * 2 and
            curr['close'] < curr['open']):  # Bearish body
            intensity = curr['upper_shadow'] / (curr['range'] + 1e-10)
            events.append({
                'ts_utc': curr['ts_utc'],
                'event_key': 'pin_bar_bear',
                'family': 'Candlestick',
                'is_active': 1,
                'intensity': intensity
            })
        
        # 5. DOJI (body très petit par rapport au range)
        if (curr['body_ratio'] < 0.1 and  # Body < 10% du range
            curr['range'] > 0):  # Range significatif
            intensity = 1.0 - curr['body_ratio']  # Plus le body est petit, plus intense
            events.append({
                'ts_utc': curr['ts_utc'],
                'event_key': 'doji',
                'family': 'Candlestick',
                'is_active': 1,
                'intensity': intensity
            })
        
        # 6. INSIDE BAR BREAK UP
        if (i >= 1 and
            curr['high'] < prev['high'] and
            curr['low'] > prev['low']):  # Inside bar
            # Chercher break up dans les 5 minutes suivantes
            for j in range(i+1, min(i+6, len(df))):
                future = df.iloc[j]
                if future['close'] > prev['high']:  # Break up
                    intensity = (future['close'] - prev['high']) / (prev['range'] + 1e-10)
                    events.append({
                        'ts_utc': future['ts_utc'],
                        'event_key': 'inside_bar_break_up',
                        'family': 'Candlestick',
                        'is_active': 1,
                        'intensity': intensity
                    })
                    break
        
        # 7. INSIDE BAR BREAK DOWN
        if (i >= 1 and
            curr['high'] < prev['high'] and
            curr['low'] > prev['low']):  # Inside bar
            # Chercher break down dans les 5 minutes suivantes
            for j in range(i+1, min(i+6, len(df))):
                future = df.iloc[j]
                if future['close'] < prev['low']:  # Break down
                    intensity = (prev['low'] - future['close']) / (prev['range'] + 1e-10)
                    events.append({
                        'ts_utc': future['ts_utc'],
                        'event_key': 'inside_bar_break_down',
                        'family': 'Candlestick',
                        'is_active': 1,
                        'intensity': intensity
                    })
                    break
    
    print(f"   ✅ {len(events)} événements chandeliers détectés")
    return events

def detect_momentum_reversal(df):
    """Détecte micro-momentum et reversals"""
    print("📈 Détection momentum/reversal...")
    
    events = []
    
    # Calculer returns
    df['return_1m'] = df['close'].pct_change()
    
    # Returns sur fenêtres glissantes (pas de look-ahead)
    df['return_5m'] = df['close'].pct_change(5)
    df['return_15m'] = df['close'].pct_change(15)
    
    # Calculer z-scores pour returns (fenêtre roulante 100 périodes)
    window = 100
    for col in ['return_5m', 'return_15m']:
        mean_col = f'{col}_mean'
        std_col = f'{col}_std'
        z_col = f'{col}_z'
        
        df[mean_col] = df[col].rolling(window=window, min_periods=20).mean()
        df[std_col] = df[col].rolling(window=window, min_periods=20).std()
        df[z_col] = (df[col] - df[mean_col]) / (df[std_col] + 1e-10)
    
    # Détecter return_5m_pos (z > 1)
    mask_5m_pos = (df['return_5m_z'] > 1) & (df['return_5m'] > 0)
    for idx in df[mask_5m_pos].index:
        events.append({
            'ts_utc': df.iloc[idx]['ts_utc'],
            'event_key': 'return_5m_pos',
            'family': 'Momentum',
            'is_active': 1,
            'intensity': df.iloc[idx]['return_5m_z']
        })
    
    # Détecter return_5m_neg (z < -1)
    mask_5m_neg = (df['return_5m_z'] < -1) & (df['return_5m'] < 0)
    for idx in df[mask_5m_neg].index:
        events.append({
            'ts_utc': df.iloc[idx]['ts_utc'],
            'event_key': 'return_5m_neg',
            'family': 'Momentum',
            'is_active': 1,
            'intensity': abs(df.iloc[idx]['return_5m_z'])
        })
    
    # Détecter return_15m_pos (z > 1)
    mask_15m_pos = (df['return_15m_z'] > 1) & (df['return_15m'] > 0)
    for idx in df[mask_15m_pos].index:
        events.append({
            'ts_utc': df.iloc[idx]['ts_utc'],
            'event_key': 'return_15m_pos',
            'family': 'Momentum',
            'is_active': 1,
            'intensity': df.iloc[idx]['return_15m_z']
        })
    
    # Détecter return_15m_neg (z < -1)
    mask_15m_neg = (df['return_15m_z'] < -1) & (df['return_15m'] < 0)
    for idx in df[mask_15m_neg].index:
        events.append({
            'ts_utc': df.iloc[idx]['ts_utc'],
            'event_key': 'return_15m_neg',
            'family': 'Momentum',
            'is_active': 1,
            'intensity': abs(df.iloc[idx]['return_15m_z'])
        })
    
    print(f"   ✅ {len(events)} événements momentum détectés")
    return events

def detect_volatility_squeeze(df):
    """Détecte volatilité / squeeze (ATR)"""
    print("📊 Détection volatilité (ATR)...")
    
    events = []
    
    # Calculer True Range
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['close'].shift(1))
    df['tr3'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    # ATR sur 20 périodes (pas de look-ahead)
    df['atr_20m'] = df['tr'].rolling(window=20, min_periods=10).mean()
    
    # Calculer z-score ATR (fenêtre roulante 100 périodes)
    window = 100
    df['atr_mean'] = df['atr_20m'].rolling(window=window, min_periods=20).mean()
    df['atr_std'] = df['atr_20m'].rolling(window=window, min_periods=20).std()
    df['atr_z'] = (df['atr_20m'] - df['atr_mean']) / (df['atr_std'] + 1e-10)
    
    # ATR HIGH (z > 1)
    mask_atr_high = df['atr_z'] > 1
    for idx in df[mask_atr_high].index:
        events.append({
            'ts_utc': df.iloc[idx]['ts_utc'],
            'event_key': 'atr_20m_high',
            'family': 'Volatility',
            'is_active': 1,
            'intensity': df.iloc[idx]['atr_z']
        })
    
    # ATR LOW (z < -1)
    mask_atr_low = df['atr_z'] < -1
    for idx in df[mask_atr_low].index:
        events.append({
            'ts_utc': df.iloc[idx]['ts_utc'],
            'event_key': 'atr_20m_low',
            'family': 'Volatility',
            'is_active': 1,
            'intensity': abs(df.iloc[idx]['atr_z'])
        })
    
    print(f"   ✅ {len(events)} événements volatilité détectés")
    return events

def detect_spread_stress(df):
    """Détecte spread stress"""
    print("💹 Détection spread stress...")
    
    events = []
    
    # Calculer z-score spread (fenêtre roulante 100 périodes)
    window = 100
    df['spread_mean'] = df['spread'].rolling(window=window, min_periods=20).mean()
    df['spread_std'] = df['spread'].rolling(window=window, min_periods=20).std()
    df['spread_z'] = (df['spread'] - df['spread_mean']) / (df['spread_std'] + 1e-10)
    
    # SPREAD SPIKE (z > 2)
    mask_spread_spike = df['spread_z'] > 2
    for idx in df[mask_spread_spike].index:
        events.append({
            'ts_utc': df.iloc[idx]['ts_utc'],
            'event_key': 'spread_spike',
            'family': 'Spread',
            'is_active': 1,
            'intensity': df.iloc[idx]['spread_z']
        })
    
    print(f"   ✅ {len(events)} événements spread détectés")
    return events

def main():
    print("="*80)
    print("GÉNÉRATION ÉVÉNEMENTS TECHNIQUES M1")
    print("="*80)
    print()
    
    # Charger données OHLC
    df = load_ohlc_data()
    
    # Détecter tous les événements
    all_events = []
    
    # 1. Patterns chandeliers
    all_events.extend(detect_candlestick_patterns(df))
    
    # 2. Momentum/reversal
    all_events.extend(detect_momentum_reversal(df))
    
    # 3. Volatilité
    all_events.extend(detect_volatility_squeeze(df))
    
    # 4. Spread stress
    all_events.extend(detect_spread_stress(df))
    
    # Créer DataFrame
    if len(all_events) == 0:
        print("⚠️  Aucun événement détecté")
        return
    
    df_events = pd.DataFrame(all_events)
    
    # Trier par timestamp
    df_events = df_events.sort_values('ts_utc').reset_index(drop=True)
    
    # Formater ts_utc en ISO 8601 UTC
    df_events['ts_utc'] = pd.to_datetime(df_events['ts_utc']).dt.strftime('%Y-%m-%d %H:%M:%S+00:00')
    
    # S'assurer que is_active est int
    df_events['is_active'] = df_events['is_active'].astype(int)
    
    # Sauvegarder
    df_events.to_csv(OUTPUT_FILE, index=False)
    
    print()
    print("="*80)
    print("✅ EXPORT TERMINÉ")
    print("="*80)
    print()
    print(f"📁 Fichier généré : {OUTPUT_FILE}")
    print(f"   Total : {len(df_events):,} événements")
    print()
    
    # Statistiques par famille
    print("📊 Répartition par famille :")
    for family, count in df_events['family'].value_counts().items():
        print(f"   {family}: {count:,}")
    print()
    
    # Statistiques par event_key
    print("📋 Top 10 event_keys :")
    for event_key, count in df_events['event_key'].value_counts().head(10).items():
        print(f"   {event_key}: {count:,}")
    print()
    
    # Aperçu
    print("📋 Aperçu (5 premières lignes) :")
    print(df_events.head().to_string(index=False))
    print()
    
    # Vérifier intensité
    print(f"📈 Intensité moyenne : {df_events['intensity'].mean():.3f}")
    print(f"   Intensité min : {df_events['intensity'].min():.3f}")
    print(f"   Intensité max : {df_events['intensity'].max():.3f}")
    print()

if __name__ == '__main__':
    main()


