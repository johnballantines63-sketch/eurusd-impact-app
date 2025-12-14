# ⚡ START HERE SESSION 24

**🔥 ACTION IMMÉDIATE REQUISE**

---

## 📋 LECTURE OBLIGATOIRE (15 min)

**Lis dans cet ordre :**

1. **MESSAGE_POUR_CLAUDE_SESSION24.md** (10 min) ⭐⭐⭐
   - Contexte complet
   - Plan d'action détaillé
   - Scripts à utiliser

2. **RAPPORT_SESSION23_FINAL.md** (5 min) ⭐⭐
   - Diagnostic Session 23
   - Problème identifié
   - Fichiers créés

---

## 🎯 MISSION SESSION 24

**PRIORITÉ ABSOLUE : Réimporter prices_1m depuis EODHD**

**Problème :** Les données prices_1m actuelles sont incorrectes
- 11 septembre donne 18-36 pips
- Devrait donner ~522 pips (référence MT5 Session 20)
- Écart ×27 !

**Solution :** Réimporter depuis EODHD API

---

## ✅ CHECKLIST SESSION 24

### Phase 1 : Import prix (30-45 min) 🔥
- [ ] Identifier script import EODHD
- [ ] Configurer pour EURUSD 1 minute
- [ ] Importer septembre 2025 minimum
- [ ] **VALIDER 11 septembre = ~522 pips** ✅

### Phase 2 : Recalcul mouvements (30 min)
- [ ] Exécuter `calculate_extreme_cases_session23.py`
- [ ] Vérifier 11 septembre : 522 pips Phase 1, 114 pips Pullback
- [ ] CSV avec 944 cas corrects

### Phase 3 : Formule V4 (30 min)
- [ ] Analyser patterns empiriques
- [ ] Créer formule V4 basée données réelles
- [ ] Pas de seuils arbitraires

### Phase 4 : Implémentation (30 min)
- [ ] Modifier `sequence_multi_event_timeline_v87.py`
- [ ] Tester 11 septembre : erreur <30%
- [ ] Validation autres cas

### Phase 5 : Rapport (30 min)
- [ ] Créer RAPPORT_SESSION24_FINAL.md
- [ ] Documenter formule V4
- [ ] Message Session 25

---

## 🔥 VALIDATION CRITIQUE

**Après import EODHD, teste IMMÉDIATEMENT :**

```python
# 11 septembre 2025 14:30-14:45
# DOIT donner ~522 pips ±50 pips

if 450 < phase1_pips < 600:
    print("✅ OK - Continuer")
else:
    print("❌ STOP - Investiguer")
```

**Si échec → ARRÊTE et documente pourquoi**

---

## 📊 DONNÉES RÉFÉRENCE

**11 septembre 2025 (MT5 Session 20) :**
- Phase 1 : **522 pips** ⬆️
- Pullback : **114 pips** ⬇️
- Impact NET : **408 pips**
- Surprise : **33.3%**
- Score : **46.13**

**Ces chiffres sont la VÉRITÉ ABSOLUE**

---

## 📁 SCRIPTS PRÊTS

**À réutiliser :**
- `calculate_extreme_cases_session23.py` ⭐
- `analyze_empirical_v4_session23.py`
- 8 autres scripts de diagnostic

**Ne recrée PAS les scripts. Réutilise !**

---

## ⏱️ TEMPS ESTIMÉ

**Total Session 24 : 2h30-3h**
- Import + validation : 45 min
- Recalcul : 30 min
- Analyse + V4 : 60 min
- Implémentation : 30 min
- Rapport : 30 min

---

## ⚠️ PIÈGES

❌ Ne commence PAS par la formule  
❌ N'accepte PAS des données ~36 pips  
❌ N'oublie PAS le décalage horaire UTC  
❌ Ne sur-optimise PAS sur 11 sept uniquement  

---

**COMMENCE PAR LIRE MESSAGE_POUR_CLAUDE_SESSION24.md** 📖

**GO ! 🚀**
