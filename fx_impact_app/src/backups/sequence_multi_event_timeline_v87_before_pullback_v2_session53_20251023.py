"""
Module pour créer une timeline séquentielle avec SOMME VECTORIELLE
Version 8.7.2 : Multiplicateur non-linéaire OPTIMISÉ (Session 15)

BACKUP AVANT MODIFICATION PULLBACK V2 - SESSION 53 (23 octobre 2025)
=======================================================================
Ce backup contient la version avec calculate_pullback() LINÉAIRE (4% /min)
AVANT l'implémentation de calculate_pullback_v2() LOGARITHMIQUE (Session 53)

Raison backup: Implémentation formule pullback avancée (logarithmique)
Ancienne formule: 4% par minute (MAE 12.1 pips)
Nouvelle formule: 0.30 × ln(minutes + 1) (MAE 0.2 pips)
"""

# [CONTENU ORIGINAL SAUVEGARDÉ - Voir fichier sequence_multi_event_timeline_v87.py pour version actuelle]
