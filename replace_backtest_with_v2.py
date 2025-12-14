#!/usr/bin/env python3
"""
Remplace le code backtest v1 (incorrect) par la v2 (historique famille)
"""

from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("/Users/andrevalentin/Projects/eurusd_news_impact_calculator")
PLANIFICATEUR_PATH = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
BACKUP_DIR = PLANIFICATEUR_PATH.parent / "backups"

# Marqueurs pour identifier la section à remplacer
START_MARKER = "# === SECTION : BACKTEST"
END_MARKER = "# === FIN SECTION BACKTEST ==="

# Nouveau code v2 (depuis artifact)
NEW_BACKTEST_CODE = '''
            st.divider()

            # === SECTION : BACKTEST (basé sur historique des familles) ===
            st.subheader("🎯 Backtest : Validation Historique des Prédictions")

            st.info("""
**💡 Méthode de backtest :**

Pour chaque événement sélectionné (ex: CPI 10 oct 2025), le système :
1. Identifie la famille (ex: "CPI")
2. Récupère TOUS les événements similaires historiques (2022-2024)
3. Calcule les métriques réelles sur ces événements passés
4. Compare avec les prédictions statistiques du modèle

→ Validation sur **3 ans de données réelles**
""")

            with st.spinner("📥 Analyse historique des familles..."):
                try:
                    # Préparer connexion DB
                    conn = duckdb.connect(get_db_path(), read_only=True)
                    
                    backtest_families = []
                    
                    # ═══════════════════════════════════════════════════════════════════
                    # POUR CHAQUE ÉVÉNEMENT SÉLECTIONNÉ
                    # ═══════════════════════════════════════════════════════════════════
                    
                    for pred in predictions:
                        family = pred['event']['family']
                        
                        if family is None:
                            continue
                        
                        st.markdown(f"### 📊 Backtest : {family}")
                        
                        # ─────────────────────────────────────────────────────────────
                        # 1. RÉCUPÉRER ÉVÉNEMENTS HISTORIQUES DE CETTE FAMILLE
                        # ─────────────────────────────────────────────────────────────
                        
                        # Pattern de la famille
                        pattern = FAMILY_PATTERNS.get(family, '')
                        if not pattern:
                            st.warning(f"⚠️ Pattern introuvable pour {family}")
                            continue
                        
                        # Requête événements historiques (3 dernières années)
                        three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
                        now_str = datetime.now().strftime('%Y-%m-%d')
                        
                        query = f"""
                            SELECT DISTINCT
                                e.ts_utc,
                                e.event_key,
                                e.actual,
                                e.previous,
                                e.estimate,
                                e.forecast
                            FROM events e
                            INNER JOIN event_families ef ON e.event_key = ef.event_key
                            WHERE ef.family = '{family}'
                              AND DATE(e.ts_utc) >= '{three_years_ago}'
                              AND DATE(e.ts_utc) <= '{now_str}'
                              AND e.actual IS NOT NULL
                              AND e.ts_utc < NOW()
                            ORDER BY e.ts_utc DESC
                            LIMIT 50
                        """
                        
                        historical_events = conn.execute(query).fetchall()
                        
                        if len(historical_events) == 0:
                            st.warning(f"⚠️ Aucun événement historique trouvé pour {family}")
                            continue
                        
                        st.caption(f"🔍 {len(historical_events)} événements historiques trouvés")
                        
                        # ─────────────────────────────────────────────────────────────
                        # 2. CALCULER MÉTRIQUES RÉELLES POUR CHAQUE ÉVÉNEMENT
                        # ─────────────────────────────────────────────────────────────
                        
                        historical_results = []
                        
                        progress_bar = st.progress(0, text=f"Analyse de {len(historical_events)} événements...")
                        
                        for idx, (ts_utc, event_key, actual, previous, estimate, forecast) in enumerate(historical_events):
                            # Mise à jour progression
                            progress_bar.progress((idx + 1) / len(historical_events), 
                                                 text=f"Analyse {idx+1}/{len(historical_events)}")
                            
                            # Convertir timestamp
                            if isinstance(ts_utc, str):
                                event_time = pd.to_datetime(ts_utc)
                            else:
                                event_time = ts_utc
                            
                            # Normaliser timezone
                            if hasattr(event_time, 'tz') and event_time.tz is not None:
                                event_time = event_time.tz_convert('UTC').tz_localize(None)
                            elif hasattr(event_time, 'tz_localize'):
                                event_time = pd.Timestamp(event_time).tz_localize(None)
                            
                            # Récupérer prix réels (60 min après événement)
                            prices_batch = get_real_prices_batch([event_time], window_minutes=60)
                            
                            if 0 not in prices_batch or prices_batch[0] is None or len(prices_batch[0]) == 0:
                                continue
                            
                            prices_df = prices_batch[0]
                            
                            # Calculer métriques réelles
                            real_metrics = measure_real_impact(prices_df)
                            
                            if real_metrics is None or not real_metrics['had_reaction']:
                                continue
                            
                            # Calculer surprise
                            reference = forecast if pd.notna(forecast) else previous
                            if pd.notna(actual) and pd.notna(reference) and reference != 0:
                                surprise = actual - reference
                            else:
                                continue
                            
                            # Prédiction pour cet événement historique
                            precomputed_stats = st.session_state.get('precomputed_stats', {})
                            hist_pred = predict_impact_fast(family, surprise, precomputed_stats)
                            
                            if hist_pred is None:
                                continue
                            
                            # Comparer
                            pred_impact = hist_pred['predicted_pips'] * hist_pred['direction']
                            real_impact = real_metrics['real_impact_pips']
                            
                            impact_error = abs(pred_impact - real_impact)
                            latency_error = abs(hist_pred['latency_median'] - real_metrics['real_latency_minutes'])
                            ttr_error = abs(hist_pred['ttr_median'] - real_metrics['real_ttr_minutes'])
                            
                            direction_correct = (np.sign(pred_impact) == np.sign(real_impact))
                            
                            historical_results.append({
                                'date': event_time.strftime('%Y-%m-%d'),
                                'event_key': event_key,
                                'surprise': surprise,
                                'pred_impact': pred_impact,
                                'real_impact': real_impact,
                                'impact_error': impact_error,
                                'pred_latency': hist_pred['latency_median'],
                                'real_latency': real_metrics['real_latency_minutes'],
                                'latency_error': latency_error,
                                'pred_ttr': hist_pred['ttr_median'],
                                'real_ttr': real_metrics['real_ttr_minutes'],
                                'ttr_error': ttr_error,
                                'direction_correct': direction_correct
                            })
                        
                        progress_bar.empty()
                        
                        # ─────────────────────────────────────────────────────────────
                        # 3. STATISTIQUES GLOBALES POUR CETTE FAMILLE
                        # ─────────────────────────────────────────────────────────────
                        
                        if len(historical_results) == 0:
                            st.warning(f"⚠️ Aucune donnée valide pour calculer les métriques de {family}")
                            continue
                        
                        st.success(f"✅ {len(historical_results)} événements analysés avec succès")
                        
                        # Calculer métriques agrégées
                        impact_errors = [r['impact_error'] for r in historical_results]
                        latency_errors = [r['latency_error'] for r in historical_results]
                        ttr_errors = [r['ttr_error'] for r in historical_results]
                        
                        mae_impact = np.mean(impact_errors)
                        rmse_impact = np.sqrt(np.mean([e**2 for e in impact_errors]))
                        
                        mae_latency = np.mean(latency_errors)
                        rmse_latency = np.sqrt(np.mean([e**2 for e in latency_errors]))
                        
                        mae_ttr = np.mean(ttr_errors)
                        rmse_ttr = np.sqrt(np.mean([e**2 for e in ttr_errors]))
                        
                        direction_accuracy = sum(1 for r in historical_results if r['direction_correct']) / len(historical_results) * 100
                        
                        # Affichage métriques
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        
                        with col_s1:
                            st.metric("🎯 Direction", f"{direction_accuracy:.0f}%")
                            st.caption(f"{sum(1 for r in historical_results if r['direction_correct'])}/{len(historical_results)} correct")
                        
                        with col_s2:
                            st.metric("📊 MAE Impact", f"{mae_impact:.1f} pips")
                            st.caption(f"RMSE: {rmse_impact:.1f} pips")
                        
                        with col_s3:
                            st.metric("⏱️ MAE Latence", f"{mae_latency:.1f} min")
                            st.caption(f"RMSE: {rmse_latency:.1f} min")
                        
                        with col_s4:
                            st.metric("🔄 MAE TTR", f"{mae_ttr:.1f} min")
                            st.caption(f"RMSE: {rmse_ttr:.1f} min")
                        
                        # ─────────────────────────────────────────────────────────────
                        # 4. TABLEAU DÉTAILLÉ
                        # ─────────────────────────────────────────────────────────────
                        
                        with st.expander("📋 Détails des événements historiques", expanded=False):
                            df_backtest = pd.DataFrame(historical_results)
                            
                            df_display = df_backtest[[
                                'date', 'surprise', 'pred_impact', 'real_impact', 'impact_error',
                                'pred_latency', 'real_latency', 'latency_error',
                                'pred_ttr', 'real_ttr', 'ttr_error', 'direction_correct'
                            ]].copy()
                            
                            df_display.columns = [
                                'Date', 'Surprise', 'Impact Prédit', 'Impact Réel', 'Erreur Impact',
                                'Latence Prédite', 'Latence Réelle', 'Erreur Latence',
                                'TTR Prédit', 'TTR Réel', 'Erreur TTR', 'Direction OK'
                            ]
                            
                            # Formatter
                            df_display['Surprise'] = df_display['Surprise'].apply(lambda x: f"{x:+.2f}")
                            df_display['Impact Prédit'] = df_display['Impact Prédit'].apply(lambda x: f"{x:+.1f}")
                            df_display['Impact Réel'] = df_display['Impact Réel'].apply(lambda x: f"{x:+.1f}")
                            df_display['Erreur Impact'] = df_display['Erreur Impact'].apply(lambda x: f"{x:.1f}")
                            df_display['Direction OK'] = df_display['Direction OK'].apply(lambda x: "✅" if x else "❌")
                            
                            st.dataframe(df_display, use_container_width=True, height=400)
                        
                        # ─────────────────────────────────────────────────────────────
                        # 5. INTERPRÉTATION
                        # ─────────────────────────────────────────────────────────────
                        
                        st.markdown("#### 💡 Interprétation")
                        
                        col_i1, col_i2 = st.columns(2)
                        
                        with col_i1:
                            if mae_impact < 5:
                                st.success(f"🎯 **Impact excellent** : MAE {mae_impact:.1f} pips (< 5)")
                            elif mae_impact < 10:
                                st.info(f"✅ **Impact bon** : MAE {mae_impact:.1f} pips (< 10)")
                            else:
                                st.warning(f"⚠️ **Impact moyen** : MAE {mae_impact:.1f} pips (> 10)")
                            
                            if mae_latency < 3:
                                st.success(f"⚡ **Latence excellente** : MAE {mae_latency:.1f} min (< 3)")
                            elif mae_latency < 5:
                                st.info(f"✅ **Latence bonne** : MAE {mae_latency:.1f} min (< 5)")
                            else:
                                st.warning(f"⚠️ **Latence moyenne** : MAE {mae_latency:.1f} min (> 5)")
                        
                        with col_i2:
                            if mae_ttr < 10:
                                st.success(f"🔄 **TTR excellent** : MAE {mae_ttr:.1f} min (< 10)")
                            elif mae_ttr < 15:
                                st.info(f"✅ **TTR bon** : MAE {mae_ttr:.1f} min (< 15)")
                            else:
                                st.warning(f"⚠️ **TTR moyen** : MAE {mae_ttr:.1f} min (> 15)")
                            
                            if direction_accuracy >= 80:
                                st.success(f"🎯 **Direction excellente** : {direction_accuracy:.0f}% (≥ 80%)")
                            elif direction_accuracy >= 60:
                                st.info(f"✅ **Direction bonne** : {direction_accuracy:.0f}% (≥ 60%)")
                            else:
                                st.error(f"❌ **Direction critique** : {direction_accuracy:.0f}% (< 60%)")
                        
                        # Stocker résultats
                        backtest_families.append({
                            'family': family,
                            'n_events': len(historical_results),
                            'mae_impact': mae_impact,
                            'mae_latency': mae_latency,
                            'mae_ttr': mae_ttr,
                            'direction_accuracy': direction_accuracy
                        })
                        
                        st.divider()
                    
                    conn.close()
                    
                    # ═══════════════════════════════════════════════════════════════════
                    # RÉSUMÉ GLOBAL (si plusieurs familles)
                    # ═══════════════════════════════════════════════════════════════════
                    
                    if len(backtest_families) > 1:
                        st.markdown("### 📊 Résumé Global Multi-Familles")
                        
                        avg_mae_impact = np.mean([f['mae_impact'] for f in backtest_families])
                        avg_mae_latency = np.mean([f['mae_latency'] for f in backtest_families])
                        avg_mae_ttr = np.mean([f['mae_ttr'] for f in backtest_families])
                        avg_direction = np.mean([f['direction_accuracy'] for f in backtest_families])
                        
                        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
                        
                        with col_g1:
                            st.metric("🎯 Direction Moyenne", f"{avg_direction:.0f}%")
                        
                        with col_g2:
                            st.metric("📊 MAE Impact Moyen", f"{avg_mae_impact:.1f} pips")
                        
                        with col_g3:
                            st.metric("⏱️ MAE Latence Moyenne", f"{avg_mae_latency:.1f} min")
                        
                        with col_g4:
                            st.metric("🔄 MAE TTR Moyen", f"{avg_mae_ttr:.1f} min")
                        
                        # Tableau comparatif
                        df_summary = pd.DataFrame(backtest_families)
                        df_summary.columns = ['Famille', 'N Events', 'MAE Impact', 'MAE Latence', 'MAE TTR', 'Direction %']
                        df_summary = df_summary.sort_values('MAE Impact')
                        
                        st.dataframe(df_summary, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors du backtest : {e}")
                    import traceback
                    st.code(traceback.format_exc())

            # === FIN SECTION BACKTEST ===
'''

