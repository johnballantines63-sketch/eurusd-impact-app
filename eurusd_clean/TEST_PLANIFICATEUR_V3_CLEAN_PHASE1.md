# 🧪 GUIDE DE TEST - Planificateur V3.0 Clean - Phase 1

## 🚀 Lancement

Le serveur Streamlit est lancé sur le port **8502**.

**Accès :** http://localhost:8502

---

## ✅ Checklist de Test Phase 1

### 1. **Validation Date**

- [ ] **Test 1.1 : Format ISO (YYYY-MM-DD)**
  - Saisir : `2025-09-11`
  - ✅ Doit être accepté

- [ ] **Test 1.2 : Format Européen (DD.MM.YYYY)**
  - Saisir : `11.09.2025`
  - ✅ Doit être accepté

- [ ] **Test 1.3 : Format avec slash (DD/MM/YYYY)**
  - Saisir : `11/09/2025`
  - ✅ Doit être accepté

- [ ] **Test 1.4 : Date invalide**
  - Saisir : `2025-13-45` ou `abc`
  - ❌ Doit afficher erreur de validation

- [ ] **Test 1.5 : Date hors période**
  - Saisir : `2022-01-01` ou `2026-01-01`
  - ❌ Doit afficher "Date hors période données (2023-2025)"

### 2. **Chargement Événements**

- [ ] **Test 2.1 : Date avec événements HIGH**
  - Date : `2025-09-11` (ou une date connue avec événements)
  - ✅ Doit charger des événements
  - ✅ Doit afficher le nombre d'événements
  - ✅ Doit afficher un DataFrame avec colonnes : ts_bern, country, event_title, importance_n, empirical_score

- [ ] **Test 2.2 : Date sans événements**
  - Date : `2025-01-15` (ou une date sans événements)
  - ⚠️ Doit afficher "Aucun événement trouvé pour cette date"

- [ ] **Test 2.3 : Filtrage pays**
  - Vérifier que seuls les pays pertinents (US, EU, DE, FR, etc.) sont chargés
  - ❌ Pas de pays RU, CN, JP (sauf si pertinent)

- [ ] **Test 2.4 : Exclusion conférences**
  - Vérifier qu'aucun événement "Press Conference" ou "Speech" n'apparaît
  - ✅ Seuls les événements avec 'actual' mesurable

### 3. **Chargement Prix**

- [ ] **Test 3.1 : Date avec prix**
  - Date : `2025-09-11` (ou une date connue)
  - ✅ Doit charger des prix M1
  - ✅ Doit afficher le nombre de bougies
  - ✅ Index datetime en timezone Europe/Zurich

- [ ] **Test 3.2 : Date sans prix**
  - Date : `2025-01-15` (ou une date sans prix)
  - ⚠️ Doit afficher "Aucun prix trouvé pour cette date"

### 4. **Auto-Refresh**

- [ ] **Test 4.1 : Premier lancement**
  - ✅ Doit déclencher auto-refresh si données obsolètes
  - ✅ Doit afficher barre de progression
  - ✅ Doit afficher message de succès ou âge des données

- [ ] **Test 4.2 : Rechargement page**
  - Recharger la page (F5)
  - ✅ Ne doit PAS re-déclencher auto-refresh (session_state)

---

## 🐛 Problèmes Potentiels à Vérifier

### Erreurs d'Import
- ❌ `ModuleNotFoundError: No module named 'config'`
  - **Solution :** Vérifier que `src/config.py` existe

- ❌ `ModuleNotFoundError: No module named 'core.event_utils'`
  - **Solution :** Vérifier que `src/core/event_utils.py` existe

### Erreurs de DB
- ❌ `FileNotFoundError: warehouse.duckdb`
  - **Solution :** Vérifier le chemin dans `config.DB_PATH`

- ❌ `_duckdb.BinderException: Table "events" does not exist`
  - **Solution :** Vérifier que la DB contient la table `events`

### Erreurs de Timezone
- ❌ `pytz.exceptions.UnknownTimeZoneError: Europe/Zurich`
  - **Solution :** Vérifier installation pytz

### Erreurs de Cache
- ⚠️ Cache non trouvé (normal si pas encore généré)
  - **Info :** Ce n'est pas bloquant pour Phase 1

---

## 📝 Notes de Test

**Date de test :** _______________

**Résultats :**
- ✅ Tests réussis : __ / __
- ❌ Tests échoués : __ / __
- ⚠️ Problèmes identifiés : 

**Commentaires :**
_________________________________________________
_________________________________________________
_________________________________________________

---

## 🔄 Après les Tests

Une fois les tests validés, on passera à la **Phase 2** :
- Enrichissement Events (scores, surprises)
- Détection Pattern
- Prédictions de base


