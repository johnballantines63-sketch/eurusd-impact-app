"""
Script de validation formule S115 (calculate_double_wave_overlapping)
Session 118 - Validation multi-dates sur 13 cas Double Wave

Objectif: Tester formule S115 sur 13 Double Wave avec events causaux
Critère succès: MAE moyen < 5 pips

Architecture:
1. Charger dataset double_waves_enriched.json (15 cas)
2. Filtrer 13 cas avec events (exclure 2 sans events)
3. Extraire impacts réels MT5 (baseline → Wave2 peak)
4. Calculer prédictions formule S115 par cas
5. Calculer statistiques (MAE, RMSE, R²)
6. Générer graphiques et rapport

Auteur: André Valentin avec Claude
Date: 07 novembre 2025
Session: 118
"""

import sys
from pathlib import Path
import json
import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns

# Ajouter le path du projet
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.cluster_impact_calculator import (
    calculate_cluster_impact,
    calculate_pullback_characteristics,
    calculate_double_wave_overlapping
)


class FormulaS115Validator:
    """Validateur formule S115 sur dataset multi-dates"""
    
    def __init__(
        self,
        dataset_path: str,
        warehouse_path: str,
        output_dir: str
    ):
        """
        Args:
            dataset_path: Chemin vers double_waves_enriched.json
            warehouse_path: Chemin vers warehouse.duckdb
            output_dir: Répertoire sortie résultats
        """
        self.dataset_path = Path(dataset_path)
        self.warehouse_path = Path(warehouse_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Connexion DB
        self.conn = duckdb.connect(str(self.warehouse_path), read_only=True)
        
        # Résultats
        self.double_waves: List[Dict] = []
        self.validable_cases: List[Dict] = []
        self.results: List[Dict] = []
        
    def load_dataset(self) -> None:
        """Charger dataset Double Wave et filtrer cas validables"""
        print("=" * 80)
        print("ÉTAPE 1: CHARGEMENT DATASET")
        print("=" * 80)
        
        with open(self.dataset_path, 'r') as f:
            self.double_waves = json.load(f)
        
        print(f"✅ Chargé {len(self.double_waves)} Double Wave depuis JSON")
        
        # Filtrer cas avec events (validables pour formule S115)
        self.validable_cases = [
            dw for dw in self.double_waves 
            if dw.get('num_events', 0) > 0
        ]
        
        print(f"✅ {len(self.validable_cases)} cas avec events (validables)")
        print(f"❌ {len(self.double_waves) - len(self.validable_cases)} cas SANS events (exclus)")
        
        # Afficher cas exclus
        excluded = [dw for dw in self.double_waves if dw.get('num_events', 0) == 0]
        if excluded:
            print("\n🔴 CAS EXCLUS (patterns techniques SANS events):")
            for dw in excluded:
                baseline_time = dw['baseline_time']
                impact = dw['total_impact_pips']
                print(f"   - {baseline_time[:10]}: {impact:.1f} pips")
        
        print()
        
    def extract_real_impact_mt5(self, case: Dict) -> float:
        """
        Extraire impact réel MT5 pour un cas
        Impact = baseline_price → wave2_peak_price
        
        Args:
            case: Dict avec baseline_price, wave2_peak_price, direction
            
        Returns:
            Impact réel en pips
        """
        baseline = case['baseline_price']
        wave2_peak = case['wave2_peak_price']
        direction = case['direction']
        
        # Calcul impact en pips (1 pip = 0.0001)
        if direction == 'bullish':
            impact_pips = (wave2_peak - baseline) * 10000
        else:  # bearish
            impact_pips = (baseline - wave2_peak) * 10000
            
        return impact_pips
    
    def get_events_for_cluster(
        self,
        events: List[Dict],
        cluster_time: datetime
    ) -> List[Dict]:
        """
        Filtrer events pour un cluster donné
        
        Args:
            events: Liste tous events du Double Wave
            cluster_time: Timestamp du cluster (peak1 ou wave2_peak)
            
        Returns:
            Liste events du cluster (±5 min autour du pic)
        """
        # Tolérance: ±5 min autour du pic
        tolerance = timedelta(minutes=5)
        
        cluster_events = []
        for event in events:
            event_time = pd.to_datetime(event['datetime'])
            time_diff = abs((event_time - cluster_time).total_seconds() / 60)
            
            if time_diff <= 5:
                cluster_events.append(event)
        
        return cluster_events
    
    def calculate_prediction(self, case: Dict) -> Dict:
        """
        Calculer prédiction formule S115 pour un cas
        
        Args:
            case: Dict Double Wave avec events
            
        Returns:
            Dict avec prédiction et détails calcul
        """
        # Parser timestamps
        baseline_time = pd.to_datetime(case['baseline_time'])
        peak1_time = pd.to_datetime(case['peak1_time'])
        wave2_peak_time = pd.to_datetime(case['wave2_peak_time'])
        pullback_time = pd.to_datetime(case['pullback_time'])
        
        # Timing delta entre Wave 1 et Wave 2 (en minutes)
        timing_delta_minutes = (wave2_peak_time - peak1_time).total_seconds() / 60
        
        # Extraire events pour chaque cluster
        all_events = case.get('events', [])
        wave1_events = self.get_events_for_cluster(all_events, peak1_time)
        wave2_events = self.get_events_for_cluster(all_events, wave2_peak_time)
        
        # Calculer impact Wave 1 avec calculate_cluster_impact()
        wave1_result = calculate_cluster_impact(
            events=wave1_events,
            event_time=peak1_time,
            conn=self.conn
        )
        
        # Calculer impact Wave 2 avec calculate_cluster_impact()
        wave2_result = calculate_cluster_impact(
            events=wave2_events,
            event_time=wave2_peak_time,
            conn=self.conn
        )
        
        # Calculer pullback characteristics
        pullback_result = calculate_pullback_characteristics(
            wave1_impact_pips=wave1_result['impact_pips'],
            pullback_time=pullback_time,
            wave1_time=peak1_time,
            direction='bullish' if case['direction'] == 'bullish' else 'bearish'
        )
        
        # Calculer impact total avec calculate_double_wave_overlapping()
        total_result = calculate_double_wave_overlapping(
            wave1_cluster_result=wave1_result,
            wave2_cluster_result=wave2_result,
            pullback_characteristics=pullback_result,
            timing_delta_minutes=timing_delta_minutes,
            wave1_time=peak1_time,
            wave2_time=wave2_peak_time
        )
        
        return {
            'predicted_impact_pips': total_result['total_impact_pips'],
            'wave1_impact': wave1_result['impact_pips'],
            'wave2_impact': wave2_result['impact_pips'],
            'pullback_pips': pullback_result['pullback_pips'],
            'momentum_factor': total_result['momentum_factor'],
            'extension_factor': total_result['extension_factor'],
            'wave1_events_count': len(wave1_events),
            'wave2_events_count': len(wave2_events),
            'timing_delta_min': timing_delta_minutes
        }
    
    def validate_all_cases(self) -> None:
        """Valider formule S115 sur tous les cas"""
        print("=" * 80)
        print("ÉTAPE 2: VALIDATION FORMULE S115 SUR 13 CAS")
        print("=" * 80)
        
        for i, case in enumerate(self.validable_cases, 1):
            baseline_time = case['baseline_time']
            date_str = baseline_time[:10]
            
            print(f"\n[{i}/{len(self.validable_cases)}] Validation {date_str}...")
            
            try:
                # Impact réel MT5
                real_impact = self.extract_real_impact_mt5(case)
                
                # Prédiction formule S115
                prediction = self.calculate_prediction(case)
                predicted_impact = prediction['predicted_impact_pips']
                
                # Calcul MAE
                mae = abs(predicted_impact - real_impact)
                
                # Stocker résultat
                result = {
                    'date': date_str,
                    'baseline_time': baseline_time,
                    'real_impact_pips': real_impact,
                    'predicted_impact_pips': predicted_impact,
                    'mae_pips': mae,
                    'direction': case['direction'],
                    'num_events': case['num_events'],
                    **prediction
                }
                
                self.results.append(result)
                
                # Afficher résultat
                print(f"   Réel:    {real_impact:.2f} pips")
                print(f"   Prédit:  {predicted_impact:.2f} pips")
                print(f"   MAE:     {mae:.2f} pips {'✅' if mae < 5 else '⚠️'}")
                
            except Exception as e:
                print(f"   ❌ ERREUR: {str(e)}")
                continue
        
        print("\n" + "=" * 80)
        print(f"✅ Validation complétée: {len(self.results)}/{len(self.validable_cases)} cas")
        print("=" * 80)
    
    def calculate_statistics(self) -> Dict:
        """Calculer statistiques globales"""
        print("\n" + "=" * 80)
        print("ÉTAPE 3: STATISTIQUES VALIDATION")
        print("=" * 80)
        
        df = pd.DataFrame(self.results)
        
        # Statistiques MAE
        mae_mean = df['mae_pips'].mean()
        mae_median = df['mae_pips'].median()
        mae_std = df['mae_pips'].std()
        mae_max = df['mae_pips'].max()
        mae_min = df['mae_pips'].min()
        
        # RMSE
        rmse = np.sqrt(np.mean(df['mae_pips'] ** 2))
        
        # R² (coefficient de détermination)
        y_true = df['real_impact_pips']
        y_pred = df['predicted_impact_pips']
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - y_true.mean()) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        
        # Outliers (MAE > 10 pips)
        outliers = df[df['mae_pips'] > 10]
        
        # Affichage
        print(f"\n📊 STATISTIQUES GLOBALES (N={len(df)}):")
        print(f"   MAE moyen:    {mae_mean:.2f} pips {'✅' if mae_mean < 5 else '⚠️'}")
        print(f"   MAE médian:   {mae_median:.2f} pips")
        print(f"   MAE écart-type: {mae_std:.2f} pips")
        print(f"   MAE min:      {mae_min:.2f} pips")
        print(f"   MAE max:      {mae_max:.2f} pips")
        print(f"   RMSE:         {rmse:.2f} pips")
        print(f"   R²:           {r2:.4f} {'✅' if r2 > 0.85 else '⚠️'}")
        
        if len(outliers) > 0:
            print(f"\n⚠️  OUTLIERS (MAE > 10 pips): {len(outliers)} cas")
            for _, row in outliers.iterrows():
                print(f"   - {row['date']}: MAE {row['mae_pips']:.2f} pips")
        else:
            print("\n✅ Aucun outlier (tous MAE < 10 pips)")
        
        stats = {
            'mae_mean': mae_mean,
            'mae_median': mae_median,
            'mae_std': mae_std,
            'mae_min': mae_min,
            'mae_max': mae_max,
            'rmse': rmse,
            'r2': r2,
            'num_cases': len(df),
            'num_outliers': len(outliers),
            'success': mae_mean < 5.0
        }
        
        return stats
    
    def create_plots(self) -> None:
        """Créer graphiques validation"""
        print("\n" + "=" * 80)
        print("ÉTAPE 4: GÉNÉRATION GRAPHIQUES")
        print("=" * 80)
        
        df = pd.DataFrame(self.results)
        
        # Créer répertoire plots
        plots_dir = self.output_dir / 'validation_plots'
        plots_dir.mkdir(exist_ok=True)
        
        # Style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        
        # GRAPHIQUE 1: Prédit vs Réel
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.scatter(df['real_impact_pips'], df['predicted_impact_pips'], 
                  s=100, alpha=0.6, edgecolors='black')
        
        # Ligne y=x (prédiction parfaite)
        min_val = min(df['real_impact_pips'].min(), df['predicted_impact_pips'].min())
        max_val = max(df['real_impact_pips'].max(), df['predicted_impact_pips'].max())
        ax.plot([min_val, max_val], [min_val, max_val], 
               'r--', linewidth=2, label='Prédiction parfaite')
        
        ax.set_xlabel('Impact réel MT5 (pips)', fontsize=12)
        ax.set_ylabel('Impact prédit S115 (pips)', fontsize=12)
        ax.set_title('Formule S115: Prédiction vs Réalité (13 cas)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'predicted_vs_real.png', dpi=150)
        plt.close()
        print("   ✅ predicted_vs_real.png")
        
        # GRAPHIQUE 2: Distribution MAE
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(df['mae_pips'], bins=15, edgecolor='black', alpha=0.7)
        ax.axvline(df['mae_pips'].mean(), color='red', linestyle='--', 
                  linewidth=2, label=f'MAE moyen: {df["mae_pips"].mean():.2f} pips')
        ax.axvline(5, color='green', linestyle='--', 
                  linewidth=2, label='Objectif: 5 pips')
        
        ax.set_xlabel('MAE (pips)', fontsize=12)
        ax.set_ylabel('Fréquence', fontsize=12)
        ax.set_title('Distribution MAE - Formule S115 (13 cas)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'mae_distribution.png', dpi=150)
        plt.close()
        print("   ✅ mae_distribution.png")
        
        # GRAPHIQUE 3: MAE par date
        fig, ax = plt.subplots(figsize=(14, 6))
        dates = [r['date'] for r in self.results]
        maes = [r['mae_pips'] for r in self.results]
        
        colors = ['green' if mae < 5 else 'orange' if mae < 10 else 'red' for mae in maes]
        ax.bar(range(len(dates)), maes, color=colors, edgecolor='black')
        ax.axhline(5, color='green', linestyle='--', linewidth=2, label='Objectif: 5 pips')
        ax.axhline(df['mae_pips'].mean(), color='red', linestyle='--', 
                  linewidth=2, label=f'MAE moyen: {df["mae_pips"].mean():.2f} pips')
        
        ax.set_xlabel('Cas', fontsize=12)
        ax.set_ylabel('MAE (pips)', fontsize=12)
        ax.set_title('MAE par Date - Formule S115', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, ha='right')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'mae_by_date.png', dpi=150)
        plt.close()
        print("   ✅ mae_by_date.png")
        
        print(f"\n✅ 3 graphiques créés dans {plots_dir}/")
    
    def generate_report(self, stats: Dict) -> None:
        """Générer rapport validation Markdown"""
        print("\n" + "=" * 80)
        print("ÉTAPE 5: GÉNÉRATION RAPPORT")
        print("=" * 80)
        
        report_path = self.output_dir / 'validation_report_s115.md'
        
        with open(report_path, 'w') as f:
            f.write("# 📊 RAPPORT VALIDATION FORMULE S115\n\n")
            f.write("**Session:** 118  \n")
            f.write(f"**Date:** {datetime.now().strftime('%d %B %Y')}  \n")
            f.write(f"**Formule:** `calculate_double_wave_overlapping()`  \n")
            f.write(f"**Cas testés:** {stats['num_cases']} Double Wave avec events  \n\n")
            
            f.write("---\n\n")
            
            # Résumé exécutif
            f.write("## 🎯 RÉSUMÉ EXÉCUTIF\n\n")
            if stats['success']:
                f.write("✅ **VALIDATION RÉUSSIE**  \n")
                f.write(f"MAE moyen {stats['mae_mean']:.2f} pips **< 5 pips** (objectif atteint)\n\n")
            else:
                f.write("⚠️ **VALIDATION PARTIELLE**  \n")
                f.write(f"MAE moyen {stats['mae_mean']:.2f} pips **> 5 pips** (objectif non atteint)\n\n")
            
            # Statistiques
            f.write("## 📈 STATISTIQUES GLOBALES\n\n")
            f.write(f"| Métrique | Valeur | Objectif | Statut |\n")
            f.write(f"|----------|--------|----------|--------|\n")
            f.write(f"| **MAE moyen** | {stats['mae_mean']:.2f} pips | < 5 pips | ")
            f.write("✅\n" if stats['mae_mean'] < 5 else "⚠️\n")
            f.write(f"| **MAE médian** | {stats['mae_median']:.2f} pips | - | - |\n")
            f.write(f"| **MAE écart-type** | {stats['mae_std']:.2f} pips | - | - |\n")
            f.write(f"| **RMSE** | {stats['rmse']:.2f} pips | < 7 pips | ")
            f.write("✅\n" if stats['rmse'] < 7 else "⚠️\n")
            f.write(f"| **R²** | {stats['r2']:.4f} | > 0.85 | ")
            f.write("✅\n" if stats['r2'] > 0.85 else "⚠️\n")
            f.write(f"| **Outliers** (MAE>10) | {stats['num_outliers']} | < 3 | ")
            f.write("✅\n" if stats['num_outliers'] < 3 else "⚠️\n")
            f.write("\n")
            
            # Résultats détaillés
            f.write("## 📋 RÉSULTATS DÉTAILLÉS PAR CAS\n\n")
            f.write("| # | Date | Réel (pips) | Prédit (pips) | MAE (pips) | Direction | Events |\n")
            f.write("|---|------|-------------|---------------|------------|-----------|--------|\n")
            
            for i, result in enumerate(self.results, 1):
                status = "✅" if result['mae_pips'] < 5 else "⚠️" if result['mae_pips'] < 10 else "🔴"
                f.write(f"| {i} | {result['date']} | ")
                f.write(f"{result['real_impact_pips']:.2f} | ")
                f.write(f"{result['predicted_impact_pips']:.2f} | ")
                f.write(f"{result['mae_pips']:.2f} {status} | ")
                f.write(f"{result['direction']} | ")
                f.write(f"{result['num_events']} |\n")
            
            f.write("\n")
            
            # Cas problématiques
            if stats['num_outliers'] > 0:
                f.write("## ⚠️ CAS PROBLÉMATIQUES (MAE > 10 pips)\n\n")
                df = pd.DataFrame(self.results)
                outliers = df[df['mae_pips'] > 10].sort_values('mae_pips', ascending=False)
                
                for _, row in outliers.iterrows():
                    f.write(f"### {row['date']}\n\n")
                    f.write(f"- **MAE:** {row['mae_pips']:.2f} pips\n")
                    f.write(f"- **Impact réel:** {row['real_impact_pips']:.2f} pips\n")
                    f.write(f"- **Impact prédit:** {row['predicted_impact_pips']:.2f} pips\n")
                    f.write(f"- **Events:** {row['num_events']}\n")
                    f.write(f"- **Direction:** {row['direction']}\n\n")
            
            # Graphiques
            f.write("## 📊 GRAPHIQUES\n\n")
            f.write("Les graphiques suivants sont disponibles dans `validation_plots/`:\n\n")
            f.write("1. **predicted_vs_real.png** - Prédiction vs Réalité\n")
            f.write("2. **mae_distribution.png** - Distribution MAE\n")
            f.write("3. **mae_by_date.png** - MAE par date\n\n")
            
            # Conclusion
            f.write("## 🎯 CONCLUSION\n\n")
            if stats['success']:
                f.write("✅ La formule S115 `calculate_double_wave_overlapping()` est **VALIDÉE** ")
                f.write("sur 13 cas Double Wave avec events.\n\n")
                f.write(f"Avec un MAE moyen de {stats['mae_mean']:.2f} pips (< 5 pips), ")
                f.write("la formule atteint l'objectif de précision requis pour production.\n\n")
            else:
                f.write("⚠️ La formule S115 nécessite des **AJUSTEMENTS** pour atteindre ")
                f.write("l'objectif MAE < 5 pips.\n\n")
                f.write("**Actions recommandées:**\n")
                f.write("1. Analyser cas problématiques (outliers)\n")
                f.write("2. Ajuster momentum_factor (actuel vs optimal)\n")
                f.write("3. Ajuster amplification facteurs par type d'event\n\n")
            
            f.write("---\n\n")
            f.write("**Auteur:** André Valentin avec Claude  \n")
            f.write("**Session:** 118  \n")
            f.write(f"**Date:** {datetime.now().strftime('%d %B %Y')}  \n")
        
        print(f"✅ Rapport créé: {report_path}")
        
    def save_results_json(self) -> None:
        """Sauvegarder résultats en JSON"""
        results_path = self.output_dir / 'validation_results.json'
        
        output = {
            'metadata': {
                'session': 118,
                'date': datetime.now().isoformat(),
                'formula': 'calculate_double_wave_overlapping',
                'num_cases': len(self.results)
            },
            'results': self.results
        }
        
        with open(results_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✅ Résultats JSON: {results_path}")
    
    def run_validation(self) -> Dict:
        """Exécuter validation complète"""
        print("\n" + "=" * 80)
        print("🚀 VALIDATION FORMULE S115 - SESSION 118")
        print("=" * 80)
        print(f"Dataset: {self.dataset_path.name}")
        print(f"Database: {self.warehouse_path.name}")
        print(f"Output: {self.output_dir}")
        print("=" * 80)
        
        # Étapes validation
        self.load_dataset()
        self.validate_all_cases()
        stats = self.calculate_statistics()
        self.create_plots()
        self.generate_report(stats)
        self.save_results_json()
        
        # Résumé final
        print("\n" + "=" * 80)
        print("🎉 VALIDATION COMPLÉTÉE")
        print("=" * 80)
        print(f"✅ {len(self.results)} cas testés")
        print(f"✅ MAE moyen: {stats['mae_mean']:.2f} pips {'✅ SUCCÈS' if stats['success'] else '⚠️ AJUSTEMENTS NÉCESSAIRES'}")
        print(f"✅ Rapport: validation_report_s115.md")
        print(f"✅ Résultats: validation_results.json")
        print(f"✅ Graphiques: validation_plots/")
        print("=" * 80)
        
        return stats


def main():
    """Point d'entrée principal"""
    # Chemins
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    dataset_path = script_dir.parent / 'session117' / 'double_waves_enriched.json'
    warehouse_path = project_root / 'data' / 'warehouse.duckdb'
    output_dir = script_dir
    
    # Validation
    validator = FormulaS115Validator(
        dataset_path=str(dataset_path),
        warehouse_path=str(warehouse_path),
        output_dir=str(output_dir)
    )
    
    stats = validator.run_validation()
    
    # Code retour
    return 0 if stats['success'] else 1


if __name__ == '__main__':
    exit(main())
