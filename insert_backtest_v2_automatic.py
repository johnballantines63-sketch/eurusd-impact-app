#!/usr/bin/env python3
"""
Script d'insertion automatique du Backtest v2 dans 4_Planificateur-Multi-Evenements.py
Version sécurisée avec backup, détection d'indentation et validation
"""

import re
import shutil
from pathlib import Path
from datetime import datetime
import ast

# Chemins
PROJECT_ROOT = Path(__file__).parent
TARGET_FILE = PROJECT_ROOT / "fx_impact_app" / "streamlit_app" / "pages" / "4_Planificateur-Multi-Evenements.py"
BACKUP_DIR = TARGET_FILE.parent / "backups"

# Code du backtest v2 (sans indentation - sera ajoutée dynamiquement)
BACKTEST_V2_CODE = '''st.divider()
st.subheader("🎯 Backtest : Validation Historique des Prédictions")

st.info("""
**💡 Comment fonctionne ce backtest ?**

Au lieu de vérifier si la prédiction d'UN événement futur sera correcte (impossible !), 
ce backtest valide la **fiabilité du modèle de prédiction** en testant sur des dizaines 
d'événements historiques de la même famille.

**Exemple :** Vous sélectionnez le CPI du 10 octobre 2025 (futur)
→ Le backtest analyse les **36 derniers CPI** (2022-2024) pour calculer :
- MAE Impact : précision du modèle en pips
- MAE Latence : précision du temps de réaction
- MAE TTR : précision du Time To Reversal
- Direction : % de prédictions de direction correctes

**Résultat :** Vous savez si vous pouvez faire confiance au modèle pour cet événement !
""")

# Vérifier qu'il y a des prédictions
if len(predictions) == 0:
    st.warning("⚠️ Aucune prédiction disponible pour le backtest")
else:
    # Identifier toutes les familles uniques des événements sélectionnés
    families_to_test = list(set([p['event']['family'] for p in predictions]))
    
    st.info(f"📊 **{len(families_to_test)} famille(s) à tester** : {', '.join(families_to_test)}")
    
    # Bouton pour lancer le backtest
    if st.button("🚀 Lancer le Backtest", type="primary", use_container_width=True):
        
        all_family_results = {}
        
        with st.spinner("🔍 Analyse des événements historiques..."):
            
            conn = duckdb.connect(get_db_path(), read_only=True)
            
            for family in families_to_test:
                
                st.markdown(f"### 📈 Famille : **{family}**")
                
                # ════════════════════════════════════════════════════
                # ÉTAPE 1 : Récupérer tous les événements historiques
                # ════════════════════════════════════════════════════
                
                with st.expander(f"🔍 Recherche événements historiques {family}", expanded=False):
                    
                    # Requête pour trouver tous les événements de cette famille
                    # dans les 3 dernières années avec actual != NULL
                    query = f"""
                    SELECT DISTINCT
                        e.ts_utc,
                        e.event_key,
                        e.country,
                        e.actual,
                        e.previous,
                        e.estimate,
                        ef.family
                    FROM events e
                    INNER JOIN event_families ef ON e.event_key = ef.event_key
                    WHERE ef.family = '{family}'
                      AND e.ts_utc >= NOW() - INTERVAL '3 years'
                      AND e.ts_utc < NOW()
                      AND e.actual IS NOT NULL
                      AND e.estimate IS NOT NULL
                      AND e.estimate != 0
                    ORDER BY e.ts_utc DESC
                    LIMIT 50
                    """
                    
                    try:
                        historical_events = conn.execute(query).fetchdf()
                        
                        if len(historical_events) == 0:
                            st.warning(f"⚠️ Aucun événement historique trouvé pour {family}")
                            continue
                        
                        st.success(f"✅ {len(historical_events)} événements trouvés")
                        
                        # Afficher aperçu
                        st.dataframe(
                            historical_events.head(5)[['ts_utc', 'event_key', 'actual', 'estimate']],
                            use_container_width=True
                        )
                    
                    except Exception as e:
                        st.error(f"❌ Erreur requête : {e}")
                        continue
                
                # ════════════════════════════════════════════════════
                # ÉTAPE 2 : Analyser chaque événement historique
                # ════════════════════════════════════════════════════
                
                st.markdown("#### 🔄 Analyse en cours...")
                
                progress_bar = st.progress(0)
                results = []
                
                for idx, event in historical_events.iterrows():
                    
                    # Calculer surprise
                    surprise = event['actual'] - event['estimate']
                    
                    # Prédiction du modèle
                    precomputed_stats = st.session_state.get('precomputed_stats', {})
                    pred = predict_impact_fast(family, surprise, precomputed_stats)
                    
                    if pred is None:
                        continue
                    
                    # Récupérer prix réels
                    event_time = pd.to_datetime(event['ts_utc'])
                    prices_batch = get_real_prices_batch([event_time], window_minutes=60)
                    
                    if 0 not in prices_batch or prices_batch[0] is None:
                        continue
                    
                    prices_df = prices_batch[0]
                    
                    # Mesurer impact réel
                    real_metrics = measure_real_impact(prices_df)
                    
                    if real_metrics is None or not real_metrics['had_reaction']:
                        continue
                    
                    # Comparer prédiction vs réalité
                    pred_impact = pred['predicted_pips'] * pred['direction']
                    real_impact = real_metrics['real_impact_pips']
                    
                    pred_direction = np.sign(pred_impact)
                    real_direction = np.sign(real_impact)
                    
                    results.append({
                        'date': event_time,
                        'pred_impact': pred_impact,
                        'real_impact': real_impact,
                        'impact_error': abs(pred_impact - real_impact),
                        'pred_latency': pred['latency_median'],
                        'real_latency': real_metrics['real_latency_minutes'],
                        'latency_error': abs(pred['latency_median'] - real_metrics['real_latency_minutes']),
                        'pred_ttr': pred['ttr_median'],
                        'real_ttr': real_metrics['real_ttr_minutes'],
                        'ttr_error': abs(pred['ttr_median'] - real_metrics['real_ttr_minutes']),
                        'direction_correct': (pred_direction == real_direction)
                    })
                    
                    # Mettre à jour progress
                    progress = (idx + 1) / len(historical_events)
                    progress_bar.progress(progress)
                
                progress_bar.empty()
                
                # ════════════════════════════════════════════════════
                # ÉTAPE 3 : Calculer statistiques globales
                # ════════════════════════════════════════════════════
                
                if len(results) == 0:
                    st.warning(f"⚠️ Aucune métrique calculée pour {family}")
                    continue
                
                st.success(f"✅ {len(results)} événements analysés avec succès")
                
                # Calcul MAE/RMSE
                mae_impact = np.mean([r['impact_error'] for r in results])
                rmse_impact = np.sqrt(np.mean([r['impact_error']**2 for r in results]))
                
                mae_latency = np.mean([r['latency_error'] for r in results])
                rmse_latency = np.sqrt(np.mean([r['latency_error']**2 for r in results]))
                
                mae_ttr = np.mean([r['ttr_error'] for r in results])
                rmse_ttr = np.sqrt(np.mean([r['ttr_error']**2 for r in results]))
                
                direction_accuracy = sum(1 for r in results if r['direction_correct']) / len(results) * 100
                
                # Stocker résultats
                all_family_results[family] = {
                    'n_events': len(results),
                    'mae_impact': mae_impact,
                    'rmse_impact': rmse_impact,
                    'mae_latency': mae_latency,
                    'rmse_latency': rmse_latency,
                    'mae_ttr': mae_ttr,
                    'rmse_ttr': rmse_ttr,
                    'direction_accuracy': direction_accuracy,
                    'results': results
                }
                
                # ════════════════════════════════════════════════════
                # ÉTAPE 4 : Afficher résultats
                # ════════════════════════════════════════════════════
                
                st.markdown("#### 📊 Résultats du Backtest")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Impact
                    if mae_impact < 5:
                        st.success(f"**MAE Impact**\\n\\n{mae_impact:.1f} pips\\n\\n✅ Excellent")
                    elif mae_impact < 10:
                        st.info(f"**MAE Impact**\\n\\n{mae_impact:.1f} pips\\n\\nℹ️ Bon")
                    else:
                        st.warning(f"**MAE Impact**\\n\\n{mae_impact:.1f} pips\\n\\n⚠️ Moyen")
                    
                    st.caption(f"RMSE: {rmse_impact:.1f} pips")
                
                with col2:
                    # Latence
                    if mae_latency < 3:
                        st.success(f"**MAE Latence**\\n\\n{mae_latency:.1f} min\\n\\n✅ Excellent")
                    elif mae_latency < 5:
                        st.info(f"**MAE Latence**\\n\\n{mae_latency:.1f} min\\n\\nℹ️ Bon")
                    else:
                        st.warning(f"**MAE Latence**\\n\\n{mae_latency:.1f} min\\n\\n⚠️ Moyen")
                    
                    st.caption(f"RMSE: {rmse_latency:.1f} min")
                
                with col3:
                    # TTR
                    if mae_ttr < 10:
                        st.success(f"**MAE TTR**\\n\\n{mae_ttr:.1f} min\\n\\n✅ Excellent")
                    elif mae_ttr < 15:
                        st.info(f"**MAE TTR**\\n\\n{mae_ttr:.1f} min\\n\\nℹ️ Bon")
                    else:
                        st.warning(f"**MAE TTR**\\n\\n{mae_ttr:.1f} min\\n\\n⚠️ Moyen")
                    
                    st.caption(f"RMSE: {rmse_ttr:.1f} min")
                
                with col4:
                    # Direction
                    if direction_accuracy >= 80:
                        st.success(f"**Direction**\\n\\n{direction_accuracy:.0f}%\\n\\n✅ Excellent")
                    elif direction_accuracy >= 60:
                        st.info(f"**Direction**\\n\\n{direction_accuracy:.0f}%\\n\\nℹ️ Bon")
                    else:
                        st.error(f"**Direction**\\n\\n{direction_accuracy:.0f}%\\n\\n❌ Critique")
                    
                    st.caption(f"{sum(1 for r in results if r['direction_correct'])}/{len(results)} corrects")
                
                # Tableau détaillé dans expander
                with st.expander(f"📋 Détail des {len(results)} événements testés", expanded=False):
                    df_results = pd.DataFrame(results)
                    df_display = df_results[[
                        'date', 'pred_impact', 'real_impact', 'impact_error',
                        'pred_latency', 'real_latency', 'latency_error',
                        'pred_ttr', 'real_ttr', 'ttr_error', 'direction_correct'
                    ]].copy()
                    
                    df_display.columns = [
                        'Date', 'Impact Prédit', 'Impact Réel', 'Erreur',
                        'Latence Prédite', 'Latence Réelle', 'Erreur',
                        'TTR Prédit', 'TTR Réel', 'Erreur', 'Direction OK'
                    ]
                    
                    # Formatter avec gestion des valeurs manquantes
                    df_display['Impact Prédit'] = df_display['Impact Prédit'].apply(lambda x: f"{x:+.1f}" if pd.notna(x) else "N/A")
                    df_display['Impact Réel'] = df_display['Impact Réel'].apply(lambda x: f"{x:+.1f}" if pd.notna(x) else "N/A")
                    df_display['Erreur'] = df_display['Erreur'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
                    df_display['Direction OK'] = df_display['Direction OK'].apply(lambda x: "✅" if x else "❌")
                    
                    st.dataframe(df_display, use_container_width=True)
                
                st.divider()
            
            conn.close()
        
        # ════════════════════════════════════════════════════════════
        # RÉSUMÉ GLOBAL (si plusieurs familles)
        # ════════════════════════════════════════════════════════════
        
        if len(all_family_results) > 1:
            st.markdown("### 🎯 Résumé Global Multi-Familles")
            
            # Calculer moyennes pondérées
            total_events = sum(r['n_events'] for r in all_family_results.values())
            
            weighted_mae_impact = sum(
                r['mae_impact'] * r['n_events'] for r in all_family_results.values()
            ) / total_events
            
            weighted_mae_latency = sum(
                r['mae_latency'] * r['n_events'] for r in all_family_results.values()
            ) / total_events
            
            weighted_mae_ttr = sum(
                r['mae_ttr'] * r['n_events'] for r in all_family_results.values()
            ) / total_events
            
            weighted_direction = sum(
                r['direction_accuracy'] * r['n_events'] for r in all_family_results.values()
            ) / total_events
            
            col_g1, col_g2, col_g3, col_g4 = st.columns(4)
            
            with col_g1:
                st.metric("MAE Impact Global", f"{weighted_mae_impact:.1f} pips")
            
            with col_g2:
                st.metric("MAE Latence Global", f"{weighted_mae_latency:.1f} min")
            
            with col_g3:
                st.metric("MAE TTR Global", f"{weighted_mae_ttr:.1f} min")
            
            with col_g4:
                st.metric("Direction Globale", f"{weighted_direction:.0f}%")
            
            st.caption(f"Basé sur {total_events} événements historiques au total")
        
        st.success("✅ **Backtest terminé !** Vous pouvez maintenant évaluer la fiabilité du modèle.")
'''


