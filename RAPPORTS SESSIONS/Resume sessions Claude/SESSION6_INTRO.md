# 🚀 SESSION 6 - FIX SCORES EMPIRIQUES MULTI-ÉVÉNEMENTS

**Date :** [À remplir]  
**Tokens : [À mettre à jour régulièrement]**  
**Rapport précédent :** `RAPPORT_SESSION5_DIAGNOSTIC_COMPLET_SCORES.md`

---

## 📋 CONTEXTE RAPIDE

### Situation actuelle
Le système de pullback fonctionne correctement **EN THÉORIE**, mais les impacts prédits sont 6-8x trop faibles car tous les événements affichent **Score: 0/100** au lieu de leurs vrais scores empiriques (70-90/100).

### Problème identifié Session 5
```
❌ Calendrier affiche :
   14:30 - CPI (US) | Score: 0/100
   14:45 - Current Account (DE) | Score: 0/100

✅ Base de données contient :
   CPI (US) : Score = 82-86/100
   Current Account (DE) : Score = 68/100
   
→ Le code NE LIT PAS les scores de la DB !
```

### Conséquence
```
Impact Phase 1 : 54.9 pips ❌ (devrait être ~200-300 pips)
Impact Phase 2 : 24.9 pips ❌ (devrait être ~150-200 pips)
Pullback : 22 pips ❌ (devrait être ~80-120 pips)

Le % pullback est correct (40%) mais appliqué sur une base trop faible.
```

---

## 🎯 OBJECTIF SESSION 6

**Corriger la lecture des scores empiriques dans `4_Planificateur-Multi-Evenements.py`**

### Fichier à modifier
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py
```

### Fichier de référence (même fix déjà implémenté avec succès)
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fix_calendar_scores.py
```

### Base de données (CORRECTE - ne pas modifier)
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb
  └─ Table: event_families
     └─ Colonne: empirical_score (0-100)
     └─ Colonne: empirical_impact ('HIGH', 'MEDIUM', 'LOW')
```

---

## ✅ CE QUI FONCTIONNE DÉJÀ

- ✅ **Base de données** : 96.7% des événements ont un score correct
- ✅ **Module backend v8.6.7** : Pullback calculé correctement (formule 4%/min, plafond 50%)
- ✅ **Clés enrichies** : Toutes les clés nécessaires ajoutées (peak_time, cumulative_price, etc.)
- ✅ **Validation** : Script `validate_calendar_scores.py` confirme que les scores existent

---

## ❌ CE QUI NE FONCTIONNE PAS

- ❌ **Lecture des scores** : Le code recalcule mal au lieu de lire depuis la DB
- ❌ **Affichage** : Tous les événements montrent Score: 0/100
- ❌ **Impacts prédits** : Trop faibles (54 pips au lieu de 200-300 pips)
- ❌ **Pullback visuel** : Trop petit (22 pips au lieu de 80-120 pips)

---

## 📝 TÂCHES À EFFECTUER

### TÂCHE 1 : Créer le script de fix (PRIORITÉ HAUTE)

**Créer :** `fix_multi_events_scores.py`

**Basé sur :** `fix_calendar_scores.py` (lignes 50-120)

**Objectif :** Modifier `4_Planificateur-Multi-Evenements.py` pour lire directement `empirical_score` depuis la DB.

**Code à insérer :**
```python
# Charger les scores depuis event_families
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)

empirical_scores = conn.execute("""
    SELECT event_key, country, empirical_score, empirical_impact
    FROM event_families
    WHERE empirical_score IS NOT NULL
""").fetchdf()

# Créer dict pour lookup
score_lookup = {
    (row['event_key'], row['country']): {
        'score': row['empirical_score'],
        'impact': row['empirical_impact']
    }
    for _, row in empirical_scores.iterrows()
}

# Enrichir événements avec fallback EU ↔ EA
for event in events:
    event_key = event['event_key']
    country = event['country']
    
    score_data = score_lookup.get((event_key, country))
    if not score_data and country == 'EU':
        score_data = score_lookup.get((event_key, 'EA'))
    elif not score_data and country == 'EA':
        score_data = score_lookup.get((event_key, 'EU'))
    
    if score_data:
        event['score'] = score_data['score']
        event['empirical_impact'] = score_data['impact']
    else:
        event['score'] = 50  # Fallback raisonnable
        event['empirical_impact'] = 'MEDIUM'
