#!/usr/bin/env python3
p="/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES.py"
with open(p) as f:lines=f.readlines()
lines[1079]="    if predictions.get('is_double_wave') and predictions.get('double_wave_timeline'):\n"
lines[1082]="    elif predictions.get('is_single_wave_strong') and predictions.get('single_wave_timeline'):\n"
with open(p,'w') as f:f.writelines(lines)
print("✅")
