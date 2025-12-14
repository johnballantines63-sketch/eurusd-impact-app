"""
Script déduplication événements - LOGIQUE CORRIGÉE
===================================================

PROBLÈME RÉSOLU Session 113:
La logique était INVERSÉE ! Le script RETIRAIT les dérivés temporels
(_mom, _yoy) qui ont les MEILLEURS scores empiriques.

LOGIQUE CORRECTE (alignée avec eodhd_client_corrected.py):
1. GARDER les dérivés temporels (_mom, _yoy, _qoq)
2. RETIRER les événements "base" SI des dérivés existent
3. Normaliser et dédupliquer les clés restantes

EXEMPLE:
- "inflation rate" + "inflation rate_mom" + "inflation rate_yoy"
  → GARDE : inflation rate_mom, inflation rate_yoy
  → RETIRE : inflation rate (base)

Session 113 - André Valentin
"""
import pandas as pd

def deduplicate_events(events_df, verbose=True):
    """
    Dédupliquer événements en gardant les dérivés temporels prioritaires.
    
    LOGIQUE CORRIGÉE:
    1. EXCLURE événements sans estimate (pas de surprise calculable)
    2. Identifier événements "base" ayant des dérivés
    3. RETIRER les "base" SI dérivés existent
    4. GARDER tous les dérivés (_mom, _yoy, _qoq)
    5. Normaliser et dédupliquer clés restantes
    
    Args:
        events_df: DataFrame avec colonnes event_key, event_title, event
        verbose: Afficher détails déduplication (défaut True)
        
    Returns:
        DataFrame dédupliqué
    """
    if verbose:
        print("\n" + "="*80)
        print("DÉDUPLICATION ÉVÉNEMENTS")
        print("="*80)
    
    if verbose:
        print(f"\nÉvénements avant déduplication: {len(events_df)}")
    
    # Afficher tous les event_key
    print("\nEvent keys présents:")
    for idx, row in events_df.iterrows():
        estimate_str = f"est={row.get('estimate', 'N/A')}" if pd.notna(row.get('estimate')) else "est=N/A"
        print(f"  {row.get('event_key', 'N/A'):40s} | {estimate_str}")
    
    # ==========================================================================
    # RÈGLE 0 : Exclure événements sans estimate (Session 113)
    # ==========================================================================
    
    print("\n" + "-"*80)
    print("RÈGLE 0: Exclure événements sans estimate")
    print("-"*80)
    print("(Sans estimate, pas de surprise calculable)")
    
    # Filtrer événements sans estimate
    has_estimate = events_df['estimate'].notna()
    events_without_estimate = events_df[~has_estimate]
    
    if not events_without_estimate.empty:
        print(f"\nÉvénements exclus (pas d'estimate): {len(events_without_estimate)}")
        for _, row in events_without_estimate.iterrows():
            print(f"  - {row['event_key']} (actual={row.get('actual', 'N/A')}, estimate=N/A)")
    
    events_df = events_df[has_estimate].copy()
    print(f"\nAprès filtre estimate: {len(events_df)} événements")
    
    print("\n" + "-"*80)
    print("RÈGLE 1: GARDER dérivés temporels, RETIRER événements base")
    print("-"*80)
    
    temporal_suffixes = ['_mom', '_yoy', '_qoq', '_mtd', '_ytd']
    
    def get_base_key(event_key):
        """Extrait la clé base en retirant le suffixe temporel."""
        if pd.isna(event_key):
            return event_key
        for suffix in temporal_suffixes:
            if event_key.endswith(suffix):
                return event_key[:-len(suffix)]
        return event_key
    
    def has_temporal_suffix(event_key):
        """Vérifie si événement a un suffixe temporel."""
        if pd.isna(event_key):
            return False
        return any(event_key.endswith(suffix) for suffix in temporal_suffixes)
    
    # Identifier tous les événements avec dérivés
    events_df['base_key'] = events_df['event_key'].apply(get_base_key)
    events_df['is_temporal'] = events_df['event_key'].apply(has_temporal_suffix)
    
    # Trouver quelles bases ont des dérivés
    bases_with_temporals = set(
        events_df[events_df['is_temporal']]['base_key'].unique()
    )
    
    # Marquer événements base à retirer (ceux qui ont des dérivés)
    def should_remove_base(row):
        """True si événement base doit être retiré."""
        if row['is_temporal']:
            return False  # Ne jamais retirer les dérivés
        return row['base_key'] in bases_with_temporals
    
    events_df['remove_base'] = events_df.apply(should_remove_base, axis=1)
    
    # Afficher événements base retirés
    base_removed = events_df[events_df['remove_base']]
    if not base_removed.empty:
        print(f"\nÉvénements base retirés (dérivés existent): {len(base_removed)}")
        for _, row in base_removed.iterrows():
            # Trouver les dérivés correspondants
            base = row['base_key']
            derivs = events_df[
                (events_df['base_key'] == base) & 
                (events_df['is_temporal'])
            ]['event_key'].tolist()
            print(f"  - {row['event_key']:35s} (dérivés: {', '.join(derivs)})")
    
    # Filtrer : garder dérivés + bases sans dérivés
    events_filtered = events_df[~events_df['remove_base']].copy()
    print(f"\nAprès filtre bases: {len(events_filtered)} événements")
    
    # Afficher événements gardés
    print(f"\nÉvénements gardés:")
    for _, row in events_filtered.iterrows():
        status = "dérivé ✅" if row['is_temporal'] else "base (sans dérivé)"
        print(f"  {row['event_key']:35s} ({status})")
    
    # ==========================================================================
    # RÈGLE 2 : Normalisation event_key pour vraies duplications
    # ==========================================================================
    
    print("\n" + "-"*80)
    print("RÈGLE 2: Normalisation event_key")
    print("-"*80)
    
    def normalize_event_key(key):
        """Normalise event_key en supprimant variations typographiques."""
        if pd.isna(key):
            return key
        # Remplacer tirets par espaces, supprimer points, lowercase
        normalized = key.replace('-', ' ').replace('.', '').strip()
        # Remplacer espaces multiples par un seul
        normalized = ' '.join(normalized.split())
        return normalized.lower()
    
    # Ajouter colonne normalisée
    events_filtered['event_key_normalized'] = events_filtered['event_key'].apply(normalize_event_key)
    
    # Afficher les normalisations
    print("\nNormalisations:")
    has_normalizations = False
    for idx, row in events_filtered.iterrows():
        original = row['event_key']
        normalized = row['event_key_normalized']
        if original.lower().replace('-', ' ').replace('.', '').strip() != normalized:
            print(f"  {original:45s} → {normalized}")
            has_normalizations = True
    
    if not has_normalizations:
        print("  (aucune normalisation nécessaire)")
    
    # ==========================================================================
    # RÈGLE 3 : Déduplication par event_key_normalized
    # ==========================================================================
    
    print("\n" + "-"*80)
    print("RÈGLE 3: Déduplication par event_key normalisé")
    print("-"*80)
    
    # Grouper par event_key_normalized
    duplicates_found = events_filtered.groupby('event_key_normalized').size()
    duplicates_found = duplicates_found[duplicates_found > 1]
    
    if not duplicates_found.empty:
        print(f"\nEvent_key normalisés avec duplications: {len(duplicates_found)}")
        for event_key_norm, count in duplicates_found.items():
            print(f"  - {event_key_norm}: {count} occurrences")
            
            # Afficher les variantes
            variants = events_filtered[events_filtered['event_key_normalized'] == event_key_norm]
            for idx, row in variants.iterrows():
                original = row['event_key']
                title = row.get('event', 'None')
                print(f"    → {original:45s} | {title}")
    else:
        print("\nAucune duplication trouvée")
    
    # Déduplication: garder première occurrence par event_key_normalized
    events_dedup = events_filtered.drop_duplicates(subset=['event_key_normalized'], keep='first')
    
    print(f"\nAprès déduplication: {len(events_dedup)} événements")
    
    # ==========================================================================
    # VALIDATION
    # ==========================================================================
    
    print("\n" + "="*80)
    print("RÉSULTAT FINAL")
    print("="*80)
    
    print(f"\nÉvénements avant: {len(events_df)}")
    print(f"Événements après: {len(events_dedup)}")
    print(f"Événements retirés: {len(events_df) - len(events_dedup)}")
    
    print("\nÉvénements finaux:")
    for idx, row in events_dedup.iterrows():
        print(f"  {row['event_key']:45s} | {row.get('event', 'N/A')}")
    
    # Supprimer colonnes temporaires avant retour
    events_dedup = events_dedup.drop(columns=['base_key', 'is_temporal', 'remove_base', 'event_key_normalized'])
    
    return events_dedup


