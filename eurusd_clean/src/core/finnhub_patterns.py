#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finnhub_patterns.py
-------------------
Module pour charger et utiliser les patterns Finnhub dans le Planificateur.
"""
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import pytz

from config import DB_PATH, TIMEZONE_BERN


def load_finnhub_patterns(
    date: datetime,
    db_path: Path = DB_PATH,
    timezone_str: str = TIMEZONE_BERN,
    window_hours: int = 24,
    resolution: Optional[str] = None
) -> pd.DataFrame:
    """
    Charge les patterns Finnhub pour une date donnée.
    
    Parameters
    ----------
    date : datetime
        Date cible
    db_path : Path
        Chemin vers la DB
    timezone_str : str
        Timezone (défaut: Europe/Zurich)
    window_hours : int
        Fenêtre de recherche autour de la date (défaut: 24h)
    resolution : Optional[str]
        Résolution spécifique (M1, M5, M15, M30, H1, D, W, M) ou None pour toutes
    
    Returns
    -------
    pd.DataFrame
        DataFrame avec colonnes: pattern_id, resolution, pattern_name, pattern_type,
        start_time, end_time, start_price, end_price, entry_price, stop_loss,
        profit1, profit2, status, mature
    """
    import duckdb
    
    tz = pytz.timezone(timezone_str)
    
    # Convertir date en UTC pour la requête
    if date.tzinfo is None:
        date_local = tz.localize(date)
    else:
        date_local = date.astimezone(tz)
    
    date_start = date_local - timedelta(hours=window_hours)
    date_end = date_local + timedelta(hours=window_hours)
    
    # Convertir en UTC pour la DB
    date_start_utc = date_start.astimezone(pytz.UTC)
    date_end_utc = date_end.astimezone(pytz.UTC)
    
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Vérifier si la table existe
    try:
        conn.execute("SELECT 1 FROM finnhub_patterns LIMIT 1")
    except:
        conn.close()
        return pd.DataFrame()
    
    # Construire la requête
    query = """
    SELECT 
        pattern_id,
        resolution,
        pattern_name,
        pattern_type,
        start_time,
        end_time,
        start_price,
        end_price,
        entry_price,
        stop_loss,
        profit1,
        profit2,
        status,
        mature
    FROM finnhub_patterns
    WHERE start_time >= ? 
      AND start_time <= ?
    """
    
    params = [date_start_utc.isoformat(), date_end_utc.isoformat()]
    
    if resolution:
        query += " AND resolution = ?"
        params.append(resolution)
    
    query += " ORDER BY start_time"
    
    df = conn.execute(query, params).df()
    conn.close()
    
    if df.empty:
        return df
    
    # Convertir les timestamps en timezone locale
    if 'start_time' in df.columns:
        df['start_time'] = pd.to_datetime(df['start_time'], utc=True).dt.tz_convert(tz)
    if 'end_time' in df.columns:
        df['end_time'] = pd.to_datetime(df['end_time'], utc=True).dt.tz_convert(tz)
    
    return df


def find_patterns_near_time(
    patterns: pd.DataFrame,
    target_time: datetime,
    window_minutes: int = 60
) -> pd.DataFrame:
    """
    Trouve les patterns proches d'une heure cible.
    
    Parameters
    ----------
    patterns : pd.DataFrame
        DataFrame de patterns (résultat de load_finnhub_patterns)
    target_time : datetime
        Heure cible
    window_minutes : int
        Fenêtre de recherche en minutes (défaut: 60)
    
    Returns
    -------
    pd.DataFrame
        Patterns filtrés
    """
    if patterns.empty:
        return patterns
    
    # Normaliser target_time
    if target_time.tzinfo is None:
        target_time = pytz.timezone(TIMEZONE_BERN).localize(target_time)
    
    window_start = target_time - timedelta(minutes=window_minutes)
    window_end = target_time + timedelta(minutes=window_minutes)
    
    mask = (
        (patterns['start_time'] >= window_start) &
        (patterns['start_time'] <= window_end)
    )
    
    return patterns[mask].copy()


def get_pattern_direction(pattern_type: str) -> Optional[str]:
    """
    Extrait la direction (UP/DOWN) d'un pattern Finnhub.
    
    Parameters
    ----------
    pattern_type : str
        Type de pattern (ex: "Bullish", "Bearish", "Reversal", etc.)
    
    Returns
    -------
    Optional[str]
        "UP", "DOWN", ou None
    """
    if not pattern_type:
        return None
    
    pattern_lower = pattern_type.lower()
    
    if 'bull' in pattern_lower or 'up' in pattern_lower:
        return 'UP'
    elif 'bear' in pattern_lower or 'down' in pattern_lower:
        return 'DOWN'
    else:
        return None


def match_finnhub_pattern_to_detection(
    detected_pattern: str,
    finnhub_patterns: pd.DataFrame,
    movement_time: datetime,
    window_minutes: int = 120
) -> Dict:
    """
    Compare un pattern détecté par notre algorithme avec les patterns Finnhub.
    
    Parameters
    ----------
    detected_pattern : str
        Pattern détecté (ex: "DOUBLE_WAVE", "SINGLE_WAVE_FORT_UP")
    finnhub_patterns : pd.DataFrame
        Patterns Finnhub chargés
    movement_time : datetime
        Heure du mouvement détecté
    window_minutes : int
        Fenêtre de recherche (défaut: 120 minutes)
    
    Returns
    -------
    Dict
        {
            'match_found': bool,
            'finnhub_patterns': List[Dict],
            'confidence_boost': float,  # Boost de confiance si match
            'direction_match': bool
        }
    """
    if finnhub_patterns.empty:
        return {
            'match_found': False,
            'finnhub_patterns': [],
            'confidence_boost': 0.0,
            'direction_match': False
        }
    
    # Filtrer patterns proches du mouvement
    patterns_near = find_patterns_near_time(finnhub_patterns, movement_time, window_minutes)
    
    if patterns_near.empty:
        return {
            'match_found': False,
            'finnhub_patterns': [],
            'confidence_boost': 0.0,
            'direction_match': False
        }
    
    # Extraire direction du pattern détecté
    detected_direction = None
    if '_UP' in detected_pattern:
        detected_direction = 'UP'
    elif '_DOWN' in detected_pattern:
        detected_direction = 'DOWN'
    
    # Vérifier correspondance de direction
    direction_matches = []
    for _, row in patterns_near.iterrows():
        finnhub_direction = get_pattern_direction(row.get('pattern_type', ''))
        if finnhub_direction and detected_direction:
            direction_matches.append(finnhub_direction == detected_direction)
        else:
            direction_matches.append(False)
    
    # Calculer boost de confiance
    confidence_boost = 0.0
    if any(direction_matches):
        # Au moins un pattern Finnhub confirme la direction
        confidence_boost = 0.15  # +15% de confiance
    elif len(patterns_near) > 0:
        # Patterns présents mais direction non confirmée
        confidence_boost = 0.05  # +5% de confiance
    
    # Préparer liste de patterns pour retour
    patterns_list = []
    for idx, row in patterns_near.iterrows():
        patterns_list.append({
            'pattern_name': row.get('pattern_name', ''),
            'pattern_type': row.get('pattern_type', ''),
            'resolution': row.get('resolution', ''),
            'start_time': row.get('start_time'),
            'entry_price': row.get('entry_price'),
            'stop_loss': row.get('stop_loss'),
            'profit1': row.get('profit1'),
            'profit2': row.get('profit2'),
            'status': row.get('status', ''),
            'mature': row.get('mature', 0)
        })
    
    return {
        'match_found': len(patterns_near) > 0,
        'finnhub_patterns': patterns_list,
        'confidence_boost': confidence_boost,
        'direction_match': any(direction_matches) if direction_matches else False
    }


