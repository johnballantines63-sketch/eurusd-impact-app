#!/bin/bash
# TEST CORRECTION NaN - Session 89

echo "================================================================================"
echo "🧪 TEST CORRECTION actual=None / NaN"
echo "================================================================================"
echo ""

cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session89

echo "📋 ÉTAPE 1/2 : Tests unitaires (9 tests)..."
echo "--------------------------------------------------------------------------------"
python surprise_utils.py
echo ""

echo "📋 ÉTAPE 2/2 : Retest date 17.09.2025..."
echo "--------------------------------------------------------------------------------"
python -c "
import sys
sys.path.insert(0, '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session89')

from test_multi_dates import test_date

# Test uniquement 17.09.2025
result = test_date('2025-09-17', '12:30:00', '17 Sept (Std) - RETEST')

if result:
    print(f'\n📊 RÉSULTAT RETEST 17.09.2025:')
    print(f'   Erreur: {result[\"error_pips\"]:.1f} pips')
    print(f'   MAE OK: {\"✅\" if result[\"mae_ok\"] else \"❌\"}')
else:
    print('❌ Test échoué')
"

echo ""
echo "================================================================================"
echo "✅ TEST CORRECTION TERMINÉ"
echo "================================================================================"
