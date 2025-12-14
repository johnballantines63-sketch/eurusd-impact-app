"""
Investigation : Où sont les événements HIGH classiques ?

Chercher dans les 149 patterns :
1. Combien ont USD_NFP / USD_CPI ?
2. Pourquoi classés "X_others" ?
3. Analyse fenêtre temporelle

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Investigation
"""

import json
from pathlib import Path

# Fichier
CLUSTERS_FILE = Path(__file__).parent / 'validation_results' / 'clusters_analysis.json'


def investigate_high_events():
    """Chercher événements HIGH classiques dans patterns"""
    
    print("=" * 80)
    print("INVESTIGATION : OÙ SONT LES ÉVÉNEMENTS HIGH CLASSIQUES ?")
    print("=" * 80)
    print()
    
    # Charger analyse
    with open(CLUSTERS_FILE, 'r') as f:
        data = json.load(f)
    
    patterns = data['patterns_enriched']
    
    print(f"📊 Patterns total : {len(patterns)}")
    print()
    
    # ========================================================================
    # RECHERCHE NFP
    # ========================================================================
    
    print("=" * 80)
    print("1. RECHERCHE USD NFP")
    print("=" * 80)
    print()
    
    nfp_patterns = []
    
    for pattern in patterns:
        events = pattern.get('events', [])
        for event in events:
            event_name = event.get('event_name', '').upper()
            country = event.get('country', '').upper()
            
            if country == 'USD' and ('NFP' in event_name or 'NON-FARM' in event_name or 'EMPLOYMENT CHANGE' in event_name):
                nfp_patterns.append({
                    'date': pattern['date'],
                    'event_name': event['event_name'],
                    'importance': event.get('importance'),
                    'cluster_sig': pattern['cluster_signature'],
                    'amplitude': pattern['wave2_amp_pips'],
                    'delta_minutes': event.get('delta_minutes')
                })
                break
    
    print(f"Patterns avec NFP : {len(nfp_patterns)}")
    print()
    
    if len(nfp_patterns) > 0:
        print("Détails :")
        for i, p in enumerate(nfp_patterns, 1):
            print(f"\n[{i}] {p['date']}")
            print(f"    Event        : {p['event_name']}")
            print(f"    Importance   : {p['importance']}")
            print(f"    Delta        : {p['delta_minutes']:.1f} min")
            print(f"    Cluster sig  : {p['cluster_sig']}")
            print(f"    Amplitude    : {p['amplitude']:.1f} pips")
    else:
        print("❌ AUCUN pattern avec NFP détecté !")
        print()
        print("Hypothèses :")
        print("   1. Fenêtre ±30 min rate NFP (souvent à 14:30 = -1 min baseline 14:29)")
        print("   2. NFP nommé différemment dans DB")
        print("   3. Rev12 ne détecte pas Double Wave sur NFP")
    
    print()
    
    # ========================================================================
    # RECHERCHE CPI
    # ========================================================================
    
    print("=" * 80)
    print("2. RECHERCHE USD CPI")
    print("=" * 80)
    print()
    
    cpi_patterns = []
    
    for pattern in patterns:
        events = pattern.get('events', [])
        for event in events:
            event_name = event.get('event_name', '').upper()
            country = event.get('country', '').upper()
            
            if country == 'USD' and 'CPI' in event_name:
                cpi_patterns.append({
                    'date': pattern['date'],
                    'event_name': event['event_name'],
                    'importance': event.get('importance'),
                    'cluster_sig': pattern['cluster_signature'],
                    'amplitude': pattern['wave2_amp_pips'],
                    'delta_minutes': event.get('delta_minutes')
                })
                break
    
    print(f"Patterns avec CPI : {len(cpi_patterns)}")
    print()
    
    if len(cpi_patterns) > 0:
        print("Détails :")
        for i, p in enumerate(cpi_patterns, 1):
            print(f"\n[{i}] {p['date']}")
            print(f"    Event        : {p['event_name']}")
            print(f"    Importance   : {p['importance']}")
            print(f"    Delta        : {p['delta_minutes']:.1f} min")
            print(f"    Cluster sig  : {p['cluster_sig']}")
            print(f"    Amplitude    : {p['amplitude']:.1f} pips")
    
    print()
    
    # ========================================================================
    # RECHERCHE 11 SEPTEMBRE
    # ========================================================================
    
    print("=" * 80)
    print("3. RECHERCHE 11 SEPTEMBRE 2025 (CAS RÉFÉRENCE)")
    print("=" * 80)
    print()
    
    sept11 = None
    for pattern in patterns:
        if pattern['date'] == '2025-09-11':
            sept11 = pattern
            break
    
    if sept11:
        print("✅ 11 septembre trouvé dans les 149 patterns")
        print()
        print(f"Cluster signature : {sept11['cluster_signature']}")
        print(f"Amplitude         : {sept11['wave2_amp_pips']:.1f} pips")
        print(f"Events count      : {sept11['events_count']}")
        print()
        
        if sept11['events_count'] > 0:
            print("Events détectés :")
            for i, event in enumerate(sept11['events'], 1):
                print(f"  [{i}] {event['country'].upper()} - {event['event_name']}")
                print(f"      Importance : {event.get('importance')}")
                print(f"      Delta      : {event.get('delta_minutes'):.1f} min")
        else:
            print("❌ Classé NO_EVENTS (aucun event détecté)")
    else:
        print("❌ 11 septembre PAS dans les 149 patterns Rev12")
        print()
        print("Hypothèses :")
        print("   1. Rev12 n'a pas détecté Double Wave ce jour")
        print("   2. Date hors période scan (jan 2024 - oct 2025)")
        print("   3. Problème baseline/timing")
    
    print()
    
    # ========================================================================
    # ANALYSE CLUSTERS "X_OTHERS"
    # ========================================================================
    
    print("=" * 80)
    print("4. ANALYSE CLUSTERS 'X_OTHERS'")
    print("=" * 80)
    print()
    
    others_clusters = [p for p in patterns if '_others' in p['cluster_signature']]
    
    print(f"Patterns avec 'X_others' : {len(others_clusters)} ({len(others_clusters)/len(patterns)*100:.1f}%)")
    print()
    
    if len(others_clusters) > 0:
        print("TOP 5 clusters 'others' :")
        
        # Grouper
        from collections import defaultdict
        groups = defaultdict(list)
        for p in others_clusters:
            groups[p['cluster_signature']].append(p)
        
        sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for sig, pats in sorted_groups[:5]:
            print(f"\n   • {sig}")
            print(f"     {len(pats)} occurrences")
            print(f"     Exemple date : {pats[0]['date']}")
            print(f"     Events count : {pats[0]['events_count']}")
    
    print()
    
    # ========================================================================
    # ANALYSE FENÊTRE TEMPORELLE
    # ========================================================================
    
    print("=" * 80)
    print("5. ANALYSE FENÊTRE TEMPORELLE")
    print("=" * 80)
    print()
    
    print("Fenêtre actuelle : ±30 min autour baseline (14:29)")
    print("Range détection  : 13:59 - 14:59")
    print()
    
    # Compter events par delta
    all_deltas = []
    for pattern in patterns:
        for event in pattern.get('events', []):
            delta = event.get('delta_minutes', 0)
            all_deltas.append(delta)
    
    if len(all_deltas) > 0:
        print(f"Total events détectés : {len(all_deltas)}")
        print()
        
        # Distribution
        in_minus_10 = sum(1 for d in all_deltas if -10 <= d <= 0)
        in_0_10 = sum(1 for d in all_deltas if 0 < d <= 10)
        in_10_20 = sum(1 for d in all_deltas if 10 < d <= 20)
        out_range = sum(1 for d in all_deltas if d < -10 or d > 20)
        
        print("Distribution temporelle :")
        print(f"   -10 à 0 min   : {in_minus_10} ({in_minus_10/len(all_deltas)*100:.1f}%)")
        print(f"   0 à +10 min   : {in_0_10} ({in_0_10/len(all_deltas)*100:.1f}%)")
        print(f"   +10 à +20 min : {in_10_20} ({in_10_20/len(all_deltas)*100:.1f}%)")
        print(f"   Hors cœur     : {out_range} ({out_range/len(all_deltas)*100:.1f}%)")
        print()
        
        # Events hors fenêtre
        very_early = [d for d in all_deltas if d < -20]
        very_late = [d for d in all_deltas if d > 20]
        
        if len(very_early) > 0:
            print(f"⚠️  Events très en avance (< -20 min) : {len(very_early)}")
            print(f"   Min : {min(very_early):.1f} min")
        
        if len(very_late) > 0:
            print(f"⚠️  Events très en retard (> +20 min) : {len(very_late)}")
            print(f"   Max : {max(very_late):.1f} min")
    
    print()
    
    # ========================================================================
    # CONCLUSION
    # ========================================================================
    
    print("=" * 80)
    print("CONCLUSION INVESTIGATION")
    print("=" * 80)
    print()
    
    print(f"1. NFP détectés     : {len(nfp_patterns)}/{len(patterns)}")
    print(f"2. CPI détectés     : {len(cpi_patterns)}/{len(patterns)}")
    print(f"3. 11 sept présent  : {'✅' if sept11 else '❌'}")
    print(f"4. NO_EVENTS        : {sum(1 for p in patterns if p['cluster_signature'] == 'NO_EVENTS')}/{len(patterns)} (26%)")
    print()
    
    if len(nfp_patterns) == 0 and len(cpi_patterns) == 0:
        print("🔬 DIAGNOSTIC :")
        print()
        print("❌ Événements HIGH majeurs (NFP, CPI) absents des patterns")
        print()
        print("HYPOTHÈSES :")
        print("   1. Rev12 détecte surtout patterns techniques mineurs")
        print("   2. Seuil détection inadapté pour events majeurs")
        print("   3. Fenêtre temporelle rate timing events HIGH")
        print("   4. Events HIGH créent patterns différents (pas Double Wave)")
        print()
        print("ACTIONS :")
        print("   → Vérifier si 11 sept dans 149 patterns")
        print("   → Analyser pourquoi NFP/CPI absents")
        print("   → Peut-être focus sur clusters techniques stables")
        print("   → Ou ajuster Rev12 pour capturer events majeurs")
    else:
        print("✅ Événements HIGH détectés, analyse clusters possible")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    investigate_high_events()
