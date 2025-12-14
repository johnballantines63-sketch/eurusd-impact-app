# 📋 DATES SÉLECTIONNÉES POUR VALIDATION DOUBLE WAVE
# Session 66 - Sélection manuelle après analyse CSV

# Critères sélection:
# - Surprise réaliste (20-100%)
# - Cluster significatif (≥3)
# - Types prioritaires: CPI, Employment
# - Exclure aberrations (>100%)

SELECTED_DATES = [
    # CPI Dates (Surprise 50-100%)
    {
        'date': '2022-09-13',
        'type': 'CPI',
        'events': 3,
        'surprise': 100.0,
        'event_titles': 'Core Inflation Rate | Inflation Rate | CPI',
        'priority': 'HIGH',  # Surprise la plus élevée réaliste
        'expected_dw': False,  # Cluster=3 < 5
        'notes': 'Cas limite: Surprise élevée mais cluster petit'
    },
    {
        'date': '2025-02-12',
        'type': 'CPI',
        'events': 3,
        'surprise': 66.67,
        'event_titles': 'Core Inflation Rate | CPI s.a | Inflation Rate',
        'priority': 'MEDIUM',
        'expected_dw': False,
        'notes': 'Cas typique CPI mensuel'
    },
    {
        'date': '2025-06-11',
        'type': 'CPI',
        'events': 3,
        'surprise': 66.67,
        'event_titles': 'Core Inflation Rate | CPI s.a | Inflation Rate',
        'priority': 'MEDIUM',
        'expected_dw': False,
        'notes': 'Cas typique CPI mensuel'
    },
    {
        'date': '2024-09-11',
        'type': 'CPI',
        'events': 3,
        'surprise': 50.0,
        'event_titles': 'Core Inflation Rate | CPI s.a | Inflation Rate',
        'priority': 'MEDIUM',
        'expected_dw': False,
        'notes': 'Cas typique CPI mensuel'
    },
    {
        'date': '2025-07-15',
        'type': 'CPI',
        'events': 3,
        'surprise': 33.33,
        'event_titles': 'Core Inflation Rate | CPI s.a | Inflation Rate',
        'priority': 'LOW',
        'expected_dw': False,
        'notes': 'Surprise modérée'
    },
    {
        'date': '2022-10-13',
        'type': 'CPI',
        'events': 3,
        'surprise': 20.0,
        'event_titles': 'Core Inflation Rate | Inflation Rate | CPI',
        'priority': 'LOW',
        'expected_dw': False,
        'notes': 'Surprise minimale acceptable'
    },
    
    # Employment Dates (Surprise réaliste 20-100%)
    {
        'date': '2024-12-06',
        'type': 'Employment',
        'events': 5,
        'surprise': 21.43,
        'event_titles': 'Government Payrolls | Manufacturing Payrolls | Non Farm Payrolls | Nonfarm Payrolls Private | Unemployment Rate',
        'priority': 'HIGH',  # Cluster=5, Surprise réaliste
        'expected_dw': True,  # Remplit critères si surprise>20% validée
        'notes': 'MEILLEUR CANDIDAT Employment: Cluster≥5 + Surprise réaliste'
    },
    {
        'date': '2025-07-03',
        'type': 'Employment',
        'events': 3,
        'surprise': 33.64,
        'event_titles': 'Non Farm Payrolls | Jobless Claims 4-Week Average | U-6 Unemployment Rate',
        'priority': 'MEDIUM',
        'expected_dw': False,
        'notes': 'NFP avec surprise modérée'
    },
    {
        'date': '2022-12-02',
        'type': 'Employment',
        'events': 4,
        'surprise': 31.5,
        'event_titles': 'Unemployment Rate | Non Farm Payrolls | Nonfarm Payrolls Private | Manufacturing Payrolls',
        'priority': 'MEDIUM',
        'expected_dw': False,
        'notes': 'Cluster=4, proche du seuil'
    },
    
    # Mixed High-Quality (Clusters ≥5, Surprise 20-100%)
    # NOTE: Aucune date Mixed ne remplit critères réalistes
    # Toutes ont surprises >100% (aberrations)
    
    # Cas Référence (11 septembre 2025)
    {
        'date': '2025-09-11',
        'type': 'CPI_REFERENCE',
        'events': 9,  # Devrait avoir 9 événements selon Session 64
        'surprise': 33.3,
        'event_titles': 'CPI + Jobless Claims cluster',
        'priority': 'REFERENCE',
        'expected_dw': True,
        'notes': 'CAS RÉFÉRENCE VALIDÉ - Session 64'
    }
]

# Statistiques sélection
TOTAL_SELECTED = 10
CPI_COUNT = 6
EMPLOYMENT_COUNT = 3
REFERENCE = 1

# Dates attendues Double Wave (≥5 events, ≥20% surprise)
EXPECTED_DW_COUNT = 2  # 2024-12-06, 2025-09-11

# Dates Single Wave attendues
EXPECTED_SW_COUNT = 8

print("="*80)
print("DATES SÉLECTIONNÉES POUR VALIDATION SESSION 66")
print("="*80)
print(f"\nTotal dates: {TOTAL_SELECTED}")
print(f"  - CPI: {CPI_COUNT}")
print(f"  - Employment: {EMPLOYMENT_COUNT}")
print(f"  - Référence: {REFERENCE}")
print(f"\nDouble Wave attendu: {EXPECTED_DW_COUNT} dates")
print(f"Single Wave attendu: {EXPECTED_SW_COUNT} dates")
print("\n" + "="*80)
print("LISTE DÉTAILLÉE")
print("="*80)

for i, date_info in enumerate(SELECTED_DATES, 1):
    print(f"\n{i}. {date_info['date']} [{date_info['priority']}]")
    print(f"   Type: {date_info['type']}")
    print(f"   Events: {date_info['events']}")
    print(f"   Surprise: {date_info['surprise']:.2f}%")
    print(f"   Attendu: {'Double Wave' if date_info['expected_dw'] else 'Single Wave'}")
    print(f"   Notes: {date_info['notes']}")
