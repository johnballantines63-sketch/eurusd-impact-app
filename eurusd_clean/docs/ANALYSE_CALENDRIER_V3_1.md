# ANALYSE CALENDRIER V3.1 — Pourquoi S1 Sous-Performe

**Date :** 2025-12-12  
**Contexte :** Validation V3.1

---

## 1. OBSERVATION

**Résultat walk-forward :**
- S0_baseline (V2.1) : Spearman 0.1644
- S1_calendar (V2.1 + calendrier) : Spearman 0.1103
- **Delta : -0.0541** ❌

Le calendrier seul **dilue le signal** au lieu de l'améliorer.

---

## 2. HYPOTHÈSES (Saines)

### 2.1 Calendrier Non Conditionnel

**Le calendrier est non conditionnel :**
- Un lundi n'est pas "à risque" en soi
- Un vendredi n'est dangereux que si le régime est déjà tendu
- Un début de mois n'est pas systématiquement volatil

**Les effets calendrier sont interactionnels, pas linéaires.**

### 2.2 Dilution du Signal

**Ajouter des features non conditionnelles peut :**
- Diluer le signal principal (score V2.1)
- Introduire du bruit si les patterns calendrier ne sont pas pertinents
- Faire sur-ajuster le modèle Ridge sur des corrélations spurious

---

## 3. VALIDATION : Calendrier Utile en Interaction

**Observation :**
- S2_regime seul : Spearman 0.2469 (+0.0826 vs S0)
- S3_full (calendrier + régime) : Spearman 0.3158 (+0.1515 vs S0)

**Conclusion :** Le calendrier apporte de la valeur **en combinaison avec le régime**, pas seul.

**Interprétation :**
- Le calendrier conditionne l'effet du régime
- Exemple : Vendredi + régime haute volatilité = risque très élevé
- Mais : Vendredi seul (sans contexte régime) = pas de signal

---

## 4. INTERACTIONS POSSIBLES (À Explorer V3.4)

**Interactions probables :**
- `regime_high × is_fri` : Vendredi en régime tendu
- `regime_low × is_mon` : Lundi en régime calme
- `regime_high × is_month_end` : Fin de mois en régime tendu

**Statut :** À explorer en V3.4 si nécessaire. Pour V3.1, le modèle composite S3_full capture déjà ces interactions implicitement via Ridge.

---

## 5. CONCLUSION

**Le calendrier seul (S1) sous-performe car :**
1. Il est non conditionnel (pas de signal intrinsèque)
2. Il dilue le signal principal (score V2.1)
3. Les effets calendrier sont interactionnels avec le régime

**Le calendrier est utile en combinaison avec le régime (S3_full) car :**
1. Il conditionne l'effet du régime
2. Le modèle Ridge capture les interactions implicitement
3. Le gain S3 vs S2 confirme cette hypothèse

**Décision V3.1 :**
- ❌ Calendrier seul (S1) : NON RETENU
- ✅ Modèle composite (S3_full) : RETENU

---

**Document créé le :** 2025-12-12  
**Version :** V3.1