def main():
    print("🔄 REMPLACEMENT BACKTEST v1 → v2")
    print("=" * 80)
    
    if not PLANIFICATEUR_PATH.exists():
        print(f"❌ Fichier introuvable : {PLANIFICATEUR_PATH}")
        return False
    
    print(f"✅ Fichier trouvé : {PLANIFICATEUR_PATH}")
    
    # Lire contenu
    with open(PLANIFICATEUR_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 Taille actuelle : {len(content)} caractères")
    
    # Trouver section backtest v1
    start_idx = content.find(START_MARKER)
    
    if start_idx == -1:
        print(f"❌ Marqueur de début introuvable : {START_MARKER}")
        print("💡 Le backtest v1 n'a peut-être jamais été inséré")
        return False
    
    end_idx = content.find(END_MARKER, start_idx)
    
    if end_idx == -1:
        print(f"❌ Marqueur de fin introuvable : {END_MARKER}")
        return False
    
    # Inclure le marqueur de fin
    end_idx += len(END_MARKER)
    
    print(f"✅ Section backtest v1 trouvée : lignes {content[:start_idx].count(chr(10))+1} à {content[:end_idx].count(chr(10))+1}")
    print(f"📏 Taille section v1 : {end_idx - start_idx} caractères")
    
    # Backup
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup_before_backtest_v2_{timestamp}.py"
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 Backup créé : {backup_path}")
    
    # Remplacer
    new_content = content[:start_idx] + NEW_BACKTEST_CODE + content[end_idx:]
    
    # Écrire
    with open(PLANIFICATEUR_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Backtest v2 inséré : {len(NEW_BACKTEST_CODE)} caractères")
    print(f"📄 Nouvelle taille : {len(new_content)} caractères")
    print(f"📊 Delta : {len(new_content) - len(content):+} caractères")
    
    print("\n" + "=" * 80)
    print("✅ REMPLACEMENT RÉUSSI")
    print("=" * 80)
    
    print("\n🎯 DIFFÉRENCE CONCEPTUELLE :")
    print("❌ v1 (incorrect) : Cherchait prix à la DATE de l'événement sélectionné")
    print("✅ v2 (correct)   : Backtest sur 3 ans d'HISTORIQUE de la famille")
    
    print("\n📋 PROCHAINES ÉTAPES :")
    print("1. Redémarrer Streamlit")
    print("2. Planificateur → Date : 10 octobre 2025 (ou autre date future)")
    print("3. Sélectionner événements (ex: CPI, Jobless)")
    print("4. Mode séquentiel : ON")
    print("5. Section Backtest analysera automatiquement l'historique ✅")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
