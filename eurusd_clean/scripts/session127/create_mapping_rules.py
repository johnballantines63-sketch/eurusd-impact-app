"""
SESSION 127 - Création Table Mapping Event Name → Event Key Principal

Objectif : Résoudre 46 scores avec variantes en appliquant règles décision
Règles :
  1. MoM > YoY (réaction immédiate marché)
  2. Final > Advance (sample size plus grand)
  3. Core ≠ Non-Core (événements différents)

Auteur : André Valentin
Date : 11 novembre 2025
"""

import pandas as pd
from pathlib import Path

# Données extraites du rapport audit
VARIANTS_DATA = [
    {
        'event_name': 'ppi',
        'score': 27.26,
        'variants': [
            ('core ppi_mom', 26, 'MED'),
            ('core ppi_yoy', 25, 'MED'),
            ('ppi_yoy', 22, 'MED'),
            ('ppi_mom', 22, 'MED'),
            ('ppi ex food, energy and trade_yoy', 16, 'MED'),
            ('ppi ex food, energy and trade_mom', 16, 'MED'),
        ]
    },
    {
        'event_name': 'redbook',
        'score': 17.65,
        'variants': [
            ('redbook_yoy', 104, 'MED'),
        ]
    },
    {
        'event_name': 'inflation_rate',
        'score': 48.84,
        'variants': [
            ('inflation rate_mom', 25, 'HIGH'),
            ('core inflation rate_mom', 25, 'HIGH'),
            ('core inflation rate_yoy', 24, 'HIGH'),
            ('inflation rate_yoy', 23, 'HIGH'),
        ]
    },
    {
        'event_name': 'pce_price_index',
        'score': 25.38,
        'variants': [
            ('pce price index_mom', 24, 'MED'),
            ('pce price index_yoy', 24, 'MED'),
            ('core pce price index_yoy', 24, 'MED'),
            ('core pce price index_mom', 23, 'MED'),
        ]
    },
    {
        'event_name': 'retail_sales',
        'score': 34.68,
        'variants': [
            ('retail sales ex autos_mom', 23, 'MED'),
            ('retail sales_yoy', 23, 'MED'),
            ('retail sales_mom', 23, 'MED'),
            ('retail sales ex gas/autos_mom', 22, 'MED'),
        ]
    },
    {
        'event_name': 'durable_goods_orders',
        'score': 26.52,
        'variants': [
            ('durable goods orders ex transp_mom', 25, 'LOW'),
            ('durable goods orders ex defense_mom', 25, 'LOW'),
            ('durable goods orders_mom', 24, 'LOW'),
        ]
    },
    {
        'event_name': 'retail_inventories_ex_autos',
        'score': 25.44,
        'variants': [
            ('retail inventories ex autos_mom', 42, 'MED'),
            ('retail inventories ex autos mom adv', 19, 'MED'),
        ]
    },
    {
        'event_name': 'wholesale_inventories',
        'score': 23.78,
        'variants': [
            ('wholesale inventories_mom', 41, 'MED'),
            ('wholesale inventories mom adv', 19, 'MED'),
        ]
    },
    {
        'event_name': 'pce_prices',
        'score': 38.52,
        'variants': [
            ('core pce prices_qoq', 20, 'MED'),
            ('pce prices_qoq', 20, 'MED'),
            ('core pce prices qoq adv', 7, 'MED'),
            ('pce prices qoq adv', 7, 'MED'),
        ]
    },
    {
        'event_name': 'core_ppi',
        'score': 31.63,
        'variants': [
            ('core ppi_mom', 26, 'MED'),
            ('core ppi_yoy', 25, 'MED'),
        ]
    },
    {
        'event_name': 'core_inflation_rate',
        'score': 47.18,
        'variants': [
            ('core inflation rate_mom', 25, 'HIGH'),
            ('core inflation rate_yoy', 24, 'HIGH'),
        ]
    },
    {
        'event_name': 'house_price_index',
        'score': 17.72,
        'variants': [
            ('house price index_mom', 24, 'MED'),
            ('house price index_yoy', 24, 'MED'),
        ]
    },
    {
        'event_name': 'pending_home_sales',
        'score': 21.54,
        'variants': [
            ('pending home sales_mom', 24, 'LOW'),
            ('pending home sales_yoy', 24, 'LOW'),
        ]
    },
    {
        'event_name': 'export_prices',
        'score': 26.56,
        'variants': [
            ('export prices_yoy', 24, 'MED'),
            ('export prices_mom', 24, 'MED'),
        ]
    },
    {
        'event_name': 'manufacturing_production',
        'score': 22.10,
        'variants': [
            ('manufacturing production_yoy', 24, 'MED'),
            ('manufacturing production_mom', 24, 'MED'),
        ]
    },
    {
        'event_name': 'import_prices',
        'score': 25.48,
        'variants': [
            ('import prices_yoy', 24, 'MED'),
            ('import prices_mom', 24, 'MED'),
        ]
    },
    {
        'event_name': 'industrial_production',
        'score': 22.08,
        'variants': [
            ('industrial production_mom', 24, 'LOW'),
            ('industrial production_yoy', 24, 'LOW'),
        ]
    },
    {
        'event_name': 'factory_orders',
        'score': 25.06,
        'variants': [
            ('factory orders ex transportation', 24, 'LOW'),
            ('factory orders_mom', 24, 'LOW'),
        ]
    },
    {
        'event_name': 'average_hourly_earnings',
        'score': 60.63,
        'variants': [
            ('average hourly earnings_mom', 24, 'MED'),
            ('average hourly earnings_yoy', 23, 'MED'),
        ]
    },
    {
        'event_name': 'core_pce_price_index',
        'score': 26.98,
        'variants': [
            ('core pce price index_yoy', 24, 'MED'),
            ('core pce price index_mom', 23, 'MED'),
        ]
    },
    {
        'event_name': 'used_car_prices',
        'score': 20.60,
        'variants': [
            ('used car prices_mom', 22, 'MED'),
            ('used car prices_yoy', 22, 'MED'),
        ]
    },
    {
        'event_name': 'trade_balance',
        'score': 34.47,
        'variants': [
            ('goods trade balance adv', 21, 'MED'),
            ('goods trade balance', 16, 'MED'),
        ]
    },
    {
        'event_name': 'ppi_ex_food,_energy_and_trade',
        'score': 28.98,
        'variants': [
            ('ppi ex food, energy and trade_yoy', 16, 'MED'),
            ('ppi ex food, energy and trade_mom', 16, 'MED'),
        ]
    },
    {
        'event_name': 'real_consumer_spending',
        'score': 40.72,
        'variants': [
            ('real consumer spending_qoq', 21, 'MED'),
            ('real consumer spending qoq adv', 7, 'MED'),
        ]
    },
    {
        'event_name': 'gdp_growth_rate',
        'score': 38.52,
        'variants': [
            ('gdp growth rate_qoq', 21, 'HIGH'),
            ('gdp growth rate qoq adv', 7, 'HIGH'),
        ]
    },
    {
        'event_name': 'core_pce_prices',
        'score': 40.31,
        'variants': [
            ('core pce prices_qoq', 20, 'MED'),
            ('core pce prices qoq adv', 7, 'MED'),
        ]
    },
    {
        'event_name': 'gdp_sales',
        'score': 38.06,
        'variants': [
            ('gdp sales_qoq', 20, 'HIGH'),
            ('gdp sales qoq adv', 7, 'HIGH'),
        ]
    },
    {
        'event_name': 'gdp_price_index',
        'score': 38.06,
        'variants': [
            ('gdp price index_qoq', 20, 'HIGH'),
            ('gdp price index qoq adv', 7, 'HIGH'),
        ]
    },
    {
        'event_name': 'durable_goods_orders_ex_defense',
        'score': 26.96,
        'variants': [
            ('durable goods orders ex defense_mom', 25, 'LOW'),
        ]
    },
    {
        'event_name': 'durable_goods_orders_ex_transp',
        'score': 27.13,
        'variants': [
            ('durable goods orders ex transp_mom', 25, 'LOW'),
        ]
    },
    {
        'event_name': 'business_inventories',
        'score': 22.54,
        'variants': [
            ('business inventories_mom', 25, 'MED'),
        ]
    },
    {
        'event_name': 'existing_home_sales',
        'score': 19.30,
        'variants': [
            ('existing home sales_mom', 24, 'LOW'),
        ]
    },
    {
        'event_name': 'housing_starts',
        'score': 17.00,
        'variants': [
            ('housing starts_mom', 24, 'LOW'),
        ]
    },
    {
        'event_name': 'construction_spending',
        'score': 27.07,
        'variants': [
            ('construction spending_mom', 24, 'MED'),
        ]
    },
    {
        'event_name': 'personal_spending',
        'score': 26.32,
        'variants': [
            ('personal spending_mom', 24, 'MED'),
        ]
    },
    {
        'event_name': 'retail_sales_ex_autos',
        'score': 32.54,
        'variants': [
            ('retail sales ex autos_mom', 23, 'MED'),
        ]
    },
    {
        'event_name': 'leading_index',
        'score': 21.60,
        'variants': [
            ('cb leading index_mom', 22, 'MED'),
            ('leading index_mom', 1, 'MED'),
        ]
    },
    {
        'event_name': 'retail_sales_ex_gas/autos',
        'score': 32.41,
        'variants': [
            ('retail sales ex gas/autos_mom', 22, 'MED'),
        ]
    },
    {
        'event_name': 'cb_leading_index',
        'score': 17.73,
        'variants': [
            ('cb leading index_mom', 22, 'MED'),
        ]
    },
    {
        'event_name': 'unit_labour_costs',
        'score': 22.86,
        'variants': [
            ('unit labour costs_qoq', 16, 'MED'),
        ]
    },
    {
        'event_name': 'nonfarm_productivity',
        'score': 20.66,
        'variants': [
            ('nonfarm productivity_qoq', 16, 'HIGH'),
        ]
    },
    {
        'event_name': 'beige_book',
        'score': 8.79,
        'variants': [
            ('fed beige book', 15, 'MED'),
        ]
    },
    {
        'event_name': 'corporate_profits',
        'score': 31.68,
        'variants': [
            ('corporate profits_qoq', 14, 'MED'),
        ]
    },
    {
        'event_name': 'employment_cost_index',
        'score': 23.80,
        'variants': [
            ('employment cost index_qoq', 8, 'MED'),
        ]
    },
    {
        'event_name': 'producer_price_index',
        'score': 31.45,
        'variants': [
            ('producer price index_yoy', 3, 'MED'),
            ('producer price index_mom', 3, 'MED'),
        ]
    },
    {
        'event_name': 'wholesale_sales',
        'score': 21.84,
        'variants': [
            ('wholesale sales_mom', 1, 'MED'),
        ]
    },
]


