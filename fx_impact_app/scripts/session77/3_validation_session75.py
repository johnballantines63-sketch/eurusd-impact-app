#!/usr/bin/env python3
"""
VALIDATION SESSION 75 - SESSION 77
=================================

Test formules V2 calibrées sur 7 mouvements qualité Session 75.

Objectif : MAE < 32 pips (amélioration 50% vs Session 75)
          MAE Session 75 V1 : 64.9 pips
          Cible V2 : 32 pips

Bonus : Chercher meilleur résultat possible !

Date : 25 octobre 2025
Session : 77
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

SCRIPT_DIR = Path(__file__).parent
DB_PATH = ROOT_DIR / "data" / "warehouse.duckdb"


# ════════════════════════════════════════════════════════════════
# IMPORTER FONCTIONS SESSION 77
# ════════════════════════════════════════════════════════════════

FAMILY_SENTIMENT = {
    'NFP': -1, 'Unemployment_Rate': 1, 'Average_Hourly_Earnings': -1,
    'CPI': 1, 'Core_CPI': 1, 'PPI': 1, 'Core_PPI': 1,
    'Retail_Sales': -1, 'GDP': -1, 'ISM_Manufacturing_PMI': -1,
    'ISM_Services_PMI': -1, 'Consumer_Confidence': -1,
    'Durable_Goods_Orders': -1, 'Trade_Balance': -1,
    'Industrial_Production': -1, 'Housing_Starts': -1,
    'Building_Permits': -1, 'Existing_Home_Sales': -1,
    'New_Home_Sales': -1, 'Jobless_Claims': 1,
    'Continuing_Claims': 1, 'Core_PCE_Price_Index': 1,
    'ECB_Interest_Rate_Decision': 1, 'ECB_Press_Conference': 1,
    'EU_CPI': -1, 'EU_Core_CPI': -1, 'EU_GDP': -1,
    'EU_Unemployment_Rate': 1, 'German_IFO_Business_Climate': -1,
    'German_ZEW_Economic_Sentiment': -1, 'German_GDP': -1,
    'German_CPI': -1, 'BOE_Interest_Rate_Decision': 0,
    'UK_CPI': 0, 'UK_GDP': 0, 'UK_Unemployment_Rate': 0,
    'Michigan_Consumer_Sentiment': -1, 'CB_Consumer_Confidence': -1,
    'ADP_Employment_Change': -1, 'Philadelphia_Fed_Manufacturing_Index': -1,
    'Chicago_PMI': -1, 'Factory_Orders': -1, 'Wholesale_Inventories': -1,
}


def calculate_adjusted_empirical_score(base_score: float, surprise_pct: float) -> float:
    """Score ajusté par surprise (Session 55)"""
    if surprise_pct < 5:
        factor = 1.0
    elif surprise_pct < 15:
        factor = 1.0 + (surprise_pct - 5) / 10 * 0.5
    elif surprise_pct < 30:
        factor = 1.5 + (surprise_pct - 15) / 15 * 0.4
    else:
        factor = 1.9
    return base_score * factor


def calculate_amplification_factor(score_ajuste: float, surprise_pct: float) -> float:
    """Facteur amplification surprise (Sessions 14-15)"""
    if score_ajuste < 40:
        return 1.0
    surprise_capped = min(surprise_pct, 30.0)
    if surprise_capped < 5:
        return 1.0
    elif surprise_capped < 15:
        return 1.0 + (surprise_capped - 5) / 10 * 1.5
    else:
        return 2.5


def calculate_impact_with_params(
    events_cluster: List[Dict],
    intercept_multi: float,
    coef_multi: float,
    intercept_single: float,
    coef_single: float
) -> float:
    """Calcule impact avec paramètres donnés (structure Sessions 51-55)"""
    if not events_cluster:
        return 0.0
    
    nb_events = len(events_cluster)
    surprise_max = max(e.get('surprise_pct', 0) for e in events_cluster)
    
    # Impacts individuels
    impacts_signes = []
    for event in events_cluster:
        score_base = event.get('empirical_score', 0)
        surprise_pct = event.get('surprise_pct', 0)
        score_ajuste = calculate_adjusted_empirical_score(score_base, surprise_pct)
        
        if nb_events >= 2:
            impact_brut = intercept_multi + coef_multi * score_ajuste
        else:
            impact_brut = intercept_single + coef_single * score_ajuste
        
        famille = event.get('family', 'Unknown')
        direction = FAMILY_SENTIMENT.get(famille, 0)
        impact_signe = impact_brut * direction
        impacts_signes.append(impact_signe)
    
    # Somme vectorielle
    impact_total = sum(impacts_signes)
    
    # Amplification
    scores_ajustes = [
        calculate_adjusted_empirical_score(e.get('empirical_score', 0), e.get('surprise_pct', 0))
        for e in events_cluster
    ]
    score_ajuste_moyen = np.mean(scores_ajustes)
    amplification = calculate_amplification_factor(score_ajuste_moyen, surprise_max)
    impact_amplifie = impact_total * amplification
    
    # Correction 0.758
    impact_final = abs(impact_amplifie) * 0.758
    
    return impact_final


def reconstitute_event_cluster(
    movement_row: pd.Series,
    conn: duckdb.DuckDBPyConnection
) -> List[Dict]:
    """Reconstruit cluster événements pour 1 mouvement"""
    date_str = movement_row['date']
    time_str = movement_row['time']
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    start_time = dt - timedelta(minutes=130)
    end_time = dt + timedelta(minutes=130)
    
    query = f"""
    SELECT 
        e.event_key, e.event_title, e.country,
        e.actual, e.previous, e.estimate, e.forecast,
        AVG(ef.empirical_score) as empirical_score,
        MIN(ef.family) as family
    FROM events e
    INNER JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
      AND e.ts_utc <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
    GROUP BY e.event_key, e.event_title, e.country, e.actual, e.previous, e.estimate, e.forecast, e.ts_utc
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query).fetchdf()
    
    if df_events.empty:
        return []
    
    events = []
    for _, row in df_events.iterrows():
        actual = row.get('actual')
        estimate = row.get('estimate') or row.get('forecast') or row.get('previous')
        
        surprise_pct = 0.0
        if actual is not None and estimate is not None and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
        
        event = {
            'event_key': row.get('event_key', ''),
            'event_title': row.get('event_title', ''),
            'family': row.get('family', 'Unknown'),
            'empirical_score': row.get('empirical_score', 0),
            'surprise_pct': surprise_pct,
            'actual': actual,
            'estimate': estimate
        }
        events.append(event)
    
    return events


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print()
    print("=" * 60)
    print("VALIDATION SESSION 75 - SESSION 77")
    print("=" * 60)
    print()
    
    # ════════════════════════════════════════════════════════════════
    # CHARGER PARAMÈTRES CALIBRÉS
    # ════════════════════════════════════════════════════════════════
    
    PARAMS_FILE = SCRIPT_DIR / "calibration_results_session77.txt"
    
    if not PARAMS_FILE.exists():
        print(f"❌ Fichier paramètres non trouvé : {PARAMS_FILE.name}")
        print(f"   → Exécuter d'abord 1_grid_search_calibration.py")
        return 1
    
    print(f"📂 Chargement paramètres calibrés...")
    
    # Parser fichier résultats
    with open(PARAMS_FILE, 'r') as f:
        content = f.read()
    
    import re
    intercept_multi_v2 = float(re.search(r'intercept_multi\s+:\s+([-\d.]+)', content).group(1))
    coef_multi_v2 = float(re.search(r'coef_multi\s+:\s+([-\d.]+)', content).group(1))
    intercept_single_v2 = float(re.search(r'intercept_single\s+:\s+([-\d.]+)', content).group(1))
    coef_single_v2 = float(re.search(r'coef_single\s+:\s+([-\d.]+)', content).group(1))
    
    print(f"✅ Paramètres V2 chargés")
    print()
    
    # ════════════════════════════════════════════════════════════════
    # CHARGER DATASET SESSION 75
    # ════════════════════════════════════════════════════════════════
    
    DATASET_PATH = SCRIPT_DIR.parent / "session75" / "dataset_session75_filtered.csv"
    
    if not DATASET_PATH.exists():
        print(f"❌ Dataset Session 75 non trouvé : {DATASET_PATH}")
        return 1
    
    print(f"📂 Dataset : {DATASET_PATH.name}")
    df_s75 = pd.read_csv(DATASET_PATH)
    print(f"✅ {len(df_s75)} mouvements chargés")
    print()
    
    # ════════════════════════════════════════════════════════════════
    # CONNEXION DB
    # ════════════════════════════════════════════════════════════════
    
    if not DB_PATH.exists():
        print(f"❌ Base de données non trouvée : {DB_PATH}")
        return 1
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ════════════════════════════════════════════════════════════════
    # CALCUL IMPACTS V1 et V2
    # ════════════════════════════════════════════════════════════════
    
    print("🎯 CALCUL IMPACTS")
    print("=" * 60)
    
    impacts_v1 = []
    impacts_v2 = []
    impacts_real = []
    details = []
    
    for i, row in df_s75.iterrows():
        # Reconstituer cluster
        events = reconstitute_event_cluster(row, conn)
        
        if not events:
            print(f"⚠️  Mouvement {i+1} : Aucun événement trouvé")
            continue
        
        # Impact réel
        impact_real = row['impact_pips']
        impacts_real.append(impact_real)
        
        # Impact V1
        impact_v1 = calculate_impact_with_params(
            events,
            intercept_multi=-10.47,
            coef_multi=0.477,
            intercept_single=-7.08,
            coef_single=0.419
        )
        impacts_v1.append(impact_v1)
        
        # Impact V2
        impact_v2 = calculate_impact_with_params(
            events,
            intercept_multi=intercept_multi_v2,
            coef_multi=coef_multi_v2,
            intercept_single=intercept_single_v2,
            coef_single=coef_single_v2
        )
        impacts_v2.append(impact_v2)
        
        # Détails
        mae_v1 = abs(impact_v1 - impact_real)
        mae_v2 = abs(impact_v2 - impact_real)
        
        details.append({
            'date': row['date'],
            'time': row['time'],
            'nb_events': len(events),
            'impact_real': impact_real,
            'impact_v1': impact_v1,
            'mae_v1': mae_v1,
            'impact_v2': impact_v2,
            'mae_v2': mae_v2,
            'delta_mae': mae_v2 - mae_v1
        })
        
        print(f"Mouvement {i+1} : {row['date']} {row['time']}")
        print(f"  Réel : {impact_real:.1f} pips | V1 : {impact_v1:.1f} ({mae_v1:.1f}) | V2 : {impact_v2:.1f} ({mae_v2:.1f})")
    
    conn.close()
    
    print()
    
    # ════════════════════════════════════════════════════════════════
    # MÉTRIQUES GLOBALES
    # ════════════════════════════════════════════════════════════════
    
    mae_v1_global = np.mean([abs(v1 - real) for v1, real in zip(impacts_v1, impacts_real)])
    mae_v2_global = np.mean([abs(v2 - real) for v2, real in zip(impacts_v2, impacts_real)])
    
    print("📊 MÉTRIQUES GLOBALES")
    print("=" * 60)
    print(f"MAE V1 (Sessions 51-55) : {mae_v1_global:.1f} pips")
    print(f"MAE V2 (calibré S77)    : {mae_v2_global:.1f} pips")
    print()
    
    # Amélioration
    delta_mae = mae_v2_global - mae_v1_global
    if delta_mae < 0:
        print(f"✅ Amélioration : {abs(delta_mae):.1f} pips ({abs(delta_mae)/mae_v1_global*100:.1f}%)")
    elif delta_mae > 0:
        print(f"⚠️  Dégradation : +{delta_mae:.1f} pips (+{delta_mae/mae_v1_global*100:.1f}%)")
    else:
        print(f"➡️  Identique")
    print()
    
    # ════════════════════════════════════════════════════════════════
    # CRITÈRES SUCCÈS
    # ════════════════════════════════════════════════════════════════
    
    print("🎯 CRITÈRES SUCCÈS")
    print("=" * 60)
    
    # Objectif Session 75
    mae_s75_original = 64.9
    target_50pct = 32.0
    
    print(f"MAE Session 75 original : {mae_s75_original:.1f} pips")
    print(f"Cible 50% amélioration  : {target_50pct:.1f} pips")
    print()
    
    if mae_v2_global < target_50pct:
        improvement_pct = (mae_s75_original - mae_v2_global) / mae_s75_original * 100
        print(f"✅ OBJECTIF ATTEINT : {mae_v2_global:.1f} pips < {target_50pct:.1f} pips")
        print(f"   Amélioration vs S75 : {improvement_pct:.1f}%")
        status = "SUCCÈS"
    elif mae_v2_global < 40:
        improvement_pct = (mae_s75_original - mae_v2_global) / mae_s75_original * 100
        print(f"⚠️  PROCHE OBJECTIF : {mae_v2_global:.1f} pips (cible {target_50pct:.1f})")
        print(f"   Amélioration vs S75 : {improvement_pct:.1f}%")
        status = "ACCEPTABLE"
    else:
        print(f"❌ OBJECTIF NON ATTEINT : {mae_v2_global:.1f} pips > {target_50pct:.1f} pips")
        status = "INSUFFISANT"
    
    print()
    
    # Comparaison V1 vs V2
    print("Comparaison V1 vs V2 :")
    if mae_v2_global < mae_v1_global:
        print(f"✅ V2 meilleur que V1 : -{abs(delta_mae):.1f} pips")
    elif mae_v2_global > mae_v1_global:
        print(f"❌ V2 moins bon que V1 : +{delta_mae:.1f} pips")
    else:
        print(f"➡️  V2 identique à V1")
    
    print()
    
    # ════════════════════════════════════════════════════════════════
    # SAUVEGARDER RÉSULTATS
    # ════════════════════════════════════════════════════════════════
    
    OUTPUT_PATH = SCRIPT_DIR / "validation_session75_results_session77.txt"
    
    with open(OUTPUT_PATH, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("VALIDATION SESSION 75 - SESSION 77\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("DATASET\n")
        f.write("-" * 60 + "\n")
        f.write(f"Fichier : dataset_session75_filtered.csv\n")
        f.write(f"Mouvements : {len(impacts_real)}\n")
        f.write("\n")
        
        f.write("MÉTRIQUES GLOBALES\n")
        f.write("-" * 60 + "\n")
        f.write(f"MAE V1 (Sessions 51-55) : {mae_v1_global:.1f} pips\n")
        f.write(f"MAE V2 (calibré S77)    : {mae_v2_global:.1f} pips\n")
        f.write(f"Delta                   : {delta_mae:+.1f} pips\n")
        f.write("\n")
        
        f.write("COMPARAISON AVEC OBJECTIF SESSION 75\n")
        f.write("-" * 60 + "\n")
        f.write(f"MAE Session 75 original : {mae_s75_original:.1f} pips\n")
        f.write(f"Cible 50% amélioration  : {target_50pct:.1f} pips\n")
        f.write(f"MAE V2 obtenu           : {mae_v2_global:.1f} pips\n")
        if mae_v2_global < target_50pct:
            improvement_pct = (mae_s75_original - mae_v2_global) / mae_s75_original * 100
            f.write(f"Amélioration            : {improvement_pct:.1f}%\n")
        f.write("\n")
        
        f.write("DÉTAILS PAR MOUVEMENT\n")
        f.write("-" * 60 + "\n")
        for d in details:
            f.write(f"{d['date']} {d['time']} ({d['nb_events']} events)\n")
            f.write(f"  Réel : {d['impact_real']:.1f} pips\n")
            f.write(f"  V1   : {d['impact_v1']:.1f} pips (MAE {d['mae_v1']:.1f})\n")
            f.write(f"  V2   : {d['impact_v2']:.1f} pips (MAE {d['mae_v2']:.1f})\n")
            f.write(f"  Δ    : {d['delta_mae']:+.1f} pips\n")
            f.write("\n")
        
        f.write("STATUT\n")
        f.write("-" * 60 + "\n")
        f.write(f"{status}\n")
        f.write("\n")
    
    print(f"💾 Résultats sauvegardés : {OUTPUT_PATH.name}")
    print()
    
    # Sauvegarder CSV détaillé
    OUTPUT_CSV = SCRIPT_DIR / "validation_session75_details_session77.csv"
    df_details = pd.DataFrame(details)
    df_details.to_csv(OUTPUT_CSV, index=False)
    
    print(f"💾 Détails CSV : {OUTPUT_CSV.name}")
    print()
    
    print("=" * 60)
    print("✅ ÉTAPE 3 TERMINÉE")
    print("=" * 60)
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
