"""
VALIDATION FORMULES 92.XX - CHARGEMENT DEPUIS DB
================================================

OBJECTIF : Valider les formules hybrides Session 92 en chargeant les données
           EXACTEMENT comme le Planificateur V2.4 (pas données hard-codées)

MÉTHODOLOGIE :
1. Charger événements depuis DB avec query SQL Planificateur (lignes 189-210)
2. Extraire families, surprises, num_events depuis ces données DB
3. Appliquer formules 92.xx (formulas_hybrid_empirical.py)
4. Comparer avec impacts réels (prices_1m)
5. Mesurer MAE

Ce script est le PONT MANQUANT entre :
- Tests Session 92 (données hard-codées) → MAE 6.5 pips ✅
- Intégration Planificateur (données DB) → MAE ? (non testé avant)

Session 98 - 29 octobre 2025
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ajouter les modules nécessaires
script_dir = Path(__file__).parent
eurusd_clean_dir = script_dir.parent.parent  # eurusd_clean/
project_root = eurusd_clean_dir.parent  # eurusd_news_impact_calculator_MPC/

# Ajouter chemins
sys.path.insert(0, str(project_root / "fx_impact_app" / "src"))
sys.path.insert(0, str(eurusd_clean_dir / "scripts" / "session92"))

from formulas_hybrid_empirical import calculate_impact_hybrid

# Import config.py
try:
    from config import get_db_path
except ImportError:
    # Fallback: définir directement le chemin DB
    def get_db_path():
        return str(project_root / "fx_impact_app" / "data" / "warehouse.duckdb")

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = get_db_path()

# Dates CPI de référence à tester (Session 92-93)
TEST_DATES = [
    '2025-09-11',  # Référence validée S81
    '2025-01-15',  # CPI
    '2025-05-13',  # CPI
    '2024-12-11',  # CPI
    '2024-10-10',  # CPI + Jobless
]

print("="*100)
print("🔬 VALIDATION FORMULES 92.XX - CHARGEMENT DEPUIS DB")
print("="*100)
print(f"\n📁 Database: {DB_PATH}")
print(f"📅 Dates à tester: {len(TEST_DATES)}")
print()

# ============================================================================
# FONCTION 1 : CHARGER ÉVÉNEMENTS COMME PLANIFICATEUR
# ============================================================================

def load_events_from_db_like_planificateur(date_str: str) -> pd.DataFrame:
    """
    Charge les événements HIGH IMPACT pour une date donnée
    EXACTEMENT comme le Planificateur V2.4 (lignes 189-210)
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
    
    Returns:
        DataFrame avec colonnes: event_key, event_title, ts_utc, actual, 
                                estimate, family, empirical_score, latency_median
    """
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Query SQL EXACTE du Planificateur (lignes 189-210)
    query = """
    SELECT 
        e.event_key,
        e.event_title as label,
        e.ts_utc,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.family,
        ef.empirical_score,
        ef.latency_median
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
    
    df = conn.execute(query, [date_str]).df()
    conn.close()
    
    return df


# ============================================================================
# FONCTION 2 : EXTRAIRE DONNÉES POUR FORMULES 92.XX
# ============================================================================

def extract_data_for_formulas_92xx(df_events: pd.DataFrame) -> dict:
    """
    Extrait les données nécessaires pour formules 92.xx depuis DataFrame DB
    
    Args:
        df_events: DataFrame retourné par load_events_from_db_like_planificateur
    
    Returns:
        dict avec: families, surprises, num_events
    """
    if df_events.empty:
        return None
    
    # 1. Extraire families
    families = df_events['family'].dropna().unique().tolist()
    
    # 2. Calculer surprises individuelles (EXACTEMENT comme Planificateur)
    surprises = []
    for _, event in df_events.iterrows():
        actual = event['actual']
        # Fallback estimate → forecast → previous (comme Planificateur)
        estimate = event['estimate'] if pd.notna(event['estimate']) else \
                   event.get('forecast') if pd.notna(event.get('forecast')) else \
                   event.get('previous')
        
        if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
            surprise_pct = abs((actual - estimate) / estimate) * 100
            surprises.append(surprise_pct)
    
    # 3. Nombre événements
    num_events = len(df_events)
    
    return {
        'families': families,
        'surprises': surprises,
        'num_events': num_events
    }


# ============================================================================
# FONCTION 3 : MESURER IMPACT RÉEL DEPUIS PRIX
# ============================================================================

