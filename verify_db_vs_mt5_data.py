"""
VÉRIFICATION DONNÉES DB vs RÉALITÉ MT5
Comparaison des résultats réels avec ce qui est stocké
"""

import duckdb
import pandas as pd
from pathlib import Path

print("=" * 80)
print("🔍 VÉRIFICATION DONNÉES DB vs RÉALITÉ MT5")
print("=" * 80)
print()

DB_PATH = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

# ════════════════════════════════════════════════════════════════
# Données réelles MT5 (fournies par l'utilisateur)
# ════════════════════════════════════════════════════════════════

print("📊 DONNÉES RÉELLES MT5 (11 SEPTEMBRE 2025, 14:30) :")
print()

mt5_data = [
    {"title": "Continuing Jobless Claims", "actual": 1939, "estimate": 1950, "unit": "K"},
    {"title": "Initial Jobless Claims", "actual": 263, "estimate": 235, "unit": "K"},
    {"title": "Jobless Claims 4-Week Average", "actual": 240.5, "estimate": 232, "unit": "K"},
    {"title": "Core Inflation Rate (Monthly)", "actual": 0.3, "estimate": 0.3, "unit": "%"},
    {"title": "CPI", "actual": 322.132, "estimate": 323, "unit": ""},
    {"title": "CPI s.a", "actual": 323.05, "estimate": 323.89, "unit": ""},
    {"title": "Inflation Rate (Monthly)", "actual": 0.4, "estimate": 0.3, "unit": "%"},
    {"title": "Inflation Rate (Annual)", "actual": 2.9, "estimate": 2.9, "unit": "%"},
    {"title": "Core Inflation Rate (Annual)", "actual": 3.1, "estimate": 3.1, "unit": "%"},
]

for item in mt5_data:
    surprise = abs((item["actual"] - item["estimate"]) / item["estimate"]) * 100 if item["estimate"] != 0 else 0
    print(f"  {item['title']:35s} | A={item['actual']:7.2f} E={item['estimate']:7.2f} | Surprise: {surprise:5.1f}%")

print()

# ════════════════════════════════════════════════════════════════
# Données dans la DB
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📚 DONNÉES DANS LA DB (warehouse.duckdb) :")
print("=" * 80)
print()

query_db = """
SELECT 
    event_title,
    actual,
    estimate,
    forecast,
    CASE 
        WHEN estimate IS NOT NULL AND estimate != 0 
        THEN ABS((actual - estimate) / estimate) * 100.0
        ELSE NULL
    END as surprise_pct
FROM events
WHERE strftime(ts_utc, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
  AND country = 'US'
ORDER BY event_title
"""

db_data = conn.execute(query_db).fetchdf()

print(f"Événements trouvés : {len(db_data)}")
print()

for idx, row in db_data.iterrows():
    actual = row['actual'] if pd.notna(row['actual']) else "N/A"
    estimate = row['estimate'] if pd.notna(row['estimate']) else "N/A"
    forecast = row['forecast'] if pd.notna(row['forecast']) else "N/A"
    surprise = f"{row['surprise_pct']:.1f}%" if pd.notna(row['surprise_pct']) else "N/A"
    
    print(f"  {row['event_title']:40s}")
    print(f"     Actual={actual}, Estimate={estimate}, Forecast={forecast}")
    print(f"     Surprise DB: {surprise}")
    print()

# ════════════════════════════════════════════════════════════════
# Comparaison détaillée
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("🔍 ANALYSE DES DIVERGENCES")
print("=" * 80)
print()

# Mapping manuel pour comparaison
mappings = {
    "Initial Jobless Claims": ["Initial Jobless Claims"],
    "Continuing Jobless Claims": ["Continuing Jobless Claims"],
    "Jobless Claims 4-Week Average": ["Jobless Claims 4-Week Average"],
    "Inflation Rate": ["Inflation Rate"],
    "Core Inflation Rate": ["Core Inflation Rate"],
    "CPI": ["CPI"],
    "CPI s.a": ["CPI s.a"],
}

divergences = []

