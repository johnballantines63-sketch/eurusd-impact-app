# 🚀 GUIDE LANCEMENT PHASE 1 - SESSION 130

**Date :** 12 novembre 2025  
**Session :** 130  
**Phase :** 1 (Fondations - Étapes 1-3)

---

## ⚡ LANCEMENT RAPIDE (RECOMMANDÉ)

### **Option 1 : Script Launcher (automatique)** ⭐

**macOS/Linux :**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
chmod +x scripts/session130/launch_phase1.sh
./scripts/session130/launch_phase1.sh
```

**Windows :**
```cmd
cd C:\Users\...\eurusd_news_impact_calculator_MPC\eurusd_clean
scripts\session130\launch_phase1.bat
```

**Ce script va :**
1. ✅ Lancer validation rapide (3 dates)
2. ⏸️  Demander confirmation
3. 🚀 Lancer scan complet si OK

**Durée totale :** ~45 minutes

---

## 🔧 LANCEMENT MANUEL (si launcher ne fonctionne pas)

### **Étape A : Validation rapide** (30 secondes)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/session130/validate_phase1_quick.py
```

**Attendu :**
- ✅ Connexion DB OK
- ✅ 3/3 dates détectées (11 sept, 1er août, 5 sept)
- ✅ Patterns classifiés
- ✅ Cas référence sélectionnés

**Si validation OK** → Continuer Étape B  
**Si validation échoue** → Revenir vers Claude avec logs d'erreur

---

### **Étape B : Scan complet 2023-2025** (~45 minutes)

```bash
python scripts/session130/run_phase1.py
```

**Ce script lance séquentiellement :**
1. `scan_by_month.py` - Scanner mois par mois (~40 min)
2. `classify_patterns.py` - Classification (~2 min)
3. `define_reference_cases.py` - Cas référence (~1 min)

**Attendu :**
- 📊 100-150 mouvements détectés
- 📁 3 fichiers JSON créés
- ✅ 11 septembre présent et classifié

---

## 📊 FICHIERS CRÉÉS (après scan complet)

```
scripts/session130/
├── movements_2023_2025_complete.json       # Tous mouvements (~200-300 KB)
├── patterns_classified.json                # Groupés par pattern (~150-250 KB)
├── reference_cases.json                    # Cas référence (~20-30 KB)
└── scan_progress.json                      # Progression (si interrompu)
```

---

## ✅ VALIDATION RÉSULTATS

### **Après scan terminé, vérifier :**

**1. Nombre mouvements :**
```bash
python -c "import json; print(len(json.load(open('scripts/session130/movements_2023_2025_complete.json'))['movements']))"
```
**Attendu :** >= 100 mouvements

**2. Distribution patterns :**
```bash
python -c "import json; d=json.load(open('scripts/session130/patterns_classified.json')); print({k:len(v) for k,v in d['classified'].items()})"
```
**Attendu :** Plusieurs patterns (DoubleWave, SingleWave, ZigZag)

**3. Cas référence :**
```bash
python -c "import json; d=json.load(open('scripts/session130/reference_cases.json')); print(list(d['reference_cases'].keys()))"
```
**Attendu :** >= 2 patterns avec référence

**4. Validation 11 septembre :**
```bash
python -c "import json; d=json.load(open('scripts/session130/reference_cases.json')); print([k for k,v in d['reference_cases'].items() if v['date']=='2025-09-11'])"
```
**Attendu :** `['DoubleWave_Overlap']` ou similaire

---

## 🐛 TROUBLESHOOTING

### **Problème : Import error utils_timezone**

```bash
# Vérifier que utils_timezone.py existe
ls scripts/session129/utils_timezone.py

# Si absent, le recréer (demander à Claude)
```

### **Problème : Database not found**

```bash
# Vérifier chemin DB
ls data/warehouse.duckdb

# Si absent, vérifier configuration DB_PATH dans scan_movements_2023_2025.py
```

### **Problème : Aucun mouvement détecté**

**Causes possibles :**
1. Seuil trop élevé (35 pips) → Tester avec 30 pips
2. Données prix incomplètes → Vérifier `prices_bern` table
3. Timezone incorrect → Vérifier `utils_timezone.py` importé

**Debug :**
```bash
# Tester une seule date
python scripts/session130/test_scanner_quick.py
```

### **Problème : Scanner très lent**

**Solution 1 : Scanner année par année** (au lieu 2023-2025)
```python
# Modifier scan_by_month.py ligne start_date/end_date
start_date = datetime(2024, 1, 1, tzinfo=TZ_BERN)  # Juste 2024
end_date = datetime(2024, 12, 31, tzinfo=TZ_BERN)
```

**Solution 2 : Augmenter seuil** (moins de mouvements)
```python
# Modifier scan_movements_2023_2025.py
MIN_SPIKE_PIPS = 40.0  # Au lieu de 35.0
```

### **Problème : Mémoire insuffisante**

**Solution :** Scanner mois par mois avec sauvegardes intermédiaires
```bash
# scan_by_month.py sauvegarde déjà tous les 3 mois
# Si crash, relancer et il reprendra où interrompu
```

---

## ⏸️ INTERRUPTION

**Si scan interrompu** (Ctrl+C ou crash) :

```bash
# Vérifier progression
cat scripts/session130/scan_progress.json

# Reprendre scan au dernier mois
# (modifier start_date dans scan_by_month.py)
```

---

## 🎯 APRÈS SCAN COMPLET RÉUSSI

**Revenir vers Claude avec :**

1. ✅ Confirmation scan terminé
2. 📊 Nombre total mouvements détectés
3. 📋 Distribution patterns (DoubleWave, SingleWave, etc.)
4. ✅ Validation 11 septembre présent ?
5. 📂 Taille fichiers JSON créés

**Claude va :**
- Analyser résultats
- Valider critères succès PHASE 1
- Décider si continuer PHASE 2-4

---

## 📞 BESOIN D'AIDE ?

**Problème technique ?**
1. Copier logs d'erreur complets
2. Envoyer à Claude avec contexte
3. Claude diagnostiquera et proposera solution

**Budget tokens critique ?**
- Arrêter après PHASE 1
- Documenter état complet
- Reporter PHASES 2-4 à Session 131

---

## ⏱️ DURÉE ESTIMÉE TOTALE

| Étape | Durée | Priorité |
|-------|-------|----------|
| Validation rapide | 30 sec | 🔴 CRITIQUE |
| Scan 2023-2025 | 40 min | 🔴 CRITIQUE |
| Classification | 2 min | 🔴 CRITIQUE |
| Cas référence | 1 min | 🔴 CRITIQUE |
| **TOTAL** | **~45 min** | - |

**Note :** Durée peut varier selon :
- Vitesse disque (SSD vs HDD)
- Quantité mouvements détectés
- Charge CPU

---

## 🎉 SUCCÈS ATTENDU

**Critères minimum viable :**
- ✅ 100+ mouvements détectés
- ✅ 11 septembre présent
- ✅ >= 2 patterns avec cas référence

**Critères optimal :**
- ✅ 150+ mouvements détectés
- ✅ 5 patterns avec cas référence
- ✅ 11 septembre = référence DoubleWave

---

**Créé par :** André Valentin avec Claude  
**Date :** 12 novembre 2025 - Session 130  
**Version :** 1.0  
**Statut :** ✅ PRÊT À LANCER

**🚀 LANCE MAINTENANT !**
