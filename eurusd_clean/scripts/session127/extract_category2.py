with open('/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session126/audit_scores_mapping.txt', 'r') as f:
    content = f.read()

# Trouver section CATÉGORIE 2
start = content.find('CATÉGORIE 2')
end = content.find('CATÉGORIE 3')

if start != -1 and end != -1:
    category2 = content[start:end]
    print(category2[:5000])  # Premiers 5000 caractères
else:
    print("Section CATÉGORIE 2 introuvable")
