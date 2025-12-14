@echo off
REM LAUNCHER VALIDATION PHASE 1 - SESSION 130
REM ==========================================
REM Lance validation rapide puis propose scan complet

cd /d "%~dp0..\.."

echo ================================================================================
echo LAUNCHER PHASE 1 - SESSION 130
echo ================================================================================
echo.
echo 🎯 Étape 1 : VALIDATION RAPIDE (quelques secondes)
echo    Tests infrastructure sur 3 dates connues
echo.

REM Lancer validation rapide
python scripts\session130\validate_phase1_quick.py

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo ✅ VALIDATION RÉUSSIE
    echo ================================================================================
    echo.
    echo 🚀 Prêt à lancer SCAN COMPLET 2023-2025
    echo.
    echo ⏱️  Durée estimée : ~45 minutes
    echo 📊 Output : ~100-150 mouvements détectés
    echo.
    
    set /p REPLY="Lancer SCAN COMPLET maintenant ? (o/n) "
    
    if /i "%REPLY%"=="o" (
        echo.
        echo 🚀 LANCEMENT SCAN COMPLET...
        echo.
        python scripts\session130\run_phase1.py
        
        IF %ERRORLEVEL% EQU 0 (
            echo.
            echo ================================================================================
            echo ✅✅✅ PHASE 1 TERMINÉE AVEC SUCCÈS ✅✅✅
            echo ================================================================================
            echo.
            echo 📂 Fichiers créés :
            echo    ✅ scripts\session130\movements_2023_2025_complete.json
            echo    ✅ scripts\session130\patterns_classified.json
            echo    ✅ scripts\session130\reference_cases.json
            echo.
            echo 🎯 PROCHAINE ÉTAPE :
            echo    Revenir vers Claude avec résultats pour validation
            echo.
        ) else (
            echo.
            echo ❌ SCAN COMPLET ÉCHOUÉ
            echo    Vérifier logs ci-dessus
            echo.
        )
    ) else (
        echo.
        echo ⏸️  SCAN COMPLET ANNULÉ
        echo.
        echo Pour lancer plus tard :
        echo    python scripts\session130\run_phase1.py
        echo.
    )
) else (
    echo.
    echo ================================================================================
    echo ⚠️  VALIDATION PARTIELLE ou ÉCHOUÉE
    echo ================================================================================
    echo.
    echo Vérifier logs ci-dessus avant de continuer
    echo.
    echo Pour forcer scan complet quand même :
    echo    python scripts\session130\run_phase1.py
    echo.
)

pause
