#!/usr/bin/env python3
"""
Enrichit l'affichage du mode séquentiel pour inclure toutes les sections
"""

import os
from datetime import datetime

project_root = "/Users/andrevalentin/Projects/eurusd_news_impact_calculator"
target_file = os.path.join(project_root, "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")

print("=" * 70)
print("🎨 ENRICHISSEMENT AFFICHAGE SÉQUENTIEL v8.3")
print("=" * 70)

# Backup
backup_file = target_file + f".bak_enrich_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Backup créé : {os.path.basename(backup_file)}")

# Trouver le bloc où on affiche la timeline séquentielle
# Après display_sequential_timeline(), on veut ajouter les sections classiques

old_block = """                            # Afficher timeline
                            display_sequential_timeline(phases, show_details=True)
                            
                            # Stocker dans session_state
                            st.session_state['sequential_phases'] = phases
                            st.session_state['use_sequential_mode'] = True
                            st.session_state['original_predictions'] = predictions
                            
                            st.success(f"✅ {len(phases)} phases calculées avec succès")"""

new_block = """                            # Afficher timeline
                            display_sequential_timeline(phases, show_details=True)
                            
                            # Stocker dans session_state
                            st.session_state['sequential_phases'] = phases
                            st.session_state['use_sequential_mode'] = True
                            st.session_state['original_predictions'] = predictions
                            
                            st.success(f"✅ {len(phases)} phases calculées avec succès")
                            
                            # ═══════════════════════════════════════════════════════════
                            # 📊 AJOUTER LES SECTIONS CLASSIQUES EN MODE SÉQUENTIEL
                            # ═══════════════════════════════════════════════════════════
                            
                            st.divider()
                            
                            # Calculer métriques globales pour affichage classique
                            timestamps = [pd.to_datetime(p['event']['ts_utc']) for p in predictions]
                            time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600
                            
                            vectorial_impact = sum(p['predicted_pips'] * p['direction'] for p in predictions)
                            combined_direction = "🔼 HAUSSE" if vectorial_impact > 0 else "🔽 BAISSE"
                            
                            total_impact = sum(p['predicted_pips'] for p in predictions)
                            if total_impact > 0:
                                weighted_latency = sum(p['latency_median'] * p['predicted_pips'] for p in predictions) / total_impact
                            else:
                                weighted_latency = np.mean([p['latency_median'] for p in predictions])
                            
                            min_ttr = min(p['ttr_median'] for p in predictions)
                            overlaps = detect_overlaps(predictions)
                            tradability_score = calculate_tradability_score(predictions, overlaps, time_span)
                            
                            # === SECTION : DÉTAILS CALCUL ===
                            st.subheader("📊 Détails du Calcul Vectoriel")
                            
                            calc_data = []
                            for p in predictions:
                                calc_data.append({
                                    'Événement': f"{p['event']['family']} ({p['event']['country']})",
                                    'Heure': pd.to_datetime(p['event']['ts_utc']).strftime('%H:%M'),
                                    'Surprise': f"{p['surprise']:+.2f}",
                                    'Impact': f"{p['predicted_pips']:.1f}",
                                    'Direction': "🔼 UP" if p['direction'] > 0 else "🔽 DOWN",
                                    'Latence': f"{p['latency_median']:.0f} min",
                                    'TTR': f"{p['ttr_median']:.0f} min",
                                    'Contribution': f"{p['predicted_pips'] * p['direction']:+.1f} pips"
                                })
                            
                            st.table(pd.DataFrame(calc_data))
                            
                            st.divider()
                            
                            # === SECTION : RÉSULTAT FINAL ===
                            st.subheader("🎯 Impact Combiné Final")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric(
                                    "Impact Total",
                                    f"{abs(vectorial_impact):.1f} pips",
                                    delta=combined_direction
                                )
                            
                            with col2:
                                st.metric(
                                    "Latence Attendue",
                                    f"{weighted_latency:.0f} min",
                                    help="Moyenne pondérée par impact"
                                )
                            
                            with col3:
                                st.metric(
                                    "TTR Combiné",
                                    f"{min_ttr:.0f} min",
                                    help="Premier retournement attendu"
                                )
                            
                            with col4:
                                cohesion = "Forte" if len(set([p['direction'] for p in predictions])) == 1 else "Faible"
                                st.metric("Cohésion", cohesion)
                            
                            st.divider()
                            
                            # === SECTION : RETRACEMENT FIBONACCI ===
                            st.subheader("📐 Niveaux de Retracement Fibonacci")
                            
                            fib_levels = calculate_fibonacci_levels(abs(vectorial_impact), np.sign(vectorial_impact))
                            
                            fib_col1, fib_col2 = st.columns(2)
                            
                            with fib_col1:
                                st.markdown("**Zones de Support/Résistance**")
                                for level, pips in fib_levels.items():
                                    if level in ['38.2%', '50%', '61.8%']:
                                        st.info(f"**{level}** : {pips:+.1f} pips")
                                    else:
                                        st.caption(f"{level} : {pips:+.1f} pips")
                            
                            with fib_col2:
                                st.markdown("**Recommandations**")
                                st.write("🎯 **Zone d'entrée idéale** : 23.6% - 38.2%")
                                st.write("⚠️ **Stop loss suggéré** : en dessous de 78.6%")
                                st.write("🎁 **Take profit** : 100% (mouvement complet)")
                                st.write("💰 **TP partiel** : 61.8% (zone de résistance)")
                            
                            st.divider()
                            
                            # === SECTION : FENÊTRE DE TRADING ===
                            st.subheader("⏰ Fenêtre de Trading Suggérée")
                            
                            first_event_time = min(timestamps)
                            
                            entry_time = first_event_time - timedelta(minutes=2)
                            reaction_time = first_event_time + timedelta(minutes=weighted_latency)
                            exit_time = first_event_time + timedelta(minutes=min_ttr)
                            
                            col_t1, col_t2, col_t3 = st.columns(3)
                            
                            with col_t1:
                                st.info(f"**🕐 Entrée suggérée**\\n\\n{entry_time.strftime('%H:%M')}\\n\\n(2 min avant)")
                            
                            with col_t2:
                                st.success(f"**📊 Réaction attendue**\\n\\n{reaction_time.strftime('%H:%M')}\\n\\n(+{weighted_latency:.0f} min)")
                            
                            with col_t3:
                                st.warning(f"**🎯 Sortie suggérée**\\n\\n{exit_time.strftime('%H:%M')}\\n\\n(TTR à {min_ttr:.0f} min)")
                            
                            # === FIN SECTIONS CLASSIQUES ==="""

