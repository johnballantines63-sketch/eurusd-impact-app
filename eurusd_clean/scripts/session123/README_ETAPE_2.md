# ⬇️ ÉTAPE 2 : TÉLÉCHARGEMENT HISTORIQUE JBLANKED

**Session :** 123  
**Durée estimée :** 1-2 heures  
**Statut :** 🟡 PRÊT À EXÉCUTER

---

## 🎯 OBJECTIF

Télécharger **tous les événements économiques 2015-2025** depuis JBlanked API pour remplir la base de données.

---

## 📊 CE QUI VA ÊTRE TÉLÉCHARGÉ

### **Années**
```
2015 → ~400 événements
2016 → ~450 événements  
2017 → ~450 événements
2018 → ~500 événements
2019 → ~500 événements
2020 → ~500 événements
2021 → ~550 événements
2022 → ~550 événements
2023 → ~550 événements
2024 → ~600 événements
2025 → ~400 événements (10 mois)

TOTAL ESTIMÉ: 5,000-6,000 événements
```

### **Fichiers créés**
```
data/jblanked_raw/
├── events_2015.json
├── events_2016.json
├── events_2017.json
├── events_2018.json
├── events_2019.json
├── events_2020.json
├── events_2021.json
├── events_2022.json
├── events_2023.json
├── events_2024.json
├── events_2025.json
└── download_report.json (rapport téléchargement)
```

---

## 🚀 EXÉCUTION

### **Commande**

```bash
cd scripts/session123/
python download_jblanked_history.py
```

### **Durée**

```
11 années × ~10 secondes/année = ~2 minutes téléchargement pur
+ Rate limiting 2s × 10 intervalles = 20 secondes
+ Traitement/sauvegarde = ~1 minute

TOTAL RÉEL: ~3-5 minutes (pas 2 heures !)
```

**Note :** Estimation initiale 2h était très conservatrice. En réalité, le téléchargement sera beaucoup plus rapide.

---

## ⚙️ CE QUE LE SCRIPT FAIT

### **1. Téléchargement année par année**
```python
for year in 2015..2025:
    download(year)
    wait(2 seconds)  # Rate limiting
```

### **2. Gestion erreurs**
- HTTP 401 → API Key invalide (stop)
- HTTP 429 → Rate limit (attente 60s, retry)
- Timeout → Skip année, continuer
- Connexion → Skip année, continuer

### **3. Statistiques temps réel**
```
📅 ANNÉE 2015
   Status: 200
   ✅ SUCCÈS - 412 événements
   💾 Sauvegardé: events_2015.json (88.3 KB)
   
⏳ Attente 2s (rate limiting)...
```

### **4. Rapport final**
```
✅ ANNÉES TÉLÉCHARGÉES (11 années)
📊 STATISTIQUES:
   Total événements: 5,245
   Durée totale: 3.2 min
✅ OBJECTIF 5,000+ ÉVÉNEMENTS ATTEINT
```

---

## 📁 STRUCTURE DONNÉES

### **Format événement JBlanked**
```json
{
  "Name": "Non-Farm Employment Change",
  "Currency": "USD",
  "Date": "2025.08.01 15:30:00",
  "Actual": 114000,
  "Forecast": 175000,
  "Previous": 206000,
  "Outcome": "Actual < Forecast < Previous",
  "Strength": "Strong Data",
  "Quality": "Bad Data"
}
```

### **Colonnes importantes**
- ✅ **Name** : Nom événement
- ✅ **Currency** : Pays (USD, EUR, GBP, etc.)
- ✅ **Date** : Timestamp GMT+3 (conversion Étape 3)
- ✅ **Actual** : Valeur publiée
- ✅ **Forecast** : Consensus
- ✅ **Previous** : Valeur précédente

---

## ⚠️ POINTS CRITIQUES

### **1. Rate Limiting**

**Stratégie :** 2 secondes entre chaque année

**Pourquoi ?**
- Éviter HTTP 429 (too many requests)
- Respecter API JBlanked
- Assurer stabilité téléchargement

**Si 429 quand même :**
- Script attendra 60 secondes
- Retry automatique
- Continue avec années suivantes

### **2. Ne PAS interrompre**

**Si interruption (Ctrl+C) :**
- Années déjà téléchargées = OK (fichiers sauvegardés)
- Années restantes = manquantes
- **Solution :** Relancer script (skip années existantes automatiquement ?)

**Recommandation :** Laisser tourner jusqu'au bout (~5 min)

### **3. API Key valide**

**Si erreur 401 :**
- Vérifier API Key JBlanked
- Vérifier abonnement actif
- Contact support si nécessaire

**API Key actuelle :**
```
qT4V27gU.oZXOPJgBWKnKN8rISnz02JQfRSmtx4W7
```

---

## ✅ CRITÈRES SUCCÈS

### **Téléchargement réussi si :**

- [x] 11 fichiers JSON créés (2015-2025)
- [x] Total événements >= 5,000
- [x] Aucune année manquante critique
- [x] Fichier rapport créé
- [x] Tous fichiers > 0 bytes

### **Validation post-téléchargement**

```bash
# Vérifier fichiers
ls -lh data/jblanked_raw/

# Compter événements
cat data/jblanked_raw/events_*.json | grep '"Name"' | wc -l

# Vérifier août 2025 (cas test)
cat data/jblanked_raw/events_2025.json | grep -i "non-farm"
```

---

## 🔄 EN CAS DE PROBLÈME

### **Problème 1 : Erreur 401**

```
❌ ERREUR 401 - API Key invalide

Actions:
1. Vérifier API Key copiée correctement
2. Vérifier abonnement JBlanked actif
3. Régénérer API Key si nécessaire
```

### **Problème 2 : Erreur 429**

```
⚠️ ERREUR 429 - Rate limit

Script attendra automatiquement 60s puis retry.
Si persiste: augmenter délai à 5s dans code.
```

### **Problème 3 : Timeout**

```
❌ TIMEOUT - Requête > 60s

Causes possibles:
- Connexion internet lente
- Serveur JBlanked lent
- Année avec beaucoup d'événements

Solution: Script skip et continue autres années
```

### **Problème 4 : Interruption**

```
Si Ctrl+C pendant téléchargement:
1. Noter dernière année téléchargée
2. Relancer script
3. Skip manuellement années déjà faites
```

---

## 📈 MÉTRIQUES ATTENDUES

### **Par année (moyenne)**

```
Événements: ~450-500
Taille fichier: 80-120 KB
Durée download: 5-10 secondes
```

### **Total attendu**

```
Fichiers: 11
Taille totale: ~1 MB
Événements: 5,000-6,000
Durée: 3-5 minutes
```

---

## 🚀 PROCHAINE ÉTAPE APRÈS SUCCÈS

**ÉTAPE 3 : Mapping et nettoyage**

Actions :
1. Charger 11 fichiers JSON
2. Normaliser event_key
3. Convertir timestamps (GMT+3 → UTC)
4. Mapper colonnes vers structure DB
5. Gérer doublons
6. Préparer pour import

**Durée estimée :** 1 heure

---

## 💾 BACKUP

**Après téléchargement réussi :**

```bash
# Créer backup fichiers bruts
cd data/
tar -czf jblanked_raw_backup_20251109.tar.gz jblanked_raw/
```

**Pourquoi ?**
- Sécurité si erreur Étape 3-5
- Possibilité retraiter données
- Historique complet sauvegardé

---

**Créé le :** 09 novembre 2025  
**Auteur :** André Valentin avec Claude  
**Session :** 123 - Étape 2  
**Statut :** ✅ PRÊT À LANCER
