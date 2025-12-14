# Workflow Double Source - Session 123

Workflow complet pour merger JBlanked VIP + EODHD Fundamentals vers table master.

**Auteur:** André Valentin avec Claude  
**Date:** 09 novembre 2025  
**Session:** 123

---

## 🎯 Objectif

Créer table `economic_events` master avec:
- JBlanked VIP 2020-2025 (source principale, dates critiques validées)
- EODHD Fundamentals 2020-2025 (source complémentaire, complétude)
- Merge intelligent avec déduplication
- ~5,500-6,300 événements attendus

---

## 📋 Scripts créés

1. **download_jblanked_2020_2025.py** - Télécharge JBlanked 2020-2025
2. **download_eodhd_2020_2025.py** - Télécharge EODHD 2020-2025 (limit=1000)
3. **normalize.py** - Module normalisation (mappings)
4. **merge_sources.py** - Merge intelligent → Master
5. **import_master_to_db.py** - Import DB final
6. **run_workflow.py** - Orchestration complète

---

## 🚀 Exécution

### Option A : Workflow automatique (RECOMMANDÉ)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session123/
python run_workflow.py
```

Cette commande exécute automatiquement:
1. Téléchargement JBlanked
2. Téléchargement EODHD  
3. Merge sources

Puis manuellement:
```bash
python import_master_to_db.py
```

### Option B : Étape par étape

```bash
# Étape 1 : JBlanked
python download_jblanked_2020_2025.py

# Étape 2 : EODHD
python download_eodhd_2020_2025.py

# Étape 3 : Merge
python merge_sources.py

# Étape 4 : Import DB
python import_master_to_db.py
```

---

## 📊 Fichiers créés

```
data/
├── jblanked_2020_2025/
│   ├── events_2020.json
│   ├── events_2021.json
│   ├── events_2022.json
│   ├── events_2023.json
│   ├── events_2024.json
│   ├── events_2025.json
│   └── jblanked_all_2020_2025.json  (toutes années)
│
├── eodhd_2020_2025/
│   ├── events_2020.json
│   ├── events_2021.json
│   ├── events_2022.json
│   ├── events_2023.json
│   ├── events_2024.json
│   ├── events_2025.json
│   └── eodhd_all_2020_2025.json  (toutes années)
│
└── master/
    └── events_master_2020_2025.json  (merge final)

warehouse.duckdb  (base données finale)
```

---

## 🔑 Normalisation

### Event Key unique

Format: `{country}_{event_name}_{datetime}`

Exemple: `usd_nonfarm_payrolls_20250801_1230`

**Objectif:** Même événement dans JBlanked et EODHD génère même clé → déduplication

### Mappings

**Codes pays:**
- US → usd
- GB/UK → gbp
- DE/EU/FR → eur
- etc.

**Noms événements:**
- "Non-Farm Employment Change" → nonfarm_payrolls
- "Nonfarm Payrolls" → nonfarm_payrolls
- "CPI m/m" → cpi_mom
- etc.

**Timestamps:**
- JBlanked GMT+3 → UTC (-3h)
- EODHD déjà UTC

---

## 📈 Statistiques attendues

```
JBlanked seul        : ~1,850 événements (370/an × 5 ans)
EODHD seul           : ~5,000 événements (1000/an × 5 ans)
Doublons (validés)   : ~500-800 événements
──────────────────────────────────────────────
MASTER Total         : ~5,500-6,300 événements

Par source:
  JBLANKED uniquement : 1,000-1,350
  EODHD uniquement    : 4,200-4,500
  BOTH (validés)      : 500-800
```

---

## ✅ Validation

### Dates critiques

**1er août 2025:**
- Attendu: 27+ événements (JBlanked validé MT5)
- USD: 10+ événements

**11 septembre 2025:**
- Attendu: 4+ événements après merge
- Limitation connue (aucune source complète)

### Requête test

```python
import duckdb
conn = duckdb.connect('warehouse.duckdb')

# Total
print(conn.execute("SELECT COUNT(*) FROM economic_events").fetchone())

# 1er août 2025
print(conn.execute("""
    SELECT * FROM economic_events 
    WHERE DATE(datetime_utc) = '2025-08-01' 
    AND country = 'usd'
    ORDER BY datetime_utc
""").fetchall())
```

---

## ⏱️ Durée estimée

- Téléchargement JBlanked: 3-5 min
- Téléchargement EODHD: 3-5 min
- Merge: 2-3 min
- Import DB: 2-3 min

**Total: 10-16 minutes**

---

## 🐛 Troubleshooting

### Erreur API JBlanked

```
❌ Status 402 - Crédits insuffisants
```

**Solution:** Vérifier crédits mensuels API VIP

### Erreur API EODHD

```
❌ Status 401 - Unauthorized
```

**Solution:** Vérifier API key Fundamentals

### EODHD retourne toujours 50 événements

```
⚠️ Seulement 50 événements (vs 1000 attendu)
```

**Solution:** Paramètre `limit=1000` manquant (déjà ajouté dans scripts)

### Import DB échoue

```
❌ Table already exists
```

**Solution:** Script fait backup automatique, mais si erreur:
```python
conn.execute("DROP TABLE IF EXISTS economic_events")
```

---

## 📝 Notes importantes

1. **JBlanked = Source prioritaire** pour conflits (dates critiques validées)
2. **EODHD = Complément** (comble lacunes JBlanked)
3. **Doublons marqués BOTH** = validation croisée ✅
4. **11 septembre incomplet** = limitation acceptée temporairement
5. **Backup automatique** table existante avant import

---

## 🎯 Après import

1. Vérifier complétude table master
2. Tester formules sur 1er août 2025
3. Chercher date alternative pour gold standard (11 sept incomplet)
4. Session future: Ajouter 3ème source si nécessaire

---

## ✅ Checklist finale

- [ ] Scripts créés
- [ ] API keys configurées
- [ ] Workflow exécuté
- [ ] Master créé (5,500+ événements)
- [ ] Import DB réussi
- [ ] 1er août validé (27+ événements)
- [ ] Backup DB créé
- [ ] Documentation complète

---

## 📧 Support EODHD

Si problèmes persistent avec EODHD (gaps critiques):

**Email:** support@eodhistoricaldata.com  
**Sujet:** Fundamentals Plan - Data Gaps  
**Demander:** Explication technique OU remboursement

---

**Session 123 réussie si table master complète importée avec succès.** ✅
