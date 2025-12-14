# ⚠️ TODO SESSION 122 - MISE À JOUR MASTER_PLAN.md

**Fichier à mettre à jour :**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
```

---

## 📝 SECTIONS À METTRE À JOUR

### **1. Section "État actuel" - Ajouter Session 121**

Ajouter après "Session 120 (En cours)" :

```markdown
#### **6. Scanner V3 - Approche Prix → Patterns (Session 121)** ✅ **NEW**

**Problème résolu :** Approche events → prix génère doublons (1 événement = plusieurs détections)  
**Solution :** Scanner bottom-up : Prix → Patterns → Événements

```python
class ScannerV3:
    """
    Détection patterns depuis prix directement
    
    ALGORITHME:
    1. Scanner prix chronologiquement minute par minute
    2. Détecter spikes > 30 pips
    3. Appliquer détecteur séquentiel Rev12
    4. Associer événements APRÈS validation pattern
    
    AVANTAGES:
    - 1 mouvement réel = 1 détection unique
    - Clusters multi-événements correctement associés
    - Cohérence avec approche empirique bottom-up
    """
```

**Validation 1er août 2025 :**
```
Pattern détecté:    EXTENDED
Impact:             184.7 pips
Direction:          bullish
Peak:               15:37 CEST
Événements associés: 0 (mouvement unclustered - NFP absents DB)
```

**Module :** `scripts/session121/scan_price_movements_v3.py`
```

### **2. Section "Roadmap" - Marquer Session 121 complétée**

Ajouter :

```markdown
- [x] **Session 121** : Scanner V3 + Diagnostic DB (PARTIELLE - erreur procédurale)
  - ✅ Scanner Prix → Patterns créé et testé
  - ✅ Diagnostic import EODHD (48% événements manquants 1er août)
  - ✅ Identification structure event_key vs event_title
  - ⚠️ Procédure démarrage non respectée (2h perdues)
```

### **3. Section "Structure Database" - Clarifier event_key**

Ajouter après la structure events :

```markdown
**⚠️ IMPORTANT - event_title vs event_key :**
```
event_title : NULL (non utilisé, placeholder)
event_key   : Vrais noms événements ("ism manufacturing pmi", "michigan consumer sentiment")
```

**Pour identifier événements, utiliser event_key, PAS event_title !**

**Exemple requête correcte :**
```sql
SELECT event_key, actual FROM events
WHERE country = 'US' AND importance_n = 3
-- event_key contient les noms exploitables
```
```

### **4. Section "Problèmes Connus" - Ajouter**

```markdown
#### **Import EODHD incomplet**
**Symptôme :** Certaines dates ont moins d'événements que l'API retourne  
**Exemple :** 1er août 2025 - API: 50 événements US, DB: 26 (48% manquants)  
**Impact :** Mouvements "unclustered" (prix sans événements associés)  
**Solution :** Audit import + sources alternatives (ForexFactory, Investing.com)  
**Session :** 121
```

---

## 🎯 QUAND FAIRE CES MISES À JOUR

**Session 122 - APRÈS validation patterns** :
- Une fois scan complet terminé
- Après analyse distribution empirique
- Avant fin Session 122 (documentation finale)

---

**Créé :** 08 novembre 2025 - Fin Session 121  
**Tokens Session 121 :** 91k / 145k (63%)
