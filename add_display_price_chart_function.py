"""
Script pour ajouter la fonction display_price_chart_with_pullback()
à streamlit_sequential_ui.py

VERSION 8.6.6 - Correction du bug d'affichage ×9.3
"""


NEW_FUNCTION = '''

def display_price_chart_with_pullback(
    phases: List[Dict[str, Any]],
    start_price: float,
    base_time: datetime,
    duration_minutes: int = 120
):
    """
    Affiche le graphique de prix avec pullback visible
    
    VERSION 8.6.6 : FONCTION CRITIQUE pour corriger le bug d'affichage ×9.3
    
    Args:
        phases: Liste de phases retournées par sequence_multi_event_timeline_v86()
        start_price: Prix EUR/USD de départ
        base_time: Timestamp de référence
        duration_minutes: Durée totale à simuler
    """
    
    if not PRICE_CURVE_AVAILABLE:
        st.error("⚠️ Module price_curve_generator non disponible - impossible d'afficher le graphique")
        st.info("Vérifiez que le fichier fx_impact_app/src/price_curve_generator.py existe et contient les fonctions requises.")
        return
    
    if not phases:
        st.warning("Aucune phase à afficher")
        return
    
    # Afficher section graphique
    st.subheader("📈 Graphique de Prix avec Pullback")
    
    # Calculer statistiques pullback
    total_pullback = sum(p.get('pullback_pips', 0) for p in phases)
    phases_with_pullback = sum(1 for p in phases if p.get('pullback_pips', 0) > 0)
    
    # Colonnes pour stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🔄 Durée Pullback",
            value=f"{sum(p.get('minutes_since_prev_phase', 0) for p in phases if p.get('pullback_pips', 0) > 0):.0f} min"
        )
    
    with col2:
        st.metric(
            label="📉 Amplitude Pullback",
            value=f"{total_pullback:.1f} pips",
            delta=f"↓ {phases_with_pullback} phase{'s' if phases_with_pullback > 1 else ''}"
        )
    
    with col3:
        total_impact = sum(abs(p.get('impact_combined', 0)) for p in phases)
        st.metric(
            label="📈 Impact Total",
            value=f"+{total_impact:.1f} pips",
            help="Somme des impacts de toutes les phases (pic max)"
        )
    
    # Options graphique
    with st.expander("⚙️ Options du graphique", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            volatility = st.slider(
                "Volatilité simulée",
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Contrôle la volatilité intra-minute des chandeliers"
            )
        with col_b:
            spread_pips = st.number_input(
                "Spread bid/ask (pips)",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.5,
                help="Écart bid/ask à simuler"
            )
    
    try:
        # === DEBUG v8.6.6 : TRACER LES VALEURS AVANT GÉNÉRATION ===
        st.write("🔍 **DEBUG - Phases transmises au générateur :**")
        for phase in phases:
            st.write(f"Phase {phase['phase_num']}: impact_combined = {phase.get('impact_combined', 0):.1f} pips, "
                    f"pullback = {phase.get('pullback_pips', 0):.1f} pips")
        # === FIN DEBUG ===
        
        # Générer la courbe de prix minute par minute
        with st.spinner("Génération de la courbe de prix avec pullback..."):
            price_df = generate_candlestick_curve_from_phases(
                start_price=start_price,
                phases=phases,
                base_time=base_time,
                duration_minutes=duration_minutes,
                volatility_factor=volatility,
                spread_pips=spread_pips
            )
        
        # Créer le graphique avec zones de pullback marquées
        fig = create_sequential_phases_chart(
            price_df=price_df,
            phases=phases,
            start_price=start_price,
            title="📊 Évolution Prédite EUR/USD avec Pullback"
        )
        
        # Afficher le graphique
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiques du graphique
        with st.expander("📊 Statistiques du graphique", expanded=False):
            max_price = price_df['high'].max()
            min_price = price_df['low'].min()
            amplitude_pips = (max_price - min_price) * 10000
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("Prix départ", f"{start_price:.5f}")
            with col_stat2:
                st.metric("Prix max", f"{max_price:.5f}", delta=f"+{(max_price - start_price)*10000:.1f} pips")
            with col_stat3:
                st.metric("Prix min", f"{min_price:.5f}", delta=f"{(min_price - start_price)*10000:.1f} pips")
            with col_stat4:
                st.metric("Amplitude totale", f"{amplitude_pips:.1f} pips")
            
            # Tableau récapitulatif par phase
            st.write("**Détails par phase :**")
            phase_stats = []
            for phase in phases:
                phase_data = price_df[price_df['phase_num'] == phase['phase_num']]
                if len(phase_data) > 0:
                    phase_max = phase_data['high'].max()
                    phase_min = phase_data['low'].min()
                    phase_amplitude = (phase_max - phase_min) * 10000
                    
                    phase_stats.append({
                        'Phase': phase['phase_num'],
                        'Impact prédit (pips)': f"{phase.get('impact_combined', 0):.1f}",
                        'Amplitude observée (pips)': f"{phase_amplitude:.1f}",
                        'Pullback (pips)': f"{phase.get('pullback_pips', 0):.1f}",
                        'Prix max': f"{phase_max:.5f}",
                        'Prix min': f"{phase_min:.5f}"
                    })
            
            if phase_stats:
                st.dataframe(pd.DataFrame(phase_stats), use_container_width=True)
        
        # Téléchargement des données
        with st.expander("💾 Télécharger les données", expanded=False):
            csv = price_df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger courbe de prix (CSV)",
                data=csv,
                file_name=f"eurusd_prediction_pullback_{base_time.strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération du graphique : {str(e)}")
        st.exception(e)
        st.info("💡 Vérifiez que les phases contiennent les champs requis : impact_combined, pullback_pips, start_time, etc.")

'''


