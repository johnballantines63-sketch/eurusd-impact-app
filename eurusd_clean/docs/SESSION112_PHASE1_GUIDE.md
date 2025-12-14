# 📋 PHASE 1 - FIX TIMEZONE - GUIDE COMPLET

**Session:** 112  
**Date:** 04 novembre 2025  
**Objectif:** Résoudre définitivement le problème de timezone entre events et prices

---

## 🎯 RÉSUMÉ EXÉCUTIF

**Problème identifié:**
- Events stockés à 14:30+02:00
- Prices stockés à 12:30 pour le même événement réel
- Décalage de 2 heures causant 20+ sessions de debugging

**Solution:**
- ✅ Règle simple: Event timestamp - 2h = Prix timestamp
- ✅ Module `impact_measurement.py` corrigé
- ✅ Documentation complète créée

**Résultat attendu:**
- Précision < 1 pip sur cas de référence (11 sept 2025)
- MAE < 5 pips sur 5 cas testés

---

## 📁 FICHIERS CRÉÉS

### 1. Scripts d'exécution

| Fichier | Rôle | Durée |
|---------|------|-------|
| `phase1_1_backup_database.py` | Backup sécurité DB | 30s |
| `phase1_2_analyze_timezone.py` | Analyse décalage | 10s |
| `phase1_3_test_final.py` | Validation finale | 30s |

### 2. Modules mis à jour

| Fichier | Modifications |
|---------|---------------|
| `fx_impact_app/src/impact_measurement.py` | Ajout règle -2h |

### 3. Documentation

| Fichier | Contenu |
|---------|---------|
| `docs/REGLE_TIMEZONE_DEFINITIVE.md` | Règle timezone complète |
| `docs/SESSION112_PHASE1_GUIDE.md` | Ce document |

---

## 🚀 PROCÉDURE D'EXÉCUTION

### Étape 1 : Backup (OBLIGATOIRE)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean

python scripts/session112/phase1_1_backup_database.py
```

**Résultat attendu:**
```
✅ BACKUP RÉUSSI !
   Taille backup: 205.XX MB
   Emplacement: app/data/backups/warehouse_backup_YYYYMMDD_HHMMSS_before_timezone_fix.duckdb
```

**⚠️ CRITIQUE:** Ne pas continuer sans backup réussi !

---

### Étape 2 : Analyse timezone (OPTIONNEL)

```bash
python scripts/session112/phase1_2_analyze_timezone.py
```

**Résultat attendu:**
```
✅ CONFIRMATION: Le bon prix est 2h AVANT le timestamp event
   Prix -2h: 1.16874 (proche de 1.16874)

💡 CONCLUSION:
   Les events sont stockés avec un DÉCALAGE de +2h
   Il faut chercher les prix à: event_time - 2h
```

**Note:** Ce script confirme que la règle -2h est correcte.

---

### Étape 3 : Test validation finale (CRITIQUE)

```bash
python scripts/session112/phase1_3_test_final.py
```

**Résultat attendu:**

#### Test 1 - Cas référence (11 sept 2025)
```
📊 RÉSULTATS:
Impact mesuré:  57.1 pips
Impact attendu: 56.2 pips
Erreur:         0.9 pips (1.6%)

🎉🎉🎉 EXCELLENT ! Erreur < 1 pip
✅ Module validé avec précision sub-pip
```

#### Test 2 - Multi-cas (5 dates)
```
📈 STATISTIQUES:
   Cas réussis:  5/5
   MAE (erreur moyenne):  < 5.0 pips

🎉🎉🎉 EXCELLENCE !
   ✅ Module prêt pour production
   ✅ Timezone fixée définitivement
```

---

## ✅ CRITÈRES DE SUCCÈS

### Succès total (🎉🎉🎉)
- [ ] Erreur cas référence < 1 pip
- [ ] MAE multi-cas < 2 pips
- [ ] 5/5 cas réussis
- [ ] Prix départ = 1.16874 (±0.0001)

### Succès acceptable (✅)
- [ ] Erreur cas référence < 5 pips
- [ ] MAE multi-cas < 5 pips
- [ ] 4/5 cas réussis

### Échec (❌)
- [ ] Erreur cas référence > 10 pips
- [ ] MAE multi-cas > 10 pips
- [ ] < 3 cas réussis

---

## 🔧 DÉPANNAGE

### Problème 1 : Backup échoue

**Symptôme:**
```
❌ ERREUR: Base de données introuvable !
```

**Solution:**
1. Vérifier chemin DB :
```bash
ls -lh /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb
```

2. Si DB absente, vérifier autre emplacement :
```bash
find ~/Desktop/eurusd_news_impact_calculator_MPC -name "warehouse.duckdb"
```

3. Mettre à jour chemin dans scripts

---

### Problème 2 : Test validation échoue (MAE > 10 pips)

**Symptôme:**
```
⚠️ À AMÉLIORER
   MAE = 21.00 pips
```

**Diagnostic:**

1. Vérifier que module utilise bien -2h :
```python
# Dans impact_measurement.py, ligne ~56
hour_db = hour_bern - 2  # Doit être présent !
```

2. Tester manuellement sur 11 sept :
```python
from datetime import datetime
from impact_measurement import measure_impact_from_dukascopy

event_ts = datetime(2025, 9, 11, 14, 30, 0)
result = measure_impact_from_dukascopy(db_path, event_ts, debug=True)

