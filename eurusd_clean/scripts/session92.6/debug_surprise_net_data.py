#!/usr/bin/env python3
"""
Debug Surprise Nette - CORRIGÉ avec bons filtres
"""
from pathlib import Path
import duckdb
import pandas as pd

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

DATES_TO_CHECK = [
    "2025-01-15",
    "2025-05-13", 
    "2025-07-15",
    "2025-09-11"
]

def check_events_data(date_str: str):
    """Vérifie les données événements pour une date."""
    
    print(f"\n{'='*80}")
    print(f"DATE : {date_str}")
    print(f"{'='*80}")
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Requête événements - FILTRE CORRIGÉ
        query = """
        SELECT 
            e.ts_utc,
            e.event_title,
            e.event_key,
            e.actual,
            e.estimate,
            e.previous,
            e.importance_n,
            ef.family,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
        ORDER BY e.ts_utc
        """
        
        df = conn.execute(query, [date_str]).fetchdf()
        
        if df.empty:
            print(f"❌ AUCUN ÉVÉNEMENT TROUVÉ pour {date_str}")
            print(f"   (Recherche: empirical_score > 40)")
            return
        
        print(f"\nNombre d'événements : {len(df)}")
        print(f"(Filtre: empirical_score > 40, country = 'US')")
        print("\n" + "─"*80)
        
        # Analyser chaque événement
        surprise_net = 0.0
        events_with_data = 0
        events_missing_data = 0
        
        for idx, row in df.iterrows():
            event_name = row['event_title'] if pd.notna(row['event_title']) else f"[{row['event_key']}]"
            
            print(f"\nÉvénement {idx+1} : {event_name}")
            print(f"  Family      : {row['family']}")
            print(f"  Time        : {row['ts_utc']}")
            print(f"  Importance  : {row['importance_n']}")
            print(f"  Emp. Score  : {row['empirical_score']:.1f}")
            print(f"  Actual      : {row['actual']}")
            print(f"  Estimate    : {row['estimate']}")
            print(f"  Previous    : {row['previous']}")
            
            # Calculer surprise pour cet événement
            actual = row['actual']
            estimate = row['estimate']
            
            if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
                surprise_signed = ((actual - estimate) / abs(estimate)) * 100
                surprise_net += surprise_signed
                events_with_data += 1
                print(f"  ✅ Surprise : {surprise_signed:+.1f}%")
            else:
                events_missing_data += 1
                reasons = []
                if pd.isna(actual):
                    reasons.append("actual=NULL")
                if pd.isna(estimate):
                    reasons.append("estimate=NULL")
                if estimate == 0:
                    reasons.append("estimate=0")
                print(f"  ❌ Surprise : Non calculable ({', '.join(reasons)})")
        
        print("\n" + "─"*80)
        print(f"\nRÉSUMÉ :")
        print(f"  Total événements        : {len(df)}")
        print(f"  Avec données complètes  : {events_with_data}")
        print(f"  Données manquantes      : {events_missing_data}")
        
        if events_with_data > 0:
            print(f"  Surprise nette calculée : {surprise_net:+.1f}%")
            
            # Calculer surprise MAX pour comparaison
            surprises_abs = []
            for _, row in df.iterrows():
                actual = row['actual']
                estimate = row['estimate']
                if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
                    surprise_abs = abs((actual - estimate) / estimate) * 100
                    surprises_abs.append(surprise_abs)
            
            if surprises_abs:
                max_surprise = max(surprises_abs)
                print(f"  Surprise MAX (abs)      : {max_surprise:.1f}%")
        
        if events_with_data == 0:
            print(f"\n❌ PROBLÈME : Aucun événement avec actual/estimate valides")
            print(f"   → surprise_net = NaN attendu")
        elif events_missing_data > 0:
            print(f"\n⚠️  ATTENTION : {events_missing_data} événements sans données complètes")
    
    finally:
        conn.close()

def main():
    """Fonction principale."""
    
    print("="*80)
    print("DEBUG SURPRISE NETTE - VÉRIFICATION DONNÉES DB (CORRIGÉ)")
    print("="*80)
    print(f"\nBase de données : {DB_PATH}")
    print(f"Dates à vérifier : {', '.join(DATES_TO_CHECK)}")
    print(f"\n⚠️  Filtre utilisé : empirical_score > 40 (pas importance_n)")
    
    for date_str in DATES_TO_CHECK:
        check_events_data(date_str)
    
    print("\n" + "="*80)
    print("DEBUG TERMINÉ")
    print("="*80)

if __name__ == "__main__":
    main()