def main():
    """Ajoute la fonction au fichier streamlit_sequential_ui.py"""
    
    filepath = "fx_impact_app/streamlit_app/components/streamlit_sequential_ui.py"
    
    print(f"📝 Lecture de {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si la fonction existe déjà
    if 'def display_price_chart_with_pullback' in content:
        print("⚠️  La fonction display_price_chart_with_pullback() existe déjà !")
        response = input("Voulez-vous la remplacer ? (o/n): ")
        if response.lower() != 'o':
            print("❌ Opération annulée")
            return
        
        # Supprimer l'ancienne version
        start_marker = 'def display_price_chart_with_pullback'
        start_idx = content.find(start_marker)
        
        # Trouver la fin de la fonction (prochaine def ou if __name__)
        end_markers = ['\ndef ', '\nif __name__']
        end_idx = len(content)
        for marker in end_markers:
            idx = content.find(marker, start_idx + len(start_marker))
            if idx != -1 and idx < end_idx:
                end_idx = idx
        
        content = content[:start_idx] + content[end_idx:]
        print("✅ Ancienne version supprimée")
    
    # Trouver où insérer (avant if __name__)
    insertion_point = content.find('\nif __name__ == "__main__":')
    
    if insertion_point == -1:
        # Ajouter à la fin
        content += NEW_FUNCTION
    else:
        content = content[:insertion_point] + NEW_FUNCTION + content[insertion_point:]
    
    # Mettre à jour la section __main__ pour inclure la nouvelle fonction
    content = content.replace(
        'print("   5. display_backtest_comparison(phases, phase_errors)")',
        'print("   5. display_backtest_comparison(phases, phase_errors)")\n    print("   6. display_price_chart_with_pullback(phases, start_price, base_time, duration) ✨ NOUVEAU v8.6.6")'
    )
    
    # Écrire le fichier
    print(f"💾 Écriture de {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fonction display_price_chart_with_pullback() ajoutée avec succès !")
    print()
    print("📋 Utilisation dans le Planificateur :")
    print("   from streamlit_sequential_ui import display_price_chart_with_pullback")
    print("   display_price_chart_with_pullback(phases, start_price, base_time, duration)")
    print()
    print("🔍 Prochaines étapes :")
    print("   1. Intégrer l'appel dans le Planificateur Multi-Événements")
    print("   2. Tester sur le 11 septembre 2025")
    print("   3. Vérifier les logs DEBUG pour valider les valeurs")


if __name__ == "__main__":
    main()
