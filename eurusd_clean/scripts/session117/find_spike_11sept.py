"""
Chercher le spike de 56.2 pips du 11 septembre 2025
Tester différentes fenêtres temporelles

Auteur: André Valentin avec Claude
Date: 06 novembre 2025
"""

import duckdb
from datetime import datetime, timedelta

def find_spike_11sept():
    """Chercher le gros spike dans les données du 11 septembre"""
    
    db_path = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb"
    conn = duckdb.connect(db_path, read_only=True)
    
    print("=" * 70)
    print("🔍 RECHERCHE SPIKE 56.2 PIPS - 11 SEPTEMBRE 2025")
    print("=" * 70)
    
    # Tester différentes fenêtres horaires
    test_windows = [
        ("00:00:00", "23:59:59", "Journée complète"),
        ("10:00:00", "18:00:00", "Session trading européenne"),
        ("12:00:00", "14:00:00", "12:00-14:00 (si prix en UTC)"),
        ("12:00:00", "15:00:00", "12:00-15:00 (si prix en UTC)"),
        ("14:00:00", "17:00:00", "14:00-17:00 (Bern time)"),
    ]
    
    for start_time, end_time, description in test_windows:
        print(f"\n📊 TEST : {description}")
        print("-" * 70)
        
        query = f"""
        SELECT 
            datetime,
            high,
            low,
            (high + low) / 2 as mid_price
        FROM prices_1m
        WHERE datetime >= '2025-09-11 {start_time}'
          AND datetime <= '2025-09-11 {end_time}'
        ORDER BY datetime
        """
        
        result = conn.execute(query).fetchall()
        
        if not result:
            print(f"   ❌ Aucune donnée")
            continue
        
        print(f"   ✅ {len(result)} lignes")
        
        # Calculer statistiques
        mid_prices = [row[3] for row in result]
        min_price = min(mid_prices)
        max_price = max(mid_prices)
        range_pips = (max_price - min_price) * 10000
        
        # Trouver timestamps des extrema
        min_idx = mid_prices.index(min_price)
        max_idx = mid_prices.index(max_price)
        min_time = result[min_idx][0]
        max_time = result[max_idx][0]
        
        print(f"   Prix min : {min_price:.5f} @ {min_time}")
        print(f"   Prix max : {max_price:.5f} @ {max_time}")
        print(f"   Range : {range_pips:.1f} pips")
        
        # Vérifier si proche de 56.2 pips
        if range_pips > 50:
            print(f"   🎯 CANDIDAT TROUVÉ ! Range {range_pips:.1f} pips ≈ 56.2 pips")
    
    # Afficher aussi les plus gros mouvements minute par minute
    print("\n" + "=" * 70)
    print("📈 TOP 10 PLUS GROS MOUVEMENTS (minute)")
    print("=" * 70)
    
    query_movements = """
    WITH price_changes AS (
        SELECT 
            datetime,
            high,
            low,
            (high + low) / 2 as mid_price,
            LAG((high + low) / 2) OVER (ORDER BY datetime) as prev_mid,
            ABS((high + low) / 2 - LAG((high + low) / 2) OVER (ORDER BY datetime)) * 10000 as movement_pips
        FROM prices_1m
        WHERE datetime >= '2025-09-11 00:00:00'
          AND datetime <= '2025-09-11 23:59:59'
    )
    SELECT 
        datetime,
        mid_price,
        prev_mid,
        movement_pips
    FROM price_changes
    WHERE movement_pips IS NOT NULL
    ORDER BY movement_pips DESC
    LIMIT 10
    """
    
    movements = conn.execute(query_movements).fetchall()
    
    for row in movements:
        dt, mid, prev, move = row
        direction = "↑" if mid > prev else "↓"
        print(f"   {dt} : {direction} {move:.1f} pips ({prev:.5f} → {mid:.5f})")
    
    conn.close()
    print("\n✅ RECHERCHE TERMINÉE")


if __name__ == "__main__":
    find_spike_11sept()