```

---

### TÂCHE 2 : Tester la correction

**Après exécution du script de fix :**

1. Nettoyer cache :
```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
pkill -f streamlit
```

2. Relancer :
```bash
streamlit run fx_impact_app/streamlit_app/Home.py
```

3. Test 11 septembre 2025 :
   - Aller à "Planificateur Multi-Événements"
   - Sélectionner : CPI (US) 14:30 + Current Account (DE) 14:45
   - Remplir les valeurs réelles
   - Générer prédiction

4. **Vérifier :**

**Dans le calendrier (AVANT génération) :**
```
✅ Score affiché : 70-90/100 (au lieu de 0/100)
```

**Dans les phases (APRÈS génération) :**
```
Phase 1 : Impact 200-300 pips ✅ (au lieu de 54.9 pips)
Phase 2 : Impact 150-200 pips ✅ (au lieu de 24.9 pips)
          Pullback 80-120 pips ✅ (au lieu de 22 pips)
```

**Dans le graphique :**
```
Zone orange du pullback VISIBLE ✅ (~100 pips)
```

---

### TÂCHE 3 (BONUS) : Groupement automatique événements simultanés

**Problème observé :** Quand plusieurs événements sont à 14:30, le système crée une phase par événement au lieu de les grouper.

**Solution :** Grouper par timestamp avant d'envoyer à `sequence_multi_event_timeline_v86`.

**Priorité :** MOYENNE (après TÂCHE 1-2)

---

## 📊 MÉTRIQUES DE SUCCÈS

### Critères de validation

**✅ SUCCÈS si :**
- Score calendrier : 70-95/100 pour événements HIGH
- Impact Phase 1 : 150-350 pips
- Impact Phase 2 : 100-250 pips
- Pullback : 60-140 pips
- Zone orange visible dans graphique

**❌ ÉCHEC si :**
- Score reste à 0/100
- Impacts < 100 pips
- Pullback < 50 pips

---

## 🔄 SUIVI DES TOKENS

**Instructions pour Claude :**
- Indiquer les tokens **toutes les 3-4 réponses**
- Format : `Tokens : X / 190 000 (Y% utilisés, Z restants)`
- Alerter si > 150K tokens (79%)

---

## 📚 DOCUMENTS DE RÉFÉRENCE

### Rapport détaillé Session 5
```
RAPPORT_SESSION5_DIAGNOSTIC_COMPLET_SCORES.md
```
**Contient :** Diagnostic complet, fichiers identifiés, code à appliquer, structure des données.

### Scripts disponibles
```
validate_calendar_scores.py       - Valider scores DB
fix_calendar_scores.py            - Référence (même fix pour autre page)
```

---

## 💬 MESSAGE D'ACCUEIL POUR CLAUDE

Bonjour Claude !

Je reprends le travail sur le fix des scores empiriques dans le Planificateur Multi-Événements.

**Contexte :**
- Le pullback fonctionne mais les impacts sont trop faibles (54 pips au lieu de 200-300 pips)
- Cause : Les scores affichent 0/100 au lieu de 70-90/100
- Les scores EXISTENT dans la DB (validé avec `validate_calendar_scores.py`)
- Le code NE LIT PAS les scores de la DB

**Ce que j'attends de toi :**
1. Lire le rapport détaillé : `RAPPORT_SESSION5_DIAGNOSTIC_COMPLET_SCORES.md`
2. Créer le script `fix_multi_events_scores.py` basé sur `fix_calendar_scores.py`
3. M'aider à tester la correction
4. **Indiquer régulièrement les tokens utilisés** (toutes les 3-4 réponses)

**Fichier critique à modifier :**
```
fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py
```

**Fichier de référence (même fix, fonctionne) :**
```
fix_calendar_scores.py
```

Es-tu prêt à commencer ? 🚀

---

**Note importante :** Merci de **toujours indiquer les tokens** pour éviter de dépasser la limite !

---

**FIN TEXTE INTRO SESSION 6**
