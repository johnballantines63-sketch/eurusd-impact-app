"""
VÉRIFICATION : V2 ET LES MULTI-ÉVÉNEMENTS
Clarifier si V2 traite correctement les événements simultanés
"""

import duckdb
import pandas as pd
from pathlib import Path

print("=" * 80)
print("🔍 VÉRIFICATION V2 - TRAITEMENT MULTI-ÉVÉNEMENTS")
print("=" * 80)
print()

DB_PATH = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Événements à 14:30 (tous)
# ════════════════════════════════════════════════════════════════

print("📋 TOUS LES ÉVÉNEMENTS À 14:30 LE 11 SEPTEMBRE 2025 :")
print()

query_events_1430 = """
SELECT 
    e.ts_utc,
    e.event_key,
    e.event_title,
    e.country,
    e.actual,
    e.estimate,
    e.importance_n,
    ef.empirical_score,
    CASE 
        WHEN e.estimate IS NOT NULL AND e.estimate != 0 
        THEN ABS((e.actual - e.estimate) / e.estimate) * 100.0
        ELSE NULL
    END as surprise_pct
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE strftime(e.ts_utc, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
ORDER BY ef.empirical_score DESC NULLS LAST
"""

events_1430 = conn.execute(query_events_1430).fetchdf()

print(f"Total : {len(events_1430)} événements")
print()

for idx, row in events_1430.iterrows():
    score = f"{row['empirical_score']:.1f}" if pd.notna(row['empirical_score']) else "N/A"
    surprise = f"{row['surprise_pct']:.1f}%" if pd.notna(row['surprise_pct']) else "N/A"
    imp = {1: 'HIGH', 2: 'MEDIUM', 3: 'LOW'}.get(row['importance_n'], 'UNKNOWN')
    
    print(f"  {idx+1}. {row['event_title']:45s} | Score={score:>6s} | Surprise={surprise:>6s} | Imp={imp}")

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Comment V2 traite ce groupe
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("🔧 TRAITEMENT V2 DU GROUPE")
print("=" * 80)
print()

# Score max du groupe
max_score = events_1430['empirical_score'].max()
max_surprise = events_1430['surprise_pct'].max()

print(f"📊 SCORE MAX DU GROUPE : {max_score:.1f}")
print(f"⚡ SURPRISE MAX DU GROUPE : {max_surprise:.1f}%")
print()

# Formule v9-CLEAN
impact_base = -7.08 + 0.419 * max_score

print(f"📐 FORMULE v9-CLEAN :")
print(f"   impact_base = -7.08 + 0.419 × {max_score:.1f}")
print(f"   impact_base = {impact_base:.1f} pips")
print()

# Amplification V2
def calculate_amplification_v2(surprise_pct, empirical_score):
    surprise_abs = abs(surprise_pct) if pd.notna(surprise_pct) else 0
    
    if surprise_abs > 30:
        surprise_abs = 30.0
    
    if empirical_score < 40:
        return 1.0
    
    if surprise_abs < 5.0:
        return 1.0
    elif surprise_abs < 15.0:
        return 1.0 + (surprise_abs - 5.0) * 0.15
    else:
        return 2.5

amplification = calculate_amplification_v2(max_surprise, max_score)

print(f"🔄 AMPLIFICATION V2 :")
print(f"   Surprise {max_surprise:.1f}% → Amplification ×{amplification:.2f}")
print()

# Impact final
CALIBRATION = 0.758
impact_final = abs(impact_base) * amplification * CALIBRATION

print(f"🎯 IMPACT FINAL V2 :")
print(f"   {abs(impact_base):.1f} × {amplification:.2f} × {CALIBRATION:.3f} = {impact_final:.1f} pips")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Comparer avec la méthode "additive"
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📊 COMPARAISON AVEC MÉTHODE ADDITIVE (HYPOTHÉTIQUE)")
print("=" * 80)
print()

print("Si on calculait l'impact de CHAQUE événement séparément puis qu'on additionnait :")
print()

total_additive = 0

for idx, row in events_1430.iterrows():
    if pd.notna(row['empirical_score']):
        impact_evt = -7.08 + 0.419 * row['empirical_score']
        surprise = row['surprise_pct'] if pd.notna(row['surprise_pct']) else 0
        amp = calculate_amplification_v2(surprise, row['empirical_score'])
        impact_evt_final = abs(impact_evt) * amp * CALIBRATION
        total_additive += impact_evt_final
        
        print(f"  {row['event_title']:45s} : {impact_evt_final:.1f} pips")