def apply_mapping_rules(event_name, variants):
    """
    Applique règles décision pour choisir variante principale
    
    Règles :
    1. MoM > YoY (réaction immédiate)
    2. Final > Advance (sample size)
    3. Core séparé de Non-Core
    4. Plus grand sample size si égalité
    """
    
    # Cas spécial : 1 seule variante
    if len(variants) == 1:
        return variants[0][0], f"Seule variante disponible (n={variants[0][1]})"
    
    # Séparer Core vs Non-Core
    has_core_variants = any('core' in v[0].lower() for v in variants)
    
    if has_core_variants and 'core' not in event_name:
        # Filtrer seulement non-core
        filtered = [v for v in variants if 'core' not in v[0].lower()]
        if filtered:
            variants = filtered
    
    # Règle 1 : Privilégier MoM
    mom_variants = [v for v in variants if '_mom' in v[0]]
    if mom_variants:
        # Prendre MoM avec plus grand sample size
        best = max(mom_variants, key=lambda x: x[1])
        return best[0], f"MoM prioritaire (réaction immédiate, n={best[1]})"
    
    # Règle 2 : Privilégier QoQ final (vs adv)
    qoq_variants = [v for v in variants if '_qoq' in v[0] and 'adv' not in v[0]]
    if qoq_variants:
        best = max(qoq_variants, key=lambda x: x[1])
        return best[0], f"QoQ final prioritaire (sample size, n={best[1]})"
    
    # Règle 3 : YoY si aucun MoM/QoQ
    yoy_variants = [v for v in variants if '_yoy' in v[0]]
    if yoy_variants:
        best = max(yoy_variants, key=lambda x: x[1])
        return best[0], f"YoY retenu (n={best[1]})"
    
    # Fallback : Plus grand sample size
    best = max(variants, key=lambda x: x[1])
    return best[0], f"Plus grand sample size (n={best[1]})"