def create_backup(file_path: Path) -> Path:
    """Crée un backup du fichier avec timestamp"""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"backup_before_backtest_v2_{timestamp}.py"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup créé : {backup_path}")
    return backup_path


def detect_indentation(lines: list, start_line: int) -> int:
    """Détecte l'indentation de la ligne de référence"""
    line = lines[start_line]
    indent = len(line) - len(line.lstrip())
    print(f"🔍 Indentation détectée : {indent} espaces")
    return indent


def indent_code(code: str, indent_level: int) -> str:
    """Ajoute l'indentation à chaque ligne du code"""
    indent = " " * indent_level
    lines = code.split('\n')
    indented_lines = [indent + line if line.strip() else line for line in lines]
    return '\n'.join(indented_lines)


def find_backtest_section(lines: list) -> tuple:
    """
    Trouve les indices de début et fin de la section backtest (v1 ou v2)
    
    Returns:
        (start_idx, end_idx) ou (None, None) si non trouvé
    """
    start_idx = None
    end_idx = None
    
    # Marqueurs possibles pour le début du backtest
    backtest_markers = [
        "# === SECTION : BACKTEST ===",
        "st.subheader(\"🎯 Backtest : Prédiction vs Réalité\")",
        "st.subheader(\"🎯 Backtest : Validation Historique des Prédictions\")",
        "st.subheader('🎯 Backtest : Validation Historique des Prédictions')",
        "🎯 Backtest"  # Fallback générique
    ]
    
    # Chercher le marqueur de début
    for i, line in enumerate(lines):
        # Vérifier tous les marqueurs possibles
        if any(marker in line for marker in backtest_markers):
            # Remonter jusqu'au st.divider() précédent
            for j in range(i-1, max(0, i-20), -1):
                if "st.divider()" in lines[j]:
                    start_idx = j
                    print(f"   Marqueur trouvé à la ligne {i+1}: {line.strip()[:60]}...")
                    break
            if start_idx is None:
                start_idx = i
                print(f"   Marqueur trouvé à la ligne {i+1} (sans divider): {line.strip()[:60]}...")
            break
    
    # Chercher le marqueur de fin
    for i, line in enumerate(lines):
        if "# === FIN SECTIONS CLASSIQUES ===" in line:
            end_idx = i - 1  # Ligne juste avant le marqueur
            break
    
    return start_idx, end_idx