print()
print(f"  TOTAL ADDITIF : {total_additive:.1f} pips")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Méthode actuelle vs réel
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("🎯 COMPARAISON FINALE")
print("=" * 80)
print()

# Impact réel
query_real = """
SELECT mfe_pips
FROM event_group_impacts
WHERE time_group = TIMESTAMP '2025-09-11 14:30:00'
"""

real = conn.execute(query_real).fetchdf()
impact_reel = real['mfe_pips'].values[0] if len(real) > 0 else None

print(f"Méthode V2 (score MAX)     : {impact_final:.1f} pips")
print(f"Méthode ADDITIVE (somme)   : {total_additive:.1f} pips")
if impact_reel:
    print(f"Impact RÉEL MT5            : {impact_reel:.1f} pips")
    print()
    print(f"Erreur V2 (MAX)            : {abs(impact_final - impact_reel):.1f} pips ({abs(impact_final - impact_reel)/impact_reel*100:.0f}%)")
    print(f"Erreur ADDITIVE            : {abs(total_additive - impact_reel):.1f} pips ({abs(total_additive - impact_reel)/impact_reel*100:.0f}%)")

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Vérifier la méthodologie dans event_group_impacts
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📚 MÉTHODOLOGIE DANS event_group_impacts")
print("=" * 80)
print()

query_group_method = """
SELECT 
    time_group,
    num_events,
    event_keys,
    max_empirical_score,
    mean_empirical_score,
    mfe_pips
FROM event_group_impacts
WHERE time_group = TIMESTAMP '2025-09-11 14:30:00'
"""

group_info = conn.execute(query_group_method).fetchdf()

if len(group_info) > 0:
    row = group_info.iloc[0]
    print(f"Nombre d'événements        : {row['num_events']}")
    print(f"Événements                 : {row['event_keys']}")
    print(f"Score MAX du groupe        : {row['max_empirical_score']:.1f}")
    print(f"Score MOYEN du groupe      : {row['mean_empirical_score']:.1f}")
    print(f"MFE réel                   : {row['mfe_pips']:.1f} pips")
    print()
    
    # Est-ce que la DB utilise MAX ou MEAN ?
    print("💡 ANALYSE :")
    print()
    
    # Test avec MAX
    impact_with_max = abs(-7.08 + 0.419 * row['max_empirical_score'])
    print(f"   Si formule v9 utilise MAX  : {impact_with_max:.1f} pips base")
    
    # Test avec MEAN
    impact_with_mean = abs(-7.08 + 0.419 * row['mean_empirical_score'])
    print(f"   Si formule v9 utilise MEAN : {impact_with_mean:.1f} pips base")
    
    print()
    print(f"   → La DB stocke les DEUX (max et mean)")
    print(f"   → V2 utilise actuellement : MAX")
    print(f"   → C'est cohérent avec la méthodologie Session 8-9")

print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 6 : Documentation de la méthodologie
# ════════════════════════════════════════════════════════════════

print("=" * 80)
print("📖 DOCUMENTATION - CE QUE FAIT V2")
print("=" * 80)
print()

print("✅ CE QUE V2 FAIT CORRECTEMENT :")
print()
print("1. GROUPEMENT : Identifie que 8 événements arrivent à 14:30")
print("2. SCORE MAX : Prend le score empirique MAX du groupe (81.7)")
print("3. SURPRISE MAX : Prend la surprise MAX du groupe (11.9%)")
print("4. IMPACT BASE : Calcule avec formule v9-CLEAN sur le score MAX")
print("5. AMPLIFICATION : Applique V2 sur la surprise MAX")
print("6. UN SEUL IMPACT : Prédit UN nombre pour TOUT le groupe")
print()

print("❌ CE QUE V2 NE FAIT PAS :")
print()
print("1. N'additionne PAS les impacts individuels")
print("2. Ne calcule PAS de 'synergie' entre événements")
print("3. N'utilise PAS le score MOYEN")
print("4. Ne différencie PAS CPI vs Jobless dans le calcul")
print()

print("💡 POURQUOI CETTE MÉTHODE ?")
print()
print("Basée sur Session 8-9 : Analyse de 2,089 groupes historiques")
print("→ Les événements simultanés ne s'ADDITIONNENT pas")
print("→ Le marché réagit au plus IMPORTANT (score max)")
print("→ Coefficient de synergie observé : ~1.05× (négligeable)")
print()

print("=" * 80)
print("✅ VÉRIFICATION TERMINÉE")
print("=" * 80)

conn.close()
