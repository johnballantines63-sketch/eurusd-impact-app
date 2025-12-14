#!/usr/bin/env python3
"""
Script d'insertion automatique de la section Backtest
dans 4_Planificateur-Multi-Evenements.py
"""

from pathlib import Path
from datetime import datetime

# Chemins
PROJECT_ROOT = Path("/Users/andrevalentin/Projects/eurusd_news_impact_calculator")
PLANIFICATEUR_PATH = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
BACKUP_DIR = PLANIFICATEUR_PATH.parent / "backups"

# Créer dossier backup
BACKUP_DIR.mkdir(exist_ok=True)

# Code backtest à insérer (copié depuis l'artifact)
BACKTEST_CODE = '''
                            st.divider()

                            # === SECTION : BACKTEST (événements passés uniquement) ===
                            st.subheader("🎯 Backtest : Prédiction vs Réalité")

                            # Détection événements passés
                            now = pd.Timestamp.now(tz='UTC')

                            def to_utc_aware(ts):
                                """Convertit timestamp en UTC aware"""
                                ts = pd.to_datetime(ts)
                                if ts.tz is None:
                                    return ts.tz_localize('UTC')
                                else:
                                    return ts.tz_convert('UTC')

                            # Vérifier si tous événements sont passés
                            all_past = all(to_utc_aware(p['event']['ts_utc']) < now for p in predictions)

                            if not all_past:
                                st.info("ℹ️ **Backtest disponible uniquement pour événements passés**")
                                st.caption(f"Date actuelle : {now.strftime('%Y-%m-%d %H:%M UTC')}")
                                
                                # Afficher quels événements sont futurs
                                future_events = [p for p in predictions if to_utc_aware(p['event']['ts_utc']) >= now]
                                if len(future_events) > 0:
                                    st.warning(f"⏳ {len(future_events)} événement(s) encore à venir")
                                    for fe in future_events:
                                        evt_time = to_utc_aware(fe['event']['ts_utc'])
                                        time_until = (evt_time - now).total_seconds() / 60
                                        st.caption(f"• {fe['event']['family']} dans {time_until:.0f} min")

                            else:
                                # Tous événements passés → Backtest possible
                                st.success("✅ **Tous événements passés** → Analyse complète disponible")
                                
                                with st.spinner("📥 Récupération prix réels..."):
                                    try:
                                        # Préparer timestamps pour récupération prix
                                        event_times = [to_utc_aware(p['event']['ts_utc']) for p in predictions]
                                        first_event = min(event_times)
                                        last_event = max(event_times)
                                        
                                        # Récupérer prix (fenêtre étendue pour TTR)
                                        start_fetch = first_event - timedelta(minutes=5)
                                        window_minutes = int((last_event - first_event).total_seconds() / 60) + 90
                                        
                                        prices_batch = get_real_prices_batch([start_fetch], window_minutes=window_minutes)
                                        
                                        if 0 not in prices_batch or prices_batch[0] is None or len(prices_batch[0]) == 0:
                                            st.error("❌ Prix introuvables pour cette période")
                                            st.caption("💡 Vérifiez que les données 1min sont disponibles dans prices_1m")
                                        else:
                                            prices_df = prices_batch[0]
                                            st.success(f"✅ {len(prices_df)} points de prix récupérés")
                                            
                                            # ═══════════════════════════════════════════════════════════
                                            # ANALYSE ÉVÉNEMENT PAR ÉVÉNEMENT
                                            # ═══════════════════════════════════════════════════════════
                                            
                                            st.markdown("### 📊 Analyse Détaillée par Événement")
                                            
                                            backtest_results = []
                                            
                                            for i, pred in enumerate(predictions):
                                                event_time = to_utc_aware(pred['event']['ts_utc'])
                                                
                                                # Filtrer prix pour cet événement (0 à +60 min)
                                                event_prices = prices_df[
                                                    (prices_df['time'] >= event_time.to_pydatetime()) & 
                                                    (prices_df['time'] <= (event_time + timedelta(minutes=60)).to_pydatetime())
                                                ].copy()
                                                
                                                if len(event_prices) == 0:
                                                    st.warning(f"⚠️ Pas de prix pour {pred['event']['family']}")
                                                    continue
                                                
                                                # Calculer métriques réelles
                                                real_metrics = measure_real_impact(event_prices)
                                                
                                                if real_metrics is None:
                                                    st.warning(f"⚠️ Analyse impossible pour {pred['event']['family']}")
                                                    continue
                                                
                                                # Comparer prédiction vs réalité
                                                pred_impact = pred['predicted_pips'] * pred['direction']
                                                real_impact = real_metrics['real_impact_pips']
                                                
                                                impact_error = abs(pred_impact - real_impact)
                                                impact_error_pct = (impact_error / abs(real_impact) * 100) if real_impact != 0 else 0
                                                
                                                latency_error = abs(pred['latency_median'] - real_metrics['real_latency_minutes'])
                                                ttr_error = abs(pred['ttr_median'] - real_metrics['real_ttr_minutes'])
                                                
                                                # Stocker résultats
                                                backtest_results.append({
                                                    'event': pred['event']['family'],
                                                    'pred_impact': pred_impact,
                                                    'real_impact': real_impact,
                                                    'impact_error': impact_error,
                                                    'impact_error_pct': impact_error_pct,
                                                    'pred_latency': pred['latency_median'],
                                                    'real_latency': real_metrics['real_latency_minutes'],
                                                    'latency_error': latency_error,
                                                    'pred_ttr': pred['ttr_median'],
                                                    'real_ttr': real_metrics['real_ttr_minutes'],
                                                    'ttr_error': ttr_error,
                                                    'direction_correct': (np.sign(pred_impact) == np.sign(real_impact))
                                                })
                                                
                                                # Afficher expander pour cet événement
                                                with st.expander(
                                                    f"📊 {pred['event']['family']} - "
                                                    f"{'✅' if np.sign(pred_impact) == np.sign(real_impact) else '❌'} Direction "
                                                    f"{'✅' if impact_error < 5 else '⚠️' if impact_error < 10 else '❌'} Impact",
                                                    expanded=False
                                                ):
                                                    # Métriques comparatives
                                                    col_m1, col_m2, col_m3 = st.columns(3)
                                                    
                                                    with col_m1:
                                                        st.metric(
                                                            "Impact",
                                                            f"{real_impact:+.1f} pips",
                                                            delta=f"{pred_impact:+.1f} prédit (Δ {impact_error:.1f})"
                                                        )
                                                    
                                                    with col_m2:
                                                        st.metric(
                                                            "Latence",
                                                            f"{real_metrics['real_latency_minutes']:.0f} min",
                                                            delta=f"{pred['latency_median']:.0f} prédit (Δ {latency_error:.0f})"
                                                        )
                                                    
                                                    with col_m3:
                                                        st.metric(
                                                            "TTR",
                                                            f"{real_metrics['real_ttr_minutes']:.0f} min",
                                                            delta=f"{pred['ttr_median']:.0f} prédit (Δ {ttr_error:.0f})"
                                                        )
                                                    
                                                    # Graphique comparaison
                                                    fig = create_backtest_chart(
                                                        event_prices,
                                                        event_time,
                                                        pred_impact,
                                                        pred['latency_median'],
                                                        pred['ttr_median'],
                                                        real_metrics
                                                    )
                                                    st.plotly_chart(fig, use_container_width=True)
                                            
                                            # ═══════════════════════════════════════════════════════════
                                            # STATISTIQUES GLOBALES
                                            # ═══════════════════════════════════════════════════════════
                                            
                                            if len(backtest_results) > 0:
                                                st.divider()
                                                st.markdown("### 📈 Statistiques Globales du Backtest")
                                                
                                                # Calculer métriques agrégées
                                                impact_errors = [r['impact_error'] for r in backtest_results]
                                                latency_errors = [r['latency_error'] for r in backtest_results]
                                                ttr_errors = [r['ttr_error'] for r in backtest_results]
                                                
                                                mae_impact = np.mean(impact_errors)
                                                rmse_impact = np.sqrt(np.mean([e**2 for e in impact_errors]))
                                                
                                                mae_latency = np.mean(latency_errors)
                                                rmse_latency = np.sqrt(np.mean([e**2 for e in latency_errors]))
                                                
                                                mae_ttr = np.mean(ttr_errors)
                                                rmse_ttr = np.sqrt(np.mean([e**2 for e in ttr_errors]))
                                                
                                                direction_accuracy = sum(1 for r in backtest_results if r['direction_correct']) / len(backtest_results) * 100
                                                
                                                # Affichage métriques
                                                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                                                
                                                with col_s1:
                                                    st.metric("🎯 Direction", f"{direction_accuracy:.0f}%")
                                                    st.caption(f"{sum(1 for r in backtest_results if r['direction_correct'])}/{len(backtest_results)} correct")
                                                
                                                with col_s2:
                                                    st.metric("📊 MAE Impact", f"{mae_impact:.1f} pips")
                                                    st.caption(f"RMSE: {rmse_impact:.1f} pips")
                                                
                                                with col_s3:
                                                    st.metric("⏱️ MAE Latence", f"{mae_latency:.1f} min")
                                                    st.caption(f"RMSE: {rmse_latency:.1f} min")
                                                
                                                with col_s4:
                                                    st.metric("🔄 MAE TTR", f"{mae_ttr:.1f} min")
                                                    st.caption(f"RMSE: {rmse_ttr:.1f} min")
                                                
                                                # Tableau récapitulatif
                                                st.markdown("#### 📋 Récapitulatif Détaillé")
                                                
                                                df_backtest = pd.DataFrame(backtest_results)
                                                df_display = df_backtest[[
                                                    'event', 'pred_impact', 'real_impact', 'impact_error',
                                                    'pred_latency', 'real_latency', 'latency_error',
                                                    'pred_ttr', 'real_ttr', 'ttr_error', 'direction_correct'
                                                ]].copy()
                                                
                                                df_display.columns = [
                                                    'Événement', 'Impact Prédit', 'Impact Réel', 'Erreur Impact',
                                                    'Latence Prédite', 'Latence Réelle', 'Erreur Latence',
                                                    'TTR Prédit', 'TTR Réel', 'Erreur TTR', 'Direction OK'
                                                ]
                                                
                                                # Formatter
                                                df_display['Impact Prédit'] = df_display['Impact Prédit'].apply(lambda x: f"{x:+.1f}")
                                                df_display['Impact Réel'] = df_display['Impact Réel'].apply(lambda x: f"{x:+.1f}")
                                                df_display['Erreur Impact'] = df_display['Erreur Impact'].apply(lambda x: f"{x:.1f}")
                                                df_display['Direction OK'] = df_display['Direction OK'].apply(lambda x: "✅" if x else "❌")
                                                
                                                st.dataframe(df_display, use_container_width=True)
                                                
                                                # Interprétation
                                                st.markdown("#### 💡 Interprétation")
                                                
                                                if mae_impact < 5:
                                                    st.success("🎯 **Excellent** : Impact prédit très précis (< 5 pips erreur)")
                                                elif mae_impact < 10:
                                                    st.info("✅ **Bon** : Impact prédit précis (< 10 pips erreur)")
                                                else:
                                                    st.warning("⚠️ **Moyen** : Impact prédit à améliorer (> 10 pips erreur)")
                                                
                                                if mae_latency < 3:
                                                    st.success("⚡ **Excellent** : Latence très précise (< 3 min erreur)")
                                                elif mae_latency < 5:
                                                    st.info("✅ **Bon** : Latence précise (< 5 min erreur)")
                                                else:
                                                    st.warning("⚠️ **Moyen** : Latence à améliorer (> 5 min erreur)")
                                                
                                                if mae_ttr < 10:
                                                    st.success("🔄 **Excellent** : TTR très précis (< 10 min erreur)")
                                                elif mae_ttr < 15:
                                                    st.info("✅ **Bon** : TTR précis (< 15 min erreur)")
                                                else:
                                                    st.warning("⚠️ **Moyen** : TTR à améliorer (> 15 min erreur)")
                                                
                                                if direction_accuracy >= 80:
                                                    st.success(f"🎯 **Excellent** : Direction correcte {direction_accuracy:.0f}% du temps")
                                                elif direction_accuracy >= 60:
                                                    st.info(f"✅ **Bon** : Direction correcte {direction_accuracy:.0f}% du temps")
                                                else:
                                                    st.error(f"❌ **Critique** : Direction correcte seulement {direction_accuracy:.0f}% du temps")
                                            
                                            else:
                                                st.warning("⚠️ Aucune métrique calculée")
                                    
                                    except Exception as e:
                                        st.error(f"❌ Erreur lors du backtest : {e}")
                                        st.exception(e)

                            # === FIN SECTION BACKTEST ===
'''

