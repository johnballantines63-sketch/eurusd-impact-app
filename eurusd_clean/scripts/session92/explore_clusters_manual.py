"""
EXPLORATION MANUELLE CLUSTERS - Session 92
Analyser 3-5 clusters répétés pour comprendre la relation surprise vectorielle → impact
"""

import duckdb
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Configuration
DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

print("="*100)
print("🔬 EXPLORATION MANUELLE - CLUSTERS RÉPÉTÉS")
print("="*100)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# ============================================================================
# ÉTAPE 1 : IDENTIFIER TOP 5 CLUSTERS LES PLUS RÉPÉTÉS
# ============================================================================

print("\n📊 Étape 1 : Identifier top 5 clusters les plus répétés...\n")

query_top_clusters = """
WITH cluster_composition AS (
    SELECT 
        DATE(e.ts_utc) as event_date,
        strftime(e.ts_utc, '%H:%M') as event_time,
        STRING_AGG(e.event_key, '|' ORDER BY e.event_key) as event_keys_signature,
        STRING_AGG(e.event_title, ' + ' ORDER BY e.event_title) as event_titles,
        COUNT(DISTINCT e.event_key) as num_events,
        e.country
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.country = 'US'
        AND ef.empirical_score > 40
        AND DATE(e.ts_utc) >= '2020-01-01'
        AND DATE(e.ts_utc) <= '2025-12-31'
    GROUP BY DATE(e.ts_utc), strftime(e.ts_utc, '%H:%M'), e.country
    HAVING COUNT(DISTINCT e.event_key) >= 3
)
SELECT 
    event_keys_signature,
    event_titles,
    num_events,
    COUNT(*) as occurrences
FROM cluster_composition
GROUP BY event_keys_signature, event_titles, num_events
HAVING COUNT(*) >= 5
ORDER BY COUNT(*) DESC
LIMIT 5
"""

df_top = conn.execute(query_top_clusters).df()

print(f"✅ Top 5 clusters trouvés (≥5 occurrences chacun)\n")

for idx, row in df_top.iterrows():
    print(f"🔹 Cluster #{idx+1}")
    print(f"   Events : {row['num_events']}")
    print(f"   Occurrences : {row['occurrences']}")
    print(f"   Composition : {row['event_titles'][:80]}")
    print()

# ============================================================================
# ÉTAPE 2 : ANALYSE DÉTAILLÉE DE CHAQUE CLUSTER
# ============================================================================

print("\n" + "="*100)
print("🔬 ANALYSE DÉTAILLÉE PAR CLUSTER")
print("="*100)

