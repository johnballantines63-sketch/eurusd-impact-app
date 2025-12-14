#!/usr/bin/env python3
"""
Calcule les métriques empiriques avec mapping intelligent EA ↔ EU
Version améliorée qui gère les variantes de pays
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def get_db_path():
    return "fx_impact_app/data/warehouse.duckdb"

def measure_event_impact(conn, event_key, country, threshold_pips=5.0, window_minutes=60):
    """
    Mesure l'impact réel d'un événement avec fallback sur variantes de pays
    """
    
    # Liste des pays à essayer (avec mapping EA ↔ EU)
    countries_to_try = [country]
    
    if country == 'EA':
        countries_to_try.append('EU')
    elif country == 'EU':
        countries_to_try.append('EA')
    
    # Essayer chaque variante de pays
    for try_country in countries_to_try:
        query = """
        SELECT ts_utc, actual, previous
        FROM events
        WHERE event_key = ?
            AND country = ?
            AND actual IS NOT NULL
            AND ts_utc >= '2022-09-01'
        ORDER BY ts_utc DESC
        """
        
        events = conn.execute(query, [event_key, try_country]).fetchall()
        
        if len(events) >= 3:  # Seuil abaissé à 3 (au lieu de 5)
            print(f"      ℹ️  Utilise données de [{try_country}] ({len(events)} occurrences)")
            break
    else:
        # Aucune variante n'a assez de données
        return None
    
    if len(events) == 0:
        return None
    
    reactions = []
    
    for event_ts, actual, previous in events:
        # Convertir timestamp
        if isinstance(event_ts, str):
            event_dt = pd.to_datetime(event_ts)
        else:
            event_dt = event_ts
        
        end_dt = event_dt + timedelta(minutes=window_minutes)
        
        # Récupérer les prix
        event_epoch = int(event_dt.timestamp())
        end_epoch = int(end_dt.timestamp())
        
        try:
            price_query = f"""
            SELECT timestamp, close
            FROM prices_1m
            WHERE timestamp >= {event_epoch}
                AND timestamp <= {end_epoch}
            ORDER BY timestamp ASC
            """
            
            prices = conn.execute(price_query).fetchall()
            
            if len(prices) < 2:
                continue
            
            # Prix de référence
            ref_price = prices[0][1]
            
            # Calculer mouvement maximum et latence
            max_movement = 0
            latency = None
            
            for i, (ts, price) in enumerate(prices):
                movement_pips = abs(price - ref_price) * 10000
                
                if movement_pips > max_movement:
                    max_movement = movement_pips
                
                if latency is None and movement_pips >= threshold_pips:
                    latency = i
            
            # Surprise
            surprise = 0
            if previous is not None and previous != 0:
                surprise = abs((actual - previous) / previous) * 100
            
            reactions.append({
                'max_movement': max_movement,
                'latency': latency if latency is not None else window_minutes,
                'had_reaction': latency is not None,
                'surprise': surprise
            })
            
        except Exception as e:
            continue
    
    if len(reactions) == 0:
        return None
    
    # Calculer statistiques
    df = pd.DataFrame(reactions)
    
    return {
        'occurrences': len(events),
        'analyzed': len(reactions),
        'avg_movement': df['max_movement'].mean(),
        'median_movement': df['max_movement'].median(),
        'max_movement': df['max_movement'].max(),
        'reaction_rate': df['had_reaction'].sum() / len(df),
        'avg_latency': df[df['had_reaction']]['latency'].mean() if df['had_reaction'].sum() > 0 else None,
        'median_latency': df[df['had_reaction']]['latency'].median() if df['had_reaction'].sum() > 0 else None,
        'avg_surprise': df['surprise'].mean()
    }

def calculate_impact_score(stats):
    """Calcule un score composite 0-100"""
    
    if stats is None or stats['analyzed'] < 3:  # Seuil abaissé
        return 0
    
    volatility_score = min(stats['avg_movement'], 40)
    frequency_score = stats['reaction_rate'] * 30
    
    if stats['avg_latency'] is not None and stats['avg_latency'] > 0:
        speed_score = max(0, 30 - stats['avg_latency'])
    else:
        speed_score = 0
    
    total_score = volatility_score + frequency_score + speed_score
    
    return round(total_score, 2)

def classify_impact_level(score):
    """Classifie HIGH/MEDIUM/LOW"""
    if score >= 70:
        return 'HIGH'
    elif score >= 40:
        return 'MEDIUM'
    else:
        return 'LOW'

def calculate_with_smart_mapping():
    """
    Calcule les scores avec mapping intelligent
    """
    
    conn = duckdb.connect(get_db_path())
    
    print("="*80)
    print("  CALCUL AVEC MAPPING INTELLIGENT EA ↔ EU")
    print("="*80)
    print()
    
    # Statistiques initiales
    stats_query = """
        SELECT 
            COUNT(*) as total,
            COUNT(empirical_score) as with_score,
            COUNT(*) - COUNT(empirical_score) as without_score
        FROM event_families
    """
    
    stats = conn.execute(stats_query).fetchone()
    total, with_score, without_score = stats
    
    print(f"📈 État initial:")
    print(f"   Total: {total} | Avec score: {with_score} | Sans score: {without_score}")
    print()
    
    # Récupérer événements HIGH sans score
    query = """
        SELECT event_key, country, family, impact_level
        FROM event_families
        WHERE empirical_score IS NULL
            AND impact_level = 'HIGH'
        ORDER BY family, event_key
    """
    
    events_to_process = conn.execute(query).fetchall()
    
    print(f"🎯 {len(events_to_process)} événements HIGH à traiter")
    print()
    
    if len(events_to_process) == 0:
        print("✅ Tous les événements HIGH ont déjà un score !")
        conn.close()
        return
    
    print("🔬 Analyse en cours...")
    print("-" * 80)
    print()
    
    success = 0
    skipped = 0
    
    for i, (event_key, country, family, theoretical_impact) in enumerate(events_to_process, 1):
        
        print(f"📊 {i}/{len(events_to_process)} - [{country}] {event_key[:55]}")
        print(f"   Famille: {family} | Impact théo: {theoretical_impact}")
        
        # Mesurer avec fallback intelligent
        stats = measure_event_impact(conn, event_key, country)
        
        if stats is None or stats['analyzed'] < 3:
            print(f"   ⚠️  Données insuffisantes ({stats['analyzed'] if stats else 0} occurrences)")
            skipped += 1
            print()
            continue
        
        # Calculer score
        score = calculate_impact_score(stats)
        empirical_level = classify_impact_level(score)
        
        # Mettre à jour
        try:
            conn.execute("""
                UPDATE event_families
                SET 
                    empirical_score = ?,
                    empirical_impact = ?,
                    avg_movement_pips = ?,
                    reaction_rate = ?,
                    avg_latency_min = ?,
                    analyzed_occurrences = ?
                WHERE event_key = ? AND country = ?
            """, [
                score,
                empirical_level,
                round(stats['avg_movement'], 2),
                round(stats['reaction_rate'], 3),
                round(stats['avg_latency'], 2) if stats['avg_latency'] else None,
                stats['analyzed'],
                event_key,
                country
            ])
            
            print(f"   ✅ Score: {score:.1f} | Impact: {empirical_level}")
            print(f"      Mouvement: {stats['avg_movement']:.1f} pips | Réaction: {stats['reaction_rate']*100:.0f}%")
            if stats['avg_latency']:
                print(f"      Latence: {stats['avg_latency']:.1f} min | Analysés: {stats['analyzed']}")
            
            success += 1
            
            # Si c'est un événement EA/EU, appliquer aussi à l'autre
            if country == 'EA':
                mirror_country = 'EU'
            elif country == 'EU':
                mirror_country = 'EA'
            else:
                mirror_country = None
            
            if mirror_country:
                # Vérifier si l'entrée miroir existe et n'a pas de score
                mirror_exists = conn.execute("""
                    SELECT 1
                    FROM event_families
                    WHERE event_key = ?
                        AND country = ?
                        AND empirical_score IS NULL
                """, [event_key, mirror_country]).fetchone()
                
                if mirror_exists:
                    conn.execute("""
                        UPDATE event_families
                        SET 
                            empirical_score = ?,
                            empirical_impact = ?,
                            avg_movement_pips = ?,
                            reaction_rate = ?,
                            avg_latency_min = ?,
                            analyzed_occurrences = ?
                        WHERE event_key = ? AND country = ?
                    """, [
                        score,
                        empirical_level,
                        round(stats['avg_movement'], 2),
                        round(stats['reaction_rate'], 3),
                        round(stats['avg_latency'], 2) if stats['avg_latency'] else None,
                        stats['analyzed'],
                        event_key,
                        mirror_country
                    ])
                    print(f"      🔄 Appliqué aussi à [{mirror_country}]")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            skipped += 1
        
        print()
    
    # Statistiques finales
    stats_final = conn.execute(stats_query).fetchone()
    total_final, with_score_final, without_score_final = stats_final
    
    print("="*80)
    print("  RÉSUMÉ")
    print("="*80)
    print()
    print(f"📊 État final:")
    print(f"   Total: {total_final} | Avec score: {with_score_final} | Sans score: {without_score_final}")
    print()
    print(f"✅ Succès: {success} | ⚠️  Sautés: {skipped}")
    print()
    
    # Afficher les nouveaux scores HIGH
    if success > 0:
        print("="*80)
        print("  NOUVEAUX ÉVÉNEMENTS CALCULÉS")
        print("="*80)
        print()
        
        new_scores = conn.execute("""
            SELECT event_key, country, empirical_score, empirical_impact, 
                   avg_movement_pips, reaction_rate, analyzed_occurrences
            FROM event_families
            WHERE empirical_score IS NOT NULL
            ORDER BY empirical_score DESC
            LIMIT 10
        """).fetchall()
        
        for ek, c, score, impact, movement, reaction, n_events in new_scores:
            print(f"[{c}] {ek[:60]}")
            print(f"  Score: {score:.1f} | Impact: {impact} | Mouvement: {movement:.1f} pips")
            print(f"  Réaction: {reaction*100:.0f}% | Analysés: {n_events}")
            print()
    
    conn.close()
    
    print("="*80)
    print("  TERMINÉ")
    print("="*80)

if __name__ == "__main__":
    calculate_with_smart_mapping()
