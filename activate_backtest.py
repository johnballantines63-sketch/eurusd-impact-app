#!/usr/bin/env python3
"""
Réactiver la fonctionnalité de backtest dans le Planificateur
Ajoute comparaison prédiction vs réalité pour événements passés
"""

from pathlib import Path
from datetime import datetime

FILE_PATH = Path('fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py')

print("🔧 ACTIVATION BACKTEST DANS PLANIFICATEUR")
print("=" * 60)

# Lire
with open(FILE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
backup_path = FILE_PATH.parent / 'backups' / f"backup_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
backup_path.parent.mkdir(exist_ok=True)
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"💾 Backup: {backup_path}")

# Code à insérer après l'affichage séquentiel (avant "# PrÃ©diction combinÃ©e")
backtest_code = '''
                            # === SECTION BACKTEST : Comparaison Prédiction vs Réalité ===
                            st.divider()
                            st.subheader("🎯 Backtest : Prédiction vs Réalité")
                            
                            # Détecter si événements passés
                            now = pd.Timestamp.now(tz='UTC')
                            
                            def to_utc_aware(ts):
                                ts = pd.to_datetime(ts)
                                if ts.tz is None:
                                    return ts.tz_localize('UTC')
                                else:
                                    return ts.tz_convert('UTC')
                            
                            events_times = [to_utc_aware(p['event']['ts_utc']) for p in predictions]
                            is_past = all(t < now for t in events_times)
                            
                            if is_past:
                                st.info("📊 Événements passés détectés → Comparaison avec données réelles")
                                
                                with st.spinner("🔄 Récupération des prix réels..."):
                                    # Récupérer prix pour chaque événement
                                    backtest_results = []
                                    
                                    event_times_for_batch = [p['event']['ts_utc'] for p in predictions]
                                    prices_batch = get_real_prices_batch(event_times_for_batch, window_minutes=120)
                                    
                                    for idx, pred in enumerate(predictions):
                                        if idx not in prices_batch:
                                            continue
                                        
                                        prices_df = prices_batch[idx]
                                        if prices_df is None or len(prices_df) == 0:
                                            continue
                                        
                                        # Mesurer impact réel
                                        real_metrics = measure_real_impact(prices_df, threshold_pips=5.0)
                                        
                                        if real_metrics and real_metrics['had_reaction']:
                                            backtest_results.append({
                                                'event': pred['event']['family'],
                                                'country': pred['event']['country'],
                                                'time': pred['event']['ts_utc'],
                                                # Prédictions
                                                'pred_impact': pred['predicted_pips'],
                                                'pred_direction': pred['direction'],
                                                'pred_latency': pred['latency_median'],
                                                'pred_ttr': pred['ttr_median'],
                                                # Réalité
                                                'real_impact': abs(real_metrics['real_impact_pips']),
                                                'real_direction': real_metrics['real_direction'],
                                                'real_latency': real_metrics['real_latency_minutes'],
                                                'real_ttr': real_metrics['real_ttr_minutes'],
                                                # Écarts
                                                'error_impact': abs(pred['predicted_pips'] - abs(real_metrics['real_impact_pips'])),
                                                'error_latency': abs(pred['latency_median'] - real_metrics['real_latency_minutes']),
                                                'error_ttr': abs(pred['ttr_median'] - real_metrics['real_ttr_minutes']),
                                                'direction_correct': pred['direction'] == real_metrics['real_direction']
                                            })
                                
                                if backtest_results:
                                    # Métriques globales
                                    st.subheader("📊 Métriques d'Erreur Globales")
                                    
                                    mae_impact = sum(r['error_impact'] for r in backtest_results) / len(backtest_results)
                                    mae_latency = sum(r['error_latency'] for r in backtest_results) / len(backtest_results)
                                    mae_ttr = sum(r['error_ttr'] for r in backtest_results) / len(backtest_results)
                                    accuracy = sum(1 for r in backtest_results if r['direction_correct']) / len(backtest_results) * 100
                                    
                                    col_mae1, col_mae2, col_mae3, col_mae4 = st.columns(4)
                                    
                                    with col_mae1:
                                        st.metric(
                                            "MAE Impact",
                                            f"{mae_impact:.1f} pips",
                                            help="Erreur moyenne absolue sur l'impact"
                                        )
                                    
                                    with col_mae2:
                                        st.metric(
                                            "MAE Latence",
                                            f"{mae_latency:.1f} min",
                                            help="Erreur moyenne absolue sur la latence"
                                        )
                                    
                                    with col_mae3:
                                        color = "normal" if mae_ttr < 20 else "inverse"
                                        st.metric(
                                            "MAE TTR",
                                            f"{mae_ttr:.1f} min",
                                            delta="⚠️ PROBLÈME" if mae_ttr > 60 else "OK",
                                            delta_color=color,
                                            help="Erreur moyenne absolue sur TTR"
                                        )
                                    
                                    with col_mae4:
                                        st.metric(
                                            "Précision Direction",
                                            f"{accuracy:.0f}%",
                                            help="% de directions correctement prédites"
                                        )
                                    
                                    # Alerte si TTR très éloigné
                                    if mae_ttr > 60:
                                        st.error(
                                            f"🚨 **ALERTE CALIBRATION TTR** : Écart moyen de {mae_ttr:.0f} min ! "
                                            f"Les prédictions TTR sont très imprécises."
                                        )
                                        st.warning(
                                            "💡 **Cause possible** : Les patterns Michigan ont peu d'événements historiques "
                                            "ou le calcul TTR = latence × 2 est trop simpliste pour ces événements."
                                        )
                                    
                                    # Tableau comparatif
                                    st.subheader("📋 Comparaison Détaillée")
                                    
                                    df_backtest = pd.DataFrame(backtest_results)
                                    df_display = pd.DataFrame({
                                        'Événement': df_backtest['event'],
                                        'Heure': df_backtest['time'].apply(lambda x: pd.to_datetime(x).strftime('%H:%M')),
                                        'Impact Prédit': df_backtest['pred_impact'].round(1),
                                        'Impact Réel': df_backtest['real_impact'].round(1),
                                        'Écart Impact': df_backtest['error_impact'].round(1),
                                        'Latence Prédit': df_backtest['pred_latency'].round(0),
                                        'Latence Réel': df_backtest['real_latency'].round(0),
                                        'Écart Latence': df_backtest['error_latency'].round(0),
                                        'TTR Prédit': df_backtest['pred_ttr'].round(0),
                                        'TTR Réel': df_backtest['real_ttr'].round(0),
                                        'Écart TTR': df_backtest['error_ttr'].round(0),
                                        'Direction OK': df_backtest['direction_correct'].apply(lambda x: '✅' if x else '❌')
                                    })
                                    
                                    st.dataframe(df_display, use_container_width=True)
                                    
                                    # Graphiques individuels
                                    st.subheader("📈 Graphiques Prix Réels")
                                    
                                    for idx, pred in enumerate(predictions):
                                        if idx not in prices_batch:
                                            continue
                                        
                                        prices_df = prices_batch[idx]
                                        if prices_df is None:
                                            continue
                                        
                                        real_metrics = measure_real_impact(prices_df, threshold_pips=5.0)
                                        
                                        if real_metrics and real_metrics['had_reaction']:
                                            with st.expander(
                                                f"📊 {pred['event']['family']} - {pd.to_datetime(pred['event']['ts_utc']).strftime('%H:%M')}",
                                                expanded=False
                                            ):
                                                chart = create_backtest_chart(
                                                    prices_df,
                                                    pred['event']['ts_utc'],
                                                    pred['predicted_pips'] * pred['direction'],
                                                    pred['latency_median'],
                                                    pred['ttr_median'],
                                                    real_metrics
                                                )
                                                st.plotly_chart(chart, use_container_width=True)
                                else:
                                    st.warning("⚠️ Impossible de récupérer les prix réels pour ces événements")
                            else:
                                st.info("🔮 Événements futurs → Comparaison impossible (pas encore de données réelles)")
                            
                            st.divider()
                            
'''