def measure_real_impact_from_prices(date_str: str, event_time_str: str, 
                                   window_minutes: int = 60) -> float:
    """
    Mesure l'impact réel depuis les prix 1min
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        event_time_str: Heure au format 'HH:MM:SS'
        window_minutes: Fenêtre d'analyse en minutes
    
    Returns:
        Impact réel en pips (max mouvement depuis prix ouverture)
    """
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Construire timestamp événement (timezone +02:00 Bern time)
    event_timestamp = f"{date_str} {event_time_str}+02:00"
    
    # Query prix 1min
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_1m
    WHERE datetime >= '{event_timestamp}'::TIMESTAMP
      AND datetime < '{event_timestamp}'::TIMESTAMP + INTERVAL '{window_minutes} minutes'
    ORDER BY datetime
    """
    
    try:
        df_prices = conn.execute(query).df()
        conn.close()
        
        if df_prices.empty or len(df_prices) < 5:
            return None
        
        # Impact = max mouvement depuis prix ouverture
        start_price = df_prices.iloc[0]['open']
        high_max = df_prices['high'].max()
        low_min = df_prices['low'].min()
        
        impact_up = abs(high_max - start_price) * 10000  # pips
        impact_down = abs(start_price - low_min) * 10000
        impact_real = max(impact_up, impact_down)
        
        return impact_real
        
    except Exception as e:
        print(f"      ❌ Erreur lecture prix: {e}")
        conn.close()
        return None


# ============================================================================
# FONCTION 4 : TESTER UNE DATE
# ============================================================================

def test_date(date_str: str) -> dict:
    """
    Teste les formules 92.xx sur une date en chargeant depuis DB
    
    Returns:
        dict avec résultats: impact_pred, impact_real, error, etc.
    """
    print(f"\n{'='*100}")
    print(f"📅 DATE: {date_str}")
    print('='*100)
    
    # 1. Charger événements depuis DB (comme Planificateur)
    print("\n1️⃣ Chargement événements depuis DB...")
    df_events = load_events_from_db_like_planificateur(date_str)
    
    if df_events.empty:
        print("   ❌ Aucun événement HIGH trouvé pour cette date")
        return None
    
    print(f"   ✅ {len(df_events)} événements HIGH trouvés")
    
    # Afficher détails événements
    print(f"\n   📋 Événements chargés:")
    for idx, event in df_events.iterrows():
        label = event['label'][:50] if event['label'] else 'N/A'
        family = event['family'] if pd.notna(event['family']) else 'N/A'
        score = event['empirical_score'] if pd.notna(event['empirical_score']) else 0
        print(f"      • {label:50} | Family: {family:15} | Score: {score:5.1f}")
    
    # 2. Extraire données pour formules 92.xx
    print(f"\n2️⃣ Extraction données pour formules 92.xx...")
    data = extract_data_for_formulas_92xx(df_events)
    
    if not data or not data['surprises']:
        print("   ⚠️  Pas assez de données pour calculer surprises")
        return None
    
    print(f"   ✅ Données extraites:")
    print(f"      • Families: {data['families']}")
    print(f"      • Surprises: {[f'{s:.1f}%' for s in data['surprises']]}")
    print(f"      • Num events: {data['num_events']}")
    
    # 3. Appliquer formules 92.xx
    print(f"\n3️⃣ Application formules 92.xx (hybride empirique)...")
    result_92xx = calculate_impact_hybrid(
        event_families=data['families'],
        surprises=data['surprises'],
        num_events=data['num_events']
    )
    
    impact_predicted = result_92xx['impact_predicted']
    cluster_type = result_92xx['cluster_type']
    cluster_size = result_92xx['cluster_size']
    cluster_found = result_92xx['cluster_found']
    
    print(f"   ✅ Prédiction calculée:")
    print(f"      • Impact prédit: {impact_predicted:.1f} pips")
    print(f"      • Cluster type: {cluster_type}")
    print(f"      • Cluster size: {cluster_size}")
    print(f"      • Cluster reconnu: {'✅ OUI' if cluster_found else '❌ NON (default)'}")
    print(f"      • Base impact: {result_92xx['base_impact']:.1f} pips")
    print(f"      • Sensitivity: {result_92xx['sensitivity']:.3f}")
    print(f"      • Surprise vectorielle: {result_92xx['surprise_vectorielle']:.1f}%")
    print(f"      • Amplification factor: {result_92xx['amplification_factor']:.3f}x")
    
    # 4. Mesurer impact réel
    print(f"\n4️⃣ Mesure impact réel depuis prix 1min...")
    event_time = df_events.iloc[0]['ts_utc']
    
    # Extraire heure (format peut varier)
    if hasattr(event_time, 'strftime'):
        time_str = event_time.strftime('%H:%M:%S')
    else:
        time_str = str(event_time).split()[1]  # Prendre HH:MM:SS
    
    impact_real = measure_real_impact_from_prices(date_str, time_str)
    
    if impact_real is None:
        print("   ❌ Impossible de mesurer impact réel (données prix manquantes)")
        return None
    
    print(f"   ✅ Impact réel mesuré: {impact_real:.1f} pips")
    
    # 5. Calculer erreur
    error = abs(impact_predicted - impact_real)
    error_pct = (error / impact_real * 100) if impact_real > 0 else 0
    
    print(f"\n5️⃣ Résultat final:")
    print(f"   {'='*90}")
    print(f"   Impact prédit : {impact_predicted:>7.1f} pips")
    print(f"   Impact réel   : {impact_real:>7.1f} pips")
    print(f"   Erreur        : {error:>7.1f} pips ({error_pct:.1f}%)")
    print(f"   {'='*90}")
    
    # Verdict
    if error < 10:
        verdict = "✅✅✅ EXCELLENT"
    elif error < 20:
        verdict = "✅✅ BON"
    elif error < 30:
        verdict = "✅ ACCEPTABLE"
    else:
        verdict = "❌ À AMÉLIORER"
    
    print(f"   Verdict: {verdict}")
    
    return {
        'date': date_str,
        'num_events': data['num_events'],
        'cluster_type': cluster_type,
        'cluster_found': cluster_found,
        'surprise_vect': result_92xx['surprise_vectorielle'],
        'impact_predicted': impact_predicted,
        'impact_real': impact_real,
        'error': error,
        'error_pct': error_pct
    }


# ============================================================================
# MAIN : TESTER TOUTES LES DATES
# ============================================================================

def main():
    """
    Teste les formules 92.xx sur toutes les dates de référence
    """
    print("\n" + "="*100)
    print("🚀 DÉBUT VALIDATION")
    print("="*100)
    
    results = []
    
    for date_str in TEST_DATES:
        result = test_date(date_str)
        if result:
            results.append(result)
    
    # ============================================================================
    # SYNTHÈSE GLOBALE
    # ============================================================================
    
    if not results:
        print("\n❌ Aucun résultat disponible pour synthèse")
        return
    
    print("\n\n" + "="*100)
    print("📊 SYNTHÈSE GLOBALE")
    print("="*100)
    
    df_results = pd.DataFrame(results)
    
    # Métriques globales
    mae = df_results['error'].mean()
    rmse = np.sqrt((df_results['error'] ** 2).mean())
    max_error = df_results['error'].max()
    success_rate = (df_results['error'] < 30).sum() / len(df_results) * 100
    
    print(f"\n📈 Métriques:")
    print(f"   MAE (Mean Absolute Error) : {mae:.1f} pips")
    print(f"   RMSE                       : {rmse:.1f} pips")
    print(f"   Erreur maximale            : {max_error:.1f} pips")
    print(f"   Taux succès (< 30 pips)    : {success_rate:.0f}%")
    
    # Comparaison avec Session 92 (données hard-codées)
    print(f"\n📊 Comparaison:")
    print(f"   Session 92 (données hard-codées) : MAE 6.5 pips")
    print(f"   Session 98 (données DB réelles)  : MAE {mae:.1f} pips")
    
    if mae < 10:
        print(f"\n   ✅✅✅ EXCELLENT - Formules 92.xx VALIDÉES sur données DB réelles !")
    elif mae < 20:
        print(f"\n   ✅✅ BON - Léger écart vs données hard-codées mais acceptable")
    elif mae < 30:
        print(f"\n   ✅ ACCEPTABLE - Écart significatif, investigation nécessaire")
    else:
        print(f"\n   ❌ PROBLÈME - Écart trop important, révision nécessaire")
    
    # Tableau détaillé
    print(f"\n📋 Tableau détaillé:")
    print(f"\n{'Date':>12} {'Events':>7} {'Cluster':>15} {'Trouvé':>8} {'Surp.%':>8} "
          f"{'Prédit':>8} {'Réel':>8} {'Erreur':>8} {'Status':>8}")
    print("-"*100)
    
    for _, row in df_results.iterrows():
        cluster_found_str = 'OUI' if row['cluster_found'] else 'NON'
        status = '✅✅✅' if row['error'] < 10 else '✅✅' if row['error'] < 20 else '✅' if row['error'] < 30 else '❌'
        
        print(f"{row['date']:>12} {row['num_events']:>7} {row['cluster_type']:>15} "
              f"{cluster_found_str:>8} {row['surprise_vect']:>7.1f}% "
              f"{row['impact_predicted']:>7.1f}p {row['impact_real']:>7.1f}p "
              f"{row['error']:>7.1f}p {status:>8}")
    
    # Sauvegarder résultats
    output_path = Path(__file__).parent / "validation_92xx_from_db_results.csv"
    df_results.to_csv(output_path, index=False)
    print(f"\n💾 Résultats sauvegardés: {output_path}")
    
    print("\n" + "="*100)
    print("✅ VALIDATION TERMINÉE")
    print("="*100)
    
    return df_results


if __name__ == "__main__":
    main()