# =============================================================================
# TEST DE LA FONCTION
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("TEST DÉDUPLICATION - LOGIQUE CORRIGÉE")
    print("="*80)
    
    # Test avec données du Cluster 1 du 11 septembre
    test_data = {
        'event_key': [
            'cpi s.a',
            'inflation rate_mom',
            'real earnings_mom',
            'cpi',
            'core inflation rate_yoy',
            'core inflation rate_mom',
            'jobless claims 4-week average',
            'inflation rate_yoy',
            'initial jobless claims',
            'continuing jobless claims'
        ],
        'event': [
            'CPI s.a',
            'Inflation Rate MoM',
            'Real Earnings MoM',
            'CPI',
            'Core Inflation Rate YoY',
            'Core Inflation Rate MoM',
            'Jobless Claims 4-Week Average',
            'Inflation Rate YoY',
            'Initial Jobless Claims',
            'Continuing Jobless Claims'
        ],
        'empirical_score': [
            44.7, 45.7, 43.2, 45.1, 45.9, 45.0, 25.3, 46.1, 26.8, 26.8
        ],
        'estimate': [
            323.0, 0.3, None, 323.89, 3.1, 0.3, 232.0, 2.9, 235.0, 1950.0  # real_earnings = None !
        ],
        'actual': [
            323.364, 0.4, -0.1, 323.98, 3.1, 0.3, 240.5, 2.9, 263.0, 1939.0
        ]
    }
    
    test_df = pd.DataFrame(test_data)
    
    print(f"\n📊 Données test (scores empiriques):")
    print(test_df[['event_key', 'empirical_score', 'estimate']].to_string(index=False))
    
    result = deduplicate_events(test_df)
    
    print("\n" + "="*80)
    print("TEST VALIDATION")
    print("="*80)
    
    print(f"\n📊 Événements finaux avec scores:")
    for _, row in result.iterrows():
        score = test_df[test_df['event_key'] == row['event_key']]['empirical_score'].values
        score_str = f"{score[0]:.1f}" if len(score) > 0 else "N/A"
        print(f"   {row['event_key']:35s} score={score_str}")
    
    # Vérifier que les dérivés temporels sont gardés
    temporal_kept = result[result['event_key'].str.contains('_mom|_yoy', regex=True, na=False)]
    print(f"\n✅ Dérivés temporels gardés: {len(temporal_kept)}")
    for _, row in temporal_kept.iterrows():
        score = test_df[test_df['event_key'] == row['event_key']]['empirical_score'].values
        score_val = score[0] if len(score) > 0 else 0
        print(f"   {row['event_key']:35s} (score={score_val:.1f})")
    
    # Score moyen final
    final_scores = []
    for _, row in result.iterrows():
        score = test_df[test_df['event_key'] == row['event_key']]['empirical_score'].values
        if len(score) > 0:
            final_scores.append(score[0])
    
    if len(final_scores) > 0:
        print(f"\n📊 Score empirique moyen FINAL: {sum(final_scores)/len(final_scores):.2f}")
        print(f"   (vs {test_df['empirical_score'].mean():.2f} avant déduplication)")
    
    # Vérifier nombre - 9 événements (10 - 1 sans estimate)
    expected_count = 9
    if len(result) == expected_count:
        print(f"\n✅ TEST RÉUSSI: {len(result)} événements")
        print(f"   (real_earnings_mom exclu car pas d'estimate)")
    else:
        print(f"\n⚠️  Nombre différent: {len(result)} événements (attendu: {expected_count})")
