# 📖 GUIDE UTILISATEUR - PLANIFICATEUR V2

**Version :** 2.5 (Session 81 - Debug Mode)  
**Date :** 26 octobre 2025  
**Pour :** Utilisateurs finaux

---

## 🎯 QU'EST-CE QUE LE PLANIFICATEUR ?

Le **Planificateur V2** est une application qui prédit l'impact des événements économiques US (CPI, NFP, Fed Rates) sur la paire EUR/USD.

**Utilise :**
- 4 formules validées (précision 94-99%)
- 58,449 événements historiques
- Détection automatique du type de mouvement

**Prédit :**
- Impact en pips (amplitude mouvement)
- TTR (Time To React - temps de réaction)
- Pullback (correction après pic)
- Timeline complète du mouvement

---

## 🚀 DÉMARRAGE RAPIDE

### Étape 1 : Lancer l'Application

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app
streamlit run streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES_backup_session_72_copie.py
```

L'application s'ouvre dans votre navigateur (généralement `http://localhost:8501`)

### Étape 2 : Choisir une Date

1. Regardez le **date picker** au centre de l'écran
2. Cliquez dessus et sélectionnez une date avec événements US majeurs
3. Dates recommandées (validées) :
   - **11/09/2025** - 11 événements CPI ✅
   - **12/02/2025** - 8 événements CPI ✅
   - **01/08/2025** - 17 événements NFP ⏳

### Étape 3 : Calculer les Prédictions

1. Cliquez sur le bouton **"🎯 Calculer Prédictions"**
2. Attendez 1-3 secondes
3. Les résultats s'affichent automatiquement

---

## 📊 COMPRENDRE LES RÉSULTATS

### Section 1 : Métriques Principales

```
📈 IMPACT PRÉDIT : 57.3 pips
```
→ **Amplitude totale** du mouvement EUR/USD attendu

```
⏱️ TTR (TIME TO REACT) : 8.5 minutes
```
→ **Temps avant réaction maximale** du marché

```
📉 PULLBACK ESTIMÉ : 14.3 pips
```
→ **Correction** après le pic (retour partiel)

### Section 2 : Type de Mouvement

**Double Wave Momentum**
- Mouvement en 2 vagues successives
- Phase 1 → Pullback → Phase 2 (plus forte)
- Survient quand surprise > 20% + cluster ≥ 5 événements

**Single Wave Fort**
- Mouvement linéaire rapide
- Pic à T+8 minutes
- Stabilisation progressive
- Cas le plus fréquent (95%)

**Standard**
- Mouvement simple et court
- Peu d'événements ou faible surprise

### Section 3 : Graphique Timeline

Le graphique montre l'évolution prévue du prix EUR/USD :

**Axe X** : Temps (minutes après événement)  
**Axe Y** : Prix EUR/USD

**Lignes importantes :**
- 🟢 **Prix** : Évolution prévue
- 🔵 **Points clés** : Moments critiques (pic, pullback, stabilisation)
- ⭐ **Zones** : Phase 1, Phase 2 (si Double Wave)

### Section 4 : Événements Détectés

Tableau listant tous les événements HIGH IMPACT US trouvés pour la date :

- **Label** : Nom événement (ex: "CPI m/m")
- **Heure** : Heure publication (UTC+2 Berne)
- **Score** : Empirical score (impact historique)
- **Surprise** : Écart actual vs forecast (%)

---

## 🔍 MODE DEBUG (Optionnel)

### Activer le Mode Debug

Dans la **sidebar gauche** :
1. Cochez **"🔍 Mode Debug"**
2. Les logs détaillés apparaissent

### À Quoi Servent les Logs ?

**Pour utilisateurs avancés uniquement.**

Les logs affichent :
- Date sélectionnée et format
- Nombre d'événements chargés
- Détails calculs intermédiaires
- Type mouvement détecté
- Étapes création graphique

**Quand l'utiliser :**
- ✅ Vérifier que la bonne date est utilisée
- ✅ Comprendre pourquoi peu/beaucoup d'événements
- ✅ Déboguer si problème
- ❌ Pas nécessaire usage normal

---

## 📅 TROUVER LES BONNES DATES

### Dates Validées (Garanties) ✅

Ces dates ont été testées et fonctionnent parfaitement :

| Date | Événements | Type | Description |
|------|------------|------|-------------|
| **11/09/2025** | 11 CPI | Double Wave | Référence validée |
| **12/02/2025** | 8 CPI | Single Wave Fort | Validé Session 81 |

### Dates Recommandées ⏳

Ces dates devraient fonctionner (à confirmer) :

