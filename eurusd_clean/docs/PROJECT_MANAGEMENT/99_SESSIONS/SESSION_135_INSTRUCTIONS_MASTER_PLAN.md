# INSTRUCTIONS MISE À JOUR MASTER_PLAN.md - Session 135

**À faire manuellement par André**

---

## 📝 MODIFICATIONS À EFFECTUER

### **Fichier à modifier :**
```
/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md
```

---

## 1️⃣ HEADER (en haut du fichier)

**CHERCHER :**
```markdown
**Version :** X.Y
**Date :** [Date précédente]
**Statut :** [Statut précédent]
```

**REMPLACER PAR :**
```markdown
**Version :** X.Y+1
**Date :** 14 novembre 2025 - Session 135
**Statut :** Planificateur V3.0 fonctionnel (75% taux prédiction), workflow LOO-CV documenté pour Session 136
```

**Note :** Remplacer X.Y+1 par le nouveau numéro de version (exemple : si actuel 2.5 → mettre 2.6)

---

## 2️⃣ SECTION SESSIONS (après dernière session mentionnée)

**AJOUTER cette section :**

```markdown
**🚀 Session 135 RÉALISÉE (✅ SUCCÈS) :**
- ✅ Investigation doublons DB : Variantes MoM/YoY/U3/U6 légitimes validées
- ✅ Ajustement seuil doublewave_prediction.py : 350 → 650 points (accommode variantes)
- ✅ Tests Planificateur V3.0 : 3/4 SUCCESS (75% taux prédiction)
- ✅ MAE Test 11.09.2025 : 2.4 pips (référence MT5 56.2 pips)
- ✅ Documentation DB_STRUCTURE.md : Référence permanente structure warehouse.duckdb
- ⚠️ Limitation identifiée : Amplification fixe 0.1201 pas optimale (Test 18.12.2024 erreur -87 pips)
- 🎯 Prochaine : Session 136 (Workflow LOO-CV complet pour calibrer formule amp(R²) spécifique DoubleWave_Overlap)
```

**Placement :** Ajouter après la dernière session mentionnée dans MASTER_PLAN.md, avant la section "Prochaines étapes" ou "Roadmap"

---

## 3️⃣ FOOTER (fin du fichier)

**CHERCHER :**
```markdown
**Dernière mise à jour :** [Date précédente] - Session XXX ([Statut])

**Version :** X.Y
**Session :** XXX ([Résumé])
```

**REMPLACER PAR :**
```markdown
**Dernière mise à jour :** 14 novembre 2025 - Session 135 (✅ SUCCÈS)

**Version :** X.Y+1
**Session :** 135 (Planificateur V3.0 fonctionnel 75% taux prédiction, workflow LOO-CV documenté Session 136)
```

**Note :** X.Y+1 = même numéro de version qu'au header

---

## ✅ VALIDATION MODIFICATIONS

Après modifications, vérifier :

- [ ] Version incrémentée (X.Y → X.Y+1) dans header ET footer
- [ ] Date mise à jour : 14 novembre 2025
- [ ] Section Session 135 ajoutée avec bullet points
- [ ] Footer mis à jour avec résumé Session 135
- [ ] Cohérence numéros version (header = footer)

---

## 📊 RÉSUMÉ SESSION 135 (pour référence)

**Accomplissements :**
- Investigation doublons DB → Variantes légitimes validées
- Ajustement seuil 350 → 650 points
- Tests Planificateur V3.0 : 75% SUCCESS, MAE 2.4 pips
- Documentation DB_STRUCTURE.md créée

**Préparation Session 136 :**
- Workflow LOO-CV documenté (8 étapes)
- SESSION_136_HANDOFF.md créé
- DEMARRAGE_SESSION_136.md créé (message copier-coller)
- Infrastructure prête (detect_inversion, detect_pattern)

**Objectif Session 136 :**
Calibrer formule amplification dynamique amp(R²) spécifique DoubleWave_Overlap via workflow LOO-CV complet.

---

**Date :** 14 novembre 2025  
**Auteur :** André Valentin avec Claude  
**Session :** 135  
**Statut :** ✅ Instructions prêtes
