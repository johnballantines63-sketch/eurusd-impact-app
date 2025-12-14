#!/usr/bin/env python3
"""
Diagnostic complet de la table prices_1m pour identifier 
pourquoi les prix ne sont pas trouvés
"""

import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Configuration
PROJECT_ROOT = Path("/Users/andrevalentin/Projects/eurusd_news_impact_calculator")
DB_PATH = PROJECT_ROOT / "fx_impact_app/data/warehouse.duckdb"

def main():
    print("🔍 DIAGNOSTIC PRICES_1M")
    print("=" * 80)
    
    if not DB_PATH.exists():
        print(f"❌ Base de données introuvable : {DB_PATH}")
        return
    
    print(f"✅ Base trouvée : {DB_PATH}")
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 1. STRUCTURE DE LA TABLE
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("📋 1. STRUCTURE DE LA TABLE prices_1m")
    print("-" * 80)
    
    try:
        schema = conn.execute("DESCRIBE prices_1m").fetchall()
        
        print(f"{'Colonne':<20} {'Type':<20} {'Nullable':<10}")
        print("-" * 80)
        for col in schema:
            print(f"{col[0]:<20} {col[1]:<20} {str(col[2]):<10}")
        
        print()
    except Exception as e:
        print(f"❌ Erreur lecture structure : {e}")
        conn.close()
        return
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2. STATISTIQUES GÉNÉRALES
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("📊 2. STATISTIQUES GÉNÉRALES")
    print("-" * 80)
    
    try:
        # Nombre total de lignes
        count = conn.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
        print(f"Total lignes : {count:,}")
        
        # Plage de dates (timestamp)
        date_range = conn.execute("""
            SELECT 
                MIN(timestamp) as min_ts,
                MAX(timestamp) as max_ts
            FROM prices_1m
        """).fetchone()
        
        if date_range[0] and date_range[1]:
            min_date = datetime.fromtimestamp(date_range[0])
            max_date = datetime.fromtimestamp(date_range[1])
            
            print(f"Date min : {min_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Date max : {max_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Durée : {(max_date - min_date).days} jours")
        else:
            print("⚠️ Timestamps NULL")
        
        print()
    except Exception as e:
        print(f"❌ Erreur statistiques : {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3. VÉRIFICATION 10 OCTOBRE 2025
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("🎯 3. VÉRIFICATION 10 OCTOBRE 2025")
    print("-" * 80)
    
    target_date = datetime(2025, 10, 10, 0, 0, 0)
    target_epoch = int(target_date.timestamp())
    next_day_epoch = int((target_date + timedelta(days=1)).timestamp())
    
    print(f"Date cible : {target_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Epoch cible : {target_epoch}")
    print()
    
    try:
        # Recherche exacte
        query = f"""
            SELECT COUNT(*) as count
            FROM prices_1m
            WHERE timestamp >= {target_epoch}
              AND timestamp < {next_day_epoch}
        """
        
        count_oct10 = conn.execute(query).fetchone()[0]
        
        if count_oct10 > 0:
            print(f"✅ {count_oct10} prix trouvés pour le 10 octobre 2025")
            
            # Afficher premiers/derniers
            sample = conn.execute(f"""
                SELECT timestamp, close
                FROM prices_1m
                WHERE timestamp >= {target_epoch}
                  AND timestamp < {next_day_epoch}
                ORDER BY timestamp
                LIMIT 5
            """).fetchall()
            
            print("\n📊 Premiers prix :")
            for ts, price in sample:
                dt = datetime.fromtimestamp(ts)
                print(f"  {dt.strftime('%H:%M:%S')} : {price:.5f}")
        else:
            print(f"❌ Aucun prix pour le 10 octobre 2025")
            print("\n🔍 Recherche dates proches...")
            
            # Chercher jours avant/après
            for offset in [-1, -2, -3, 1, 2, 3]:
                check_date = target_date + timedelta(days=offset)
                check_epoch = int(check_date.timestamp())
                check_next = int((check_date + timedelta(days=1)).timestamp())
                
                count_check = conn.execute(f"""
                    SELECT COUNT(*)
                    FROM prices_1m
                    WHERE timestamp >= {check_epoch}
                      AND timestamp < {check_next}
                """).fetchone()[0]
                
                if count_check > 0:
                    print(f"  {check_date.strftime('%Y-%m-%d')} : {count_check} prix ✅")
                else:
                    print(f"  {check_date.strftime('%Y-%m-%d')} : aucun ❌")
        
        print()
    except Exception as e:
        print(f"❌ Erreur vérification : {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4. DISTRIBUTION PAR MOIS
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("📅 4. DISTRIBUTION PAR MOIS (2025)")
    print("-" * 80)
    
    try:
        # Calculer epochs pour 2025
        year_2025_start = int(datetime(2025, 1, 1, 0, 0, 0).timestamp())
        year_2025_end = int(datetime(2026, 1, 1, 0, 0, 0).timestamp())
        
        monthly = conn.execute(f"""
            SELECT 
                strftime('%Y-%m', FROM_UNIXTIME(timestamp)) as month,
                COUNT(*) as count,
                MIN(timestamp) as min_ts,
                MAX(timestamp) as max_ts
            FROM prices_1m
            WHERE timestamp >= {year_2025_start}
              AND timestamp < {year_2025_end}
            GROUP BY month
            ORDER BY month
        """).fetchall()
        
        if len(monthly) > 0:
            print(f"{'Mois':<10} {'Prix':<10} {'Première':<20} {'Dernière':<20}")
            print("-" * 80)
            for month, count, min_ts, max_ts in monthly:
                first = datetime.fromtimestamp(min_ts).strftime('%Y-%m-%d %H:%M')
                last = datetime.fromtimestamp(max_ts).strftime('%Y-%m-%d %H:%M')
                print(f"{month:<10} {count:>8,} {first:<20} {last:<20}")
        else:
            print("❌ Aucune donnée pour 2025")
        
        print()
    except Exception as e:
        print(f"❌ Erreur distribution : {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 5. TEST REQUÊTE MANUELLE
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("🧪 5. TEST REQUÊTE MANUELLE (format get_real_prices_batch)")
    print("-" * 80)
    
    try:
        # Simuler événement 10 oct 2025 14:30 UTC
        event_time = datetime(2025, 10, 10, 14, 30, 0)
        event_epoch = int(event_time.timestamp())
        end_epoch = event_epoch + (60 * 60)  # +60 min
        
        print(f"Événement : {event_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Epoch : {event_epoch} → {end_epoch}")
        print()
        
        query = f"""
            SELECT timestamp, close
            FROM prices_1m
            WHERE timestamp >= {event_epoch} AND timestamp <= {end_epoch}
            ORDER BY timestamp ASC
            LIMIT 10
        """
        
        results = conn.execute(query).fetchall()
        
        if len(results) > 0:
            print(f"✅ {len(results)} prix trouvés")
            print("\n📊 Aperçu :")
            for ts, price in results[:5]:
                dt = datetime.fromtimestamp(ts)
                print(f"  {dt.strftime('%H:%M:%S')} : {price:.5f}")
        else:
            print("❌ Aucun prix trouvé avec cette requête")
            print("\n💡 La table prices_1m ne contient probablement pas de données pour octobre 2025")
            print("   → Les données s'arrêtent peut-être en 2024")
    
    except Exception as e:
        print(f"❌ Erreur test requête : {e}")
    
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ DIAGNOSTIC TERMINÉ")
    print("=" * 80)
    
    print("\n📋 RECOMMANDATIONS :")
    print("1. Si données 2025 manquantes → Utiliser événements 2024 pour backtest")
    print("2. Si table vide → Relancer import EODHD avec fetch_historical_prices()")
    print("3. Si format incorrect → Vérifier colonnes timestamp vs time_utc")

if __name__ == "__main__":
    main()
