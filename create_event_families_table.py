#!/usr/bin/env python3
"""
Crée une table de référence event_families dans la base de données
Cette table permet un mapping propre entre event_key et familles tradables

Exclut automatiquement:
- Auctions (bonds, bills, notes)
- Speeches non-impactants
- Données de stocks pétroliers (EIA)
- Données hebdomadaires peu volatiles
"""

import duckdb
import json
from datetime import datetime

def get_db_path():
    return "fx_impact_app/data/warehouse.duckdb"

def create_event_families_table():
    """Crée et remplit la table event_families"""
    
    conn = duckdb.connect(get_db_path())
    
    print("="*80)
    print("  CRÉATION TABLE EVENT_FAMILIES")
    print("="*80)
    print()
    
    # 1. Créer la table
    print("📊 Création de la structure...")
    
    conn.execute("""
    DROP TABLE IF EXISTS event_families
    """)
    
    conn.execute("""
    CREATE TABLE event_families (
        event_key VARCHAR NOT NULL,
        country VARCHAR NOT NULL,
        family VARCHAR NOT NULL,
        is_tradable BOOLEAN DEFAULT TRUE,
        impact_level VARCHAR,  -- HIGH, MEDIUM, LOW
        notes VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (event_key, country)
    )
    """)
    
    print("✅ Table créée")
    print()
    
    # 2. Définir les événements tradables par famille
    tradable_events = {
        'NFP': {
            'keywords': ['non farm payrolls', 'nonfarm payrolls private', 'government payrolls', 'manufacturing payrolls'],
            'impact': 'HIGH',
            'exclude': ['hmrc payrolls']  # UK moins impactant
        },
        'CPI': {
            'keywords': ['cpi', 'consumer price index'],
            'impact': 'HIGH',
            'exclude': ['baden wuerttemberg', 'bavaria', 'brandenburg', 'hesse', 'saxony', 
                       'north rhine westphalia', 'brc shop price', 'halifax house price',
                       'house price index', 'producer price index', 'wage price index',
                       'tokyo', 'gdp price index', 'pce price index', 'globaldairytrade']
        },
        'Inflation': {
            'keywords': ['inflation rate', 'core inflation rate', 'harmonised inflation rate'],
            'impact': 'HIGH',
            'exclude': ['inflation expectations', 'michigan inflation']
        },
        'GDP': {
            'keywords': ['gdp growth rate', 'gross domestic product'],
            'impact': 'HIGH',
            'exclude': ['atlanta fed gdpnow', 'gdp capital expenditure', 'gdp consumption',
                       'gdp deflator', 'gdp sales', 'gdp external demand', 'gdp private consumption',
                       'niesr monthly gdp', 'gdp price index', 'full year gdp']
        },
        'PMI': {
            'keywords': ['manufacturing pmi', 'services pmi', 'composite pmi'],
            'impact': 'HIGH',
            'exclude': ['construction pmi', 'ai group', 'chicago pmi']
        },
        'Retail_Sales': {
            'keywords': ['retail sales'],
            'impact': 'HIGH',
            'exclude': ['brc retail sales monitor']
        },
        'Unemployment': {
            'keywords': ['unemployment rate'],
            'impact': 'HIGH',
            'exclude': ['unemployment change', 'unemployment benefit', 'u 6 unemployment']
        },
        'Interest_Rate': {
            'keywords': ['interest rate decision'],
            'impact': 'HIGH',
            'exclude': ['interest rate projection']
        },
        'Jobless_Claims': {
            'keywords': ['initial jobless claims', 'continuing jobless claims'],
            'impact': 'MEDIUM',
            'exclude': ['jobless claims 4 week']
        },
        'Industrial_Production': {
            'keywords': ['industrial production'],
            'impact': 'MEDIUM',
            'exclude': ['industrial production mom']
        },
        'Trade_Balance': {
            'keywords': ['trade balance'],
            'impact': 'MEDIUM',
            'exclude': ['goods trade balance']
        },
        'Consumer_Confidence': {
            'keywords': ['consumer confidence', 'michigan consumer sentiment', 'cb consumer confidence'],
            'impact': 'MEDIUM',
            'exclude': ['business confidence', 'anz', 'nab', 'nzier', 'westpac']
        },
        'Wages': {
            'keywords': ['average hourly earnings', 'average earnings'],
            'impact': 'MEDIUM',
            'exclude': ['employment cost wages', 'employment wages', 'real earnings', 'average cash earnings']
        },
        'FOMC_Minutes': {
            'keywords': ['fomc minutes'],
            'impact': 'HIGH',
            'exclude': []
        },
        'Fed_Speech': {
            'keywords': ['fed chair', 'fed president', 'fed vice chair'],
            'impact': 'MEDIUM',
            'exclude': []
        },
        'ECB_Decision': {
            'keywords': ['ecb interest rate decision', 'ecb press conference'],
            'impact': 'HIGH',
            'exclude': ['ecb general council', 'ecb non monetary']
        },
        'Building_Permits': {
            'keywords': ['building permits', 'housing starts'],
            'impact': 'MEDIUM',
            'exclude': []
        },
        'Durable_Goods': {
            'keywords': ['durable goods orders'],
            'impact': 'MEDIUM',
            'exclude': ['durable goods orders ex']
        },
        'Factory_Orders': {
            'keywords': ['factory orders'],
            'impact': 'LOW',
            'exclude': ['factory orders ex']
        }
    }
    
    # 3. Récupérer tous les event_key de la base
    print("📥 Récupération des événements...")
    
    all_events = conn.execute("""
        SELECT DISTINCT event_key, country
        FROM events
        WHERE actual IS NOT NULL
    """).fetchall()
    
    print(f"   {len(all_events)} événements uniques avec actual")
    print()
    
    # 4. Classifier et insérer
    print("🔍 Classification des événements...")
    
    classified = 0
    tradable = 0
    non_tradable = 0
    
    for event_key, country in all_events:
        event_lower = event_key.lower()
        
        # Exclure automatiquement les non-tradables
        non_tradable_keywords = [
            'auction', 'bill auction', 'bond auction', 'note auction',
            'btp auction', 'bund auction', 'gilt auction', 'oat auction',
            'btf auction', 'letras auction', 'jgb auction', 'tips auction',
            'speech', 'remarks', 'testimony', 'statement', 'minutes',
            'meeting minutes', 'outlook report', 'bulletin', 'report',
            'eia', 'api crude', 'baker hughes', 'redbook',
            'stock investment by foreigners', 'foreign bond investment',
            'mba', 'mortgage'
        ]
        
        is_excluded = False
        for keyword in non_tradable_keywords:
            if keyword in event_lower:
                # Exceptions: garder FOMC minutes et certains statements
                if 'fomc minutes' in event_lower:
                    continue
                if 'press conference' in event_lower:
                    continue
                    
                is_excluded = True
                non_tradable += 1
                break
        
        if is_excluded:
            continue
        
        # Classifier dans une famille
        family_found = None
        impact = None
        
        for family, config in tradable_events.items():
            # Vérifier les exclusions spécifiques
            if any(excl in event_lower for excl in config['exclude']):
                continue
            
            # Vérifier les keywords
            if any(kw in event_lower for kw in config['keywords']):
                family_found = family
                impact = config['impact']
                break
        
        if family_found:
            conn.execute("""
                INSERT INTO event_families (event_key, family, country, is_tradable, impact_level)
                VALUES (?, ?, ?, TRUE, ?)
            """, [event_key, family_found, country, impact])
            
            classified += 1
            tradable += 1
    
    print(f"✅ Classification terminée:")
    print(f"   Événements classifiés et tradables: {tradable}")
    print(f"   Événements exclus (auctions, etc.): {non_tradable}")
    print()
    
    # 5. Statistiques par famille
    print("="*80)
    print("  STATISTIQUES PAR FAMILLE")
    print("="*80)
    print()
    
    stats = conn.execute("""
        SELECT 
            family,
            impact_level,
            COUNT(*) as event_count,
            COUNT(DISTINCT country) as countries
        FROM event_families
        GROUP BY family, impact_level
        ORDER BY 
            CASE impact_level 
                WHEN 'HIGH' THEN 1 
                WHEN 'MEDIUM' THEN 2 
                WHEN 'LOW' THEN 3 
            END,
            event_count DESC
    """).fetchall()
    
    for family, impact, count, countries in stats:
        print(f"{family:25} [{impact:6}] {count:4} événements | {countries} pays")
    
    # 6. Compter les occurrences totales
    print()
    print("="*80)
    print("  OCCURRENCES TOTALES PAR FAMILLE")
    print("="*80)
    print()
    
    occurrences = conn.execute("""
        SELECT 
            ef.family,
            ef.impact_level,
            COUNT(e.ts_utc) as total_occurrences
        FROM event_families ef
        JOIN events e ON ef.event_key = e.event_key
        WHERE e.actual IS NOT NULL
        GROUP BY ef.family, ef.impact_level
        ORDER BY 
            CASE ef.impact_level 
                WHEN 'HIGH' THEN 1 
                WHEN 'MEDIUM' THEN 2 
                WHEN 'LOW' THEN 3 
            END,
            total_occurrences DESC
    """).fetchall()
    
    total_occ = 0
    for family, impact, occ in occurrences:
        print(f"{family:25} [{impact:6}] {occ:6} occurrences")
        total_occ += occ
    
    print()
    print(f"TOTAL OCCURRENCES TRADABLES: {total_occ}")
    
    # 7. Exemples d'événements par famille
    print()
    print("="*80)
    print("  EXEMPLES D'ÉVÉNEMENTS PAR FAMILLE (top 3)")
    print("="*80)
    print()
    
    for family, _, _, _ in stats[:10]:  # Top 10 familles
        examples = conn.execute("""
            SELECT DISTINCT ef.event_key, ef.country
            FROM event_families ef
            JOIN events e ON ef.event_key = e.event_key
            WHERE ef.family = ?
            GROUP BY ef.event_key, ef.country
            ORDER BY COUNT(e.ts_utc) DESC
            LIMIT 3
        """, [family]).fetchall()
        
        print(f"\n{family}:")
        for event_key, country in examples:
            print(f"  [{country}] {event_key}")
    
    # 8. Créer un index pour les requêtes rapides
    print()
    print("📇 Création des index...")
    conn.execute("CREATE INDEX idx_family ON event_families(family)")
    conn.execute("CREATE INDEX idx_country ON event_families(country)")
    conn.execute("CREATE INDEX idx_tradable ON event_families(is_tradable)")
    print("✅ Index créés")
    
    conn.close()
    
    print()
    print("="*80)
    print("  CRÉATION TERMINÉE")
    print("="*80)
    print()
    print("La table event_families est maintenant disponible dans la base.")
    print("Utilisez-la pour filtrer uniquement les événements tradables.")
    print()
    print("Exemple de requête:")
    print("""
    SELECT e.ts_utc, e.event_key, e.actual, ef.family, ef.impact_level
    FROM events e
    JOIN event_families ef ON e.event_key = ef.event_key
    WHERE ef.is_tradable = TRUE
        AND ef.impact_level IN ('HIGH', 'MEDIUM')
        AND e.actual IS NOT NULL
    ORDER BY e.ts_utc DESC
    LIMIT 100
    """)

if __name__ == "__main__":
    create_event_families_table()
