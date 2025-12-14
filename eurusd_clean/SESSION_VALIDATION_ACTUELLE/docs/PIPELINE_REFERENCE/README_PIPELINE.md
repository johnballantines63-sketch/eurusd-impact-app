# Documentation du Pipeline de Prédiction d'Impact

## 🚀 Démarrage Rapide

### Utilisation Basique
```python
from scripts.run_pipeline_complete import PipelineExecutor
from config import DB_PATH

executor = PipelineExecutor(DB_PATH, verbose=True)
result = executor.execute_complete_pipeline('2025-09-11')

if result['success']:
    prediction = result['final_prediction']
    print(f"Impact prédit : {prediction['prediction_finale']:.1f} pips")
    print(f"Target de sortie : {prediction['exit_target']:.1f} pips")
```

### Command Line
```bash
python3 scripts/run_pipeline_complete.py --date 2025-09-11
```

---

## 📚 Documentation Complète

### Documentation Principale
- **[INDEX_DOCUMENTATION_COMPLETE.md](INDEX_DOCUMENTATION_COMPLETE.md)** : Index complet de toute la documentation
- **[PIPELINE_REFERENCE_COMPLETE.md](PIPELINE_REFERENCE_COMPLETE.md)** : Référence complète du pipeline
- **[PIPELINE_ARCHITECTURE_DETAILED.md](PIPELINE_ARCHITECTURE_DETAILED.md)** : Architecture détaillée
- **[PIPELINE_FORMULAS_REFERENCE.md](PIPELINE_FORMULAS_REFERENCE.md)** : Référence des formules
- **[PIPELINE_DECISIONS_LOG.md](PIPELINE_DECISIONS_LOG.md)** : Journal des décisions
- **[PIPELINE_TESTING_GUIDE.md](PIPELINE_TESTING_GUIDE.md)** : Guide de test

### Documentation par Thème
Voir [INDEX_DOCUMENTATION_COMPLETE.md](INDEX_DOCUMENTATION_COMPLETE.md) pour la liste complète.

---

## 🎯 Points Clés

### Performance
- **MAE** : 8.4 pips
- **Taux de succès** : 63.2% (acceptable) / 55.3% (excellent)
- **Amélioration** : 64.3% vs baseline

### Solutions Implémentées
1. ✅ **Pic Absolu** : Capture mouvements complets (Wave 3)
2. ✅ **Critères Tendance Assouplis** : Plus de tendances détectées
3. ✅ **Seuil Jaccard 0.60** : Plus de clusters identiques

### Décisions Clés
- Utiliser pic absolu au lieu de Wave 2 détecté
- Option C sans pondération hybride
- Pas de corrections DOUBLE_WAVE dynamiques
- M30 pour impact, M1 pour pattern

---

## 🔧 Configuration

### Paramètres Principaux
```python
WINDOW_MINUTES = 30
SUPPORT_THRESHOLD = 0.8
JACCARD_THRESHOLD = 0.60
MIN_HOURS_BEFORE_EVENT = 12
MIN_DURATION_HOURS = 6.0  # Adapté selon timeframe
EXIT_PERCENTAGE = 0.80
```

### Timeframes
- **Impact** : M30 (par défaut)
- **Pattern** : M1 (toujours)
- **Tendance** : Multi-timeframe (M1, M5, M15, M30, H1)

---

## 📊 Structure du Pipeline

```
Étape 1 : Charger Événements
    ↓
Étape 2 : Détecter Clusters
    ↓
Étape 3 : Définir Noyau Dur
    ↓
Étape 4 : Rechercher Clusters Identiques
    ↓
Étape 5 : Calculer Tendances
    ↓
Étape 6 : Calculer Impacts Base & Amplifications
    ↓
Étape 7 : Analyser Relation Tendance → Amplification
    ↓
Étape 8 : Appliquer Cluster Cible + Pattern + Ajustements
    ↓
Prédiction Finale
```

---

## 🧪 Tests

### Test Complet
```bash
python3 scripts/test_pipeline_validation_finale.py
```

### Test Pic Absolu
```bash
python3 scripts/test_pic_absolu_multiples_dates.py
```

### Test Erreur Spécifique
```bash
python3 scripts/analyser_erreur_23_06.py
```

---

## 📖 Pour Aller Plus Loin

1. **Comprendre l'architecture** : Lire `PIPELINE_ARCHITECTURE_DETAILED.md`
2. **Comprendre les formules** : Lire `PIPELINE_FORMULAS_REFERENCE.md`
3. **Comprendre les décisions** : Lire `PIPELINE_DECISIONS_LOG.md`
4. **Tester le pipeline** : Suivre `PIPELINE_TESTING_GUIDE.md`

---

## ⚠️ Points d'Attention

### Avant Modifications
1. Lire `PIPELINE_DECISIONS_LOG.md` pour comprendre pourquoi
2. Tester sur dates de référence
3. Vérifier non-régression

### Debugging
1. Activer mode verbose : `verbose=True`
2. Vérifier chaque étape individuellement
3. Consulter logs détaillés

### Performance
1. MAE doit rester < 10 pips
2. Taux acceptable doit rester > 60%
3. Cas dégradés doivent rester < 20%

---

## 📞 Support

Pour questions ou problèmes :
1. Consulter `INDEX_DOCUMENTATION_COMPLETE.md`
2. Vérifier `PIPELINE_DECISIONS_LOG.md`
3. Analyser logs en mode verbose

---

**Version** : Final (avec pic absolu)
**Statut** : ✅ Validé et prêt pour production
**Dernière mise à jour** : 2025-01-XX

