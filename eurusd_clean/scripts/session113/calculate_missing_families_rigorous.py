"""
Calcul familles manquantes - Version RIGOUREUSE
================================================

Calcule empirical_score pour événements sans famille.
Applique standards de rigueur scientifique.

Session 113 - André Valentin
"""
import sys
from pathlib import Path
import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import DB_PATH
from src.core.impact_measurement import measure_impact_from_dukascopy

# ============================================================================
# CONSTANTES DE VALIDATION (Standards rigoureux)
# ============================================================================

MIN_SAMPLE_SIZE = 3          # Minimum 3 occurrences pour validité statistique
MIN_IMPACT_PIPS = 0.5        # Filtrer bruit < 0.5 pips
MAX_IMPACT_PIPS = 150.0      # Filtrer outliers > 150 pips
MIN_LOOKBACK_DAYS = 365      # Chercher au moins 1 an d'historique

print("=" * 80)
print("CALCUL FAMILLES MANQUANTES - VERSION RIGOUREUSE")
print("=" * 80)

# Pas de connexion globale - on ouvre/ferme pour chaque opération
# (pour éviter conflit avec measure_impact_from_dukascopy)

# ============================================================================
# ÉVÉNEMENTS À CALCULER
# ============================================================================

events_to_calculate = [
    ('current account', 'DE'),
    ('ecb press conference', 'EU')
]

families_inserted = 0
families_failed = 0

