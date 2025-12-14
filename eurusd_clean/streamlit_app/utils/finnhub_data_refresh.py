"""
Fonction Streamlit pour Import Automatique des Données Finnhub
===============================================================

Utilise les scripts existants pour mettre à jour prix et événements.
Peut être utilisé dans les pages Streamlit avec indicateur de progression.

Date : 2025-12-07
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import subprocess
import duckdb
import pandas as pd

# Ajouter chemins au path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Charger .env si disponible
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')
except:
    pass

# S'assurer que la clé API est dans l'environnement
if not os.environ.get('FINNHUB_API_KEY'):
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                if key.strip() == 'FINNHUB_API_KEY':
                    os.environ[key.strip()] = value.strip()
                    break

DB_PATH = Path('../fx_impact_app/data/warehouse.duckdb')


def check_price_freshness() -> Tuple[Optional[datetime], Optional[float]]:
    """
    Vérifie la fraîcheur des prix
    
    Returns:
        (dernière_date, age_heures) ou (None, None) si pas de données
    """
    if not DB_PATH.exists():
        return None, None
    
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Vérifier dernière date dans prices_1m_v
        result = conn.execute("SELECT MAX(ts_utc) FROM prices_1m_v").fetchone()
        conn.close()
        
        if result and result[0]:
            last_date = result[0]
            if isinstance(last_date, pd.Timestamp):
                last_date = last_date.to_pydatetime()
            
            age_hours = (datetime.now() - last_date.replace(tzinfo=None)).total_seconds() / 3600
            return last_date, age_hours
        
        return None, None
    except Exception:
        return None, None


def check_events_freshness() -> Tuple[Optional[datetime], Optional[float]]:
    """
    Vérifie la fraîcheur des événements (dernier événement futur)
    
    Returns:
        (dernier_événement_futur, jours_avant_premier) ou (None, None)
    """
    if not DB_PATH.exists():
        return None, None
    
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Trouver dernier événement futur
        result = conn.execute("""
            SELECT MAX(ts_utc) 
            FROM events 
            WHERE ts_utc >= CURRENT_TIMESTAMP
        """).fetchone()
        conn.close()
        
        if result and result[0]:
            last_future_event = result[0]
            if isinstance(last_future_event, pd.Timestamp):
                last_future_event = last_future_event.to_pydatetime()
            
            days_ahead = (last_future_event.replace(tzinfo=None) - datetime.now()).days
            return last_future_event, days_ahead
        
        return None, None
    except Exception:
        return None, None


def refresh_prices(progress_callback=None) -> Dict:
    """
    Met à jour les prix Finnhub jusqu'à aujourd'hui
    
    Args:
        progress_callback: Fonction callback(progress: float, message: str)
    
    Returns:
        dict avec 'success', 'message', 'prices_added', etc.
    """
    script_path = PROJECT_ROOT / 'scripts' / 'update_finnhub_prices_to_today.py'
    
    if not script_path.exists():
        return {
            'success': False,
            'message': f"Script introuvable : {script_path}",
            'prices_added': 0
        }
    
    # Vérifier clé API
    if not os.environ.get('FINNHUB_API_KEY'):
        return {
            'success': False,
            'message': "FINNHUB_API_KEY non trouvée dans l'environnement",
            'prices_added': 0
        }
    
    if progress_callback:
        progress_callback(0.1, "Vérification dernière date...")
    
    # Lancer script avec confirmation automatique
    try:
        if progress_callback:
            progress_callback(0.2, "Lancement import des prix...")
        
        completed = subprocess.run(
            ['python3', str(script_path)],
            input='oui\n',  # Confirmation automatique
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=1800,  # 30 minutes max
            env=os.environ.copy()
        )
        
        if completed.returncode == 0:
            # Parser sortie pour extraire nombre de chandeliers
            output = completed.stdout
            prices_added = 0
            
            # Chercher dans la sortie
            for line in output.split('\n'):
                if 'chandeliers insérés' in line.lower() or 'lignes insérées' in line.lower():
                    # Extraire nombre
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        prices_added = int(match.group(1))
            
            if progress_callback:
                progress_callback(1.0, f"✅ {prices_added:,} chandeliers ajoutés")
            
            return {
                'success': True,
                'message': f"Prix mis à jour : {prices_added:,} chandeliers ajoutés",
                'prices_added': prices_added,
                'output': output[-500:]  # Derniers 500 caractères
            }
        else:
            error_msg = completed.stderr[-500:] if completed.stderr else completed.stdout[-500:]
            return {
                'success': False,
                'message': f"Erreur lors de l'import : {error_msg}",
                'prices_added': 0
            }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': "Timeout : L'import a pris trop de temps (> 30 min)",
            'prices_added': 0
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Erreur : {str(e)}",
            'prices_added': 0
        }


def refresh_events(progress_callback=None) -> Dict:
    """
    Met à jour les événements Finnhub (7 jours passés → 30 jours futurs)
    
    Args:
        progress_callback: Fonction callback(progress: float, message: str)
    
    Returns:
        dict avec 'success', 'message', 'events_added', etc.
    """
    script_path = PROJECT_ROOT / 'scripts' / 'finnhub_import.py'
    
    if not script_path.exists():
        return {
            'success': False,
            'message': f"Script introuvable : {script_path}",
            'events_added': 0
        }
    
    # Vérifier clé API
    if not os.environ.get('FINNHUB_API_KEY'):
        return {
            'success': False,
            'message': "FINNHUB_API_KEY non trouvée dans l'environnement",
            'events_added': 0
        }
    
    # Calculer période
    from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    to_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    if progress_callback:
        progress_callback(0.1, f"Import événements {from_date} → {to_date}...")
    
    # Importer directement la fonction plutôt que subprocess pour meilleur contrôle
    try:
        sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
        sys.path.insert(0, str(PROJECT_ROOT / 'src'))
        
        from finnhub_import import import_finnhub_events
        from src.config import DB_PATH as config_db_path
        
        if progress_callback:
            progress_callback(0.3, "Récupération depuis Finnhub API...")
        
        import_finnhub_events(
            db_path=config_db_path,
            from_date=from_date,
            to_date=to_date,
            countries=None,
            replace=False
        )
        
        # Compter événements ajoutés
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        count = conn.execute(f"""
            SELECT COUNT(*) 
            FROM events 
            WHERE DATE(ts_utc) >= '{from_date}' AND DATE(ts_utc) <= '{to_date}'
        """).fetchone()[0]
        conn.close()
        
        if progress_callback:
            progress_callback(1.0, f"✅ {count:,} événements disponibles")
        
        return {
            'success': True,
            'message': f"Événements mis à jour : {count:,} événements pour la période",
            'events_count': count,
            'from_date': from_date,
            'to_date': to_date
        }
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()[-500:]
        return {
            'success': False,
            'message': f"Erreur : {str(e)}",
            'error_detail': error_detail,
            'events_added': 0
        }


def refresh_all_data(progress_callback=None) -> Dict:
    """
    Met à jour prix ET événements
    
    Args:
        progress_callback: Fonction callback(progress: float, message: str)
    
    Returns:
        dict avec résultats combinés
    """
    results = {
        'prices': None,
        'events': None,
        'success': False
    }
    
    # 1. Prix (0-50%)
    if progress_callback:
        progress_callback(0.0, "Mise à jour des prix...")
    
    prices_result = refresh_prices(
        progress_callback=lambda p, m: progress_callback(p * 0.5, m) if progress_callback else None
    )
    results['prices'] = prices_result
    
    # 2. Événements (50-100%)
    if progress_callback:
        progress_callback(0.5, "Mise à jour des événements...")
    
    events_result = refresh_events(
        progress_callback=lambda p, m: progress_callback(0.5 + p * 0.5, m) if progress_callback else None
    )
    results['events'] = events_result
    
    results['success'] = prices_result.get('success', False) and events_result.get('success', False)
    
    if progress_callback:
        if results['success']:
            progress_callback(1.0, "✅ Mise à jour complète terminée")
        else:
            progress_callback(1.0, "⚠️ Mise à jour terminée avec erreurs")
    
    return results