# Trouver où insérer (après le bloc séquentiel, avant les sections classiques)
insertion_marker = "# === FIN SECTIONS CLASSIQUES ==="

if insertion_marker in content:
    # Insérer avant ce marker
    content = content.replace(
        insertion_marker,
        backtest_code + "\n                            " + insertion_marker
    )
    print("✅ Code backtest inséré après timeline séquentielle")
else:
    print("⚠️ Marker non trouvé, tentative insertion alternative...")
    # Alternative : chercher après display_sequential_timeline
    alt_marker = "display_sequential_timeline(phases, show_details=True)"
    if alt_marker in content:
        # Trouver la ligne et insérer après
        lines = content.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            if alt_marker in line:
                # Insérer après cette ligne
                new_lines.append(backtest_code)
        content = '\n'.join(new_lines)
        print("✅ Code backtest inséré (méthode alternative)")
    else:
        print("❌ Impossible de trouver le point d'insertion")

# Écrire
with open(FILE_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n📊 Fonctionnalité backtest activée !")
print("\n💡 Redémarrez Streamlit et sélectionnez des événements PASSÉS")
print("   Vous verrez la section '🎯 Backtest : Prédiction vs Réalité'")
print("\n⚠️ Si MAE TTR > 60 min → Alerte calibration affichée")