# Vérifier dans output:
# "Heure prix DB: 12:30 (soustrait 2h)" ✅
# Prix référence: 1.16874 ✅
```

3. Si prix référence != 1.16874 :
   - Module ne soustrait pas 2h correctement
   - Relire `impact_measurement.py` lignes 46-65

---

### Problème 3 : Import module échoue

**Symptôme:**
```
ModuleNotFoundError: No module named 'impact_measurement'
```

**Solution:**
```python
# Ajouter path explicite dans le script
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
src_path = project_root / 'fx_impact_app' / 'src'
sys.path.insert(0, str(src_path))

from impact_measurement import measure_impact_from_dukascopy
```

---

### Problème 4 : DB verrouillée

**Symptôme:**
```
duckdb.IOException: Could not open database - database is locked
```

**Solution:**
1. Fermer toutes applications utilisant la DB :
   - Streamlit
   - DBeaver
   - Autres scripts Python

2. Si bloqué, forcer fermeture :
```bash
lsof | grep warehouse.duckdb
# Tuer processus si nécessaire
kill -9 <PID>
```

---

## 📊 VALIDATION DÉTAILLÉE

### Prix de référence attendus

| Date | Heure Event | Heure Prix DB | Prix Open attendu |
|------|-------------|---------------|-------------------|
| 2025-09-11 | 14:30 | 12:30 | ~1.16874 |
| 2025-08-12 | 14:30 | 12:30 | À vérifier |
| 2025-07-15 | 14:30 | 12:30 | À vérifier |
| 2025-06-11 | 14:30 | 12:30 | À vérifier |
| 2025-05-13 | 14:30 | 12:30 | À vérifier |

### Impacts attendus (MT5)

| Date | Impact MT5 | Tolérance |
|------|------------|-----------|
| 2025-09-11 | 56.2 pips | ±5 pips |
| 2025-08-12 | 62.6 pips | ±5 pips |
| 2025-07-15 | 24.7 pips | ±5 pips |
| 2025-06-11 | 53.9 pips | ±5 pips |
| 2025-05-13 | 34.8 pips | ±5 pips |

---

## 🔍 VÉRIFICATION MANUELLE

Si tests automatiques échouent, vérification manuelle :

```python
import duckdb
from pathlib import Path

db_path = Path("app/data/warehouse.duckdb")
con = duckdb.connect(str(db_path), read_only=True)

# 1. Vérifier event
event = con.execute("""
    SELECT ts_utc FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
    AND event_title LIKE '%CPI%'
    LIMIT 1
""").fetchone()

print(f"Event timestamp: {event[0]}")
# Attendu: 2025-09-11 14:30:00+02:00

# 2. Vérifier prix -2h
price = con.execute("""
    SELECT datetime, open FROM prices_1m
    WHERE datetime >= '2025-09-11 12:30:00'
    AND datetime < '2025-09-11 12:31:00'
""").fetchone()

print(f"Prix timestamp: {price[0]}")
print(f"Prix open: {price[1]:.5f}")
# Attendu: 1.16874

# 3. Calculer impact
prices_120min = con.execute("""
    SELECT high, low FROM prices_1m
    WHERE datetime >= '2025-09-11 12:30:00'
    AND datetime <= '2025-09-11 14:30:00'
""").df()

start_price = price[1]
max_high = prices_120min['high'].max()
impact = (max_high - start_price) * 10000

print(f"Impact calculé: {impact:.1f} pips")
# Attendu: ~57 pips

con.close()
```

---

## 📚 RÉFÉRENCES

### Documents connexes
- `REGLE_TIMEZONE_DEFINITIVE.md` - Règle timezone détaillée
- `SESSION106_METHODE_VALIDEE_MESURE_IMPACT.md` - Méthodologie originale
- `GUIDE_TIMEZONE_DEFINITIF.md` - Guide Session 86 (obsolète)

### Sessions historiques
- Session 85-86 : Première investigation timezone
- Session 92 : Tests timezone multiples
- Session 99-100 : Validation prix référence
- Session 106 : Validation méthode -2h
- **Session 112** : Fix définitif ✅

---

## ✅ CHECKLIST FINALE

Avant de considérer Phase 1 terminée :

- [ ] Backup créé avec succès
- [ ] Script analyse exécuté (optionnel)
- [ ] Test validation exécuté
- [ ] Erreur cas référence < 5 pips
- [ ] MAE multi-cas < 5 pips
- [ ] Documentation lue et comprise
- [ ] Module `impact_measurement.py` testé manuellement
- [ ] Règle -2h documentée dans PROJECT_STATE.md

---

## 🚀 PROCHAINES ÉTAPES

Une fois Phase 1 validée :

1. **Phase 2** : Restructuration architecture (Session 113)
   - Centraliser dans `eurusd_clean/`
   - DB unique
   - Code source organisé

2. **Phase 3** : Calibration amplification (Session 113)
   - Mesurer impacts réels 162 clusters
   - Analyser corrélations amp_optimal
   - Implémenter amplification dynamique

---

## 📞 SUPPORT

En cas de problème persistant :

1. Relire ce guide section DÉPANNAGE
2. Vérifier `REGLE_TIMEZONE_DEFINITIVE.md`
3. Tester manuellement (section VÉRIFICATION MANUELLE)
4. Si toujours bloqué : documenter le problème précisément

**Ne PAS** :
- Modifier la DB sans backup
- Remettre en question la règle -2h sans tests
- Essayer d'autres conversions timezone

---

*Guide créé Session 112 - Phase 1*  
*Version 1.0 - 04 novembre 2025*  
*Dernière mise à jour : 04 novembre 2025*
