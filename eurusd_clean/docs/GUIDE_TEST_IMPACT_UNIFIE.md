# 🧪 GUIDE DE TEST - Impact Unifié (Beta)

**Date** : 2025-12-11  
**Version** : Beta (intégration parallèle dans le Planificateur)

---

## 📋 Objectif

Tester l'affichage et la cohérence de la nouvelle métrique **"Impact unifié (beta)"** dans l'UI du Planificateur, en comparaison avec **"Impact détecté"**.

---

## 🚀 Lancement de l'application

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
streamlit run streamlit_app/Home.py
```

---

## 📍 Navigation dans l'UI

1. **Accéder au Planificateur** : Cliquer sur "Planificateur V3.2" dans le menu latéral
2. **Sélectionner un événement** : Utiliser soit :
   - **Chemin Calendrier** : Sélectionner une date depuis le calendrier
   - **Chemin ADN** : Entrer une date manuellement et identifier le cluster

---

## 🎯 Cas de test recommandés

### Cas 1 : NFP "propre" (ratio ≈ 1.0)

**Date** : 2020-01-10, 2020-04-03, 2021-10-08, 2021-11-05

**Attendu** :
- Impact détecté ≈ Impact unifié (écart < 5 pips)
- Les deux mesures doivent être similaires

**Interprétation** : Le mouvement commence à peu près au moment de l'événement → Les deux définitions donnent des résultats cohérents.

---

### Cas 2 : NFP avec mouvement avant l'événement (ratio >> 1.0)

**Date** : 2024-03-08, 2024-10-04, 2024-06-07

**Attendu** :
- Impact détecté >> Impact unifié
- Exemple 2024-03-08 : Impact détecté ≈ 62 pips, Impact unifié ≈ 3 pips (ratio ≈ 21x)

**Interprétation** : Le mouvement détecté commence avant 14:30 → `impact_detecte` capture le mouvement complet, `impact_unified` mesure seulement depuis 14:30.

---

### Cas 3 : NFP avec gros mouvement après l'événement (ratio << 1.0)

**Date** : 2022-11-04, 2023-01-06, 2023-03-10

**Attendu** :
- Impact unifié >> Impact détecté
- Exemple 2022-11-04 : Impact détecté ≈ 39 pips, Impact unifié ≈ 146 pips (ratio ≈ 0.27x)

**Interprétation** : Le mouvement détecté est partiel, mais `impact_unified` capture le pic maximum dans les 120 minutes après l'événement.

---

## ✅ Checklist de validation

### Affichage UI

- [ ] Les deux métriques s'affichent côte à côte dans le bloc "🎯 Détection Pattern"
- [ ] "Impact détecté" affiche la valeur en pips
- [ ] "Impact unifié (beta)" affiche :
  - [ ] La valeur en pips
  - [ ] La direction avec emoji (⬆️ ou ⬇️)
  - [ ] Le tooltip explicatif au survol

### Cohérence des valeurs

- [ ] Sur les cas "propres" : Les deux valeurs sont similaires (< 5 pips d'écart)
- [ ] Sur les cas extrêmes : Les écarts correspondent aux ratios du rapport d'audit
- [ ] Aucune erreur dans la console Streamlit

### Cas limites

- [ ] Si `cluster_anchor_time` est `None` : "Impact unifié (beta)" affiche "N/A"
- [ ] Si le calcul échoue : "Impact unifié (beta)" affiche "N/A" (pas d'erreur visible)

---

## 🔍 Observation visuelle

**Recommandation** : Ouvrir le graphique de prix en parallèle pour observer visuellement :

1. **Baseline de l'impact détecté** : Où commence le segment détecté ?
2. **Baseline de l'impact unifié** : Où est l'open de la première bougie à 14:30 ?
3. **Pic de l'impact détecté** : Quel est le pic du segment détecté ?
4. **Pic de l'impact unifié** : Quel est le pic dans les 120 minutes après 14:30 ?

**Exemple 2024-03-08** :
- Impact détecté : Baseline probablement avant 14:30, pic vers 14:35-14:40
- Impact unifié : Baseline = open bougie 14:30, pic dans les 120 min après

---

## 📊 Comparaison avec le rapport d'audit

**Rapport** : `docs/RAPPORT_AUDIT_COMPARATIF_IMPACT.md`

**Vérifier** :
- Les ratios observés dans l'UI correspondent-ils aux ratios du rapport ?
- Les cas extrêmes identifiés dans le rapport sont-ils visibles dans l'UI ?

---

## ⚠️ Problèmes connus / Limitations

1. **Impact unifié non disponible** si :
   - `cluster_anchor_time` est `None` (chemin ADN sans cluster identifié)
   - Erreur lors du calcul (gestion silencieuse)

2. **Différences attendues** :
   - Les deux mesures peuvent différer significativement (c'est normal, elles mesurent des concepts différents)
   - L'objectif est de comparer les deux pour comprendre la différence

---

## 🎯 Prochaines étapes

Une fois les tests validés :

1. **Refonte de `measure_impact_from_finnhub()`** : Utiliser `calculate_impact_unified()` en interne
2. **Mise à jour du cache des clusters** : Recalculer avec la définition unifiée
3. **Migration progressive** : Remplacer progressivement les anciennes définitions

---

**Fin du guide**
