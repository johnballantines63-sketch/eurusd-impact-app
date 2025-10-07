#!/usr/bin/env python3
"""
Calcule l'impact empirique réel de chaque événement
Basé sur l'analyse des 3 ans de données historiques

Métriques calculées:
1. Volatilité moyenne (pips)
2. Fréquence de réaction (%)
3. Latence moyenne (minutes)
4. Score composite d'impact
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def get_db_path():
    return "fx_impact_app/data/warehouse.duckdb"

def measure_event_impact(conn, event_key, country, threshold_pips=5.0, window_minutes=60):
    """Mesure l'impact réel d'un event_key spécifique"""
    
    # Récupérer toutes les occurrences de cet événement
    query = f"""
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
        
        # Récupérer les prix
        # Note: timestamp dans prices_1m est en epoch Unix (INT64)
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
    """Calcule un score composite d'impact empirique (0-100)"""
    
    if stats is None or stats['analyzed'] < 5:
        return 0
    
    # Composantes du score
    # 1. Volatilité (0-40 points) : 1 pip = 1 point, max 40
    volatility_score = min(stats['avg_movement'], 40)
    
    # 2. Fréquence de réaction (0-30 points)
    frequency_score = stats['reaction_rate'] * 30
    
    # 3. Rapidité (0-30 points) : plus rapide = mieux
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

