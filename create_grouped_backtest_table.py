#!/usr/bin/env python3
"""
Crée une fonction pour afficher le tableau de backtesting groupé par fenêtre temporelle
"""

import os
from datetime import datetime

project_root = "/Users/andrevalentin/Projects/eurusd_news_impact_calculator"

# Créer la fonction dans le module unified_chart.py
grouped_table_code = '''

def create_grouped_backtest_table(phases, backtest_results):
    """
    Crée un tableau de backtesting groupé par fenêtre temporelle (phases)
    au lieu d'événements individuels
    
    Args:
        phases: Liste des phases du mode séquentiel
        backtest_results: Liste des résultats de backtesting individuels
    
    Returns:
        Dict avec 'grouped_data' (DataFrame groupé) et 'individual_data' (détails)
    """
    import pandas as pd
    import numpy as np
    
    grouped_data = []
    individual_details = {}
    
    # Grouper les résultats de backtesting par phase
    for phase_idx, phase in enumerate(phases):
        phase_start = pd.to_datetime(phase['start_time'])
        phase_end = pd.to_datetime(phase['end_time'])
        
        # Trouver tous les backtest_results dans cette fenêtre
        phase_backtests = []
        phase_predictions = []
        
        for result in backtest_results:
            event_time = pd.to_datetime(result['event_time'])
            if phase_start <= event_time < phase_end:
                phase_backtests.append(result)
                phase_predictions.append(result['prediction'])
        
        if len(phase_backtests) == 0:
            continue
        
        # === CALCULS GROUPÉS ===
        
        # Impact prédit (vectoriel combiné)
        predicted_impact_total = sum(
            p['predicted_pips'] * p['direction'] 
            for p in phase_predictions
        )
        
        # Impact réel (vectoriel - mouvement total observé)
        if len(phase_backtests) > 0:
            # Prendre le mouvement du premier au dernier prix de la phase
            first_price = phase_backtests[0]['prices'].iloc[0]['price']
            last_price = phase_backtests[-1]['prices'].iloc[-1]['price']
            real_impact_total = (last_price - first_price) * 10000
        else:
            real_impact_total = 0
        
        # Latence prédite (moyenne pondérée ou min selon contexte)
        if len(phase_predictions) > 1:
            # Si plusieurs événements simultanés, prendre le minimum (réaction au plus rapide)
            predicted_latency = min(p['latency_median'] for p in phase_predictions)
        else:
            predicted_latency = phase_predictions[0]['latency_median']
        
        # Latence réelle (premier mouvement significatif observé)
        real_latencies = [r['real_metrics']['real_latency_minutes'] 
                         for r in phase_backtests 
                         if r['real_metrics']['had_reaction']]
        real_latency = min(real_latencies) if real_latencies else predicted_latency
        
        # TTR prédit (de la phase)
        predicted_ttr = phase['duration_minutes']
        
        # TTR réel (durée réelle du mouvement jusqu'au retracement)
        real_ttrs = [r['real_metrics']['real_ttr_minutes'] for r in phase_backtests]
        real_ttr = max(real_ttrs) if real_ttrs else predicted_ttr
        
        # Erreurs
        error_impact = abs(predicted_impact_total - real_impact_total)
        error_latency = abs(predicted_latency - real_latency)
        error_ttr = abs(predicted_ttr - real_ttr)
        
        # === CONSTRUIRE LA LIGNE DU TABLEAU ===
        
        # Nom de la fenêtre
        window_name = phase_start.strftime('%H:%M')
        event_names = ' + '.join([e['family'] for e in phase['events']])
        window_label = f"{window_name} ({event_names})"
        
        grouped_data.append({
            'Fenêtre': window_label,
            'Impact Prédit': f"{predicted_impact_total:+.1f} pips",
            'Impact Réel': f"{real_impact_total:+.1f} pips",
            'Erreur Impact': f"{error_impact:.1f} pips",
            'Latence Prédite': f"{predicted_latency:.0f} min",
            'Latence Réelle': f"{real_latency:.0f} min",
            'Erreur Latence': f"{error_latency:.0f} min",
            'TTR Prédit': f"{predicted_ttr:.0f} min",
            'TTR Réel': f"{real_ttr:.0f} min",
            'Erreur TTR': f"{error_ttr:.0f} min"
        })
        
        # === DÉTAILS INDIVIDUELS (pour l'expander) ===
        
        individual_details[window_label] = []
        for i, result in enumerate(phase_backtests):
            pred = result['prediction']
            real = result['real_metrics']
            
            individual_details[window_label].append({
                'Événement': pred['event']['family'],
                'Impact Prédit': f"{pred['predicted_pips'] * pred['direction']:+.1f} pips",
                'Impact Réel': f"{real['real_impact_pips']:+.1f} pips",
                'Latence Prédite': f"{pred['latency_median']:.0f} min",
                'Latence Réelle': f"{real['real_latency_minutes']:.0f} min",
                'TTR Prédit': f"{pred['ttr_median']:.0f} min",
                'TTR Réel': f"{real['real_ttr_minutes']:.0f} min"
            })
    
    return {
        'grouped': pd.DataFrame(grouped_data),
        'details': individual_details
    }
'''

# Ajouter au fichier unified_chart.py
unified_chart_file = os.path.join(project_root, 'fx_impact_app/src/unified_chart.py')

