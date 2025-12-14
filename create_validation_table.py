"""
Script pour créer la table validation_events dans warehouse.duckdb

Cette table stocke les événements de référence pour validation des formules.
Une fois renseignés, ces événements servent à tester toutes les formules existantes
et futures sans devoir les re-saisir à chaque fois.

Structure :
- Données événement (date, famille, pays, surprise)
- Données prédiction (predicted_pips, direction, latency, ttr)
- Métadonnées (source, notes, created_at)
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from datetime import datetime

# Ajouter fx_impact_app/src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))
from config import get_db_path


def create_validation_events_table():
    """Crée la table validation_events si elle n'existe pas"""
    
    conn = duckdb.connect(get_db_path())
    
    # Créer la table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS validation_events (
        -- Identifiant unique
        id INTEGER PRIMARY KEY,
        
        -- Données événement
        event_date DATE NOT NULL,
        event_time TIME NOT NULL,
        event_datetime TIMESTAMP NOT NULL,
        event_key VARCHAR NOT NULL,
        family VARCHAR NOT NULL,
        country VARCHAR NOT NULL,
        
        -- Données économiques
        actual DOUBLE,
        forecast DOUBLE,
        estimate DOUBLE,
        previous DOUBLE,
        surprise DOUBLE,  -- actual - forecast
        surprise_pct DOUBLE,  -- (actual - forecast) / forecast * 100
        
        -- Prédiction impact (à renseigner manuellement)
        predicted_pips DOUBLE NOT NULL,
        direction INTEGER NOT NULL,  -- +1 (UP) ou -1 (DOWN)
        latency_median DOUBLE,  -- Minutes
        ttr_median DOUBLE,  -- Minutes
        empirical_score DOUBLE,
        
        -- Métadonnées
        source VARCHAR DEFAULT 'manual',  -- 'manual', 'planificateur', etc.
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Contraintes
        UNIQUE(event_datetime, event_key, country)
    )
    """
    
    conn.execute(create_table_sql)
    
    # Créer index pour recherches rapides
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_validation_events_date 
        ON validation_events(event_date)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_validation_events_datetime 
        ON validation_events(event_datetime)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_validation_events_family 
        ON validation_events(family)
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Table validation_events créée avec succès")
    print("✅ Index créés")


def insert_validation_event(
    event_datetime: str,
    event_key: str,
    family: str,
    country: str,
    actual: float = None,
    forecast: float = None,
    estimate: float = None,
    previous: float = None,
    predicted_pips: float = 0.0,
    direction: int = 1,
    latency_median: float = 5.0,
    ttr_median: float = 10.0,
    empirical_score: float = None,
    source: str = 'manual',
    notes: str = None
):
    """
    Insère un événement de validation dans la DB
    
    Args:
        event_datetime: Format 'YYYY-MM-DD HH:MM:SS' (UTC)
        event_key: Nom de l'événement
        family: Famille de l'événement
        country: Code pays (US, DE, etc.)
        actual: Valeur réelle
        forecast: Valeur prévue
        estimate: Valeur estimée (souvent = forecast)
        previous: Valeur précédente
        predicted_pips: Impact prédit en pips
        direction: +1 (UP) ou -1 (DOWN)
        latency_median: Latence médiane en minutes
        ttr_median: TTR médian en minutes
        empirical_score: Score empirique (0-100)
        source: Source des données ('manual', 'planificateur', etc.)
        notes: Notes additionnelles
    """
    
    conn = duckdb.connect(get_db_path())
    
    # Calculer surprise et surprise_pct
    surprise = None
    surprise_pct = None
    if actual is not None and forecast is not None:
        surprise = actual - forecast
        if forecast != 0:
            surprise_pct = (surprise / forecast) * 100
    
    # Parser datetime
    dt = pd.to_datetime(event_datetime)
    event_date = dt.date()
    event_time = dt.time()
    
    # Générer ID (max + 1)
    max_id_query = "SELECT COALESCE(MAX(id), 0) as max_id FROM validation_events"
    max_id = conn.execute(max_id_query).fetchone()[0]
    new_id = max_id + 1
    
    # Insérer
    insert_sql = """
    INSERT INTO validation_events (
        id, event_date, event_time, event_datetime,
        event_key, family, country,
        actual, forecast, estimate, previous,
        surprise, surprise_pct,
        predicted_pips, direction,
        latency_median, ttr_median, empirical_score,
        source, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    conn.execute(insert_sql, [
        new_id, event_date, event_time, dt,
        event_key, family, country,
        actual, forecast, estimate, previous,
        surprise, surprise_pct,
        predicted_pips, direction,
        latency_median, ttr_median, empirical_score,
        source, notes
    ])
    
    conn.commit()
    conn.close()
    
    print(f"✅ Événement inséré : ID={new_id}, {event_key} ({family})")
    return new_id


def get_validation_events_for_date(date_str: str):
    """
    Récupère tous les événements de validation pour une date
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
    
    Returns:
        DataFrame avec tous les événements
    """
    conn = duckdb.connect(get_db_path(), read_only=True)
    
    query = """
    SELECT *
    FROM validation_events
    WHERE event_date = ?
    ORDER BY event_datetime
    """
    
    df = conn.execute(query, [date_str]).df()
    conn.close()
    
    return df


def main():
    """Fonction principale"""
    
    print("=" * 70)
    print("🗄️  CRÉATION TABLE VALIDATION_EVENTS")
    print("=" * 70)
    
    # Créer la table
    create_validation_events_table()
    
    print("\n✅ Table prête à recevoir les événements de validation")
    print("\n💡 Prochaines étapes :")
    print("   1. Renseigner événements 11 sept 2025")
    print("   2. Tester les formules avec ces événements")
    print("   3. Comparer les résultats")


if __name__ == "__main__":
    main()
