"""
MODULE CALCUL AMPLIFICATION DYNAMIQUE - SESSION 110
===================================================

Formule validée Cluster #3 (CPI) : +39.6% amélioration sur 17 dates
- Baseline : 2.5374 (cas référence 11.09.2025)
- Métrique : duration_hours depuis inversion
- Formule : amp = 2.5374 + (0.0187 × duration_hours - 1.8346)

Auteur : André Valentin
Date : 3 novembre 2025
Version : 2.7
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from scipy.stats import linregress

# =============================================================================
# CONSTANTES VALIDÉES SESSION 110
# =============================================================================

BASELINE_REFERENCE = 2.5374  # 11.09.2025 cas de référence Cluster #3
ECART_SLOPE = 0.0166         # Session 110 formule ecarts_combined
ECART_INTERCEPT = -0.9878    # Session 110 formule ecarts_combined

# Paramètres détection inversion (Session 107)
LOOKBACK_DAYS = 14
SEGMENT_HOURS = 12
MIN_R2_FOR_TREND = 0.3
MIN_HOURS_BEFORE_EVENT = 24


# =============================================================================
# CHARGEMENT BASE DE DONNÉES CLUSTERS
# =============================================================================

def load_clusters_database():
    """
    Charge base de données clusters depuis JSON
    
    Returns:
        dict: Base de données complète
    """
    db_path = Path(__file__).parent.parent / "data" / "clusters_database.json"
    
    if not db_path.exists():
        raise FileNotFoundError(f"Base de données clusters introuvable : {db_path}")
    
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def identify_cluster_from_events(events):
    """
    Identifie cluster selon composition événements
    
    Args:
        events: Liste dictionnaires événements avec clé 'event'
    
    Returns:
        dict ou None: Informations cluster si identifié
    """
    db = load_clusters_database()
    
    # Extraire noms événements (gérer None)
    event_names = [str(e.get('event', '') or '') for e in events]
    event_names_lower = [name.lower() for name in event_names if name]
    
    # Tester chaque cluster
    for cluster_key, cluster_info in db['clusters'].items():
        cluster_composition = cluster_info['composition']
        
        # Vérifier si composition correspond
        match = False
        
        # Cluster #3 : CPI présent
        if cluster_info['id'] == 3:
            match = any('cpi' in name.lower() for name in event_names_lower)
        
        # Cluster #1 : Vérifier présence événements clés
        elif cluster_info['id'] == 1:
            has_manufacturing = any('manufacturing' in name.lower() or 'ism' in name.lower() 
                                   for name in event_names_lower)
            has_consumer = any('retail' in name.lower() or 'sales' in name.lower() 
                              for name in event_names_lower)
            has_employment = any('unemployment' in name.lower() or 'jobless' in name.lower() 
                                for name in event_names_lower)
            
            # Match si au moins 2/3 événements présents
            match = sum([has_manufacturing, has_consumer, has_employment]) >= 2
        
        if match:
            return cluster_info
    
    return None


# =============================================================================
# DÉTECTION INVERSION DE TENDANCE (SESSION 107)
# =============================================================================

def detect_trend_by_inversion_S107(prices_df, event_time, lookback_days=14,
                                    segment_hours=12, min_r2_for_trend=0.3,
                                    min_hours_before_event=24):
    """
    Detecte derniere inversion de tendance avant evenement
    Methode validee Session 107
    
    DEBUG SESSION 110 : Logs actifs
    
    Args:
        prices_df: DataFrame prix avec colonnes ['datetime', 'close']
        event_time: datetime evenement (timezone aware)
        lookback_days: Periode analyse en jours
        segment_hours: Duree segments pour regression
        min_r2_for_trend: R2 minimum pour valider tendance
        min_hours_before_event: Heures minimum avant evenement
    
    Returns:
        dict ou None: Informations inversion si detectee
    """
    print(f"\n🔍 detect_trend_by_inversion_S107 appelée")
    print(f"  Event time: {event_time}")
    print(f"  Lookback: {lookback_days} jours")
    print(f"  Segment: {segment_hours}h")
    print(f"  Min R²: {min_r2_for_trend}")
    print(f"  Min hours before: {min_hours_before_event}h")
    # Filtrer période lookback
    start_time = event_time - timedelta(days=lookback_days)
    df = prices_df[
        (prices_df['datetime'] >= start_time) & 
        (prices_df['datetime'] < event_time)
    ].copy()
    
    if len(df) < 100:  # Minimum 100 bougies
        print(f"  ❌ Pas assez de bougies: {len(df)} < 100")
        return None
    
    print(f"  ✅ Bougies trouvées: {len(df)}")
    
    # Ajouter colonne secondes
    df['seconds'] = (df['datetime'] - df['datetime'].iloc[0]).dt.total_seconds()
    
    # Découper en segments
    segment_seconds = segment_hours * 3600
    df['segment'] = (df['seconds'] / segment_seconds).astype(int)
    
    segments_info = []
    
    # Analyser chaque segment
    for seg_id in df['segment'].unique():
        seg_data = df[df['segment'] == seg_id]
        
        if len(seg_data) < 10:
            continue
        
        # Régression linéaire
        X = seg_data['seconds'].values
        y = seg_data['close'].values
        
        try:
            slope, intercept, r_value, p_value, std_err = linregress(X, y)
            r2 = r_value ** 2
            
            segments_info.append({
                'segment_id': seg_id,
                'start_time': seg_data['datetime'].iloc[0],
                'end_time': seg_data['datetime'].iloc[-1],
                'slope': slope,
                'r2': r2,
                'direction': 'UP' if slope > 0 else 'DOWN',
                'n_points': len(seg_data)
            })
        except:
            continue
    
    print(f"  Segments analysés: {len(segments_info)}")
    
    if len(segments_info) < 2:
        print(f"  ❌ Pas assez de segments: {len(segments_info)} < 2")
        return None
    
    # Chercher inversions (UP→DOWN = PEAK, DOWN→UP = TROUGH)
    inversions = []
    
    for i in range(len(segments_info) - 1):
        seg_current = segments_info[i]
        seg_next = segments_info[i + 1]
        
        # Vérifier R² suffisants
        if seg_current['r2'] < min_r2_for_trend or seg_next['r2'] < min_r2_for_trend:
            continue
        
        # Détecter inversion
        if seg_current['direction'] != seg_next['direction']:
            inversion_time = seg_next['start_time']
            hours_before = (event_time - inversion_time).total_seconds() / 3600
            
            if hours_before < min_hours_before_event:
                continue
            
            reversal_type = f"{seg_current['direction']}→{seg_next['direction']}"
            
            inversions.append({
                'inversion_time': inversion_time,
                'hours_before_event': hours_before,
                'reversal_type': reversal_type,
                'r2_before': seg_current['r2'],
                'r2_after': seg_next['r2'],
                'quality_score': (seg_current['r2'] + seg_next['r2']) / 2
            })
    
    print(f"  Inversions trouvées: {len(inversions)}")
    
    if not inversions:
        print(f"  ❌ Aucune inversion valide")
        return None
    
    # Retourner inversion la plus proche de l'événement
    inversions_sorted = sorted(inversions, key=lambda x: x['hours_before_event'])
    return inversions_sorted[0]


# =============================================================================
# CALCUL AMPLIFICATION PRINCIPALE
# =============================================================================

def calculate_amplification(events, event_time, db_path):
    """
    Calcule facteur amplification selon algorithme V2.7
    
    DEBUG SESSION 110 : Logs actifs
    
    ALGORITHME :
    1. Identifier cluster evenement
    2. Charger baseline cluster
    3. Tenter detection inversion
    4. Calculer amplification :
       - Si inversion + Cluster #3 : Formule dynamique
       - Sinon : Baseline cluster
    
    Args:
        events: Liste evenements
        event_time: datetime evenement (timezone aware)
        db_path: Path vers base DuckDB prix
    
    Returns:
        dict: Resultat calcul avec metadonnees
    """
    print(f"\n🔍 calculate_amplification appelée")
    print(f"  Event time: {event_time}")
    print(f"  DB path: {db_path}")
    print(f"  Nombre events: {len(events)}")
    print(f"  Events: {[e.get('event', 'N/A') for e in events][:3]}...")  # 3 premiers
    # ÉTAPE 1 : Identifier cluster
    cluster_info = identify_cluster_from_events(events)
    
    if cluster_info is None:
        return {
            'amplification': 2.5,
            'method': 'unknown_cluster_fallback',
            'cluster_id': None,
            'cluster_name': 'Inconnu',
            'cluster_baseline': 2.5,
            'inversion_detected': False,
            'duration_hours': None,
            'ecart_calculated': None,
            'warning': 'Composition événement inconnue - baseline conservatrice'
        }
    
    # ÉTAPE 2 : Baseline cluster
    cluster_baseline = cluster_info['statistics']['mean_amp']
    
    # ÉTAPE 3 : Tenter détection inversion
    inversion = None
    
    try:
        # Charger prix
        import duckdb
        conn = duckdb.connect(str(db_path))
        
        # Query prix (méthode Session 106)
        query_start = event_time - timedelta(days=LOOKBACK_DAYS)
        query_end = event_time
        
        query = f"""
        SELECT 
            datetime,
            open,
            high,
            low,
            close
        FROM prices_1m
        WHERE datetime >= '{query_start.isoformat()}'
          AND datetime < '{query_end.isoformat()}'
        ORDER BY datetime
        """
        
        prices_df = conn.execute(query).df()
        conn.close()
        
        # 🔍 DEBUG SESSION 110
        print(f"\n🔍 DEBUG AMPLIFICATION:")
        print(f"  Query start: {query_start.isoformat()}")
        print(f"  Query end: {query_end.isoformat()}")
        print(f"  Prices loaded: {len(prices_df)} rows")
        if len(prices_df) > 0:
            print(f"  First timestamp: {prices_df['datetime'].iloc[0]}")
            print(f"  Last timestamp: {prices_df['datetime'].iloc[-1]}")
        
        # Convertir timezone - CORRECTION SESSION 110
        # Les timestamps DB sont DÉJÀ en +02:00 (Session 106)
        prices_df['datetime'] = pd.to_datetime(prices_df['datetime'])
        
        # Si pas de timezone, ajouter +02:00
        if prices_df['datetime'].dt.tz is None:
            prices_df['datetime'] = prices_df['datetime'].dt.tz_localize('Europe/Zurich')
        
        print(f"  After timezone: {prices_df['datetime'].iloc[0] if len(prices_df) > 0 else 'N/A'}")
        
        # Détecter inversion
        if len(prices_df) >= 100:
            print(f"  ✅ Assez de données ({len(prices_df)} >= 100), lancement détection...")
            inversion = detect_trend_by_inversion_S107(
                prices_df=prices_df,
                event_time=event_time,
                lookback_days=LOOKBACK_DAYS,
                segment_hours=SEGMENT_HOURS,
                min_r2_for_trend=MIN_R2_FOR_TREND,
                min_hours_before_event=MIN_HOURS_BEFORE_EVENT
            )
            if inversion:
                print(f"  ✅ INVERSION DÉTECTÉE !")
                print(f"     Type: {inversion['reversal_type']}")
                print(f"     Durée: {inversion['hours_before_event']:.1f}h")
                print(f"     Qualité: {inversion['quality_score']:.3f}")
            else:
                print(f"  ❌ Aucune inversion détectée")
        else:
            print(f"  ❌ Pas assez de données ({len(prices_df)} < 100)")
    except Exception as e:
        # Erreur chargement prix ou détection
        print(f"  ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        inversion = None
    
    # ÉTAPE 4 : Calculer amplification
    if inversion and cluster_info['id'] == 3:
        # CLUSTER #3 avec inversion : Formule dynamique Session 110
        duration_hours = inversion['hours_before_event']
        ecart = ECART_SLOPE * duration_hours + ECART_INTERCEPT
        amplification = BASELINE_REFERENCE + ecart
        
        # Limites sécurité
        amplification = max(0.5, min(amplification, 5.0))
        
        method = 'dynamic_with_trend_c3'
        
    elif inversion and cluster_info['id'] == 1:
        # CLUSTER #1 avec inversion : Formule non calibrée
        # → Utiliser baseline cluster en attendant calibration
        amplification = cluster_baseline
        ecart = None
        method = 'cluster_baseline_c1_pending_calibration'
        
    else:
        # Pas d'inversion : Baseline cluster
        amplification = cluster_baseline
        ecart = None
        method = 'cluster_baseline'
    
    return {
        'amplification': amplification,
        'method': method,
        'cluster_id': cluster_info['id'],
        'cluster_name': cluster_info['name'],
        'cluster_baseline': cluster_baseline,
        'inversion_detected': bool(inversion),
        'duration_hours': inversion['hours_before_event'] if inversion else None,
        'ecart_calculated': ecart,
        'reversal_type': inversion['reversal_type'] if inversion else None,
        'quality_score': inversion['quality_score'] if inversion else None
    }


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_cluster_statistics(cluster_id):
    """Retourne statistiques d'un cluster"""
    db = load_clusters_database()
    
    for cluster_key, cluster_info in db['clusters'].items():
        if cluster_info['id'] == cluster_id:
            return cluster_info['statistics']
    
    return None


def list_available_clusters():
    """Liste tous les clusters disponibles"""
    db = load_clusters_database()
    
    clusters = []
    for cluster_key, cluster_info in db['clusters'].items():
        clusters.append({
            'id': cluster_info['id'],
            'name': cluster_info['name'],
            'composition': cluster_info['composition'],
            'n_dates': cluster_info['statistics']['n_dates']
        })
    
    return clusters