for mt5_item in mt5_data:
    mt5_title = mt5_item["title"]
    
    # Chercher dans DB
    matching_rows = db_data[db_data['event_title'].str.contains(mt5_title.split("(")[0].strip(), case=False, na=False)]
    
    if len(matching_rows) > 0:
        db_row = matching_rows.iloc[0]
        
        # Comparer
        mt5_surprise = abs((mt5_item["actual"] - mt5_item["estimate"]) / mt5_item["estimate"]) * 100 if mt5_item["estimate"] != 0 else 0
        db_surprise = db_row['surprise_pct'] if pd.notna(db_row['surprise_pct']) else 0
        
        diff_surprise = abs(mt5_surprise - db_surprise)
        
        if diff_surprise > 0.5:  # Seuil de 0.5%
            divergences.append({
                "event": mt5_title,
                "mt5_surprise": mt5_surprise,
                "db_surprise": db_surprise,
                "diff": diff_surprise,
                "mt5_actual": mt5_item["actual"],
                "mt5_estimate": mt5_item["estimate"],
                "db_actual": db_row['actual'],
                "db_estimate": db_row['estimate']
            })

if len(divergences) > 0:
    print("⚠️ DIVERGENCES DÉTECTÉES :")
    print()
    
    for div in divergences:
        print(f"📍 {div['event']}")
        print(f"   MT5  : Actual={div['mt5_actual']}, Estimate={div['mt5_estimate']} → Surprise {div['mt5_surprise']:.1f}%")
        print(f"   DB   : Actual={div['db_actual']}, Estimate={div['db_estimate']} → Surprise {div['db_surprise']:.1f}%")
        print(f"   ÉCART: {div['diff']:.1f}% ⚠️")
        print()
else:
    print("✅ Aucune divergence significative détectée")
    print()

# ════════════════════════════════════════════════════════════════
# Impact sur les prédictions V2
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📊 IMPACT SUR LES PRÉDICTIONS V2")
print("=" * 80)
print()

if len(divergences) > 0:
    print("Si on corrigeait les données avec les valeurs MT5 :")
    print()
    
    # Trouver la surprise MAX réelle
    max_surprise_mt5 = max([div['mt5_surprise'] for div in divergences] + [11.9])  # 11.9 = Initial Jobless
    
    print(f"   Surprise MAX actuelle (DB)  : 11.9% (Initial Jobless Claims)")
    print(f"   Surprise MAX corrigée (MT5) : {max_surprise_mt5:.1f}%")
    print()
    
    if max_surprise_mt5 != 11.9:
        print(f"   ⚠️ CHANGEMENT : L'événement avec la plus grande surprise changerait !")
        print()
        
        # Recalculer l'amplification
        def calc_amp(surprise):
            if surprise > 30:
                surprise = 30
            if surprise < 5:
                return 1.0
            elif surprise < 15:
                return 1.0 + (surprise - 5.0) * 0.15
            else:
                return 2.5
        
        amp_current = calc_amp(11.9)
        amp_corrected = calc_amp(max_surprise_mt5)
        
        print(f"   Amplification actuelle : ×{amp_current:.2f}")
        print(f"   Amplification corrigée : ×{amp_corrected:.2f}")
        print(f"   Différence : {abs(amp_corrected - amp_current):.2f}")
        
        # Impact sur la prédiction
        impact_base = 27.2  # Calculé précédemment
        calibration = 0.758
        
        impact_current = impact_base * amp_current * calibration
        impact_corrected = impact_base * amp_corrected * calibration
        
        print()
        print(f"   Impact prédit actuel   : {impact_current:.1f} pips")
        print(f"   Impact prédit corrigé  : {impact_corrected:.1f} pips")
        print(f"   Impact réel MT5        : 59.2 pips")
        print()
        print(f"   Erreur actuelle   : {abs(impact_current - 59.2):.1f} pips ({abs(impact_current - 59.2)/59.2*100:.0f}%)")
        print(f"   Erreur corrigée   : {abs(impact_corrected - 59.2):.1f} pips ({abs(impact_corrected - 59.2)/59.2*100:.0f}%)")

print()
print("=" * 80)
print("💡 CONCLUSION")
print("=" * 80)
print()

if len(divergences) > 0:
    print("⚠️ PROBLÈME CONFIRMÉ :")
    print()
    print("   La DB warehouse contient des données incomplètes ou incorrectes")
    print("   pour certains événements du 11 septembre 2025.")
    print()
    print("   CAUSES POSSIBLES :")
    print("   1. API EODHD n'a pas fourni toutes les estimations")
    print("   2. Événements multiples mal mappés (mensuel vs annuel)")
    print("   3. Mise à jour incomplète des données historiques")
    print()
    print("   SOLUTIONS :")
    print("   1. Mettre à jour manuellement les estimates manquants")
    print("   2. Implémenter Session 18 pour permettre corrections manuelles")
    print("   3. Re-scraper les données EODHD pour 11 septembre 2025")
else:
    print("✅ Les données DB sont cohérentes avec MT5")

print()
print("=" * 80)
print("✅ VÉRIFICATION TERMINÉE")
print("=" * 80)

conn.close()
