#!/usr/bin/env python3
"""
Calcule les métriques empiriques manquantes pour les événements prioritaires
Focus: ECB, Jobless Claims, PPI et autres événements HIGH sans score

Métriques calculées:
- empirical_score (0-100)
- empirical_impact (HIGH/MEDIUM/LOW)
- avg_movement_pips
- reaction_rate (%)
- avg_latency_min
- analyzed_occurrences
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import sys

def get_db_path():
    """Retourne le chemin de la base de données"""
    return "fx_impact_app/data/warehouse.duckdb"

def measure_event_impact(conn, event_key, country, threshold_pips=5.0, window_minutes=60):
    """
    Mesure l'impact réel d'un événement spécifique
    
    Returns:
        dict avec les statistiques ou None si données insuffisantes
    """
    
    # Récupérer toutes les occurrences de cet événement
    query = """
    SELECT ts_utc, actual, previous
    FROM events
    WHERE event_key = ?
        AND country = ?
        AND actual IS NOT NULL
        AND ts_utc >= '2022-09-01'
    ORDER BY ts_utc DESC
    """
    
    events = conn.execute(query, [event_key, country]).fetchall()
    
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
        
        # Récupérer les prix (timestamp en epoch Unix)
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
            
            # Prix de référence (première minute)
            ref_price = prices[0][1]
            
            # Calculer le mouvement maximum
            max_movement = 0
            latency = None
            
            for i, (ts, price) in enumerate(prices):
                movement_pips = abs(price - ref_price) * 10000
                
                if movement_pips > max_movement:
                    max_movement = movement_pips
                
                # Détecter première réaction au-dessus du seuil
                if latency is None and movement_pips >= threshold_pips:
                    latency = i  # minutes depuis l'événement
            
            # Calculer la surprise
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
    
    # Calculer les statistiques
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
    """
    Calcule un score composite d'impact empirique (0-100)
    
    Composantes:
    - Volatilité (40 points max): 1 pip = 1 point
    - Fréquence réaction (30 points max): reaction_rate * 30
    - Rapidité (30 points max): inversement proportionnel à la latence
    """
    
    if stats is None or stats['analyzed'] < 5:
        return 0
    
    # 1. Volatilité (0-40 points)
    volatility_score = min(stats['avg_movement'], 40)
    
    # 2. Fréquence de réaction (0-30 points)
    frequency_score = stats['reaction_rate'] * 30
    
    # 3. Rapidité (0-30 points)
    if stats['avg_latency'] is not None and stats['avg_latency'] > 0:
        # Latence inversée : 1 min = 30 points, 30 min = 1 point
        speed_score = max(0, 30 - stats['avg_latency'])
    else:
        speed_score = 0
    
    total_score = volatility_score + frequency_score + speed_score
    
    return round(total_score, 2)

def classify_impact_level(score):
    """Classifie en HIGH/MEDIUM/LOW basé sur le score empirique"""
    if score >= 70:
        return 'HIGH'
    elif score >= 40:
        return 'MEDIUM'
    else:
        return 'LOW'

def ensure_columns_exist(conn):
    """S'assure que toutes les colonnes nécessaires existent"""
    
    columns_to_add = [
        ('empirical_score', 'DOUBLE'),
        ('empirical_impact', 'VARCHAR'),
        ('avg_movement_pips', 'DOUBLE'),
        ('reaction_rate', 'DOUBLE'),
        ('avg_latency_min', 'DOUBLE'),
        ('analyzed_occurrences', 'INTEGER')
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            conn.execute(f"""
                ALTER TABLE event_families 
                ADD COLUMN {col_name} {col_type}
            """)
        except:
            pass  # Colonne existe déjà

def calculate_missing_scores(priority_only=True):
    """
    Calcule les scores empiriques manquants
    
    Args:
        priority_only: Si True, calcule seulement les événements HIGH sans score
                      Si False, calcule tous les événements sans score
    """
    
    conn = duckdb.connect(get_db_path())
    
    print("="*80)
    print("  CALCUL DES MÉTRIQUES EMPIRIQUES MANQUANTES")
    print("="*80)
    print()
    
    # 1. Assurer que les colonnes existent
    print("📊 Vérification des colonnes...")
    ensure_columns_exist(conn)
    print("✅ Colonnes prêtes")
    print()
    
    # 2. Statistiques initiales
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
    print(f"   Total événements: {total}")
    print(f"   Avec score: {with_score} ({with_score/total*100:.1f}%)")
    print(f"   Sans score: {without_score} ({without_score/total*100:.1f}%)")
    print()
    
    # 3. Récupérer les événements à traiter
    if priority_only:
        query = """
            SELECT event_key, country, family, impact_level
            FROM event_families
            WHERE empirical_score IS NULL
                AND impact_level = 'HIGH'
            ORDER BY family, event_key
        """
        print("🎯 Mode: Événements HIGH prioritaires seulement")
    else:
        query = """
            SELECT event_key, country, family, impact_level
            FROM event_families
            WHERE empirical_score IS NULL
            ORDER BY family, event_key
        """
        print("🎯 Mode: Tous les événements sans score")
    
    events_to_process = conn.execute(query).fetchall()
    
    print(f"   {len(events_to_process)} événements à traiter")
    print()
    
    if len(events_to_process) == 0:
        print("✅ Tous les événements ont déjà un score !")
        conn.close()
        return
    
    # 4. Traiter chaque événement
    print("🔬 Analyse en cours...")
    print("-" * 80)
    print()
    
    processed = 0
    skipped = 0
    success = 0
    
    for i, (event_key, country, family, theoretical_impact) in enumerate(events_to_process, 1):
        
        # Afficher progression
        if i % 10 == 0 or i == 1:
            print(f"📊 Progression: {i}/{len(events_to_process)} ({i/len(events_to_process)*100:.1f}%)")
        
        # Afficher l'événement en cours
        print(f"   [{country}] {event_key[:60]}")
        print(f"      Famille: {family} | Impact théo: {theoretical_impact}")
        
        # Mesurer l'impact réel
        stats = measure_event_impact(conn, event_key, country)
        
        if stats is None or stats['analyzed'] < 5:
            print(f"      ⚠️  Données insuffisantes ({stats['analyzed'] if stats else 0} occurrences analysées)")
            skipped += 1
            print()
            continue
        
        # Calculer le score
        score = calculate_impact_score(stats)
        empirical_level = classify_impact_level(score)
        
        # Mettre à jour la base
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
            
            print(f"      ✅ Score: {score:.1f} | Impact: {empirical_level}")
            print(f"         Mouvement: {stats['avg_movement']:.1f} pips | Réaction: {stats['reaction_rate']*100:.0f}%")
            if stats['avg_latency']:
                print(f"         Latence: {stats['avg_latency']:.1f} min | Occurrences: {stats['analyzed']}")
            
            success += 1
            
        except Exception as e:
            print(f"      ❌ Erreur lors de la mise à jour: {e}")
            skipped += 1
        
        print()
        processed += 1
    
    # 5. Statistiques finales
    print("="*80)
    print("  RÉSUMÉ")
    print("="*80)
    print()
    
    stats_final = conn.execute(stats_query).fetchone()
    total_final, with_score_final, without_score_final = stats_final
    
    print(f"📊 État final:")
    print(f"   Total événements: {total_final}")
    print(f"   Avec score: {with_score_final} ({with_score_final/total_final*100:.1f}%)")
    print(f"   Sans score: {without_score_final} ({without_score_final/total_final*100:.1f}%)")
    print()
    
    print(f"✅ Traitement terminé:")
    print(f"   Traités: {processed}")
    print(f"   Succès: {success}")
    print(f"   Sautés (données insuffisantes): {skipped}")
    print()
    
    # 6. Afficher les nouveaux événements HIGH
    if success > 0:
        print("="*80)
        print("  NOUVEAUX ÉVÉNEMENTS À FORT IMPACT DÉTECTÉS")
        print("="*80)
        print()
        
        # Événements nouvellement calculés avec score HIGH
        new_high = conn.execute("""
            SELECT event_key, country, empirical_score, avg_movement_pips, reaction_rate
            FROM event_families
            WHERE empirical_impact = 'HIGH'
                AND empirical_score IS NOT NULL
                AND event_key IN (
                    SELECT event_key FROM (VALUES """ + 
                    ", ".join([f"('{ek}', '{c}')" for ek, c, _, _ in events_to_process[:20]]) + 
                    """) AS t(event_key, country)
                )
            ORDER BY empirical_score DESC
            LIMIT 10
        """).fetchall()
        
        if len(new_high) > 0:
            for event_key, country, score, movement, reaction in new_high:
                print(f"🔴 [{country}] {event_key[:60]}")
                print(f"   Score: {score:.1f} | Mouvement: {movement:.1f} pips | Réaction: {reaction*100:.0f}%")
                print()
        else:
            print("   Aucun nouvel événement HIGH détecté")
            print()
    
    conn.close()
    
    print("="*80)
    print("  CALCUL TERMINÉ")
    print("="*80)
    print()

def main():
    """Point d'entrée principal"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Calcule les métriques empiriques manquantes"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Calculer TOUS les événements sans score (pas seulement HIGH)"
    )
    
    args = parser.parse_args()
    
    priority_only = not args.all
    
    calculate_missing_scores(priority_only=priority_only)

if __name__ == "__main__":
    main()