def validate_python_syntax(file_path: Path) -> bool:
    """Valide la syntaxe Python du fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print("✅ Syntaxe Python valide")
        return True
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe : {e}")
        return False


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("🚀 INSERTION AUTOMATIQUE BACKTEST V2")
    print("=" * 80)
    
    # 1. Vérifier que le fichier existe
    if not TARGET_FILE.exists():
        print(f"❌ Fichier non trouvé : {TARGET_FILE}")
        return
    
    print(f"\n📄 Fichier cible : {TARGET_FILE}")
    
    # 2. Créer backup
    print("\n📦 Création du backup...")
    backup_path = create_backup(TARGET_FILE)
    
    # 3. Lire le fichier
    print("\n📖 Lecture du fichier...")
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"✅ {len(lines)} lignes lues")
    
    # 4. Trouver la section backtest v1
    print("\n🔍 Recherche de la section backtest v1...")
    start_idx, end_idx = find_backtest_section(lines)
    
    if start_idx is None or end_idx is None:
        print("❌ Section backtest non trouvée")
        print(f"   start_idx = {start_idx}, end_idx = {end_idx}")
        return
    
    print(f"✅ Section trouvée : lignes {start_idx + 1} à {end_idx + 1}")
    print(f"   → {end_idx - start_idx + 1} lignes à remplacer")
    
    # 5. Détecter indentation
    print("\n🔍 Détection de l'indentation...")
    indent_level = detect_indentation(lines, start_idx)
    
    # 6. Préparer le nouveau code avec indentation
    print("\n✏️ Préparation du backtest v2...")
    indented_backtest_v2 = indent_code(BACKTEST_V2_CODE, indent_level)
    
    # 7. Remplacer la section
    print("\n🔄 Remplacement de la section...")
    new_lines = (
        lines[:start_idx] +
        [indented_backtest_v2 + '\n'] +
        lines[end_idx + 1:]
    )
    
    # 8. Sauvegarder
    print("\n💾 Sauvegarde du fichier modifié...")
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ Fichier sauvegardé : {len(new_lines)} lignes")
    
    # 9. Valider syntaxe
    print("\n🔍 Validation de la syntaxe Python...")
    if validate_python_syntax(TARGET_FILE):
        print("\n" + "=" * 80)
        print("✅ SUCCÈS ! Backtest v2 intégré avec succès")
        print("=" * 80)
        print(f"\n📄 Fichier modifié : {TARGET_FILE}")
        print(f"📦 Backup disponible : {backup_path}")
        print("\n🚀 Prochaine étape : Tester avec Streamlit")
        print("   → streamlit run fx_impact_app/streamlit_app/Home.py")
    else:
        print("\n" + "=" * 80)
        print("❌ ERREUR DE SYNTAXE DÉTECTÉE")
        print("=" * 80)
        print("\n🔄 Restauration du backup...")
        shutil.copy2(backup_path, TARGET_FILE)
        print(f"✅ Fichier restauré depuis : {backup_path}")


if __name__ == "__main__":
    main()