for cluster_idx, cluster_row in df_top.iterrows():
    signature = cluster_row['event_keys_signature']
    num_events = cluster_row['num_events']
    
    print(f"\n\n{'='*100}")
    print(f"📦 CLUSTER #{cluster_idx+1} : {num_events} events simultanés")
    print(f"   Composition : {cluster_row['event_titles']}")
    print('='*100)
    
    # Récupérer toutes les occurrences de ce cluster
    query_occurrences = f"""
    SELECT 
        DATE(e.ts_utc) as event_date,
        strftime(e.ts_utc, '%H:%M') as event_time
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.country = 'US'
        AND ef.empirical_score > 40
    GROUP BY DATE(e.ts_utc), strftime(e.ts_utc, '%H:%M')
    HAVING STRING_AGG(e.event_key, '|' ORDER BY e.event_key) = '{signature}'
    ORDER BY event_date DESC
    """
    
    df_occurrences = conn.execute(query_occurrences).df()
    
    print(f"\n📅 {len(df_occurrences)} occurrences trouvées\n")
    
    # Pour chaque occurrence, collecter données détaillées
    occurrence_data = []
    
    for occ_idx, occ_row in df_occurrences.iterrows():
        date = occ_row['event_date']
        time = occ_row['event_time']
        
        # Extraire juste la date (YYYY-MM-DD) si c'est un datetime
        if hasattr(date, 'date'):
            date_str = date.date().isoformat()
        else:
            date_str = str(date).split()[0]  # Prendre juste YYYY-MM-DD
        
        print(f"\n   🗓️  OCCURRENCE #{occ_idx+1} : {date} {time}")
        print(f"   " + "-"*90)
        
        # Récupérer détails des events
        query_events = f"""
        SELECT 
            e.event_key,
            e.event_title,
            e.actual,
            e.estimate,
            e.forecast,
            e.previous,
            ef.family
        FROM events e
        LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
        WHERE DATE(e.ts_utc) = '{date_str}'
            AND strftime(e.ts_utc, '%H:%M') = '{time}'
            AND e.country = 'US'
        ORDER BY e.event_key
        """
        
        df_events = conn.execute(query_events).df()
        
        # Calculer surprises individuelles
        surprises_individual = []
        surprises_data = []
        
        for _, evt in df_events.iterrows():
            actual = evt['actual']
            estimate = evt['estimate'] if pd.notna(evt['estimate']) else evt.get('previous')
            if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
                surprise_raw = ((actual - estimate) / estimate) * 100
                surprise_abs = abs(surprise_raw)
                direction = 1 if surprise_raw > 0 else -1
                
                surprises_individual.append(surprise_abs)
                surprises_data.append({
                    'event': evt['event_title'][:30] if evt['event_title'] else 'N/A',
                    'actual': actual,
                    'estimate': estimate,
                    'surprise_%': surprise_abs,
                    'direction': direction
                })
                
                title = evt['event_title'][:40] if evt['event_title'] else 'N/A'
                print(f"      • {title:40} | "
                      f"Actual={actual:>8.2f} Est={estimate:>8.2f} | "
                      f"Surprise={surprise_abs:>6.1f}% Dir={direction:>2}")
        
        # Calculer différentes méthodes de surprise globale
        if len(surprises_individual) > 0:
            # Méthode A : Vectorielle (Session 51-55)
            surprise_vectorielle = np.sqrt(sum(s**2 for s in surprises_individual))
            
            # Méthode B : Maximum
            surprise_max = max(surprises_individual)
            
            # Méthode C : Moyenne
            surprise_mean = np.mean(surprises_individual)
            
            # Méthode D : Somme simple
            surprise_sum = sum(surprises_individual)
            
            print(f"\n      📊 SURPRISES GLOBALES CALCULÉES :")
            print(f"         Méthode A (Vectorielle)  : {surprise_vectorielle:>6.1f}%")
            print(f"         Méthode B (Maximum)      : {surprise_max:>6.1f}%")
            print(f"         Méthode C (Moyenne)      : {surprise_mean:>6.1f}%")
            print(f"         Méthode D (Somme)        : {surprise_sum:>6.1f}%")
        else:
            surprise_vectorielle = 0
            surprise_max = 0
            surprise_mean = 0
            surprise_sum = 0
            print(f"\n      ⚠️  Aucune surprise calculable (données manquantes)")
        
        # Mesurer impact réel
        # date_str déjà défini au début de la boucle
        query_prices = f"""
        SELECT datetime, open, high, low 
        FROM prices_1m
        WHERE datetime >= '{date_str} {time}:00+02:00'::TIMESTAMP
          AND datetime <= '{date_str} {time}:00+02:00'::TIMESTAMP + INTERVAL '60 minutes'
        ORDER BY datetime
        LIMIT 60
        """
        
        try:
            df_prices = conn.execute(query_prices).df()
            
            if not df_prices.empty and len(df_prices) >= 5:
                start_price = df_prices.iloc[0]['open']
                impact_down = abs(start_price - df_prices['low'].min()) * 10000
                impact_up = abs(df_prices['high'].max() - start_price) * 10000
                impact_real = max(impact_down, impact_up)
                
                print(f"\n      💥 IMPACT RÉEL : {impact_real:.1f} pips")
                print(f"         (Up={impact_up:.1f}p, Down={impact_down:.1f}p)")
                
                # Stocker pour analyse
                occurrence_data.append({
                    'date': date_str,
                    'time': time,
                    'impact_real': impact_real,
                    'surprise_vectorielle': surprise_vectorielle,
                    'surprise_max': surprise_max,
                    'surprise_mean': surprise_mean,
                    'surprise_sum': surprise_sum,
                    'num_events': len(surprises_individual)
                })
            else:
                print(f"\n      ❌ Pas de données prix disponibles")
        except Exception as e:
            print(f"\n      ❌ Erreur lecture prix : {e}")
    
    # ============================================================================
    # ANALYSE CORRÉLATIONS POUR CE CLUSTER
    # ============================================================================
    
    if len(occurrence_data) >= 3:
        print(f"\n\n   {'='*90}")
        print(f"   📈 ANALYSE CORRÉLATIONS (N={len(occurrence_data)} occurrences)")
        print(f"   {'='*90}\n")
        
        df_occ = pd.DataFrame(occurrence_data)
        
        # Calculer corrélations
        corr_vectorielle = df_occ['surprise_vectorielle'].corr(df_occ['impact_real'])
        corr_max = df_occ['surprise_max'].corr(df_occ['impact_real'])
        corr_mean = df_occ['surprise_mean'].corr(df_occ['impact_real'])
        corr_sum = df_occ['surprise_sum'].corr(df_occ['impact_real'])
        
        print(f"   Corrélation Surprise → Impact :")
        print(f"      Méthode A (Vectorielle) : r = {corr_vectorielle:>5.3f} {'🟢' if abs(corr_vectorielle) > 0.7 else '🟡' if abs(corr_vectorielle) > 0.4 else '🔴'}")
        print(f"      Méthode B (Maximum)     : r = {corr_max:>5.3f} {'🟢' if abs(corr_max) > 0.7 else '🟡' if abs(corr_max) > 0.4 else '🔴'}")
        print(f"      Méthode C (Moyenne)     : r = {corr_mean:>5.3f} {'🟢' if abs(corr_mean) > 0.7 else '🟡' if abs(corr_mean) > 0.4 else '🔴'}")
        print(f"      Méthode D (Somme)       : r = {corr_sum:>5.3f} {'🟢' if abs(corr_sum) > 0.7 else '🟡' if abs(corr_sum) > 0.4 else '🔴'}")
        
        # Identifier meilleure méthode
        correlations = {
            'Vectorielle': abs(corr_vectorielle),
            'Maximum': abs(corr_max),
            'Moyenne': abs(corr_mean),
            'Somme': abs(corr_sum)
        }
        best_method = max(correlations, key=correlations.get)
        best_corr = correlations[best_method]
        
        print(f"\n   🏆 MEILLEURE MÉTHODE : {best_method} (|r| = {best_corr:.3f})")
        
        # Statistiques impact
        impact_mean = df_occ['impact_real'].mean()
        impact_std = df_occ['impact_real'].std()
        impact_cv = (impact_std / impact_mean * 100) if impact_mean > 0 else 0
        
        print(f"\n   📊 STATISTIQUES IMPACT :")
        print(f"      Moyenne : {impact_mean:.1f} pips")
        print(f"      Écart-type : {impact_std:.1f} pips")
        print(f"      CV% : {impact_cv:.1f}% {'✅ (stable)' if impact_cv < 50 else '⚠️ (variable)'}")
        
        # Afficher tableau détaillé
        print(f"\n   📋 TABLEAU DÉTAILLÉ :")
        print(f"   {'Date':>12} {'Surp.Vect':>11} {'Surp.Max':>10} {'Surp.Moy':>10} {'Surp.Sum':>10} {'Impact':>8}")
        print(f"   {'-'*80}")
        for _, row in df_occ.iterrows():
            print(f"   {row['date']:>12} {row['surprise_vectorielle']:>10.1f}% {row['surprise_max']:>10.1f}% "
                  f"{row['surprise_mean']:>10.1f}% {row['surprise_sum']:>10.1f}% {row['impact_real']:>7.1f}p")

conn.close()

# ============================================================================
# SYNTHÈSE FINALE
# ============================================================================

print("\n\n" + "="*100)
print("🎯 SYNTHÈSE EXPLORATION MANUELLE")
print("="*100)

print("""
Cette exploration permet de répondre aux questions :

1. Quelle méthode de calcul de surprise_globale maximise la corrélation avec l'impact ?
   → Comparer les 4 corrélations par cluster

2. La méthode optimale est-elle universelle ou spécifique par type ?
   → Si même méthode gagne partout = universelle
   → Si varie = besoin approche adaptative

3. Les impacts sont-ils stables pour même cluster + même surprise_globale ?
   → CV% faible + haute corrélation = OUI, hypothèse validée
   → CV% élevé OU faible corrélation = NON, besoin affinement

PROCHAINES ÉTAPES selon résultats :
- Si méthode universelle trouvée → Implémenter dans formulas.py
- Si méthode spécifique → Créer lookup par type event
- Si corrélations faibles → Revoir hypothèse ou enrichir features
""")

print("\n✅ EXPLORATION TERMINÉE")
print("="*100)
