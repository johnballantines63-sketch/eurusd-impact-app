#!/bin/bash

# Script lancement test formule V2.6 - Cas référence 11.09.2025
# Session 101.5 - Validation méthodologie

echo "=========================================="
echo "TEST FORMULE V2.6 - CAS RÉFÉRENCE"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

python3 test_formule_11sept.py

echo ""
echo "=========================================="
echo "Test terminé"
echo "=========================================="
