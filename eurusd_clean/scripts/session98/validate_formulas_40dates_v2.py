"""
Script de validation formules S51-55 sur 40 dates CPI - VERSION CORRIGÉE
Session 98 - Validation complète avec données réelles

Compare prédictions (formules validées S51-55) vs impacts réels (calculés depuis prices_1m)
"""

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "app" / "data" / "warehouse.duckdb"
INPUT_CSV = BASE_DIR / "scripts" / "session92.8" / "resultats_40_dates_s92_13.csv"
OUTPUT_CSV = BASE_DIR / "scripts" / "session98" / "validation_formules_s51_55_40dates.csv"

# Paramètres formules S51-55 (Planner V2.4)
AMPLIFICATION = 2.5  # Baseline validée Session 72

print("=" * 100)
print("🔍 VALIDATION FORMULES S51-55 SUR 40 DATES CPI - VERSION CORRIGÉE")
print("=" * 100)
print(f"\n📊 Database: {DB_PATH}")
print(f"📄 Input CSV: {INPUT_CSV}")
print(f"💾 Output CSV: {OUTPUT_CSV}")
print(f"\n⚙️  Amplification: {AMPLIFICATION}")

# ============================================================================
# FONCTIONS FORMULES S51-55 (BASELINE V2.4)
# ============================================================================

def calculate_impact_d(empirical_score: float, num_events: int, amplification: float = 2.5) -> float:
    """
    Formule D validée Sessions 51-55
    
    Impact = (Score / 10) × Amplification × sqrt(N_events)
    
    Args:
        empirical_score: Score empirique (0-100)
        num_events: Nombre d'événements simultanés
        amplification: Facteur d'amplification (2.5 par défaut)
    
    Returns:
        Impact prédit en pips
    """
    base_impact = empirical_score / 10.0
    multi_event_factor = np.sqrt(num_events)
    impact = base_impact * amplification * multi_event_factor
    return impact

def calculate_ttr_b(empirical_score: float, num_events: int) -> float:
    """
    Formule TTR B validée Sessions 51-55
    
    TTR = log10(Score + 1) × sqrt(N_events) + 1
    
    Args:
        empirical_score: Score empirique (0-100)
        num_events: Nombre d'événements simultanés
    
    Returns:
        TTR (Time To React) en minutes
    """
    log_component = np.log10(empirical_score + 1)
    multi_event_factor = np.sqrt(num_events)
    ttr = log_component * multi_event_factor + 1
    return ttr

# ============================================================================
# CHARGEMENT DONNÉES
# ============================================================================

print("\n" + "=" * 100)
print("📥 CHARGEMENT DONNÉES")
print("=" * 100)

# Charger CSV avec impacts réels
df_real = pd.read_csv(INPUT_CSV)
print(f"\n✅ CSV chargé: {len(df_real)} dates")
print(f"📋 Colonnes: {list(df_real.columns)}")

# Afficher échantillon
print("\n📊 Échantillon (3 premières lignes):")
print(df_real[['date', 'event_time', 'impact_pred', 'impact_real', 'error']].head(3).to_string(index=False))

# ============================================================================
# CONNEXION DB ET CHARGEMENT ÉVÉNEMENTS
# ============================================================================

print("\n" + "=" * 100)
print("🔗 CONNEXION BASE DE DONNÉES")
print("=" * 100)

conn = duckdb.connect(str(DB_PATH), read_only=True)
print(f"✅ Connexion établie")

# ============================================================================
# FONCTION CHARGEMENT ÉVÉNEMENTS
# ============================================================================

def load_events_for_date(conn, date_str: str, time_str: str):
    """
    Charge tous les événements pour une date/heure donnée avec leur empirical_score
    
    Args:
        conn: Connexion DuckDB
        date_str: Date format 'YYYY-MM-DD'
        time_str: Heure format 'HH:MM:SS'
    
    Returns:
        DataFrame avec événements (event_title, empirical_score, actual, estimate, forecast, previous)
    """
    # Query avec JOIN pour récupérer empirical_score depuis event_families
    # Timezone: events.ts_utc contient +02:00 (Bern time)
    query = """
    SELECT 
        e.event_title,
        e.event_key,
        e.country,
        ef.empirical_score,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc::DATE = ?
      AND e.ts_utc::TIME = ?
    ORDER BY ef.empirical_score DESC NULLS LAST
    """
    
    df_events = conn.execute(query, [date_str, time_str]).df()
    
    return df_events

