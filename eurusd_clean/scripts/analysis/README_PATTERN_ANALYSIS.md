# 🔍 Guide d'Exécution - Analyse Pattern W

## Session 63 - Analyse Quantitative des Patterns CPI

### 📋 Objectif

Analyser les dates CPI historiques pour déterminer :
1. La fréquence du pattern W (double montée)
2. Les caractéristiques quantitatives du pattern W
3. La différence avec le pattern linéaire

### 🚀 Exécution du Script

#### Méthode 1 : Script bash (recommandé)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
chmod +x scripts/run_pattern_analysis.sh
./scripts/run_pattern_analysis.sh
```

#### Méthode 2 : Python direct

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/analysis/analyze_cpi_pattern_w.py
```

### 📊 Ce que le Script Fait

1. **Charge les dates CPI** (avant 11 septembre 2025)
2. **Pour chaque date** :
   - Charge les événements CPI
   - Calcule la surprise maximale
   - Charge les prix MT5 (1 heure avant, 2 heures après)
   - **Détecte le type de pattern** (W ou linéaire)
   - Mesure les caractéristiques quantitatives

3. **Critères de détection Pattern W** :
   - Au moins 2 peaks dans les 20 premières minutes
   - Un trough (creux) entre les 2 peaks
   - Amplitude minimum de chaque montée > 15 pips
   - Trough situé entre les 2 peaks

4. **Génère un résumé statistique** :
   - Nombre de patterns W vs linéaires
   - Fréquence (%)
   - Caractéristiques moyennes du pattern W
   - Export CSV des résultats

### 📁 Fichiers Générés

```
scripts/analysis/
└── cpi_pattern_analysis_results.csv    ← Résultats détaillés
```

### 🎯 Résultats Attendus

Le script affiche :

```
================================================================================
📊 ANALYSE PATTERN W - ÉVÉNEMENTS CPI
================================================================================

📅 Chargement des dates CPI historiques...

✅ 5-10 dates CPI trouvées (avant 11 sept 2025)

================================================================================
🔍 ANALYSE DÉTAILLÉE PAR DATE
================================================================================

📆 Date: 2025-08-14 (9 événements)
------------------------------------------------------------
   Événements: 9
   Surprise max: 33.3%
   Prix disponibles: 180 minutes
   ✅ Pattern détecté: W_SHAPE
      - Peak 1: +31.0 pips à T+5min
      - Trough: -26.0 pips à T+11min
      - Peak 2: +51.0 pips à T+15min
      - Total impact: +56.0 pips

[...]

================================================================================
📈 RÉSUMÉ STATISTIQUE
================================================================================

✅ Dates analysées avec prix: 5
   - Pattern W: 2 (40.0%)
   - Pattern linéaire: 3 (60.0%)

📊 Caractéristiques Pattern W (n=2):
   - Peak 1 timing moyen: T+5.5min
   - Peak 1 amplitude moyenne: 30.5 pips
   - Trough timing moyen: T+10.0min
   - Peak 2 timing moyen: T+14.5min
   - Impact total moyen: 55.0 pips
   - Surprise moyenne: 32.0%

💾 Résultats sauvegardés: [...]/cpi_pattern_analysis_results.csv

================================================================================
✅ ANALYSE TERMINÉE
================================================================================
```

### 🔍 Interprétation des Résultats

#### Si Pattern W fréquent (>50%)
→ Créer nouvelles formules pour modéliser les 2 montées

#### Si Pattern W rare (<30%)
→ Créer un détecteur de pattern basé sur :
- Surprise (%)
- Nombre d'événements simultanés
- Autre indicateur

#### Si Pattern W modéré (30-50%)
→ Analyser les corrélations :
- Pattern W lié à la surprise ?
- Pattern W lié au nombre d'événements ?
- Pattern W lié à un événement spécifique (Core CPI) ?

### ⚠️ Limitations du Script

- **Détection simplifiée** : cherche 2 peaks locaux dans les 20 premières minutes
- **Seuil arbitraire** : 15 pips minimum par montée
- **Pas de ML** : règles empiriques simples
- **Données manquantes** : certaines dates peuvent ne pas avoir de prix MT5

### 🔧 Si Besoin d'Ajustements

Le script peut être modifié pour :
- Changer les critères de détection (seuils, fenêtre temporelle)
- Analyser plus de dates (modifier `LIMIT 10`)
- Affiner la détection de peaks/troughs
- Ajouter d'autres métriques

### 📝 Prochaines Étapes

Après l'exécution :
1. Analyser les résultats du CSV
2. Déterminer la fréquence du pattern W
3. Si W fréquent : créer `formulas_pattern_w.py`
4. Si W rare : créer fonction de détection
5. Modifier le Planificateur V2 pour timeline réaliste

---

**Prêt à exécuter ?** Lancez le script et partagez les résultats ! 🚀
