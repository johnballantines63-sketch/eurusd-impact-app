#!/usr/bin/env python3
"""
LISTE ÉVÉNEMENTS CLUSTER DE RÉFÉRENCE
======================================

Affiche la liste complète des événements du cluster de référence
pour vérifier qu'on recherche les bons événements.

Auteur : André Valentin avec Claude
Date : 17 novembre 2025
"""

import json
from pathlib import Path
import sys

# Import utils Session 127 (strip_variant_suffix)
sys.path.insert(0, str(Path(__file__).parent / 'session127'))
try:
    from utils_mapping_variants import strip_variant_suffix
    STRIP_VARIANT_AVAILABLE = True
except ImportError:
    print("⚠️  utils_mapping_variants.py non trouvé")
    STRIP_VARIANT_AVAILABLE = False
    def strip_variant_suffix(x): return x

# Chemins
REFERENCE_FILE = Path(__file__).parent / "session130" / "reference_cases_with_amplifications.json"
REFERENCE_DATE = "2025-09-11"
REFERENCE_PATTERN = "DoubleWave_Overlap"


def normalize_event_key_basic(event_key: str) -> str:
    """Normalisation basique (Session 130)"""
    return event_key.lower().strip()


def normalize_event_key_with_variants(event_key: str) -> str:
    """Normalisation avec gestion variantes (Session 127)"""
    normalized = event_key.lower().strip()
    base = strip_variant_suffix(normalized)
    return base


def main():
    print("=" * 80)
    print("LISTE ÉVÉNEMENTS CLUSTER DE RÉFÉRENCE")
    print("=" * 80)
    
    # Charger cas référence
    if not REFERENCE_FILE.exists():
        print(f"❌ Fichier introuvable : {REFERENCE_FILE}")
        return 1
    
    with open(REFERENCE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ref_case = data['reference_cases'].get(REFERENCE_PATTERN)
    if not ref_case:
        print(f"❌ Pattern {REFERENCE_PATTERN} introuvable")
        return 1
    
    events = ref_case['events']
    
    print(f"\n📅 Date : {ref_case['date']}")
    print(f"📊 Pattern : {REFERENCE_PATTERN}")
    print(f"📈 Impact réel : {ref_case.get('impact_real', 0):.1f} pips")
    print(f"🔢 Nombre d'événements : {len(events)}")
    
    print(f"\n{'='*80}")
    print("LISTE COMPLÈTE DES ÉVÉNEMENTS (ORDRE CHRONOLOGIQUE)")
    print(f"{'='*80}\n")
    
    print(f"{'#':<4} {'Heure':<20} {'Event Key (ORIGINAL)':<50} {'Normalisé Basic':<40} {'Normalisé Variants':<40}")
    print("-" * 160)
    
    event_keys_raw = []
    event_keys_basic = []
    event_keys_variants = []
    
    for i, event in enumerate(events, 1):
        event_key_raw = event['event_key']
        event_key_basic = normalize_event_key_basic(event_key_raw)
        event_key_variants = normalize_event_key_with_variants(event_key_raw)
        
        ts_utc = event.get('ts_utc', 'N/A')
        country = event.get('country', 'N/A')
        
        event_keys_raw.append(event_key_raw)
        event_keys_basic.append(event_key_basic)
        event_keys_variants.append(event_key_variants)
        
        # Tronquer si trop long
        raw_display = event_key_raw[:47] + "..." if len(event_key_raw) > 50 else event_key_raw
        basic_display = event_key_basic[:37] + "..." if len(event_key_basic) > 40 else event_key_basic
        variants_display = event_key_variants[:37] + "..." if len(event_key_variants) > 40 else event_key_variants
        
        print(f"{i:<4} {ts_utc:<20} {raw_display:<50} {basic_display:<40} {variants_display:<40}")
    
    print(f"\n{'='*80}")
    print("COMPOSITION UNIQUE (SETS)")
    print(f"{'='*80}\n")
    
    composition_basic = set(event_keys_basic)
    composition_variants = set(event_keys_variants)
    
    print(f"📋 Composition BRUTE (raw) :")
    print(f"   Total événements : {len(event_keys_raw)}")
    print(f"   Événements uniques : {len(set(event_keys_raw))}")
    print(f"   Liste : {sorted(set(event_keys_raw))}")
    
    print(f"\n📋 Composition NORMALISÉE BASIC (lower + strip) :")
    print(f"   Total événements : {len(event_keys_basic)}")
    print(f"   Événements uniques : {len(composition_basic)}")
    print(f"   Liste : {sorted(composition_basic)}")
    
    print(f"\n📋 Composition NORMALISÉE VARIANTS (strip_variant_suffix) :")
    print(f"   Total événements : {len(event_keys_variants)}")
    print(f"   Événements uniques : {len(composition_variants)}")
    print(f"   Liste : {sorted(composition_variants)}")
    
    print(f"\n{'='*80}")
    print("COMPARAISON")
    print(f"{'='*80}\n")
    
    print(f"Différence Basic vs Variants :")
    only_basic = composition_basic - composition_variants
    only_variants = composition_variants - composition_basic
    
    if only_basic:
        print(f"   ⚠️  Dans Basic mais pas Variants : {sorted(only_basic)}")
    if only_variants:
        print(f"   ⚠️  Dans Variants mais pas Basic : {sorted(only_variants)}")
    
    if not only_basic and not only_variants:
        print(f"   ✅ Les deux normalisations donnent le même résultat")
    
    print(f"\n{'='*80}")
    print("RÉSUMÉ POUR RECHERCHE")
    print(f"{'='*80}\n")
    
    print(f"🔍 Composition à rechercher dans la DB :")
    print(f"\n   MÉTHODE BASIC (normalize_event_key_basic) :")
    print(f"   {sorted(composition_basic)}")
    
    print(f"\n   MÉTHODE VARIANTS (normalize_event_key_with_variants) :")
    print(f"   {sorted(composition_variants)}")
    
    print(f"\n   ⚠️  ATTENTION : Les event_keys dans la DB doivent être normalisés")
    print(f"      de la même manière pour que la recherche fonctionne !")
    
    return 0


if __name__ == "__main__":
    exit(main())

