# 🚀 Scripts Session 63 - Guide Rapide

## Lancement Simplifié (Recommandé)

**La façon la plus simple d'exécuter l'analyse :**

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/launch_analysis.py
```

Le script vous propose un menu :
```
1. Test infrastructure uniquement
2. Analyse Pattern W complète
3. Les deux (test + analyse)
0. Quitter
```

---

## Ou Exécution Manuelle

### Option 1 : Test Infrastructure Seul

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/analysis/test_infrastructure.py
```

**Durée :** ~5 secondes  
**Vérifie :** DB, tables, données disponibles

### Option 2 : Analyse Pattern W

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/analysis/analyze_cpi_pattern_w.py
```

**Durée :** 30 sec - 2 min  
**Génère :** `scripts/analysis/cpi_pattern_analysis_results.csv`

---

## 📁 Structure Scripts

```
scripts/
├── launch_analysis.py                    ⭐ Launcher interactif (RECOMMANDÉ)
├── run_pattern_analysis.sh               Script bash simple
│
└── analysis/
    ├── test_infrastructure.py            Test DB et tables
    ├── analyze_cpi_pattern_w.py          Analyse complète Pattern W
    ├── README_PATTERN_ANALYSIS.md        Guide détaillé
    └── cpi_pattern_analysis_results.csv  Résultats (généré)
```

---

## 🎯 Que Faire Après l'Analyse ?

1. **Consulter le CSV généré**
2. **Analyser la fréquence du Pattern W**
3. **Décider de la modélisation :**
   - Si W fréquent (>50%) → créer formules
   - Si W rare (<30%) → créer détecteur
   - Si W modéré (30-50%) → approche mixte

4. **Partager les résultats dans le chat Claude**

---

## 📖 Documentation Complète

Pour plus de détails, consultez :

- `docs/SESSION63_RESUME_VISUEL.md` - Vue d'ensemble
- `docs/SESSION63_ACTIONS_IMMEDIATES.md` - Actions à faire
- `docs/SESSION63_PLAN_EXECUTION.md` - Plan complet 6 étapes
- `scripts/analysis/README_PATTERN_ANALYSIS.md` - Guide technique

---

## ⚠️ Dépendances

```bash
pip install duckdb pandas
```

---

**Bonne analyse ! 🚀**