def create_mapping_table():
    """Crée table complète mapping avec justifications"""
    
    results = []
    
    for item in VARIANTS_DATA:
        event_name = item['event_name']
        score = item['score']
        variants = item['variants']
        
        # Appliquer règles
        principal_key, justification = apply_mapping_rules(event_name, variants)
        
        # Extraire importance
        importance = variants[0][2]  # Toutes variantes même importance
        
        # Compter variantes
        num_variants = len(variants)
        
        # Lister toutes variantes
        all_variants = ' | '.join([f"{v[0]} (n={v[1]})" for v in variants])
        
        results.append({
            'event_name': event_name,
            'empirical_score': score,
            'event_key_principal': principal_key,
            'importance': importance,
            'num_variants': num_variants,
            'justification': justification,
            'all_variants': all_variants
        })
    
    return pd.DataFrame(results)


def main():
    print("=" * 80)
    print("SESSION 127 - CRÉATION TABLE MAPPING VARIANTES")
    print("=" * 80)
    print()
    
    # Créer table mapping
    df = create_mapping_table()
    
    # Trier par importance puis score
    importance_order = {'HIGH': 1, 'MED': 2, 'LOW': 3}
    df['importance_num'] = df['importance'].map(importance_order)
    df = df.sort_values(['importance_num', 'empirical_score'], ascending=[True, False])
    df = df.drop('importance_num', axis=1)
    
    # Sauvegarder
    output_dir = Path(__file__).parent
    output_path = output_dir / 'event_mapping_rules.csv'
    df.to_csv(output_path, index=False)
    
    print(f"✅ Table mapping créée : {output_path}")
    print(f"   Total variantes traitées : {len(df)}")
    print()
    
    # Statistiques
    print("STATISTIQUES PAR IMPORTANCE :")
    print(df.groupby('importance').size())
    print()
    
    # Afficher cas HIGH
    high_df = df[df['importance'] == 'HIGH']
    if not high_df.empty:
        print("=" * 80)
        print("MAPPING HIGH IMPORTANCE (priorité absolue) :")
        print("=" * 80)
        for _, row in high_df.iterrows():
            print(f"\n{row['event_name']} (score={row['empirical_score']:.2f})")
            print(f"  → {row['event_key_principal']}")
            print(f"  → {row['justification']}")
            print(f"  Variantes : {row['num_variants']}")
    
    print()
    print("=" * 80)
    print("✅ PHASE 1.1 COMPLÉTÉE - Mapping rules créé")
    print("=" * 80)


if __name__ == "__main__":
    main()