# ============================================================================
# VALIDATION DATE PAR DATE
# ============================================================================

print("\n" + "=" * 100)
print("🧪 VALIDATION DATE PAR DATE")
print("=" * 100)

results = []

for idx, row in df_real.iterrows():
    date_str = row['date']
    time_str = row['event_time']
    impact_real = row['impact_real']
    
    print(f"\n{'=' * 80}")
    print(f"📅 Date {idx+1}/{len(df_real)}: {date_str} {time_str}")
    print(f"{'=' * 80}")
    
    try:
        # Charger événements
        df_events = load_events_for_date(conn, date_str, time_str)
        
        if len(df_events) == 0:
            print(f"⚠️  Aucun événement trouvé dans DB")
            results.append({
                'date': date_str,
                'event_time': time_str,
                'num_events': 0,
                'impact_pred_s51_55': None,
                'ttr_pred_s51_55': None,
                'impact_real': impact_real,
                'error_abs': None,
                'error_pct': None,
                'status': 'NO_EVENTS'
            })
            continue
        
        # Filtrer événements sans empirical_score
        df_events_valid = df_events[df_events['empirical_score'].notna()].copy()
        
        if len(df_events_valid) == 0:
            print(f"⚠️  Événements trouvés mais aucun avec empirical_score")
            print(f"📋 Événements sans score: {' | '.join(df_events['event_title'].tolist())}")
            results.append({
                'date': date_str,
                'event_time': time_str,
                'num_events': len(df_events),
                'impact_pred_s51_55': None,
                'ttr_pred_s51_55': None,
                'impact_real': impact_real,
                'error_abs': None,
                'error_pct': None,
                'status': 'NO_SCORE'
            })
            continue
        
        print(f"✅ Événements trouvés: {len(df_events_valid)}")
        print(f"📊 Événements: {' | '.join(df_events_valid['event_title'].tolist())}")
        
        # Calculer score max et moyen
        score_max = df_events_valid['empirical_score'].max()
        score_avg = df_events_valid['empirical_score'].mean()
        num_events = len(df_events_valid)
        
        print(f"📈 Score max: {score_max:.2f}")
        print(f"📊 Score moyen: {score_avg:.2f}")
        print(f"🔢 Nombre événements: {num_events}")
        
        # PRÉDICTION FORMULES S51-55 (Baseline V2.4)
        # Utilise score_avg comme dans Planner V2.4
        impact_pred = calculate_impact_d(score_avg, num_events, AMPLIFICATION)
        ttr_pred = calculate_ttr_b(score_avg, num_events)
        
        print(f"\n🎯 PRÉDICTION S51-55:")
        print(f"   Impact: {impact_pred:.2f} pips")
        print(f"   TTR: {ttr_pred:.2f} min")
        
        # Comparaison avec réalité
        error_abs = abs(impact_pred - impact_real)
        error_pct = (error_abs / impact_real * 100) if impact_real != 0 else 0
        
        print(f"\n📊 COMPARAISON:")
        print(f"   Impact réel: {impact_real:.2f} pips")
        print(f"   Erreur absolue: {error_abs:.2f} pips")
        print(f"   Erreur %: {error_pct:.2f}%")
        
        # Statut validation
        if error_abs < 10:
            status = '✅ EXCELLENT'
        elif error_abs < 30:
            status = '✅ BON'
        else:
            status = '⚠️ À AMÉLIORER'
        
        print(f"   Status: {status}")
        
        # Stocker résultats
        results.append({
            'date': date_str,
            'event_time': time_str,
            'num_events': num_events,
            'score_max': score_max,
            'score_avg': score_avg,
            'events': ' | '.join(df_events_valid['event_title'].tolist()),
            'impact_pred_s51_55': impact_pred,
            'ttr_pred_s51_55': ttr_pred,
            'impact_real': impact_real,
            'error_abs': error_abs,
            'error_pct': error_pct,
            'status': status
        })
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        results.append({
            'date': date_str,
            'event_time': time_str,
            'num_events': None,
            'impact_pred_s51_55': None,
            'ttr_pred_s51_55': None,
            'impact_real': impact_real,
            'error_abs': None,
            'error_pct': None,
            'status': f'ERROR: {str(e)}'
        })

