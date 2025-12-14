#!/usr/bin/env python3
"""
Vérifie l'état du projet et détecte les bugs
1. Vérifie backtest_multi_events_phases_FIXED.py
2. Analyse predict_impact() dans Planificateur
3. Détecte bug impact = 0
"""
from pathlib import Path
import re

PROJECT_ROOT = Path("/Users/andrevalentin/Projects/eurusd_news_impact_calculator")

print("=" * 60)
print("🔍 DIAGNOSTIC COMPLET PROJET EUR/USD")
print("=" * 60)

# 1. VÉRIFIER BACKTEST EXISTANT
print("\n1️⃣ Recherche backtest_multi_events_phases_FIXED.py...")
backtest_path = PROJECT_ROOT / "backtest_multi_events_phases_FIXED.py"

if backtest_path.exists():
    print(f"✅ TROUVÉ : {backtest_path}")
    size = backtest_path.stat().st_size
    print(f"   Taille : {size:,} bytes")
    
    # Analyser contenu
    content = backtest_path.read_text()
    lines = len(content.split('\n'))
    print(f"   Lignes : {lines}")
    
    # Chercher fonctions clés
    if 'predict_impact_simple' in content:
        print("   ✅ predict_impact_simple() trouvée")
    if 'calculate_real_ttr' in content:
        print("   ✅ calculate_real_ttr() trouvée")
    if 'sequence_multi_event_timeline' in content:
        print("   ✅ Import sequence_multi_event_timeline")
    
    print("\n   📊 Ce backtest est PRÊT À UTILISER !")
else:
    print(f"❌ NON TROUVÉ : {backtest_path}")
    print("   ⚠️ Le backtest validé n'existe plus !")

# 2. ANALYSER PLANIFICATEUR
print("\n2️⃣ Analyse du Planificateur Streamlit...")
planif_path = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

if not planif_path.exists():
    print(f"❌ Planificateur NON TROUVÉ : {planif_path}")
else:
    print(f"✅ Planificateur trouvé : {planif_path}")
    content = planif_path.read_text()
    lines = content.split('\n')
    total_lines = len(lines)
    print(f"   Lignes totales : {total_lines}")
    
    # 3. CHERCHER BUG IMPACT = 0
    print("\n3️⃣ Recherche bug impact = 0...")
    
    # Chercher predict_impact_fast ou predict_impact_simple
    bug_found = False
    for i, line in enumerate(lines, 1):
        # Chercher définition fonction
        if re.search(r'def predict_impact.*\(', line):
            print(f"\n   📍 Fonction trouvée ligne {i}: {line.strip()}")
            
            # Analyser les 30 lignes suivantes
            for j in range(i, min(i+30, total_lines)):
                snippet = lines[j].strip()
                
                # Détecter bug : surprise absolue au lieu de %
                if 'surprise' in snippet and '=' in snippet and 'actual - estimate' in snippet:
                    if 'surprise_pct' not in snippet and '* 100' not in snippet:
                        print(f"   ❌ BUG DÉTECTÉ ligne {j+1}:")
                        print(f"      {lines[j]}")
                        bug_found = True
                
                # Détecter calcul impact cassé
                if 'impact' in snippet and '=' in snippet and 'surprise' in snippet:
                    if '30' in snippet or '0.3' in snippet:
                        print(f"   ❌ CALCUL CASSÉ ligne {j+1}:")
                        print(f"      {lines[j]}")
                        bug_found = True
    
    if bug_found:
        print("\n   ⚠️ BUG IMPACT = 0 CONFIRMÉ !")
        print("   → Correction nécessaire")
    else:
        print("\n   ✅ Pas de bug évident détecté")
        print("   (Mais impact = 0 peut avoir d'autres causes)")
    
    # 4. CHERCHER DROP_DUPLICATES
    print("\n4️⃣ Recherche drop_duplicates problématique...")
    
    for i, line in enumerate(lines, 1):
        if 'drop_duplicates' in line and 'family' in line:
            print(f"   ⚠️ Ligne {i}: {line.strip()}")
            print("   → Devrait être : drop_duplicates(subset=['ts_utc', 'event_key'])")

# 5. RÉSUMÉ
print("\n" + "=" * 60)
print("📊 RÉSUMÉ")
print("=" * 60)

if backtest_path.exists():
    print("✅ Backtest validé disponible")
    print(f"   → Lancer : python3 {backtest_path.name}")
else:
    print("❌ Backtest validé MANQUANT")

if bug_found:
    print("❌ Bug impact = 0 détecté dans Planificateur")
    print("   → Correction automatique possible")
else:
    print("⚠️ Bug impact = 0 non localisé automatiquement")
    print("   → Analyse manuelle nécessaire")

print("\n🎯 PROCHAINES ACTIONS :")
print("1. Si backtest existe → Le tester")
print("2. Si bug détecté → Créer script de correction")
print("3. Envoyer fichier Planificateur complet pour analyse détaillée")

print("\n" + "=" * 60)