| Date | Événements | Type | Description |
|------|------------|------|-------------|
| **01/08/2025** | 17 NFP | Double Wave | Cas extrême NFP |
| **10/04/2024** | 10 CPI | Single Wave Fort | CPI historique |
| **18/12/2024** | 13 Rates | Double Wave | Décisions Fed/BCE |

### Comment Identifier une Bonne Date ?

**✅ Bonnes dates :**
- Jour de publication CPI (10-15 du mois)
- Premier vendredi du mois (NFP)
- Meetings Fed (8 fois/an)
- Dates avec 5+ événements HIGH IMPACT US

**❌ Dates à éviter :**
- Weekends (samedi/dimanche)
- Jours fériés US majeurs
- Dates sans événements économiques

### Ressources

📖 **Guide complet dates :** `GUIDE_DATES_DISPONIBLES.md`  
🔧 **Script liste dates :** `scripts/session82/list_available_dates.py`

---

## ⚠️ LIMITATIONS & PRÉCAUTIONS

### Ce que le Planificateur FAIT

✅ **Prédit l'impact moyen** basé sur données historiques  
✅ **Identifie le type de mouvement** (Double Wave vs Single Wave)  
✅ **Estime la timeline** (TTR, pullback, stabilisation)  
✅ **Agrège multi-événements** (somme vectorielle)

### Ce que le Planificateur NE FAIT PAS

❌ **Prédit la direction** exacte (UP/DOWN)  
❌ **Garantit le résultat** (marchés imprévisibles)  
❌ **Prend en compte** sentiment marché ou contexte géopolitique  
❌ **Remplace l'analyse** d'un trader professionnel

### Important à Savoir

⚠️ **Les prédictions sont des estimations** basées sur comportements passés  
⚠️ **Les marchés peuvent réagir différemment** selon contexte  
⚠️ **La surprise réelle** (actual vs forecast) affecte fortement l'impact  
⚠️ **Direction prédite** peut être inversée (formule donne amplitude)

### Usage Recommandé

✅ **Planification trading** - Identifier jours à fort potentiel  
✅ **Gestion risque** - Ajuster stops selon impact prédit  
✅ **Analyse événements** - Comprendre importance relative  
✅ **Backtesting stratégies** - Valider approches sur dates passées

❌ **Ne PAS utiliser comme seul signal** de trading  
❌ **Ne PAS ignorer** autres facteurs (technique, sentiment)  
❌ **Ne PAS trader** sans stop loss / gestion risque

---

## 🐛 RÉSOLUTION PROBLÈMES

### Problème : "0 événements trouvés"

**Causes possibles :**
- Date n'a pas d'événements HIGH IMPACT US
- Date trop ancienne (< 2024) ou future (> 2025)
- Jour férié US ou weekend

**Solution :**
1. Vérifier que la date est bien un jour ouvré US
2. Consulter `GUIDE_DATES_DISPONIBLES.md` pour dates confirmées
3. Essayer une date validée (11/09/2025 ou 12/02/2025)

---

### Problème : "Graphique ne s'affiche pas"

**Causes possibles :**
- Erreur calcul prédictions
- Données événements incomplètes
- Bug création graphique Plotly

**Solution :**
1. Activer **Mode Debug** dans sidebar
2. Lire les logs pour identifier l'erreur
3. Vérifier que les événements ont actual/forecast
4. Essayer une autre date

---

### Problème : "Calcul trop lent" (> 10 secondes)

**Causes possibles :**
- Beaucoup d'événements (15+)
- Connexion DB lente
- Ressources système limitées

