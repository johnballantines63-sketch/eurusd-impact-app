with open('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/audit_scores_mapping.txt', 'r') as f:
    lines = f.readlines()
    
print("=== RECHERCHE 'unemployment' ===")
for i, line in enumerate(lines):
    if 'unemployment' in line.lower() and 'event_key' in line.lower():
        print(f"Ligne {i}: {line.strip()}")
        # Print context (2 lines after)
        for j in range(1, min(4, len(lines)-i)):
            print(f"       {lines[i+j].strip()}")
        print()

print("\n=== RECHERCHE 'gdp' ===")        
for i, line in enumerate(lines):
    if 'gdp' in line.lower() and 'event_key' in line.lower():
        print(f"Ligne {i}: {line.strip()}")
        # Print context (2 lines after)
        for j in range(1, min(4, len(lines)-i)):
            print(f"       {lines[i+j].strip()}")
        print()
