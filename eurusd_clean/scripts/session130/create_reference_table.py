#!/usr/bin/env python3
"""
ÉTABLIR TABLE RÉFÉRENCE - SESSION 130 ÉTAPE 5
==============================================

Crée table récapitulative markdown avec toutes les métriques.

Input : reference_cases_with_amplifications.json
Output : REFERENCE_TABLE.md (table complète)

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 130
"""

import json
from pathlib import Path
from datetime import datetime

# Chemins
INPUT_FILE = Path(__file__).parent / "reference_cases_with_amplifications.json"
OUTPUT_FILE = Path(__file__).parent / "REFERENCE_TABLE.md"


def format_value(value, decimals=2, na_text="N/A"):
    """Formate valeur pour affichage"""
    if value is None:
        return na_text
    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}"
    return str(value)


def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("ÉTABLIR TABLE RÉFÉRENCE - ÉTAPE 5")
    print("=" * 80)
    
    # Charger données
    print(f"\n📂 Chargement : {INPUT_FILE}")
    
    if not INPUT_FILE.exists():
        print(f"❌ Fichier introuvable : {INPUT_FILE}")
        return 1
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    reference_cases = data['reference_cases']
    print(f"✅ {len(reference_cases)} cas référence chargés")
    
    # Créer table markdown
    print(f"\n📋 Création table référence...")
    
    md_content = []
    
    # Header
    md_content.append("# 📋 TABLE RÉFÉRENCE - CAS CALIBRATION PAR PATTERN")
    md_content.append("")
    md_content.append(f"**Date génération :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append(f"**Session :** 130 - PHASE 2")
    md_content.append(f"**Source :** PHASE 1 (scan 2023-2025, 100 mouvements)")
    md_content.append("")
    md_content.append("---")
    md_content.append("")
    
    # Table principale
    md_content.append("## 🎯 CAS RÉFÉRENCE SÉLECTIONNÉS")
    md_content.append("")
    md_content.append("| Pattern | Date | Impact (pips) | Score Total | N Events | Amp Idéale | R² Tendance | Statut |")
    md_content.append("|---------|------|---------------|-------------|----------|------------|-------------|--------|")
    
    for pattern, case in reference_cases.items():
        impact = format_value(case.get('impact_real'), 1)
        score = format_value(case.get('total_score'), 2)
        n_events = case.get('n_events_with_score', case.get('n_events', 0))
        amp = format_value(case.get('amp_ideal'), 6)
        r2 = format_value(case.get('r2_trend'), 4)
        
        # Statut
        if 'error' in case:
            statut = "❌ Erreur"
        elif case.get('amp_ideal') is None:
            statut = "⚠️ No score"
        elif case.get('status') == 'validated':
            statut = "✅ Validé"
        else:
            statut = "⏳ À valider"
        
        md_content.append(f"| {pattern:<20s} | {case['date']} | {impact:>13s} | {score:>11s} | {n_events:>8d} | {amp:>10s} | {r2:>11s} | {statut} |")
    
    md_content.append("")
    md_content.append("---")
    md_content.append("")
    
    # Détails par pattern
    md_content.append("## 📊 DÉTAILS PAR PATTERN")
    md_content.append("")
    
    for pattern, case in reference_cases.items():
        md_content.append(f"### **{pattern}**")
        md_content.append("")
        md_content.append(f"**Date référence :** {case['date']}")
        md_content.append(f"**Statut :** {case.get('status', 'to_validate')}")
        
        if case.get('status') == 'validated':
            md_content.append(f"**Validation :** Session 115 (MAE 0.29 pips)")
        
        md_content.append("")
        md_content.append("**Métriques :**")
        md_content.append(f"- Impact réel : {format_value(case.get('impact_real'), 2)} pips")
        md_content.append(f"- Score total : {format_value(case.get('total_score'), 2)}")
        md_content.append(f"- N events : {case.get('n_events', 0)} (dont {case.get('n_events_with_score', 0)} avec score)")
        md_content.append(f"- Amp idéale : {format_value(case.get('amp_ideal'), 6)}")
        md_content.append(f"- R² tendance (7j) : {format_value(case.get('r2_trend'), 4)}")
        md_content.append("")
        
        # Validation
        if 'validation' in case:
            val = case['validation']
            md_content.append("**Validation calcul :**")
            md_content.append(f"- Impact prédit : {format_value(val.get('impact_predicted'), 2)} pips")
            md_content.append(f"- MAE : {format_value(val.get('mae'), 4)} pips")
            md_content.append("")
        
        # Events détails
        if 'events_details' in case and case['events_details']:
            md_content.append("**Événements causaux :**")
            for i, event in enumerate(case['events_details'], 1):
                score = format_value(event.get('score'), 2, "N/A")
                importance = event.get('importance', 'N/A')
                country = event.get('country', 'N/A')
                event_key = event.get('event_key', 'unknown')
                
                if event.get('score') is not None:
                    md_content.append(f"{i}. `{event_key}` - Score: {score} ({importance}, {country})")
                else:
                    md_content.append(f"{i}. `{event_key}` - ⚠️ Score non trouvé ({importance}, {country})")
            md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    # Formules
    md_content.append("## 📐 FORMULES UTILISÉES")
    md_content.append("")
    md_content.append("### Amplification idéale")
    md_content.append("```")
    md_content.append("amp_ideal = impact_real / (score_total × sqrt(n_events))")
    md_content.append("```")
    md_content.append("")
    md_content.append("### Prédiction impact")
    md_content.append("```")
    md_content.append("impact_predicted = score_total × amp × sqrt(n_events)")
    md_content.append("```")
    md_content.append("")
    md_content.append("### R² tendance")
    md_content.append("```")
    md_content.append("R² = coefficient détermination régression linéaire (7 jours avant événement)")
    md_content.append("```")
    md_content.append("")
    md_content.append("---")
    md_content.append("")
    
    # Notes
    md_content.append("## 📝 NOTES")
    md_content.append("")
    md_content.append("- **Amp idéale** : Valeur qui prédit exactement l'impact du cas référence")
    md_content.append("- **Score total** : Somme scores empiriques événements cluster")
    md_content.append("- **N events** : Nombre événements avec score disponible")
    md_content.append("- **R² tendance** : Mesure force tendance pré-événement (0=aucune, 1=parfaite)")
    md_content.append("- **Statut validé** : Cas testé et validé session précédente (ex: 11 sept S115)")
    md_content.append("")
    md_content.append("---")
    md_content.append("")
    md_content.append(f"**Généré par :** Session 130 - PHASE 2  ")
    md_content.append(f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    md_content.append(f"**Auteur :** André Valentin avec Claude")
    
    # Sauvegarder
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    print(f"✅ Table créée : {OUTPUT_FILE}")
    print(f"   Lignes : {len(md_content)}")
    print(f"   Taille : {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    
    # Afficher table principale
    print(f"\n" + "=" * 80)
    print("TABLE RÉFÉRENCE PRINCIPALE")
    print("=" * 80)
    print("")
    
    # Reproduire table
    print("| Pattern | Date | Impact | Score | N | Amp | R² | Statut |")
    print("|---------|------|--------|-------|---|-----|-------|--------|")
    
    for pattern, case in reference_cases.items():
        impact = format_value(case.get('impact_real'), 1)
        score = format_value(case.get('total_score'), 1)
        n_events = case.get('n_events_with_score', case.get('n_events', 0))
        amp = format_value(case.get('amp_ideal'), 4)
        r2 = format_value(case.get('r2_trend'), 3)
        
        if 'error' in case:
            statut = "❌"
        elif case.get('amp_ideal') is None:
            statut = "⚠️"
        elif case.get('status') == 'validated':
            statut = "✅"
        else:
            statut = "⏳"
        
        # Tronquer pattern si trop long
        pattern_short = pattern[:18] + ".." if len(pattern) > 20 else pattern
        
        print(f"| {pattern_short:<20s} | {case['date']} | {impact:>6s} | {score:>5s} | {n_events:>1d} | {amp:>7s} | {r2:>5s} | {statut:^6s} |")
    
    print("")
    print("=" * 80)
    print("✅ ÉTAPE 5 TERMINÉE")
    print("=" * 80)
    
    print(f"\n🎯 PHASE 2 COMPLÉTÉE !")
    print(f"   Fichiers créés :")
    print(f"   - reference_cases_with_amplifications.json")
    print(f"   - REFERENCE_TABLE.md")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        import sys
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
