import sys
sys.path.insert(0, '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/src')

import subprocess
subprocess.run([
    'streamlit', 'run',
    '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py'
])
