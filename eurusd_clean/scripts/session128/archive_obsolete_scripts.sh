#!/bin/bash
# Script pour archiver scripts obsolètes Session 128

ARCHIVE_DIR="archive_before_db_fix"

echo "Archivage scripts obsolètes Session 128..."
echo ""

# Scripts test obsolètes
mv test_session115_ORIGINAL_adapted.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_session115_avec_estimate.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_session115_reproduced.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_double_wave_11sept_adapted.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_double_wave_final.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_1_mapping_variants_non_regression.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_2_pipeline_calibration_non_regression.py "$ARCHIVE_DIR/" 2>/dev/null
mv test_3_reference_case_11_sept.py "$ARCHIVE_DIR/" 2>/dev/null

# Scripts debug obsolètes
mv debug_11_sept.py "$ARCHIVE_DIR/" 2>/dev/null
mv debug_11_sept_all.py "$ARCHIVE_DIR/" 2>/dev/null
mv debug_economic_events.py "$ARCHIVE_DIR/" 2>/dev/null
mv debug_estimates.py "$ARCHIVE_DIR/" 2>/dev/null
mv debug_import_11sept.py "$ARCHIVE_DIR/" 2>/dev/null
mv debug_importance_format.py "$ARCHIVE_DIR/" 2>/dev/null
mv debug_join.py "$ARCHIVE_DIR/" 2>/dev/null
mv debug_tables.py "$ARCHIVE_DIR/" 2>/dev/null
mv debug_scores_divergence.py "$ARCHIVE_DIR/" 2>/dev/null

# Scripts check obsolètes
mv check_11sept_tables.py "$ARCHIVE_DIR/" 2>/dev/null
mv check_current_account_timestamp.py "$ARCHIVE_DIR/" 2>/dev/null
mv check_events_table.py "$ARCHIVE_DIR/" 2>/dev/null
mv check_forecast_previous.py "$ARCHIVE_DIR/" 2>/dev/null
mv check_jobless_raw_data.py "$ARCHIVE_DIR/" 2>/dev/null
mv check_jobless_timestamps.py "$ARCHIVE_DIR/" 2>/dev/null
mv check_tables.py "$ARCHIVE_DIR/" 2>/dev/null

# Scripts import obsolètes
mv import_eodhd_corrected.py "$ARCHIVE_DIR/" 2>/dev/null

# Scripts analysis obsolètes
mv analyze_eodhd_source.py "$ARCHIVE_DIR/" 2>/dev/null
mv analyze_raw_data.py "$ARCHIVE_DIR/" 2>/dev/null
mv inspect_country_codes.py "$ARCHIVE_DIR/" 2>/dev/null
mv investigate_exhaustive.py "$ARCHIVE_DIR/" 2>/dev/null
mv list_all_events_11sept.py "$ARCHIVE_DIR/" 2>/dev/null
mv show_all_columns.py "$ARCHIVE_DIR/" 2>/dev/null
mv verify_db_11sept.py "$ARCHIVE_DIR/" 2>/dev/null
mv verify_surprises.py "$ARCHIVE_DIR/" 2>/dev/null

# Scripts utilitaires obsolètes
mv migrate_country_codes.py "$ARCHIVE_DIR/" 2>/dev/null
mv run_all_tests.py "$ARCHIVE_DIR/" 2>/dev/null
mv launch_tests.sh "$ARCHIVE_DIR/" 2>/dev/null

echo "✅ Archivage terminé"
echo ""
echo "Scripts archivés dans: $ARCHIVE_DIR/"
echo "Scripts valides restants: 7"
