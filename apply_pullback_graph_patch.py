#!/usr/bin/env python3
"""
Script de modification automatique pour intégrer le graphique avec pullback
Version 8.6.2 - Phase 2
"""

import re
from pathlib import Path

def apply_pullback_graph_modification():
    """Applique la modification pour le graphique avec pullback"""
    
    planner_path = Path(__file__).parent / "fx_impact_app" / "streamlit_app" / "pages" / "4_Planificateur-Multi-Evenements.py"
    
    if not planner_path.exists():
        print(f"❌ Fichier non trouvé : {planner_path}")
        return False
    
    print("=" * 70)
    print("MODIFICATION GRAPHIQUE PULLBACK - v8.6.2")
    print("=" * 70)
    print()
    print(f"📄 Fichier : {planner_path}")
    print()
    
    # Lire le fichier
    with open(planner_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si la modification est déjà appliquée
    if 'generate_candlestick_curve_from_phases' in content and 'NOUVEAU v8.6.2 : Générer courbe AVEC PULLBACK VISUEL' in content:
        print("✅ Modification déjà appliquée !")
        return True
    
    print("🔍 Recherche du bloc à modifier...")
    
    # Chercher le pattern à remplacer
    pattern = r'# ✅ Générer la courbe avec la bonne signature de fonction\s*\n\s*# La fonction attend une liste de predictions, pas total_impact_pips\s*\n\s*price_df = generate_candlestick_curve_multi_events\('
    
    if not re.search(pattern, content):
        print("❌ Pattern non trouvé. Le code a peut-être changé.")
        print("   Recherche manuelle nécessaire")
        return False
    
    print("✅ Bloc trouvé !")
    print()
    print("✏️  Application du patch...")
    
    # Remplacement complet du bloc de génération
    old_block = r'''# ✅ Générer la courbe avec la bonne signature de fonction
                                        # La fonction attend une liste de predictions, pas total_impact_pips
                                        price_df = generate_candlestick_curve_multi_events\(
                                            start_price=start_price_input,
                                            predictions=events_for_generator,
                                            base_time=min\(pred\["event_time"\] for pred in events_for_generator\),
                                            duration_minutes=duration_minutes,
                                            volatility_factor=volatility_factor,
                                            spread_pips=spread_pips
                                        \)
                                        
                                        if price_df is not None and len\(price_df\) > 0:
                                            # ✅ Calculer mouvement dominant depuis les données générées \(UNIQUE calcul\)
                                            max_movement = \(price_df\['high'\]\.max\(\) - start_price_input\) \* 10000
                                            min_movement = \(price_df\['low'\]\.min\(\) - start_price_input\) \* 10000
                                            observed_movement = max_movement if abs\(max_movement\) > abs\(min_movement\) else min_movement

                                            # Calculer Fibonacci si demandé
                                            fib_levels = None
                                            if show_fibonacci:
                                                fib_levels = calculate_fibonacci_price_levels\(
                                                    start_price=start_price_input,
                                                    impact_pips=abs\(observed_movement\),
                                                    direction=1 if observed_movement > 0 else -1
                                                \)
                                            
                                            # Créer graphique avec le mouvement observé
                                            fig = create_candlestick_prediction_chart\(
                                                price_df=price_df,
                                                total_impact_pips=abs\(observed_movement\),
                                                direction=1 if observed_movement > 0 else -1,
                                                event_markers=\[\],
                                                start_price=start_price_input,
                                                fib_levels=fib_levels,
                                                show_spread=show_bid_ask
                                            \)
                                            
                                            # Afficher
                                            st\.plotly_chart\(fig, use_container_width=True, key="minute_prediction_chart_155755_6050"\)'''
    
    new_block = '''# ✅ NOUVEAU v8.6.2 : Générer courbe AVEC PULLBACK VISUEL
                                        # Vérifier si phases disponibles pour nouveau générateur
                                        if 'phases' in locals() and phases and len(phases) > 0:
                                            # 🆕 UTILISER LE NOUVEAU GÉNÉRATEUR AVEC PHASES
                                            st.info("✨ Utilisation du nouveau générateur avec pullback visuel")
                                            
                                            price_df = generate_candlestick_curve_from_phases(
                                                start_price=start_price_input,
                                                phases=phases,
                                                base_time=min(pd.to_datetime(p['start_time']) for p in phases),
                                                duration_minutes=duration_minutes,
                                                volatility_factor=volatility_factor,
                                                spread_pips=spread_pips
                                            )
                                            
                                            if price_df is not None and len(price_df) > 0:
                                                # Créer graphique avec zones de pullback colorées
                                                fig = create_sequential_phases_chart(
                                                    price_df=price_df,
                                                    phases=phases,
                                                    start_price=start_price_input,
                                                    title="📊 Évolution Prédite EUR/USD avec Pullback"
                                                )
                                                
                                                # Afficher
                                                st.plotly_chart(fig, use_container_width=True, key="minute_prediction_chart_155755_6050")
                                                
                                                # Stats supplémentaires sur pullback
                                                pullback_rows = price_df[price_df['phase'] == 'pullback']
                                                if len(pullback_rows) > 0:
                                                    st.success(f"🔄 Pullback détecté : {len(pullback_rows)} minutes de descente entre phases")
                                        
                                        else:
                                            # FALLBACK : Ancien système si pas de phases
                                            st.warning("⚠️ Phases non disponibles, utilisation ancien système vectoriel")
                                            
                                            price_df = generate_candlestick_curve_multi_events(
                                                start_price=start_price_input,
                                                predictions=events_for_generator,
                                                base_time=min(pred["event_time"] for pred in events_for_generator),
                                                duration_minutes=duration_minutes,
                                                volatility_factor=volatility_factor,
                                                spread_pips=spread_pips
                                            )
                                            
                                            if price_df is not None and len(price_df) > 0:
                                                # Calculs pour ancien système
                                                max_movement = (price_df['high'].max() - start_price_input) * 10000
                                                min_movement = (price_df['low'].min() - start_price_input) * 10000
                                                observed_movement = max_movement if abs(max_movement) > abs(min_movement) else min_movement

                                                fib_levels = None
                                                if show_fibonacci:
                                                    fib_levels = calculate_fibonacci_price_levels(
                                                        start_price=start_price_input,
                                                        impact_pips=abs(observed_movement),
                                                        direction=1 if observed_movement > 0 else -1
                                                    )
                                                
                                                fig = create_candlestick_prediction_chart(
                                                    price_df=price_df,
                                                    total_impact_pips=abs(observed_movement),
                                                    direction=1 if observed_movement > 0 else -1,
                                                    event_markers=[],
                                                    start_price=start_price_input,
                                                    fib_levels=fib_levels,
                                                    show_spread=show_bid_ask
                                                )
                                                
                                                st.plotly_chart(fig, use_container_width=True, key="minute_prediction_chart_155755_6050")'''
    
    # Appliquer le remplacement
    new_content = re.sub(old_block, new_block, content, flags=re.MULTILINE | re.DOTALL)
    
    if new_content == content:
        print("❌ Remplacement échoué (contenu inchangé)")
        print("   Le pattern exact n'a pas été trouvé")
        return False
    
    # Sauvegarder
    backup_path = planner_path.with_suffix('.py.backup_before_pullback_graph')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Backup créé : {backup_path.name}")
    
    with open(planner_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Modification appliquée avec succès !")
    print()
    print("🧪 Test requis :")
    print("   cd ~/Desktop/eurusd_news_impact_calculator_MPC")
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")
    print()
    print("📅 Date de test : 11 septembre 2025")
    print("   - Activer mode séquentiel")
    print("   - Cliquer 'Générer Graphique'")
    print("   - Vérifier pullback orange entre phases")
    print()
    
    return True

if __name__ == "__main__":
    success = apply_pullback_graph_modification()
    
    if not success:
        print()
        print("⚠️  Modification automatique impossible")
        print("   Appliquer modification manuelle avec MODIFICATION_GRAPHIQUE_PULLBACK.py")
        exit(1)
    else:
        print("✅ Modification réussie - Prêt pour test")
        exit(0)
