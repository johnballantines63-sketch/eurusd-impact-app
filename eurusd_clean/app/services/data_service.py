"""
DataService - Interface unique d'accès à warehouse.duckdb

Ce service est la SEULE interface pour accéder à la base de données.
Toutes les requêtes SQL doivent passer par ce service.

RÈGLES CRITIQUES:
1. Toujours joindre event_families sur event_key ET country
2. Ne JAMAIS utiliser ef.event_name (n'existe pas!)
3. Utiliser estimate ou previous comme fallback pour forecast
4. Utiliser strftime() pour manipuler timestamps (pas CAST AS TIME)

Usage:
    from app.services import DataService
    
    data_service = DataService()
    events = data_service.get_events(
        start_date='2025-09-01',
        end_date='2025-09-30',
        countries=['US', 'EU']
    )
"""

from __future__ import annotations
import duckdb
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pathlib import Path
from contextlib import contextmanager

from app.config import config


class DataService:
    """
    Service d'accès aux données - Interface unique vers warehouse.duckdb
    
    Ce service encapsule toutes les requêtes SQL et gère la connexion
    à la base de données de manière propre et sécurisée.
    
    Attributes:
        db_path (str): Chemin vers warehouse.duckdb
        connection (duckdb.DuckDBPyConnection): Connexion active (si ouverte)
    
    Examples:
        >>> data_service = DataService()
        >>> 
        >>> # Récupérer événements d'une période
        >>> events = data_service.get_events(
        ...     start_date='2025-09-01',
        ...     end_date='2025-09-30',
        ...     countries=['US']
        ... )
        >>> 
        >>> # Récupérer prix EUR/USD
        >>> prices = data_service.get_prices(
        ...     start_time='2025-09-11 14:00:00',
        ...     end_time='2025-09-11 15:00:00'
        ... )
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialise le DataService.
        
        Args:
            db_path: Chemin vers warehouse.duckdb (optionnel, utilise config si absent)
        """
        self.db_path = db_path or config.get_legacy_db_path()
        self.connection: Optional[duckdb.DuckDBPyConnection] = None
        
        # Valider que DB existe
        db_file = Path(self.db_path)
        if not db_file.exists():
            raise FileNotFoundError(
                f"Base de données introuvable : {self.db_path}\n"
                f"Vérifiez que warehouse.duckdb existe."
            )
        
        # Valider taille
        size_mb = db_file.stat().st_size / (1024 * 1024)
        if size_mb < 100:
            raise ValueError(
                f"Base de données trop petite : {size_mb:.1f} MB\n"
                f"Attendu > 100 MB. Vérifiez l'intégrité de la DB."
            )
    
    # ========================================================================
    # GESTION CONNEXION
    # ========================================================================
    
    @contextmanager
    def get_connection(self):
        """
        Context manager pour obtenir une connexion DB.
        
        La connexion est automatiquement fermée à la fin du bloc.
        
        Yields:
            duckdb.DuckDBPyConnection: Connexion active
            
        Examples:
            >>> data_service = DataService()
            >>> with data_service.get_connection() as conn:
            ...     result = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        """
        conn = duckdb.connect(self.db_path, read_only=True)
        try:
            yield conn
        finally:
            conn.close()
    
    def connect(self) -> duckdb.DuckDBPyConnection:
        """
        Ouvre une connexion persistante.
        
        À utiliser avec précaution - préférer get_connection() en général.
        N'oubliez pas d'appeler close() après usage.
        
        Returns:
            Connexion active
            
        Examples:
            >>> data_service = DataService()
            >>> conn = data_service.connect()
            >>> # ... utiliser conn ...
            >>> data_service.close()
        """
        if self.connection is None:
            self.connection = duckdb.connect(self.db_path, read_only=True)
        return self.connection
    
    def close(self):
        """Ferme la connexion persistante si ouverte."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Support context manager."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support context manager."""
        self.close()
    
    # ========================================================================
    # ÉVÉNEMENTS ÉCONOMIQUES
    # ========================================================================
    
    def get_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        countries: Optional[List[str]] = None,
        min_importance: int = 1,
        with_family: bool = True,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Récupère les événements économiques avec filtres.
        
        ATTENTION : Cette fonction joint correctement event_families sur
        event_key ET country (erreur récurrente évitée).
        
        Args:
            start_date: Date début (format 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS')
            end_date: Date fin (format 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS')
            countries: Liste pays ('US', 'EU', 'GB') ou None = tous
            min_importance: Importance minimale (1-3)
            with_family: Inclure infos event_families
            limit: Nombre max résultats (None = pas de limite)
            
        Returns:
            DataFrame avec colonnes :
            - ts_utc, event_title, event_key, country
            - importance (importance_n renommé)
            - actual, estimate, forecast, previous
            - unit, event_type
            - surprise_pct (si calculable)
            - family, avg_movement_pips, ... (si with_family=True)
            
        Examples:
            >>> data_service = DataService()
            >>> 
            >>> # Événements US de septembre 2025
            >>> events = data_service.get_events(
            ...     start_date='2025-09-01',
            ...     end_date='2025-09-30',
            ...     countries=['US']
            ... )
            >>> 
            >>> # Événements haute importance tous pays
            >>> high_impact = data_service.get_events(
            ...     start_date='2025-09-01',
            ...     end_date='2025-09-30',
            ...     min_importance=3
            ... )
        """
        # Construction requête
        query = """
        SELECT
            e.ts_utc,
            e.event_title,
            e.event_key,
            e.country,
            e.importance_n as importance,
            e.actual,
            e.estimate,
            e.forecast,
            e.previous,
            e.unit,
            e.event_type,
            -- Calcul surprise avec fallback estimate/previous
            CASE 
                WHEN e.actual IS NOT NULL AND 
                     COALESCE(e.estimate, e.forecast, e.previous) IS NOT NULL AND
                     COALESCE(e.estimate, e.forecast, e.previous) != 0
                THEN 100.0 * (e.actual - COALESCE(e.estimate, e.forecast, e.previous)) 
                     / COALESCE(e.estimate, e.forecast, e.previous)
                ELSE NULL
            END AS surprise_pct
        """
        
        if with_family:
            query += """,
            ef.family,
            ef.avg_movement_pips,
            ef.empirical_score,
            ef.sample_size,
            ef.latency_median,
            ef.ttr_median
        """
        
        query += "\nFROM events e\n"
        
        if with_family:
            # CRITIQUE : Toujours joindre sur event_key ET country
            query += """
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        """
        
        # Filtres WHERE
        where_clauses = []
        
        if start_date:
            where_clauses.append(f"e.ts_utc >= '{start_date}'")
        
        if end_date:
            where_clauses.append(f"e.ts_utc <= '{end_date}'")
        
        if countries:
            countries_str = "', '".join(countries)
            where_clauses.append(f"e.country IN ('{countries_str}')")
        
        if min_importance > 1:
            where_clauses.append(f"e.importance_n >= {min_importance}")
        
        if where_clauses:
            query += "\nWHERE " + " AND ".join(where_clauses)
        
        query += "\nORDER BY e.ts_utc, e.country"
        
        if limit:
            query += f"\nLIMIT {limit}"
        
        # Exécution
        with self.get_connection() as conn:
            df = conn.execute(query).fetchdf()
        
        return df
    
    def get_event_by_key(self, event_key: str, country: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un événement spécifique par sa clé et pays.
        
        Args:
            event_key: Clé de l'événement (ex: 'cpi-yy')
            country: Pays ('US', 'EU', 'GB')
            
        Returns:
            Dictionnaire avec infos événement ou None si introuvable
        """
        query = """
        SELECT 
            e.*,
            ef.family,
            ef.avg_movement_pips,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.event_key = ? AND e.country = ?
        ORDER BY e.ts_utc DESC
        LIMIT 1
        """
        
        with self.get_connection() as conn:
            result = conn.execute(query, [event_key, country]).fetchdf()
        
        if len(result) == 0:
            return None
        
        return result.iloc[0].to_dict()
    
    # ========================================================================
    # FAMILLES D'ÉVÉNEMENTS
    # ========================================================================
    
    def get_event_families(
        self,
        countries: Optional[List[str]] = None,
        min_avg_movement: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Récupère les familles d'événements avec leurs statistiques.
        
        Args:
            countries: Liste pays ou None = tous
            min_avg_movement: Mouvement moyen minimum en pips
            
        Returns:
            DataFrame avec familles et leurs caractéristiques
            
        Examples:
            >>> data_service = DataService()
            >>> 
            >>> # Familles US avec impact > 5 pips
            >>> families = data_service.get_event_families(
            ...     countries=['US'],
            ...     min_avg_movement=5.0
            ... )
        """
        query = """
        SELECT 
            ef.event_key,
            ef.country,
            ef.family,
            ef.avg_movement_pips,
            ef.empirical_score,
            ef.sample_size,
            ef.latency_median,
            ef.ttr_median,
            COUNT(e.event_key) as event_count
        FROM event_families ef
        LEFT JOIN events e 
            ON ef.event_key = e.event_key 
            AND ef.country = e.country
        """
        
        where_clauses = []
        
        if countries:
            countries_str = "', '".join(countries)
            where_clauses.append(f"ef.country IN ('{countries_str}')")
        
        if min_avg_movement is not None:
            where_clauses.append(f"ef.avg_movement_pips >= {min_avg_movement}")
        
        if where_clauses:
            query += "\nWHERE " + " AND ".join(where_clauses)
        
        query += """
        GROUP BY 
            ef.event_key, ef.country, ef.family,
            ef.avg_movement_pips, ef.empirical_score, ef.sample_size,
            ef.latency_median, ef.ttr_median
        ORDER BY ef.avg_movement_pips DESC
        """
        
        with self.get_connection() as conn:
            df = conn.execute(query).fetchdf()
        
        return df
    
    # ========================================================================
    # PRIX EUR/USD
    # ========================================================================
    
    def get_prices(
        self,
        start_time: str,
        end_time: str,
        timeframe: str = '1m'
    ) -> pd.DataFrame:
        """
        Récupère les prix EUR/USD pour une période donnée.
        
        Args:
            start_time: Timestamp début (format 'YYYY-MM-DD HH:MM:SS')
            end_time: Timestamp fin (format 'YYYY-MM-DD HH:MM:SS')
            timeframe: Timeframe ('1m', '5m', '15m', '1h')
            
        Returns:
            DataFrame avec colonnes :
            - ts_utc, open, high, low, close, volume
            
        Examples:
            >>> data_service = DataService()
            >>> 
            >>> # Prix 1 minute autour CPI US
            >>> prices = data_service.get_prices(
            ...     start_time='2025-09-11 14:00:00',
            ...     end_time='2025-09-11 15:00:00',
            ...     timeframe='1m'
            ... )
        """
        if timeframe not in config.SUPPORTED_TIMEFRAMES:
            raise ValueError(
                f"Timeframe '{timeframe}' non supporté. "
                f"Choix : {config.SUPPORTED_TIMEFRAMES}"
            )
        
        table_name = f"prices_{timeframe}"
        
        query = f"""
        SELECT 
            datetime as ts_utc,
            open,
            high,
            low,
            close,
            volume
        FROM {table_name}
        WHERE datetime >= '{start_time}'
          AND datetime <= '{end_time}'
        ORDER BY datetime
        """
        
        with self.get_connection() as conn:
            df = conn.execute(query).fetchdf()
        
        return df
    
    def get_price_at_time(
        self,
        timestamp: str,
        price_type: str = 'close'
    ) -> Optional[float]:
        """
        Récupère le prix à un instant précis.
        
        Args:
            timestamp: Timestamp exact (format 'YYYY-MM-DD HH:MM:SS')
            price_type: Type prix ('open', 'high', 'low', 'close')
            
        Returns:
            Prix ou None si données manquantes
        """
        valid_types = ['open', 'high', 'low', 'close']
        if price_type not in valid_types:
            raise ValueError(f"price_type doit être dans {valid_types}")
        
        query = f"""
        SELECT {price_type}
        FROM prices_1m
        WHERE datetime = '{timestamp}'
        LIMIT 1
        """
        
        with self.get_connection() as conn:
            result = conn.execute(query).fetchone()
        
        return result[0] if result else None
    
    # ========================================================================
    # IMPACTS CALCULÉS
    # ========================================================================
    
    def get_event_impacts(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_phase1_pips: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Récupère les impacts calculés depuis event_impacts_v2.
        
        ATTENTION : phase1_pips peut être NULL (pas encore calculé).
        
        Args:
            start_date: Date début
            end_date: Date fin
            min_phase1_pips: Impact Phase 1 minimum en pips
            
        Returns:
            DataFrame avec impacts calculés
            
        Examples:
            >>> data_service = DataService()
            >>> 
            >>> # Impacts significatifs de septembre
            >>> impacts = data_service.get_event_impacts(
            ...     start_date='2025-09-01',
            ...     end_date='2025-09-30',
            ...     min_phase1_pips=5.0
            ... )
        """
        query = """
        SELECT 
            ei.*
        FROM event_impacts_v2 ei
        """
        
        where_clauses = []
        
        if start_date:
            where_clauses.append(f"ei.ts_utc >= '{start_date}'")
        
        if end_date:
            where_clauses.append(f"ei.ts_utc <= '{end_date}'")
        
        if min_phase1_pips is not None:
            where_clauses.append(f"ei.phase1_pips >= {min_phase1_pips}")
        
        if where_clauses:
            query += "\nWHERE " + " AND ".join(where_clauses)
        
        query += "\nORDER BY ei.ts_utc"
        
        with self.get_connection() as conn:
            df = conn.execute(query).fetchdf()
        
        return df
    
    # ========================================================================
    # STATISTIQUES & UTILITAIRES
    # ========================================================================
    
    def get_db_stats(self) -> Dict[str, Any]:
        """
        Récupère statistiques sur la base de données.
        
        Returns:
            Dictionnaire avec statistiques (tables, counts, dates, etc.)
            
        Examples:
            >>> data_service = DataService()
            >>> stats = data_service.get_db_stats()
            >>> print(f"Événements : {stats['events_count']}")
        """
        stats = {}
        
        with self.get_connection() as conn:
            # Tables
            tables = conn.execute("SHOW TABLES").fetchdf()
            stats['tables'] = tables['name'].tolist()
            
            # Counts
            stats['events_count'] = conn.execute(
                "SELECT COUNT(*) FROM events"
            ).fetchone()[0]
            
            stats['families_count'] = conn.execute(
                "SELECT COUNT(*) FROM event_families"
            ).fetchone()[0]
            
            stats['prices_count'] = conn.execute(
                "SELECT COUNT(*) FROM prices_1m"
            ).fetchone()[0]
            
            # Plage dates événements
            date_range = conn.execute("""
                SELECT 
                    MIN(ts_utc) as first_event,
                    MAX(ts_utc) as last_event
                FROM events
            """).fetchone()
            
            stats['first_event'] = str(date_range[0]) if date_range[0] else None
            stats['last_event'] = str(date_range[1]) if date_range[1] else None
            
            # Plage dates prix
            price_range = conn.execute("""
                SELECT 
                    MIN(datetime) as first_price,
                    MAX(datetime) as last_price
                FROM prices_1m
            """).fetchone()
            
            stats['first_price'] = str(price_range[0]) if price_range[0] else None
            stats['last_price'] = str(price_range[1]) if price_range[1] else None
            
            # Par pays
            by_country = conn.execute("""
                SELECT country, COUNT(*) as count
                FROM events
                GROUP BY country
                ORDER BY count DESC
            """).fetchdf()
            
            stats['events_by_country'] = by_country.to_dict('records')
        
        return stats
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à la base de données.
        
        Returns:
            True si connexion OK, False sinon
        """
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False


if __name__ == "__main__":
    # Tests basiques
    print("=" * 70)
    print("TEST - DataService")
    print("=" * 70)
    
    try:
        # Initialisation
        data_service = DataService()
        print("✅ DataService initialisé")
        
        # Test connexion
        if data_service.test_connection():
            print("✅ Connexion DB OK")
        else:
            print("❌ Connexion DB échouée")
            exit(1)
        
        # Stats DB
        print("\n📊 Statistiques DB:")
        stats = data_service.get_db_stats()
        print(f"  Événements : {stats['events_count']:,}")
        print(f"  Familles : {stats['families_count']:,}")
        print(f"  Prix 1m : {stats['prices_count']:,}")
        print(f"  Période événements : {stats['first_event']} → {stats['last_event']}")
        
        # Test récupération événements
        print("\n📅 Test get_events():")
        events = data_service.get_events(
            start_date='2025-09-01',
            end_date='2025-09-30',
            countries=['US'],
            min_importance=3,
            limit=5
        )
        print(f"  Récupéré {len(events)} événements US haute importance")
        if len(events) > 0:
            print(f"  Premier : {events.iloc[0]['event_title']}")
        
        # Test récupération familles
        print("\n👨‍👩‍👧‍👦 Test get_event_families():")
        families = data_service.get_event_families(
            countries=['US'],
            min_avg_movement=5.0
        )
        print(f"  Récupéré {len(families)} familles impact > 5 pips")
        
        print("\n" + "=" * 70)
        print("✅ Tous les tests passent")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        exit(1)
