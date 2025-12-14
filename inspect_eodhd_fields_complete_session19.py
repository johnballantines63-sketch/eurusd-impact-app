#!/usr/bin/env python3
"""
Script Session 19 : Inspection COMPLÈTE des champs EODHD
=========================================================

But : Examiner TOUS les champs retournés par l'API EODHD pour :
1. Identifier les champs manquants dans notre DB
2. Comprendre leur utilité potentielle
3. Décider lesquels importer

On inspecte plusieurs dates/pays pour avoir un échantillon représentatif.
"""

import sys
from pathlib import Path
import pandas as pd
from collections import Counter, defaultdict
import json

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from fx_impact_app.src.eodhd_client import fetch_calendar_json

# Couleurs
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_section(msg: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{msg}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")

def print_subsection(msg: str):
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[{msg}]{Colors.END}")


# =============================================================================
# PHASE 1 : Collecter un échantillon représentatif
# =============================================================================

def collect_sample_data():
    """Collecte des données de plusieurs dates/pays"""
    print_section("PHASE 1 : Collecte échantillon de données EODHD")
    
    # Dates importantes (variété d'événements)
    test_dates = [
        ('2025-09-11', 'US'),  # Le cas problématique
        ('2025-01-10', 'US'),  # NFP
        ('2024-06-12', 'US'),  # CPI
        ('2024-12-18', 'US'),  # FOMC
        ('2025-03-20', 'EU'),  # ECB
        ('2024-09-19', 'GB'),  # BoE
        ('2024-08-02', 'JP'),  # BoJ
    ]
    
    all_items = []
    
    for date, country in test_dates:
        print(f"\n   Récupération : {date} ({country})...", end=' ')
        try:
            items = fetch_calendar_json(date, date, countries=[country])
            all_items.extend(items)
            print(f"✅ {len(items)} événements")
        except Exception as e:
            print(f"❌ Erreur : {e}")
    
    print(f"\n   {Colors.GREEN}Total échantillon : {len(all_items)} événements{Colors.END}")
    
    return all_items


# =============================================================================
# PHASE 2 : Analyser TOUS les champs
# =============================================================================

def analyze_all_fields(items):
    """Analyse tous les champs présents"""
    print_section("PHASE 2 : Analyse de TOUS les champs")
    
    # Collecter tous les champs uniques
    all_fields = set()
    field_counts = Counter()
    field_examples = defaultdict(list)
    field_types = defaultdict(set)
    
    for item in items:
        for key, value in item.items():
            all_fields.add(key)
            field_counts[key] += 1
            
            # Type
            field_types[key].add(type(value).__name__)
            
            # Exemples (limiter à 3)
            if len(field_examples[key]) < 3 and value is not None and value != '':
                field_examples[key].append(str(value)[:100])  # Limiter longueur
    
    # Afficher résumé
    print_subsection(f"Total champs uniques trouvés : {len(all_fields)}")
    
    # Trier par fréquence
    sorted_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Champ':<30} {'Présence':>10} {'%':>6} {'Types':>20} {'Exemples'}")
    print("-" * 120)
    
    for field, count in sorted_fields:
        pct = (count / len(items)) * 100
        types = ', '.join(field_types[field])
        examples = ' | '.join(field_examples[field][:2])
        
        # Colorier selon importance
        if pct > 80:
            color = Colors.GREEN
        elif pct > 30:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        
        print(f"{field:<30} {color}{count:>10}{Colors.END} {pct:>5.1f}% {types:<20} {examples[:60]}")
    
    return all_fields, field_counts, field_examples, field_types


# =============================================================================
# PHASE 3 : Comparer avec notre schéma DB
# =============================================================================

def compare_with_db_schema(all_fields):
    """Compare avec les champs qu'on importe actuellement"""
    print_section("PHASE 3 : Comparaison avec schéma DB actuel")
    
    # Champs actuellement importés dans notre DB
    db_fields = {
        'ts_utc',      # Depuis 'date'
        'country',     # Depuis 'country'
        'event_title', # Depuis 'event'
        'event_key',   # Calculé
        'label',       # Depuis 'label'
        'type',        # Depuis 'category'
        'estimate',    # Depuis 'estimate'
        'forecast',    # Depuis 'forecast'
        'previous',    # Depuis 'previous'
        'actual',      # Depuis 'actual'
        'unit',        # Depuis 'unit'
        'importance_n' # Depuis 'importance'
    }
    
    # Mapping EODHD -> DB
    eodhd_to_db = {
        'date': 'ts_utc',
        'country': 'country',
        'event': 'event_title',
        'label': 'label',
        'category': 'type',
        'estimate': 'estimate',
        'forecast': 'forecast',
        'previous': 'previous',
        'actual': 'actual',
        'unit': 'unit',
        'importance': 'importance_n'
    }
    
    print_subsection("Champs EODHD actuellement importés")
    for eodhd_field, db_field in eodhd_to_db.items():
        status = "✅" if eodhd_field in all_fields else "❌"
        print(f"   {status} {eodhd_field:<20} → {db_field}")
    
    # Champs EODHD NON importés
    imported_eodhd = set(eodhd_to_db.keys())
    not_imported = all_fields - imported_eodhd
    
    print_subsection(f"Champs EODHD NON importés ({len(not_imported)})")
    
    for field in sorted(not_imported):
        print(f"   ❌ {field}")
    
    return not_imported


# =============================================================================
# PHASE 4 : Analyser les champs manquants importants
# =============================================================================

def analyze_missing_fields(items, not_imported, field_counts, field_examples):
    """Analyse détaillée des champs manquants"""
    print_section("PHASE 4 : Analyse des champs manquants IMPORTANTS")
    
    # Champs potentiellement importants (présents dans >20% des événements)
    important_missing = {
        field for field in not_imported 
        if field_counts[field] / len(items) > 0.2
    }
    
    print_subsection(f"Champs manquants présents dans >20% des événements ({len(important_missing)})")
    
    for field in sorted(important_missing):
        count = field_counts[field]
        pct = (count / len(items)) * 100
        examples = field_examples[field]
        
        print(f"\n   📊 {Colors.BOLD}{field}{Colors.END}")
        print(f"      Présence : {count}/{len(items)} ({pct:.1f}%)")
        print(f"      Exemples : {examples}")
        
        # Extraire des exemples réels
        real_examples = []
        for item in items:
            if field in item and item[field] is not None and item[field] != '':
                real_examples.append({
                    'event': item.get('event', 'N/A'),
                    'country': item.get('country', 'N/A'),
                    field: item[field]
                })
                if len(real_examples) >= 3:
                    break
        
        if real_examples:
            print(f"      Contexte :")
            for ex in real_examples:
                print(f"         {ex['country']} | {ex['event'][:40]:<40} | {field}={ex[field]}")


# =============================================================================
# PHASE 5 : Focus sur 'comparison' (notre problème actuel)
# =============================================================================

def analyze_comparison_field(items):
    """Analyse spécifique du champ 'comparison'"""
    print_section("PHASE 5 : Analyse détaillée du champ 'comparison'")
    
    # Stats sur comparison
    with_comparison = [item for item in items if 'comparison' in item and item['comparison']]
    
    print(f"   Total événements avec 'comparison' : {len(with_comparison)} / {len(items)} ({len(with_comparison)/len(items)*100:.1f}%)")
    
    # Valeurs uniques
    comparison_values = Counter()
    comparison_by_event = defaultdict(list)
    
    for item in with_comparison:
        comp = item['comparison']
        event = item.get('event', 'Unknown')
        comparison_values[comp] += 1
        comparison_by_event[event].append(comp)
    
    print_subsection("Valeurs de 'comparison'")
    for comp, count in comparison_values.most_common():
        print(f"   {comp:<10} : {count:>4} événements")
    
    print_subsection("Événements avec plusieurs 'comparison'")
    multi_comp = {event: comps for event, comps in comparison_by_event.items() if len(set(comps)) > 1}
    
    if multi_comp:
        for event, comps in sorted(multi_comp.items())[:10]:
            unique_comps = set(comps)
            print(f"   {event[:50]:<50} : {', '.join(unique_comps)}")
    else:
        print("   Aucun événement avec plusieurs versions trouvé dans l'échantillon")


# =============================================================================
# PHASE 6 : Recommandations
# =============================================================================

def generate_recommendations(all_fields, not_imported, field_counts, items):
    """Génère des recommandations"""
    print_section("PHASE 6 : Recommandations")
    
    # Champs critiques à ajouter
    critical_fields = []
    
    # 1. comparison (notre problème actuel)
    if 'comparison' in not_imported:
        pct = (field_counts['comparison'] / len(items)) * 100
        critical_fields.append({
            'field': 'comparison',
            'priority': 'CRITIQUE',
            'reason': 'Permet de distinguer MoM/YoY/QoQ (problème actuel)',
            'presence': f"{pct:.1f}%",
            'action': 'AJOUTER à calendar_to_events_df() et à la table events'
        })
    
    # 2. Autres champs fréquents
    for field in not_imported:
        pct = (field_counts[field] / len(items)) * 100
        
        if pct > 50 and field not in ['comparison']:
            priority = 'HAUTE' if pct > 80 else 'MOYENNE'
            critical_fields.append({
                'field': field,
                'priority': priority,
                'reason': f'Présent dans {pct:.1f}% des événements',
                'presence': f"{pct:.1f}%",
                'action': 'À ÉVALUER'
            })
    
    # Trier par priorité
    priority_order = {'CRITIQUE': 0, 'HAUTE': 1, 'MOYENNE': 2}
    critical_fields.sort(key=lambda x: (priority_order[x['priority']], -float(x['presence'].rstrip('%'))))
    
    print_subsection("Champs recommandés pour l'import")
    print(f"\n{'Priorité':<12} {'Champ':<25} {'Présence':>10} {'Action':<30} {'Raison'}")
    print("-" * 120)
    
    for rec in critical_fields[:10]:  # Top 10
        color = Colors.RED if rec['priority'] == 'CRITIQUE' else Colors.YELLOW if rec['priority'] == 'HAUTE' else Colors.BLUE
        print(f"{color}{rec['priority']:<12}{Colors.END} {rec['field']:<25} {rec['presence']:>10} {rec['action']:<30} {rec['reason']}")
    
    # Résumé
    print_subsection("Plan d'action recommandé")
    print(f"""
    1. {Colors.RED}IMMÉDIAT{Colors.END} : Ajouter 'comparison' (déjà fait dans le code)
    
    2. {Colors.YELLOW}COURT TERME{Colors.END} : Évaluer et ajouter les champs haute présence :
       - Ajouter colonnes à la table events
       - Modifier calendar_to_events_df() pour les extraire
       - Documenter leur utilité
    
    3. {Colors.BLUE}MOYEN TERME{Colors.END} : Stratégie de stockage :
       - Stocker JSON brut complet dans une colonne dédiée ?
       - Permet flexibilité future sans re-import
       - Trade-off : taille DB vs flexibilité
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}SESSION 19 : Inspection COMPLÈTE des champs EODHD{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    # Phase 1 : Collecter échantillon
    items = collect_sample_data()
    
    if not items:
        print(f"{Colors.RED}❌ Aucune donnée collectée{Colors.END}")
        return 1
    
    # Phase 2 : Analyser tous les champs
    all_fields, field_counts, field_examples, field_types = analyze_all_fields(items)
    
    # Phase 3 : Comparer avec DB
    not_imported = compare_with_db_schema(all_fields)
    
    # Phase 4 : Analyser champs manquants
    analyze_missing_fields(items, not_imported, field_counts, field_examples)
    
    # Phase 5 : Focus comparison
    analyze_comparison_field(items)
    
    # Phase 6 : Recommandations
    generate_recommendations(all_fields, not_imported, field_counts, items)
    
    # Export JSON pour inspection manuelle
    print_section("Export des données pour inspection manuelle")
    
    export_path = PROJECT_ROOT / "eodhd_sample_data_session19.json"
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(items[:50], f, indent=2, ensure_ascii=False)  # Limiter à 50
    
    print(f"   ✅ Échantillon exporté : {export_path.name}")
    print(f"   💡 Inspectez ce fichier pour voir tous les champs en détail")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ Inspection terminée{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Interrompu par l'utilisateur{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erreur fatale : {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
