#!/bin/bash
# Amélioration des patterns de détection d'événements dans latency_analyzer.py

cd /Users/andrevalentin/Projects/eurusd_news_impact_calculator

# Backup de l'ancien fichier
cp fx_impact_app/src/latency_analyzer.py fx_impact_app/src/latency_analyzer.py.backup

# Remplacer les patterns de familles
python << 'ENDPYTHON'
with open('fx_impact_app/src/latency_analyzer.py', 'r') as f:
    content = f.read()

# Remplacer la liste des familles (lignes ~147-149)
old_families = """        families = ['cpi', 'nfp', 'gdp', 'pmi', 'unemployment', 'retail', 
                   'fomc', 'fed', 'jobless', 'inflation', 'confidence']"""

new_families = """        # Patterns élargis pour mieux détecter les variantes
        family_patterns = {
            'cpi': 'cpi|consumer price',
            'nfp': 'nonfarm|payroll|non farm',
            'gdp': 'gdp|gross domestic',
            'pmi': 'pmi|purchasing manager',
            'unemployment': 'unemployment|jobless rate',
            'retail': 'retail sales',
            'fomc': 'fomc|federal open market',
            'fed': 'fed funds|federal reserve rate',
            'jobless': 'jobless claims|initial claims',
            'inflation': 'inflation rate|cpi',
            'confidence': 'confidence|sentiment'
        }
        families = list(family_patterns.keys())"""

content = content.replace(old_families, new_families)

# Modifier la détection de famille dans predict_latency_for_event (ligne ~147)
old_detection = """        for fam in families:
            if fam in event_key.lower():
                family_pattern = fam
                break"""

new_detection = """        for fam, pattern in family_patterns.items():
            # Chercher dans le pattern élargi
            for keyword in pattern.split('|'):
                if keyword in event_key.lower():
                    family_pattern = pattern
                    break
            if family_pattern:
                break"""

content = content.replace(old_detection, new_detection)

# Modifier get_all_families_latency_summary pour utiliser les patterns
old_summary = """    def get_all_families_latency_summary(self, threshold_pips: float = 5.0) -> List[Dict]:
        \"\"\"Résumé des latences pour toutes les familles d'événements\"\"\"
        families = ['cpi', 'nfp', 'gdp', 'pmi', 'unemployment', 'retail', 
                   'fomc', 'fed', 'jobless', 'inflation', 'confidence']
        
        results = []
        for family in families:
            stats = self.calculate_family_latency_stats(family, threshold_pips, min_events=5)
            if "error" not in stats:
                results.append(stats)"""

new_summary = """    def get_all_families_latency_summary(self, threshold_pips: float = 5.0) -> List[Dict]:
        \"\"\"Résumé des latences pour toutes les familles d'événements\"\"\"
        family_patterns = {
            'cpi': 'cpi|consumer price',
            'nfp': 'nonfarm|payroll|non farm',
            'gdp': 'gdp|gross domestic',
            'pmi': 'pmi|purchasing manager',
            'unemployment': 'unemployment|jobless rate',
            'retail': 'retail sales',
            'fomc': 'fomc|federal open market',
            'fed': 'fed funds|federal reserve rate',
            'jobless': 'jobless claims|initial claims',
            'inflation': 'inflation rate',
            'confidence': 'confidence|sentiment'
        }
        
        results = []
        for family, pattern in family_patterns.items():
            stats = self.calculate_family_latency_stats(pattern, threshold_pips, min_events=5)
            if "error" not in stats:
                stats['family'] = family  # Utiliser le nom court pour affichage
                results.append(stats)"""

content = content.replace(old_summary, new_summary)

with open('fx_impact_app/src/latency_analyzer.py', 'w') as f:
    f.write(content)

print("✅ Patterns améliorés")
ENDPYTHON

echo ""
echo "Test avec NFP..."
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('fx_impact_app/src')))
from latency_analyzer import LatencyAnalyzer

analyzer = LatencyAnalyzer()
with analyzer:
    stats = analyzer.calculate_family_latency_stats('nonfarm|payroll|non farm', threshold_pips=5.0, min_events=5)
    
if 'error' in stats:
    print(f'❌ {stats[\"error\"]}')
else:
    print(f'✅ {stats[\"events_analyzed\"]} événements NFP trouvés')
    if 'initial_reaction' in stats:
        print(f'   Latence moyenne: {stats[\"initial_reaction\"][\"mean_minutes\"]} min')
"

echo ""
echo "Prêt à déployer avec:"
echo "git add fx_impact_app/src/latency_analyzer.py"
echo "git commit -m 'Fix: Improve event family pattern matching for NFP and others'"
echo "git push origin main"