if old_block in content:
    content = content.replace(old_block, new_block)
    print("✅ Sections classiques ajoutées au mode séquentiel")
else:
    print("⚠️ Bloc d'insertion non trouvé")
    print("Recherche du marqueur st.success avec regex...")
    
    import re
    pattern = r'st\.success\(f"✅ \{len\(phases\)\} phases calculées avec succès"\)'
    match = re.search(pattern, content)
    
    if match:
        # Insérer après ce point
        insertion_point = match.end()
        
        additional_code = """
                            
                            # ═══════════════════════════════════════════════════════════
                            # 📊 AJOUTER LES SECTIONS CLASSIQUES EN MODE SÉQUENTIEL
                            # ═══════════════════════════════════════════════════════════
                            
                            st.divider()
                            
                            # Calculer métriques globales
                            timestamps = [pd.to_datetime(p['event']['ts_utc']) for p in predictions]
                            time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600
                            
                            vectorial_impact = sum(p['predicted_pips'] * p['direction'] for p in predictions)
                            combined_direction = "🔼 HAUSSE" if vectorial_impact > 0 else "🔽 BAISSE"
                            
                            total_impact = sum(p['predicted_pips'] for p in predictions)
                            if total_impact > 0:
                                weighted_latency = sum(p['latency_median'] * p['predicted_pips'] for p in predictions) / total_impact
                            else:
                                weighted_latency = np.mean([p['latency_median'] for p in predictions])
                            
                            min_ttr = min(p['ttr_median'] for p in predictions)
                            
                            # Affichage compact
                            st.subheader("📊 Résumé")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Impact Total", f"{abs(vectorial_impact):.1f} pips", delta=combined_direction)
                            with col2:
                                st.metric("Latence", f"{weighted_latency:.0f} min")
                            with col3:
                                st.metric("TTR Min", f"{min_ttr:.0f} min")"""
        
        content = content[:insertion_point] + additional_code + content[insertion_point:]
        print("✅ Sections ajoutées via regex")
    else:
        print("❌ Impossible de trouver le point d'insertion")

# Sauvegarder
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Fichier sauvegardé")

print("\n" + "=" * 70)
print("✅ ENRICHISSEMENT TERMINÉ")
print("=" * 70)
print("\n📋 PROCHAINES ÉTAPES :")
print("1. Rafraîchir la page Streamlit (F5 ou R)")
print("2. Les sections classiques devraient apparaître sous la timeline")
print("\n💡 Sections ajoutées en mode séquentiel :")
print("   - 📊 Détails du Calcul Vectoriel")
print("   - 🎯 Impact Combiné Final")
print("   - 📐 Niveaux Fibonacci")
print("   - ⏰ Fenêtre de Trading")
