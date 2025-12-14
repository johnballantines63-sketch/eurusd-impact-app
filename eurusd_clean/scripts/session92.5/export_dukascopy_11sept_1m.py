"""
Export Dukascopy Minute par Minute - 11 Septembre 2025
Session 92.5

Objectif:
    Exporter les prix 1m de 14h20 à 15h30 Bern time
    pour comparaison avec données MT5 Swissquote

Paramètres:
    - Date: 11 septembre 2025
    - Début: 14h20 Bern (12:20:00+02:00)
    - Fin: 15h30 Bern (13:30:00+02:00)
    - Durée: 70 minutes (71 lignes avec début et fin inclus)

Format CSV:
    datetime, open, high, low, close
    
Source:
    warehouse.duckdb / prices_1m (Dukascopy)
"""

import duckdb
from pathlib import Path
import csv

# Chemins
BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "fx_impact_app" / "data" / "warehouse.duckdb"
OUTPUT_CSV = Path(__file__).parent / "export_dukascopy_11sept_14h20-15h30.csv"

def export_minute_data():
    """
    Export des données minute par minute du 11 septembre 2025
    """
    print("=" * 80)
    print("EXPORT DUKASCOPY - 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    # Validation DB existe
    if not DB_PATH.exists():
        print(f"❌ ERREUR: Database introuvable: {DB_PATH}")
        return
    
    print(f"✅ Database trouvée: {DB_PATH}")
    print()
    
    # Connexion DB
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        print("✅ Connexion DB réussie")
        print()
    except Exception as e:
        print(f"❌ ERREUR connexion DB: {e}")
        return
    
    # Query SQL
    query = """
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM prices_1m
    WHERE datetime >= '2025-09-11 12:20:00+02:00'::TIMESTAMP
      AND datetime <= '2025-09-11 13:30:00+02:00'::TIMESTAMP
    ORDER BY datetime
    """
    
    print("📊 QUERY SQL:")
    print(query)
    print()
    
    # Exécution query
    try:
        result = conn.execute(query).fetchall()
        columns = ['datetime', 'open', 'high', 'low', 'close']
        print(f"✅ Query exécutée: {len(result)} lignes retournées")
        print()
    except Exception as e:
        print(f"❌ ERREUR exécution query: {e}")
        conn.close()
        return
    
    # Validation nombre lignes
    expected_lines = 71  # 14h20 à 15h30 inclus = 71 minutes
    if len(result) != expected_lines:
        print(f"⚠️  ATTENTION: {len(result)} lignes retournées, {expected_lines} attendues")
        print()
    else:
        print(f"✅ Nombre lignes correct: {len(result)}")
        print()
    
    # Validation pas de NULL
    has_null = False
    for row in result:
        if any(val is None for val in row):
            has_null = True
            print(f"⚠️  ATTENTION: Valeur NULL détectée dans ligne: {row}")
    
    if not has_null:
        print("✅ Aucune valeur NULL")
        print()
    
    # Identification peak absolue
    print("🎯 PEAK ABSOLUE DANS FENÊTRE:")
    print("-" * 80)
    
    # Prix départ (14h30 = CPI release)
    start_price = None
    for row in result:
        dt_str = str(row[0])
        if '12:30:00' in dt_str:  # 12:30:00+02:00 = 14h30 Bern
            start_price = row[2]  # open
            print(f"Prix départ 14h30 (CPI release): {start_price}")
            break
    
    if start_price is None:
        print("⚠️  Prix départ 14h30 introuvable")
        start_price = result[10][2] if len(result) > 10 else result[0][2]  # Approximation
        print(f"Prix départ approximatif: {start_price}")
    
    # Peak (high max)
    peak_row = max(result, key=lambda r: r[2])  # r[2] = high
    peak_datetime = peak_row[0]
    peak_price = peak_row[2]
    peak_impact = (peak_price - start_price) * 10000  # Conversion pips
    
    print(f"Peak time   : {peak_datetime}")
    print(f"Peak price  : {peak_price:.5f}")
    print(f"Impact      : {peak_impact:.1f} pips")
    print()
    
    # Export CSV
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(columns)
            
            # Data
            for row in result:
                writer.writerow(row)
        
        print("✅ CSV créé avec succès")
        print(f"📁 Fichier: {OUTPUT_CSV}")
        print()
    except Exception as e:
        print(f"❌ ERREUR création CSV: {e}")
        conn.close()
        return
    
    # Preview CSV
    print("=" * 80)
    print("PREVIEW CSV - 5 PREMIÈRES LIGNES (14h20-14h24)")
    print("=" * 80)
    for i, row in enumerate(result[:5]):
        print(f"{row[0]}, {row[1]:.5f}, {row[2]:.5f}, {row[3]:.5f}, {row[4]:.5f}")
    print()
    
    print("=" * 80)
    print("PREVIEW CSV - 5 LIGNES AUTOUR CPI (14h28-14h32)")
    print("=" * 80)
    # Lignes 8-12 (14h28-14h32 si 14h20 = ligne 0)
    for i in range(8, min(13, len(result))):
        row = result[i]
        marker = " ← CPI RELEASE" if '12:30:00' in str(row[0]) else ""
        print(f"{row[0]}, {row[1]:.5f}, {row[2]:.5f}, {row[3]:.5f}, {row[4]:.5f}{marker}")
    print()
    
    print("=" * 80)
    print("PREVIEW CSV - 5 LIGNES AUTOUR PEAK")
    print("=" * 80)
    # Trouver index peak
    peak_index = result.index(peak_row)
    start_preview = max(0, peak_index - 2)
    end_preview = min(len(result), peak_index + 3)
    for i in range(start_preview, end_preview):
        row = result[i]
        marker = " ← PEAK" if i == peak_index else ""
        print(f"{row[0]}, {row[1]:.5f}, {row[2]:.5f}, {row[3]:.5f}, {row[4]:.5f}{marker}")
    print()
    
    print("=" * 80)
    print("PREVIEW CSV - 5 DERNIÈRES LIGNES (15h26-15h30)")
    print("=" * 80)
    for i, row in enumerate(result[-5:]):
        print(f"{row[0]}, {row[1]:.5f}, {row[2]:.5f}, {row[3]:.5f}, {row[4]:.5f}")
    print()
    
    # Statistiques
    print("=" * 80)
    print("STATISTIQUES FENÊTRE 14h20-15h30")
    print("=" * 80)
    print(f"Lignes exportées  : {len(result)}")
    print(f"Période           : 14h20 → 15h30 Bern (70 minutes)")
    print(f"Prix départ 14h30 : {start_price:.5f}")
    print(f"Peak absolue      : {peak_price:.5f} à {peak_datetime}")
    print(f"Impact            : {peak_impact:.1f} pips")
    print(f"Fichier CSV       : {OUTPUT_CSV.name}")
    print()
    
    # Comparaison valeurs Session 92.4
    print("=" * 80)
    print("COMPARAISON SESSION 92.4")
    print("=" * 80)
    print("DB Dukascopy 60 min (Session 92.4) : 51.7 pips, Peak 15:09 (T+39)")
    print("DB Dukascopy 120 min (Session 92.4): 57.1 pips, Peak 16:07 (T+97)")
    print("MT5 Swissquote (André)              : 56.2 pips")
    print(f"Export actuel (14h20-15h30)         : {peak_impact:.1f} pips, Peak {peak_datetime}")
    print()
    
    # Message final
    print("=" * 80)
    print("✅ EXPORT TERMINÉ AVEC SUCCÈS")
    print("=" * 80)
    print()
    print("📊 Prochaine étape:")
    print("   → André compare ce CSV avec ses données MT5 Swissquote")
    print("   → Identification pattern divergence minute par minute")
    print("   → Validation divergence acceptable ou problème import")
    print()
    
    conn.close()


if __name__ == "__main__":
    export_minute_data()