def calculate_all_empirical_impacts():
    """Calcule l'impact empirique pour tous les événements"""
    
    conn = duckdb.connect(get_db_path())
    
    print("="*80)
    print("  CALCUL IMPACT EMPIRIQUE - ANALYSE DES DONNÉES RÉELLES")
    print("="*80)
    print()
    
    # 1. Ajouter les colonnes si elles n'existent pas
    print("📊 Ajout des colonnes empiriques...")
    
    try:
        conn.execute("""
            ALTER TABLE event_families 
            ADD COLUMN empirical_score DOUBLE
        """)
    except:
        pass  # Colonne existe déjà
    
    try:
        conn.execute("""
            ALTER TABLE event_families 
            ADD COLUMN empirical_impact VARCHAR
        """)
    except:
        pass
    
    try:
        conn.execute("""
            ALTER TABLE event_families 
            ADD COLUMN avg_movement_pips DOUBLE
        """)
    except:
        pass
    
    try:
        conn.execute("""
            ALTER TABLE event_families 
            ADD COLUMN reaction_rate DOUBLE
        """)
    except:
        pass
    
    try:
        conn.execute("""
            ALTER TABLE event_families 
            ADD COLUMN avg_latency_min DOUBLE
        """)
    except:
        pass
    
    try:
        conn.execute("""
            ALTER TABLE event_families 
            ADD COLUMN analyzed_occurrences INTEGER
        """)
    except:
        pass
    
    print("✅ Colonnes prêtes")
    print()
    
    # 2. Récupérer tous les événements à analyser
    print("📥 Chargement des événements...")
    
    events_to_analyze = conn.execute("""
        SELECT event_key, country, family, impact_level
        FROM event_families
        WHERE is_tradable = TRUE
        ORDER BY family, event_key
    """).fetchall()
    
    print(f"   {len(events_to_analyze)} événements à analyser")
    print()
    
    # 3. Analyser chaque événement
    print("🔬 Analyse en cours...")
    print()
    
    results = []
    analyzed = 0
    skipped = 0
    
    for i, (event_key, country, family, theoretical_impact) in enumerate(events_to_analyze, 1):
        if i % 20 == 0:
            print(f"   Progression: {i}/{len(events_to_analyze)} ({i/len(events_to_analyze)*100:.1f}%)")
        
        # Mesurer l'impact réel
        stats = measure_event_impact(conn, event_key, country)
        
        if stats is None or stats['analyzed'] < 5:
            skipped += 1
            continue
        
        # Calculer le score
        score = calculate_impact_score(stats)
        empirical_level = classify_impact_level(score)
        
        # Mettre à jour la base
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
        
        results.append({
            'event_key': event_key,
            'country': country,
            'family': family,
            'theoretical_impact': theoretical_impact,
            'empirical_impact': empirical_level,
            'score': score,
            'avg_movement': stats['avg_movement'],
            'reaction_rate': stats['reaction_rate'],
            'avg_latency': stats['avg_latency']
        })
        
        analyzed += 1
    
    print(f"\n✅ Analyse terminée:")
    print(f"   Analysés: {analyzed}")
    print(f"   Sautés (données insuffisantes): {skipped}")
    print()
    
    # 4. Statistiques comparatives
    print("="*80)
    print("  COMPARAISON THÉORIQUE vs EMPIRIQUE")
    print("="*80)
    print()
    
    comparison = conn.execute("""
        SELECT 
            impact_level as theoretical,
            empirical_impact as empirical,
            COUNT(*) as count,
            AVG(empirical_score) as avg_score,
            AVG(avg_movement_pips) as avg_movement,
            AVG(reaction_rate) as avg_reaction_rate
        FROM event_families
        WHERE empirical_score IS NOT NULL
        GROUP BY impact_level, empirical_impact
        ORDER BY 
            CASE impact_level WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
            CASE empirical_impact WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END
    """).fetchall()
    
    print("Théorique → Empirique | Événements | Score Moy | Mouv. Moy | Taux Réaction")
    print("-" * 80)
    for theo, emp, count, score, movement, reaction in comparison:
        print(f"{theo:8} → {emp:8} | {count:10} | {score:9.1f} | {movement:9.1f} | {reaction*100:12.1f}%")
    
    # 5. Top 20 événements par score empirique
    print()
    print("="*80)
    print("  TOP 20 ÉVÉNEMENTS PAR IMPACT EMPIRIQUE RÉEL")
    print("="*80)
    print()
    
    top_events = conn.execute("""
        SELECT 
            event_key,
            country,
            family,
            impact_level as theoretical,
            empirical_impact as empirical,
            empirical_score,
            avg_movement_pips,
            reaction_rate,
            avg_latency_min
        FROM event_families
        WHERE empirical_score IS NOT NULL
        ORDER BY empirical_score DESC
        LIMIT 20
    """).fetchall()
    
    for i, row in enumerate(top_events, 1):
        event_key, country, family, theo, emp, score, movement, reaction, latency = row
        print(f"{i:2}. [{country}] {event_key[:50]}")
        print(f"    Famille: {family} | Score: {score:.1f} | Théo: {theo} → Emp: {emp}")
        print(f"    Mouvement: {movement:.1f} pips | Réaction: {reaction*100:.0f}% | Latence: {latency:.1f}min")
        print()
    
    # 6. Événements surévalués (théoriquement HIGH mais empiriquement LOW)
    print("="*80)
    print("  ÉVÉNEMENTS SURÉVALUÉS (Théo HIGH → Emp MEDIUM/LOW)")
    print("="*80)
    print()
    
    overrated = conn.execute("""
        SELECT 
            event_key,
            country,
            family,
            empirical_score,
            avg_movement_pips,
            reaction_rate
        FROM event_families
        WHERE impact_level = 'HIGH'
            AND empirical_impact IN ('MEDIUM', 'LOW')
            AND empirical_score IS NOT NULL
        ORDER BY empirical_score ASC
        LIMIT 15
    """).fetchall()
    
    if len(overrated) > 0:
        for event_key, country, family, score, movement, reaction in overrated:
            print(f"[{country}] {event_key[:55]}")
            print(f"  Score: {score:.1f} | Mouv: {movement:.1f} pips | Réaction: {reaction*100:.0f}%")
            print()
    else:
        print("  Aucun événement surévalué détecté")
    
    # 7. Événements sous-évalués (théoriquement MEDIUM mais empiriquement HIGH)
    print("="*80)
    print("  ÉVÉNEMENTS SOUS-ÉVALUÉS (Théo MEDIUM → Emp HIGH)")
    print("="*80)
    print()
    
    underrated = conn.execute("""
        SELECT 
            event_key,
            country,
            family,
            empirical_score,
            avg_movement_pips,
            reaction_rate
        FROM event_families
        WHERE impact_level = 'MEDIUM'
            AND empirical_impact = 'HIGH'
            AND empirical_score IS NOT NULL
        ORDER BY empirical_score DESC
        LIMIT 15
    """).fetchall()
    
    if len(underrated) > 0:
        for event_key, country, family, score, movement, reaction in underrated:
            print(f"[{country}] {event_key[:55]}")
            print(f"  Score: {score:.1f} | Mouv: {movement:.1f} pips | Réaction: {reaction*100:.0f}%")
            print()
    else:
        print("  Aucun événement sous-évalué détecté")
    
    # 8. Recommandations
    print("="*80)
    print("  RECOMMANDATIONS DE TRADING")
    print("="*80)
    print()
    
    high_score_events = conn.execute("""
        SELECT COUNT(*)
        FROM event_families
        WHERE empirical_score >= 70
    """).fetchone()[0]
    
    medium_score_events = conn.execute("""
        SELECT COUNT(*)
        FROM event_families
        WHERE empirical_score >= 40 AND empirical_score < 70
    """).fetchone()[0]
    
    print(f"📊 Distribution des scores empiriques:")
    print(f"   Score ≥ 70 (HIGH)  : {high_score_events} événements")
    print(f"   Score 40-69 (MEDIUM): {medium_score_events} événements")
    print()
    print("💡 Recommandations:")
    print("   1. Privilégier les événements avec empirical_score ≥ 60")
    print("   2. Ignorer les événements avec empirical_score < 30")
    print("   3. Utiliser empirical_impact au lieu de impact_level pour filtrer")
    print()
    print("📝 Exemple de requête optimale:")
    print("""
    SELECT e.ts_utc, e.event_key, ef.empirical_score, ef.avg_movement_pips
    FROM events e
    JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE ef.empirical_score >= 60
        AND e.actual IS NOT NULL
    ORDER BY e.ts_utc DESC
    """)
    
    conn.close()
    
    print()
    print("="*80)
    print("  ANALYSE TERMINÉE")
    print("="*80)
    print()

if __name__ == "__main__":
    calculate_all_empirical_impacts()