def main():
    print("🔧 Insertion Section Backtest dans Planificateur")
    print("=" * 60)
    
    # Vérifier fichier existe
    if not PLANIFICATEUR_PATH.exists():
        print(f"❌ Fichier introuvable : {PLANIFICATEUR_PATH}")
        return False
    
    print(f"✅ Fichier trouvé : {PLANIFICATEUR_PATH}")
    
    # Lire contenu
    with open(PLANIFICATEUR_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 Fichier lu : {len(content)} caractères")
    
    # Vérifier si backtest déjà présent
    if "# === SECTION : BACKTEST" in content or "st.subheader(\"🎯 Backtest" in content:
        print("⚠️  Section Backtest déjà présente")
        user_input = input("Voulez-vous la remplacer ? (o/n) : ")
        if user_input.lower() != 'o':
            print("❌ Annulé")
            return False
    
    # Trouver point d'insertion : "# === FIN SECTIONS CLASSIQUES ==="
    marker = "# === FIN SECTIONS CLASSIQUES ==="
    
    if marker not in content:
        print(f"❌ Marqueur introuvable : {marker}")
        print("\n💡 Recherche marqueurs alternatifs...")
        
        # Alternative : chercher fin de section "Fenêtre de Trading"
        alt_markers = [
            "with col_t3:",
            "st.warning(f\"**🎯 Sortie suggérée**",
            "# === FIN SECTIONS CLASSIQUES ==="
        ]
        
        insertion_point = -1
        for alt in alt_markers:
            if alt in content:
                # Trouver fin de la section
                idx = content.rfind(alt)
                if idx != -1:
                    # Chercher le prochain "st.divider()" ou fin de bloc
                    next_divider = content.find("st.divider()", idx + len(alt))
                    if next_divider != -1:
                        insertion_point = next_divider
                        print(f"✅ Point d'insertion trouvé après : {alt}")
                        break
        
        if insertion_point == -1:
            print("❌ Impossible de trouver point d'insertion")
            return False
    else:
        insertion_point = content.find(marker)
        print(f"✅ Point d'insertion trouvé : ligne {content[:insertion_point].count(chr(10)) + 1}")
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup_before_backtest_{timestamp}.py"
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 Backup créé : {backup_path}")
    
    # Insérer code
    new_content = content[:insertion_point] + BACKTEST_CODE + "\n" + content[insertion_point:]
    
    # Écrire fichier
    with open(PLANIFICATEUR_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Section Backtest insérée : {len(BACKTEST_CODE)} caractères")
    print(f"📄 Nouveau fichier : {len(new_content)} caractères")
    
    print("\n" + "=" * 60)
    print("✅ INSERTION RÉUSSIE")
    print("=" * 60)
    print("\n📋 Prochaines étapes :")
    print("1. Redémarrer Streamlit : streamlit run fx_impact_app/streamlit_app/Home.py")
    print("2. Tester avec événements passés (10 octobre 2025)")
    print("3. Vérifier section '🎯 Backtest' apparaît")
    print("4. Si besoin rollback : copier backup dans fichier original")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
