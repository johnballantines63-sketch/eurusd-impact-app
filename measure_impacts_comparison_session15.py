"""
PHASE 2 : MESURE IMPACTS - SESSION 15
Mesure impacts réels vs prédits (avec et sans amplification)

Pour chaque événement extrait :
1. Calculer impact prédit v8.7 (SANS amplification)
2. Calculer impact prédit v8.7.1 (AVEC amplification)
3. Mesurer impact réel depuis prices_1m (MFE 60 min)
4. Calculer écarts et amélioration
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
import numpy as np
from datetime import datetime, timedelta

# Ajouter le dossier src au PYTHONPATH pour importer les fonctions
src_path = Path(__file__).parent / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

# Importer les fonctions de v8.7.1
from sequence_multi_event_timeline_v87 import (
    calculate_surprise_percentage,
    calculate_amplification_factor
)

print("="*80)
print("📊 PHASE 2 : MESURE IMPACTS - SESSION 15")
print("="*80)

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Chargement données
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 1 : Chargement données")
print("─"*80)

# Charger événements extraits
events_df = pd.read_csv('extracted_events_session15.csv')
events_df['ts_utc'] = pd.to_datetime(events_df['ts_utc'])

print(f"✅ {len(events_df)} événements chargés depuis extracted_events_session15.csv")

# Connexion DB pour prix
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Fonctions de calcul
# ════════════════════════════════════════════════════════════════

def predict_impact_v9_clean(empirical_score, num_events=1):
    """
    Formule v9-CLEAN (sans amplification)
    """
    if num_events >= 2:
        return -10.47 + 0.477 * empirical_score
    else:
        return -7.08 + 0.419 * empirical_score

def calculate_real_impact_mfe(ts_utc, conn, window_minutes=60):
    """
    Calcule MFE (Maximum Favorable Excursion) sur fenêtre de temps
    Retourne impact en pips et direction
    """
    # Fenêtre de temps
    start_time = ts_utc
    end_time = ts_utc + timedelta(minutes=window_minutes)
    
    # Requête prix
    query = f"""
        SELECT 
            datetime,
            close
        FROM prices_1m
        WHERE datetime >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
          AND datetime < '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
        ORDER BY datetime
    """
    
    try:
        prices = conn.execute(query).fetchdf()
        
        if len(prices) < 2:
            return None, None
        
        # Prix de départ
        start_price = prices.iloc[0]['close']
        
        # Calculer MFE (max excursion favorable)
        max_price = prices['close'].max()
        min_price = prices['close'].min()
        
        # Impact UP et DOWN
        impact_up = (max_price - start_price) * 10000  # pips
        impact_down = (start_price - min_price) * 10000  # pips
        
        # Prendre le maximum (MFE)
        if impact_up > impact_down:
            return impact_up, 'UP'
        else:
            return impact_down, 'DOWN'
            
    except Exception as e:
        print(f"   ⚠️ Erreur calcul MFE : {e}")
        return None, None

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Calcul impacts pour chaque événement
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 3 : Calcul impacts (v8.7, v8.7.1, réel)")
print("─"*80)

results = []

for idx, row in events_df.iterrows():
    print(f"\n🔄 [{idx+1}/{len(events_df)}] {row['event_title']} - {row['ts_utc']}")
    
    # Impact prédit v8.7 (SANS amplification)
    impact_v87_brut = predict_impact_v9_clean(row['empirical_score'], num_events=1)
    impact_v87_corrige = abs(impact_v87_brut) * 0.758  # Facteur correction
    
    print(f"   📊 v8.7 (sans amplif) : {impact_v87_corrige:.2f} pips")
    
    # Impact prédit v8.7.1 (AVEC amplification)
    # Créer dict événement pour fonction calculate_surprise_percentage
    event_dict = {
        'actual': row['actual'],
        'estimate': row['estimate']
    }
    
    surprise_pct = calculate_surprise_percentage(event_dict)
    amplification_factor = calculate_amplification_factor(surprise_pct)
    
    # Appliquer amplification AVANT facteur correction
    impact_v871_amplifie = abs(impact_v87_brut) * amplification_factor
    impact_v871_corrige = impact_v871_amplifie * 0.758
    
    print(f"   📊 v8.7.1 (avec amplif ×{amplification_factor:.2f}) : {impact_v871_corrige:.2f} pips")
    
    # Impact réel (MFE)
    impact_reel, direction_reelle = calculate_real_impact_mfe(row['ts_utc'], conn, window_minutes=60)
    
    if impact_reel is not None:
        print(f"   📊 Réel (MFE 60 min) : {impact_reel:.2f} pips {direction_reelle}")
        
        # Calcul écarts
        ecart_v87 = abs(impact_v87_corrige - impact_reel)
        ecart_v871 = abs(impact_v871_corrige - impact_reel)
        
        ecart_pct_v87 = (ecart_v87 / impact_reel * 100) if impact_reel > 0 else 0
        ecart_pct_v871 = (ecart_v871 / impact_reel * 100) if impact_reel > 0 else 0
        
        # Amélioration
        amelioration_pct = ecart_pct_v87 - ecart_pct_v871
        
        print(f"   ✅ Écart v8.7   : {ecart_pct_v87:.1f}%")
        print(f"   ✅ Écart v8.7.1 : {ecart_pct_v871:.1f}%")
        print(f"   {'🎯' if amelioration_pct > 0 else '⚠️'} Amélioration : {amelioration_pct:+.1f} points")
        
    else:
        print(f"   ⚠️ Pas de données prix disponibles")
        impact_reel = None
        direction_reelle = None
        ecart_pct_v87 = None
        ecart_pct_v871 = None
        amelioration_pct = None
    
    # Stocker résultats
    results.append({
        'ts_utc': row['ts_utc'],
        'event_title': row['event_title'],
        'country': row['country'],
        'tranche': row['tranche'],
        'surprise_pct': row['surprise_pct'],
        'empirical_score': row['empirical_score'],
        'amplification_factor': amplification_factor,
        'impact_v87': impact_v87_corrige,
        'impact_v871': impact_v871_corrige,
        'impact_reel': impact_reel,
        'direction_reelle': direction_reelle,
        'ecart_pct_v87': ecart_pct_v87,
        'ecart_pct_v871': ecart_pct_v871,
        'amelioration_pct': amelioration_pct
    })

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Création DataFrame résultats
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 4 : Création DataFrame résultats")
print("─"*80)

results_df = pd.DataFrame(results)

# Filtrer événements avec données réelles
results_valides = results_df[results_df['impact_reel'].notna()].copy()

print(f"\n✅ {len(results_valides)} événements avec données réelles (sur {len(results_df)})")

if len(results_valides) == 0:
    print("❌ ERREUR : Aucun événement avec données réelles!")
    conn.close()
    sys.exit(1)

# Arrondir valeurs
for col in ['surprise_pct', 'amplification_factor', 'impact_v87', 'impact_v871', 'impact_reel']:
    if col in results_valides.columns:
        results_valides[col] = results_valides[col].round(2)

for col in ['ecart_pct_v87', 'ecart_pct_v871', 'amelioration_pct']:
    if col in results_valides.columns:
        results_valides[col] = results_valides[col].round(1)

# ════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Sauvegarde
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 5 : Sauvegarde résultats")
print("─"*80)

csv_path = 'impacts_comparison_session15.csv'
results_valides.to_csv(csv_path, index=False)

print(f"✅ Fichier sauvegardé : {csv_path}")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 6 : Statistiques globales
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 6 : Statistiques globales")
print("─"*80)

print("\n📊 STATISTIQUES GLOBALES :")
print(f"   MAE v8.7   : {results_valides['ecart_pct_v87'].mean():.1f}%")
print(f"   MAE v8.7.1 : {results_valides['ecart_pct_v871'].mean():.1f}%")
print(f"   Amélioration moyenne : {results_valides['amelioration_pct'].mean():+.1f} points")

print("\n📊 STATISTIQUES PAR TRANCHE :")
stats_tranche = results_valides.groupby('tranche').agg({
    'amelioration_pct': ['count', 'mean', 'min', 'max'],
    'ecart_pct_v87': 'mean',
    'ecart_pct_v871': 'mean'
}).round(1)

print(stats_tranche)

print("\n📋 MEILLEURS RÉSULTATS (top 5 améliorations) :")
top5 = results_valides.nlargest(5, 'amelioration_pct')[
    ['event_title', 'tranche', 'surprise_pct', 'amelioration_pct']
]
print(top5.to_string(index=False))

print("\n" + "="*80)
print("✅ PHASE 2 TERMINÉE")
print("="*80)
print(f"\n📁 Fichier créé : {csv_path}")
print("🚀 Prochaine étape : Phase 3 - Analyse statistique détaillée")

conn.close()
