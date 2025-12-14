"""
Mapper "current account" à la famille "Trade_Balance"

Current Account (balance des paiements) et Trade Balance (balance commerciale)
sont très similaires économiquement, donc on peut utiliser les mêmes stats.
"""

import duckdb
from datetime import datetime

db_path = 'fx_impact_app/data/warehouse.duckdb'

print("🔧 Mapping Current Account → Trade_Balance...")
print("=" * 60)

try:
    conn = duckdb.connect(db_path)
    
    # 1. Vérifier si current account existe déjà
    existing = conn.execute("""
        SELECT * FROM event_families WHERE event_key = 'current account'
    """).fetchall()
    
    if existing:
        print("⚠️ 'current account' existe déjà dans event_families")
        print("   On va le mettre à jour...")
        
        # Update
        conn.execute("""
            UPDATE event_families
            SET family = 'Trade_Balance',
                is_tradable = true,
                impact_level = 'MEDIUM',
                notes = 'Mapped to Trade_Balance - Similar economic indicator'
            WHERE event_key = 'current account'
        """)
        print("✅ Mise à jour effectuée")
    else:
        print("📝 Création nouvelle entrée pour 'current account'...")
        
        # Insert new
        conn.execute("""
            INSERT INTO event_families (
                event_key, 
                country, 
                family, 
                is_tradable, 
                impact_level,
                notes,
                created_at
            )
            VALUES (
                'current account',
                'DE',
                'Trade_Balance',
                true,
                'MEDIUM',
                'Mapped to Trade_Balance - Similar economic indicator',
                CURRENT_TIMESTAMP
            )
        """)
        print("✅ Entrée créée")
    
    # 2. Copier les stats de Trade_Balance vers current account
    print("\n📊 Copie des stats de Trade_Balance...")
    
    # Récupérer les stats de Trade_Balance
    trade_stats = conn.execute("""
        SELECT latency_median, latency_p20, latency_p80,
               ttr_median, ttr_p20, ttr_p80, mfe_p80, n_events_latency
        FROM event_families
        WHERE family = 'Trade_Balance' AND latency_median IS NOT NULL
        LIMIT 1
    """).fetchone()
    
    if trade_stats:
        print(f"   Latence médiane: {trade_stats[0]} min")
        print(f"   TTR médian: {trade_stats[3]} min")
        print(f"   MFE P80: {trade_stats[6]} pips")
        
        # Appliquer à current account
        conn.execute("""
            UPDATE event_families
            SET latency_median = ?,
                latency_p20 = ?,
                latency_p80 = ?,
                ttr_median = ?,
                ttr_p20 = ?,
                ttr_p80 = ?,
                mfe_p80 = ?,
                n_events_latency = ?
            WHERE event_key = 'current account'
        """, trade_stats)
        
        print("✅ Stats copiées depuis Trade_Balance")
    else:
        print("⚠️ Pas de stats pour Trade_Balance, utilisation valeurs par défaut")
        conn.execute("""
            UPDATE event_families
            SET latency_median = 5.0,
                latency_p20 = 3.0,
                latency_p80 = 10.0,
                ttr_median = 49.5,
                ttr_p20 = 30.0,
                ttr_p80 = 60.0,
                mfe_p80 = 24.9,
                n_events_latency = 50
            WHERE event_key = 'current account'
        """)
        print("✅ Valeurs par défaut appliquées")
    
    # 3. Vérifier le résultat
    result = conn.execute("""
        SELECT event_key, family, is_tradable, latency_median, mfe_p80
        FROM event_families
        WHERE event_key = 'current account'
    """).fetchone()
    
    print("\n" + "=" * 60)
    print("✅ MAPPING RÉUSSI !")
    print("=" * 60)
    print(f"Event Key: {result[0]}")
    print(f"Famille: {result[1]}")
    print(f"Tradable: {result[2]}")
    print(f"Latence: {result[3]} min")
    print(f"Impact (MFE): {result[4]} pips")
    
    conn.close()
    
    print("\n🎯 Prochaine étape:")
    print("   1. Relancer Streamlit")
    print("   2. Recharger événements 11/09/2025")
    print("   3. Current Account DE devrait maintenant être SÉLECTIONNABLE")
    print("   4. Avec prédiction d'impact automatique !")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