# Fermer connexion
conn.close()

# ============================================================================
# CRÉATION DATAFRAME RÉSULTATS
# ============================================================================

print("\n" + "=" * 100)
print("📊 RÉSULTATS GLOBAUX")
print("=" * 100)

df_results = pd.DataFrame(results)

# Calculer métriques globales (seulement dates avec prédiction)
df_valid = df_results[df_results['error_abs'].notna()].copy()

if len(df_valid) > 0:
    mae = df_valid['error_abs'].mean()
    rmse = np.sqrt((df_valid['error_abs'] ** 2).mean())
    median_error = df_valid['error_abs'].median()
    max_error = df_valid['error_abs'].max()
    min_error = df_valid['error_abs'].min()
    
    # Taux de succès (erreur < 30 pips)
    success_rate = (df_valid['error_abs'] < 30).sum() / len(df_valid) * 100
    excellent_rate = (df_valid['error_abs'] < 10).sum() / len(df_valid) * 100
    
    print(f"\n📈 MÉTRIQUES GLOBALES (sur {len(df_valid)}/{len(df_results)} dates):")
    print(f"   MAE (erreur absolue moyenne): {mae:.2f} pips")
    print(f"   RMSE: {rmse:.2f} pips")
    print(f"   Erreur médiane: {median_error:.2f} pips")
    print(f"   Erreur min: {min_error:.2f} pips")
    print(f"   Erreur max: {max_error:.2f} pips")
    print(f"\n🎯 TAUX DE SUCCÈS:")
    print(f"   Excellent (<10 pips): {excellent_rate:.1f}%")
    print(f"   Bon (<30 pips): {success_rate:.1f}%")
    
    # Distribution erreurs
    print(f"\n📊 DISTRIBUTION ERREURS:")
    bins = [0, 5, 10, 20, 30, 50, 100, float('inf')]
    labels = ['0-5', '5-10', '10-20', '20-30', '30-50', '50-100', '>100']
    df_valid['error_bin'] = pd.cut(df_valid['error_abs'], bins=bins, labels=labels)
    distribution = df_valid['error_bin'].value_counts().sort_index()
    
    for bin_label, count in distribution.items():
        pct = count / len(df_valid) * 100
        print(f"   {bin_label} pips: {count} dates ({pct:.1f}%)")
    
else:
    print("⚠️ Aucune date validée")

# ============================================================================
# SAUVEGARDE RÉSULTATS
# ============================================================================

print("\n" + "=" * 100)
print("💾 SAUVEGARDE RÉSULTATS")
print("=" * 100)

df_results.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Résultats sauvegardés: {OUTPUT_CSV}")

# Afficher top 10 meilleures prédictions
if len(df_valid) > 0:
    print("\n🏆 TOP 10 MEILLEURES PRÉDICTIONS:")
    top10 = df_valid.nsmallest(10, 'error_abs')[['date', 'event_time', 'impact_pred_s51_55', 'impact_real', 'error_abs']]
    print(top10.to_string(index=False))
    
    # Afficher 10 pires prédictions
    print("\n⚠️ 10 PIRES PRÉDICTIONS:")
    worst10 = df_valid.nlargest(10, 'error_abs')[['date', 'event_time', 'impact_pred_s51_55', 'impact_real', 'error_abs']]
    print(worst10.to_string(index=False))

print("\n" + "=" * 100)
print("✅ VALIDATION TERMINÉE")
print("=" * 100)