for event_key, country in events_to_calculate:
    
    print(f"\n{'='*80}")
    print(f"CALCUL: {event_key} ({country})")
    print(f"{'='*80}")
    
    # ========================================================================
    # ÉTAPE 1 : Récupérer occurrences historiques
    # ========================================================================
    
    query = f"""
        SELECT ts_utc, actual, estimate
        FROM events
        WHERE event_key = '{event_key}'
            AND country = '{country}'
            AND ts_utc >= CURRENT_DATE - INTERVAL '{MIN_LOOKBACK_DAYS} days'
            AND actual IS NOT NULL
        ORDER BY ts_utc DESC
    """
    
    conn_events = duckdb.connect(str(DB_PATH), read_only=True)
    events = conn_events.execute(query).fetchdf()
    conn_events.close()
    
    print(f"\nOccurrences trouvées: {len(events)}")
    
    if events.empty:
        print(f"ÉCHEC: Aucune occurrence historique")
        families_failed += 1
        continue
    
    if len(events) < MIN_SAMPLE_SIZE:
        print(f"ÉCHEC: Pas assez d'occurrences (minimum {MIN_SAMPLE_SIZE})")
        families_failed += 1
        continue
    
    # ========================================================================
    # ÉTAPE 2 : Vérifier disponibilité prix pour chaque occurrence
    # ========================================================================
    
    print(f"\nVérification disponibilité prix...")
    
    events_with_prices = []
    for idx, event in events.iterrows():
        # Convertir en datetime Bern (naive)
        event_time = pd.to_datetime(event['ts_utc'])
        if event_time.tzinfo is not None:
            event_time = event_time.tz_convert('Europe/Zurich').tz_localize(None)
        
        # Vérifier existence prix dans fenêtre [event-5min, event+120min]
        conn_check = duckdb.connect(str(DB_PATH), read_only=True)
        check_query = f"""
            SELECT COUNT(*) as count
            FROM prices_bern
            WHERE datetime >= '{event_time - pd.Timedelta(minutes=5)}'
                AND datetime <= '{event_time + pd.Timedelta(minutes=120)}'
        """
        
        price_count = conn_check.execute(check_query).fetchone()[0]
        conn_check.close()
        
        if price_count > 0:
            # Stocker l'event avec le timestamp corrigé
            event_copy = event.copy()
            event_copy['ts_utc_naive'] = event_time
            events_with_prices.append(event_copy)
        else:
            print(f"  Ignoré {event_time.strftime('%Y-%m-%d %H:%M')}: Pas de prix")
    
    print(f"Événements avec prix: {len(events_with_prices)}/{len(events)}")
    
    if len(events_with_prices) < MIN_SAMPLE_SIZE:
        print(f"ÉCHEC: Pas assez d'événements avec prix (minimum {MIN_SAMPLE_SIZE})")
        families_failed += 1
        continue
    
    # ========================================================================
    # ÉTAPE 3 : Mesurer impacts
    # ========================================================================
    
    print(f"\nMesure impacts...")
    
    impacts = []
    latencies = []
    
    for event in events_with_prices:
        # Utiliser le timestamp déjà converti
        event_time = event['ts_utc_naive']
        
        try:
            result = measure_impact_from_dukascopy(
                db_path=DB_PATH,
                event_timestamp=event_time,
                lookback_minutes=5,
                lookahead_minutes=120,
                debug=False
            )
            
            if not result:
                print(f"  Ignoré {event_time.strftime('%Y-%m-%d %H:%M')}: Aucun résultat retourné")
                continue
            
            impact = result.get('impact_pips')
            if impact is None:
                print(f"  Ignoré {event_time.strftime('%Y-%m-%d %H:%M')}: impact_pips = None")
                continue
            
            impact_abs = abs(impact)
            
            # Validation plage valide
            if impact_abs < MIN_IMPACT_PIPS:
                print(f"  Filtré {event_time.strftime('%Y-%m-%d %H:%M')}: {impact_abs:.2f} pips < seuil bruit")
                continue
            
            if impact_abs > MAX_IMPACT_PIPS:
                print(f"  Filtré {event_time.strftime('%Y-%m-%d %H:%M')}: {impact_abs:.2f} pips > seuil aberrant")
                continue
            
            # Impact valide
            impacts.append(impact_abs)
            
            if result.get('latency_minutes'):
                latencies.append(result['latency_minutes'])
            
            print(f"  OK {event_time.strftime('%Y-%m-%d %H:%M')}: {impact_abs:.1f} pips")
        
        except Exception as e:
            print(f"  ERREUR {event_time.strftime('%Y-%m-%d %H:%M')}: {type(e).__name__} - {str(e)}")
            continue
    
    print(f"\nImpacts valides mesurés: {len(impacts)}")
    
    if len(impacts) < MIN_SAMPLE_SIZE:
        print(f"ÉCHEC: Pas assez d'impacts valides (minimum {MIN_SAMPLE_SIZE})")
        families_failed += 1
        continue
    
    # ========================================================================
    # ÉTAPE 4 : Calculer métriques
    # ========================================================================
    
    empirical_score = sum(impacts) / len(impacts)
    latency_median = sorted(latencies)[len(latencies)//2] if latencies else None
    
    print(f"\nMétriques calculées:")
    print(f"  Empirical Score: {empirical_score:.2f}")
    print(f"  Sample Size: {len(impacts)}")
    print(f"  Latency Median: {latency_median:.2f} min" if latency_median else "  Latency: N/A")
    print(f"  Min Impact: {min(impacts):.2f} pips")
    print(f"  Max Impact: {max(impacts):.2f} pips")
    
    # ========================================================================
    # ÉTAPE 5 : Insertion dans DB
    # ========================================================================
    
    print(f"\nInsertion dans event_families...")
    
    # Rouvrir connexion en mode write pour INSERT
    conn_insert = duckdb.connect(str(DB_PATH))
    
    try:
        conn_insert.execute("""
            INSERT OR REPLACE INTO event_families (
                event_key,
                country,
                family,
                empirical_score,
                avg_movement_pips,
                sample_size,
                latency_median,
                n_events_latency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            event_key,
            country,
            None,  # family à déterminer
            round(empirical_score, 6),
            round(empirical_score, 6),
            len(impacts),
            round(latency_median, 6) if latency_median else None,
            len(latencies)
        ])
        
        conn_insert.close()
        print(f"SUCCÈS: Famille insérée")
        families_inserted += 1
    
    except Exception as e:
        conn_insert.close()
        print(f"ÉCHEC: Erreur insertion - {type(e).__name__}: {str(e)}")
        families_failed += 1

# ============================================================================
# VÉRIFICATION FINALE
# ============================================================================

print(f"\n{'='*80}")
print("VÉRIFICATION FINALE")
print(f"{'='*80}")

conn_verify = duckdb.connect(str(DB_PATH), read_only=True)
result = conn_verify.execute("""
    SELECT 
        event_key,
        country,
        empirical_score,
        sample_size,
        latency_median
    FROM event_families
    WHERE (event_key = 'current account' AND country = 'DE')
        OR (event_key = 'ecb press conference' AND country = 'EU')
""").fetchdf()
conn_verify.close()

if not result.empty:
    print("\nFamilles dans DB:")
    print(result.to_string(index=False))
else:
    print("\nAucune famille trouvée dans DB")

# ============================================================================
# RÉSUMÉ
# ============================================================================

print(f"\n{'='*80}")
print("RÉSUMÉ")
print(f"{'='*80}")
print(f"Familles insérées: {families_inserted}")
print(f"Familles échouées: {families_failed}")
print(f"Taux de succès: {families_inserted}/{len(events_to_calculate)}")

if families_inserted == len(events_to_calculate):
    print("\nSUCCÈS COMPLET - Toutes les familles calculées")
    print("\nProchaine étape:")
    print("  bash scripts/session113/run_test_cluster_calculator.sh")
elif families_inserted > 0:
    print("\nSUCCÈS PARTIEL - Certaines familles calculées")
    print("Voir détails ci-dessus pour familles échouées")
else:
    print("\nÉCHEC COMPLET - Aucune famille calculée")
    print("\nCauses possibles:")
    print("  - Pas assez d'occurrences historiques (< 3)")
    print("  - Données prix manquantes pour périodes")
    print("  - Impacts tous filtrés (bruit ou outliers)")

print("=" * 80)