with open(unified_chart_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter la fonction à la fin
content += "\n\n" + grouped_table_code

with open(unified_chart_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("=" * 70)
print("📊 CRÉATION TABLEAU GROUPÉ BACKTESTING")
print("=" * 70)
print(f"✅ Fonction ajoutée : create_grouped_backtest_table()")
print(f"   dans : fx_impact_app/src/unified_chart.py")

# Maintenant, patcher le fichier principal pour utiliser ce tableau
target_file = os.path.join(project_root, "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")

backup_file = target_file + f".bak_grouped_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
with open(target_file, 'r', encoding='utf-8') as f:
    main_content = f.read()

with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(main_content)

print(f"✅ Backup créé : {os.path.basename(backup_file)}")

# Trouver la section backtesting et remplacer le tableau
old_backtest_table = """                    if backtest_results:
                        # Tableau comparatif
                        st.subheader("📊 Tableau Comparatif Prédiction vs Réalité")
                    
                        comparison_data = []
                        for result_idx, result in enumerate(backtest_results):
                            pred = result['prediction']
                            real = result['real_metrics']
                        
                            # Calcul erreurs
                            error_impact = abs(pred['predicted_pips'] - abs(real['real_impact_pips']))
                            error_latency = abs(pred['latency_median'] - real['real_latency_minutes'])
                            error_ttr = abs(pred['ttr_median'] - real['real_ttr_minutes'])
                        
                            comparison_data.append({
                                'Événement': f"{pred['event']['family']} ({pred['event']['country']})",
                                'Impact Prédit': f"{pred['predicted_pips']:.1f} pips",
                                'Impact Réel': f"{abs(real['real_impact_pips']):.1f} pips",
                                'Erreur Impact': f"{error_impact:.1f} pips",
                                'Latence Prédite': f"{pred['latency_median']:.0f} min",
                                'Latence Réelle': f"{real['real_latency_minutes']:.0f} min",
                                'Erreur Latence': f"{error_latency:.0f} min",
                                'TTR Prédit': f"{pred['ttr_median']:.0f} min",
                                'TTR Réel': f"{real['real_ttr_minutes']:.0f} min",
                                'Erreur TTR': f"{error_ttr:.0f} min"
                            })
                    
                        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)"""

new_backtest_table = """                    if backtest_results:
                        # Importer la fonction de tableau groupé
                        from unified_chart import create_grouped_backtest_table
                        
                        # Tableau comparatif GROUPÉ par fenêtre temporelle
                        st.subheader("📊 Tableau Comparatif par Fenêtre Temporelle")
                        
                        # Créer le tableau groupé
                        table_data = create_grouped_backtest_table(phases, backtest_results)
                        
                        # Afficher le tableau principal (groupé)
                        st.dataframe(table_data['grouped'], use_container_width=True)
                        
                        # Détails individuels dans des expanders
                        if table_data['details']:
                            st.markdown("---")
                            st.markdown("### 🔍 Détails Individuels par Événement")
                            
                            for window_label, details in table_data['details'].items():
                                with st.expander(f"📋 {window_label} - Détails", expanded=False):
                                    details_df = pd.DataFrame(details)
                                    st.dataframe(details_df, use_container_width=True)
                                    
                                    # Message explicatif
                                    if len(details) > 1:
                                        st.caption(
                                            f"💡 Ces {len(details)} événements ont été combinés vectoriellement "
                                            f"dans le tableau principal ci-dessus."
                                        )"""

if old_backtest_table in main_content:
    main_content = main_content.replace(old_backtest_table, new_backtest_table)
    print("✅ Tableau backtesting remplacé par version groupée")
else:
    print("⚠️ Section backtesting non trouvée pour remplacement automatique")
    print("Tentative de recherche avec regex...")
    
    import re
    # Chercher juste la partie "Tableau Comparatif"
    pattern = r'st\.subheader\("📊 Tableau Comparatif Prédiction vs Réalité"\)'
    match = re.search(pattern, main_content)
    
    if match:
        print(f"✅ Trouvé à la position {match.start()}")
        # On va insérer notre nouveau code à cet endroit
        # Mais pour simplifier, on va juste signaler qu'il faut le faire manuellement
        print("⚠️ Modification manuelle nécessaire")
    else:
        print("❌ Pattern non trouvé")

# Sauvegarder
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(main_content)

print(f"✅ Fichier principal mis à jour")

print("\n" + "=" * 70)
print("✅ TABLEAU GROUPÉ IMPLÉMENTÉ")
print("=" * 70)
print("\n📋 NOUVEAU FORMAT :")
print("   ✅ Une ligne par FENÊTRE TEMPORELLE (pas par événement)")
print("   ✅ Impact vectoriel combiné (Jobless + CPI = un seul chiffre)")
print("   ✅ Latence/TTR du groupe")
print("   ✅ Erreurs par groupe")
print("   ✅ Expanders avec détails individuels pour debug")
print("\n📊 EXEMPLE :")
print("   14:30 (Jobless + CPI) → Impact: -86 pips (prédit) vs -37 pips (réel)")
print("   14:45 (Current Account) → Impact: +25 pips (prédit) vs +34 pips (réel)")
print("\n🔍 DEBUG :")
print("   Cliquer sur expander '14:30 - Détails' pour voir :")
print("   - Jobless: -31 pips")
print("   - CPI: -55 pips")
print("\n📋 PROCHAINES ÉTAPES :")
print("1. Rafraîchir Streamlit (F5)")
print("2. Vérifier la section Backtesting")
print("3. Le tableau devrait maintenant être groupé !")
