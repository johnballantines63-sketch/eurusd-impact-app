"""
INSTRUCTIONS DE MODIFICATION - Remplacement graphique par version avec pullback
Version 8.6.2 - Phase 2

FICHIER : fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py
"""

# ═══════════════════════════════════════════════════════════════
# MODIFICATION À EFFECTUER
# ═══════════════════════════════════════════════════════════════

"""
LOCALISATION :
Chercher le bloc qui commence par :
    if st.button("🎨 Générer Graphique de Prédiction", type="primary", use_container_width=True, key="minute_chart_generate_155755_6050"):

Dans ce bloc, chercher la section qui génère la courbe (autour de ligne 700-800):
    # ✅ Générer la courbe avec la bonne signature de fonction
    price_df = generate_candlestick_curve_multi_events(
        ...
    )

REMPLACER CETTE SECTION PAR :
"""

# ═══════════════════════════════════════════════════════════════
# ANCIEN CODE (À REMPLACER)
# ═══════════════════════════════════════════════════════════════

"""
                                        # ✅ Générer la courbe avec la bonne signature de fonction
                                        # La fonction attend une liste de predictions, pas total_impact_pips
                                        price_df = generate_candlestick_curve_multi_events(
                                            start_price=start_price_input,
                                            predictions=events_for_generator,
                                            base_time=min(pred["event_time"] for pred in events_for_generator),
                                            duration_minutes=duration_minutes,
                                            volatility_factor=volatility_factor,
                                            spread_pips=spread_pips
                                        )
                                        
                                        if price_df is not None and len(price_df) > 0:
                                            # ✅ Calculer mouvement dominant depuis les données générées (UNIQUE calcul)
                                            max_movement = (price_df['high'].max() - start_price_input) * 10000
                                            min_movement = (price_df['low'].min() - start_price_input) * 10000
                                            observed_movement = max_movement if abs(max_movement) > abs(min_movement) else min_movement

                                            # Calculer Fibonacci si demandé
                                            fib_levels = None
                                            if show_fibonacci:
                                                fib_levels = calculate_fibonacci_price_levels(
                                                    start_price=start_price_input,
                                                    impact_pips=abs(observed_movement),
                                                    direction=1 if observed_movement > 0 else -1
                                                )
                                            
                                            # Créer graphique avec le mouvement observé
                                            fig = create_candlestick_prediction_chart(
                                                price_df=price_df,
                                                total_impact_pips=abs(observed_movement),
                                                direction=1 if observed_movement > 0 else -1,
                                                event_markers=[],
                                                start_price=start_price_input,
                                                fib_levels=fib_levels,
                                                show_spread=show_bid_ask
                                            )
                                            
                                            # Afficher
                                            st.plotly_chart(fig, use_container_width=True, key="minute_prediction_chart_155755_6050")
"""

# ═══════════════════════════════════════════════════════════════
# NOUVEAU CODE (À INSÉRER)
# ═══════════════════════════════════════════════════════════════

"""
                                        # ✅ NOUVEAU v8.6.2 : Générer courbe AVEC PULLBACK VISUEL
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
                                                
                                                st.plotly_chart(fig, use_container_width=True, key="minute_prediction_chart_155755_6050")
"""

# ═══════════════════════════════════════════════════════════════
# RÉSUMÉ DES CHANGEMENTS
# ═══════════════════════════════════════════════════════════════

"""
CHANGEMENTS APPLIQUÉS :

1. ✅ Vérification si 'phases' existe et contient des données

2. 🆕 SI PHASES DISPONIBLES :
   - Utiliser generate_candlestick_curve_from_phases()
   - Utiliser create_sequential_phases_chart()
   - Afficher stats pullback
   
3. ⚠️ SINON (FALLBACK) :
   - Utiliser ancien système (generate_candlestick_curve_multi_events)
   - Compat ascendante garantie

RÉSULTAT ATTENDU :
- Pullback visuellement en ORANGE entre phases rapprochées
- Stats supplémentaires affichées
- Message informatif sur le système utilisé
"""

print("=" * 70)
print("INSTRUCTIONS DE MODIFICATION CHARGÉES")
print("=" * 70)
print()
print("📄 Fichier à modifier :")
print("   fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")
print()
print("🔍 Rechercher le bloc :")
print('   if st.button("🎨 Générer Graphique de Prédiction"')
print()
print("✏️  Remplacer la section de génération de la courbe")
print()
print("📊 Test après modification :")
print("   1. Lancer Streamlit")
print("   2. Aller dans Planificateur")
print("   3. Sélectionner 11 septembre 2025")
print("   4. Activer mode séquentiel")
print("   5. Cliquer '🎨 Générer Graphique de Prédiction'")
print("   6. Vérifier zones orange (pullback)")
print()