**Solution :**
1. Attendre fin du calcul (peut prendre jusqu'à 10s pour 17 événements)
2. Fermer autres applications gourmandes
3. Normal pour dates NFP extrêmes (17 événements)

---

### Problème : "Date ne change pas"

**Status :** ✅ Corrigé Session 81 (Heisenbug)

**Si persiste :**
1. Activer Mode Debug
2. Vérifier que la date affichée correspond
3. Recharger page (F5)
4. Redémarrer Streamlit

---

## 📚 RESSOURCES SUPPLÉMENTAIRES

### Documentation Technique

- `PROJECT_STATE.md` - État global du projet
- `SESSION81_RAPPORT_COMPLET.md` - Correction Heisenbug
- `GUIDE_TEST_PLANIFICATEUR_SESSION82.md` - Tests validation

### Scripts Utiles

```bash
# Lister dates disponibles
python3 eurusd_clean/scripts/session82/list_available_dates.py

# Tester planificateur (dev)
python3 eurusd_clean/scripts/session82/test_planificateur_multi_dates.py
```

### Fichiers Importants

**Planificateur :**
```
fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES_backup_session_72_copie.py
```

**Base de données :**
```
fx_impact_app/data/warehouse.duckdb
```

**Formules validées :**
```
fx_impact_app/src/formulas_validated.py
```

---

## 🎯 CHECKLIST PREMIÈRE UTILISATION

### Avant de Commencer

- [ ] Python 3.8+ installé
- [ ] Streamlit installé (`pip install streamlit`)
- [ ] Plotly installé (`pip install plotly`)
- [ ] DuckDB installé (`pip install duckdb`)
- [ ] Fichier `warehouse.duckdb` présent (205 MB)

### Premier Test

- [ ] Lancer application Streamlit
- [ ] Page s'ouvre dans navigateur
- [ ] Sélectionner **11/09/2025**
- [ ] Cliquer **"Calculer Prédictions"**
- [ ] Vérifier : 11 événements trouvés
- [ ] Vérifier : Graphique s'affiche
- [ ] Vérifier : Impact ~57 pips

### Test Changement Date

- [ ] Sélectionner **12/02/2025**
- [ ] Cliquer **"Calculer Prédictions"**
- [ ] Vérifier : 8 événements trouvés
- [ ] Vérifier : Graphique différent
- [ ] Vérifier : Impact ~45 pips

### Si Tout Fonctionne

✅ **Le planificateur est prêt à l'emploi !**

Vous pouvez maintenant :
- Tester d'autres dates
- Consulter `GUIDE_DATES_DISPONIBLES.md` pour plus de dates
- Explorer le Mode Debug

---

## 💡 ASTUCES & BONNES PRATIQUES

### Astuce 1 : Planifier à l'Avance

📅 Consultez le calendrier économique US pour identifier dates CPI/NFP/Fed  
🎯 Testez les prédictions 1-2 jours avant l'événement  
⏰ Ajustez votre stratégie selon impact prédit

### Astuce 2 : Comparer Plusieurs Dates

📊 Testez plusieurs dates CPI pour voir variation d'impact  
📈 Identifiez patterns (NFP toujours > CPI par exemple)  
🔄 Validez cohérence prédictions sur dates similaires

### Astuce 3 : Analyser les Graphiques

🟢 **Double Wave** → 2 opportunités entrée (Phase 1 et Phase 2)  
🔵 **Single Wave Fort** → Entrée rapide au démarrage  
⚪ **Standard** → Mouvement court, moins intéressant

### Astuce 4 : Utiliser avec MT5

📍 Ouvrir MT5 sur EUR/USD  
⏱️ Synchroniser avec heure événement  
📊 Comparer prédiction vs réalité après événement  
📈 Valider précision formules

### Astuce 5 : Combiner avec Analyse Technique

🎯 Utiliser prédictions pour **taille position**  
📊 Combiner avec **niveaux support/résistance**  
⚡ Éviter trading contre **tendance forte** existante  
🔔 Ajuster **stops** selon pullback prédit

---

## 📞 SUPPORT & FEEDBACK

### Questions Fréquentes

**Q : Puis-je utiliser pour autres paires (GBP/USD, USD/JPY) ?**  
R : Non, formules calibrées uniquement pour EUR/USD + événements US

**Q : Les prédictions sont-elles fiables ?**  
R : Précision 94-99% sur amplitude (pas direction). Usage indicatif uniquement.

**Q : Puis-je ajouter d'autres dates ?**  
R : Oui ! Dates avec événements HIGH IMPACT US dans warehouse.duckdb

**Q : Comment améliorer les prédictions ?**  
R : Formules déjà optimisées (Sessions 51-55). Améliorations futures possibles.

### Feedback

Pour signaler bugs ou suggestions :
- Documenter le problème précisément
- Inclure date testée et résultats
- Activer Mode Debug et copier logs
- Créer rapport dans `eurusd_clean/docs/`

---

## 🏆 HISTORIQUE VERSIONS

### v2.5 - Session 81 (26 octobre 2025)

✅ **Heisenbug résolu** - Problème date figée corrigé  
✅ **Mode Debug ajouté** - Toggle sidebar optionnel  
✅ **Gestion erreurs** - Try/catch graphiques  
✅ **Multi-dates fonctionnel** - Changement date opérationnel

### v2.4 - Session 68

✅ **Single Wave Fort** - Détection automatique  
✅ **Timeline T+8 peak** - Modèle validé 8/10 dates

### v2.0 - Sessions 51-55

✅ **Formules validées** - 4 formules précision 94-99%  
✅ **Somme vectorielle** - Multi-événements  
✅ **Facteur 0.758** - Correction empirique

---

*Guide créé Session 82 - 26 octobre 2025*  
*Version Planificateur : 2.5 (Debug Mode)*  
*Pour questions : Consulter documentation technique*
