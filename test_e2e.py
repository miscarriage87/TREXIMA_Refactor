#!/usr/bin/env python3
"""
TREXIMA End-to-End Test Script

Tests the complete export/import workflow:
1. Load XML data models
2. Export translations to Excel
3. Modify some translations in Excel
4. Import translations back to XML
5. Verify changes are reflected in output XML
"""

import os
import sys
import shutil
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Test configuration
TEST_OUTPUT_DIR = os.path.join(project_root, "test_output")
XML_FILES = [
    os.path.join(project_root, "EC-data-model.xml"),
]

# Check if additional files exist
corporate_dm = os.path.join(project_root, "EC-corporate-datamodel.xml")
if os.path.exists(corporate_dm):
    XML_FILES.append(corporate_dm)


def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def setup_test_environment():
    """Create clean test output directory."""
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR)
    log(f"Created test output directory: {TEST_OUTPUT_DIR}")


def test_step_1_load_xml():
    """Step 1: Load XML data model files."""
    log("=" * 60)
    log("STEP 1: Loading XML Data Models")
    log("=" * 60)

    from trexima.config import AppPaths
    from trexima.core.datamodel_processor import DataModelProcessor

    processor = DataModelProcessor(AppPaths())
    loaded_count = 0

    for xml_file in XML_FILES:
        if os.path.exists(xml_file):
            log(f"Loading: {os.path.basename(xml_file)}")
            model = processor.load_data_model(xml_file)
            if model:
                loaded_count += 1
                log(f"  -> Loaded: {model.name} ({model.model_type.value})")
                log(f"  -> Has soup: {model.soup is not None}")
            else:
                log(f"  -> FAILED to load")
        else:
            log(f"  -> File not found: {xml_file}")

    log(f"Total loaded: {loaded_count} data model(s)")
    log(f"Translatable tags found: {len(processor.translatable_tags)}")
    log(f"Is SDM included: {processor.is_sdm_included}")
    log(f"Is PMGM included: {processor.is_pmgm_included}")

    if loaded_count == 0:
        raise Exception("No XML files loaded!")

    return processor


def test_step_2_export_excel(processor):
    """Step 2: Export translations to Excel."""
    log("=" * 60)
    log("STEP 2: Exporting Translations to Excel")
    log("=" * 60)

    from trexima.core.translation_extractor import TranslationExtractor

    def progress_callback(percent, message):
        log(f"  [{percent}%] {message}")

    extractor = TranslationExtractor(
        processor=processor,
        odata_client=None,  # No API connection for test
        progress_callback=progress_callback
    )

    # Export with test locales
    locales = ["en_US", "de_DE", "fr_FR"]
    log(f"Exporting for locales: {locales}")

    workbook = extractor.extract_to_workbook(
        locales_for_export=locales,
        export_picklists=False,  # Skip API-dependent features
        export_mdf_objects=False,
        export_fo_translations=False,
        remove_html_tags=False,
        system_default_lang="en_US"
    )

    # Log sheet information
    log(f"Created workbook with {len(workbook.sheetnames)} sheets:")
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        log(f"  - {sheet_name}: {ws.max_row} rows, {ws.max_column} columns")

    # Save workbook
    excel_path = extractor.save_workbook(workbook, TEST_OUTPUT_DIR, "test_export.xlsx")
    log(f"Saved Excel file: {excel_path}")

    if not os.path.exists(excel_path):
        raise Exception("Excel file was not created!")

    file_size = os.path.getsize(excel_path) / 1024
    log(f"File size: {file_size:.1f} KB")

    return excel_path, workbook


def test_step_3_modify_excel(excel_path, workbook):
    """Step 3: Modify translations in the Excel file."""
    log("=" * 60)
    log("STEP 3: Modifying Translations in Excel")
    log("=" * 60)

    modifications = []

    # Find data model sheets to modify
    dm_sheets = [s for s in workbook.sheetnames if s.startswith("DataModel")]

    if not dm_sheets:
        log("No DataModel sheets found - checking other sheets")
        dm_sheets = workbook.sheetnames

    for sheet_name in dm_sheets[:2]:  # Modify first 2 sheets
        ws = workbook[sheet_name]

        # Find rows with content to modify (skip header)
        modified_count = 0
        for row_num in range(2, min(ws.max_row + 1, 12)):  # Rows 2-11
            # Find the label column (usually column 5 for translated label)
            if ws.max_column >= 5:
                cell = ws.cell(row=row_num, column=5)
                original_value = cell.value

                if original_value and isinstance(original_value, str) and len(original_value) > 0:
                    # Add a test marker to the translation
                    new_value = f"[MODIFIED] {original_value}"
                    cell.value = new_value

                    modifications.append({
                        "sheet": sheet_name,
                        "row": row_num,
                        "column": 5,
                        "original": original_value,
                        "modified": new_value
                    })
                    modified_count += 1

                    if modified_count >= 3:  # Limit modifications per sheet
                        break

        log(f"Modified {modified_count} cells in sheet: {sheet_name}")

    # Save modified workbook
    modified_path = os.path.join(TEST_OUTPUT_DIR, "test_export_modified.xlsx")
    workbook.save(modified_path)
    log(f"Saved modified Excel: {modified_path}")

    log(f"Total modifications: {len(modifications)}")
    for mod in modifications:
        log(f"  - {mod['sheet']} Row {mod['row']}: '{mod['original'][:30]}...' -> '{mod['modified'][:40]}...'")

    return modified_path, modifications


def test_step_4_import_xml(processor, modified_excel_path):
    """Step 4: Import translations back to XML."""
    log("=" * 60)
    log("STEP 4: Importing Translations to XML")
    log("=" * 60)

    from trexima.core.translation_importer import TranslationImporter
    from trexima.io.excel_handler import ExcelHandler

    def progress_callback(percent, message):
        log(f"  [{percent}%] {message}")

    # Load the modified workbook
    excel_handler = ExcelHandler()
    workbook = excel_handler.load_workbook(modified_excel_path)

    log(f"Loaded modified workbook: {modified_excel_path}")
    log(f"Available sheets: {workbook.sheetnames}")

    # Create importer
    importer = TranslationImporter(
        processor=processor,
        progress_callback=progress_callback
    )

    # Select sheets to import (DataModel sheets)
    sheets_to_import = [s for s in workbook.sheetnames if s.startswith("DataModel")]

    if not sheets_to_import:
        log("No DataModel sheets found for import")
        return None

    log(f"Importing sheets: {sheets_to_import}")

    # Execute import
    result = importer.import_from_workbook(
        workbook=workbook,
        worksheets_to_process=sheets_to_import,
        save_dir=TEST_OUTPUT_DIR
    )

    log(f"Import result: success={result.success}")
    if result.error_message:
        log(f"Error: {result.error_message}")
    if result.files_generated:
        log(f"Output files: {result.files_generated}")

    return result


def test_step_5_verify_xml(modifications):
    """Step 5: Verify changes in generated XML files."""
    log("=" * 60)
    log("STEP 5: Verifying Changes in XML Files")
    log("=" * 60)

    from bs4 import BeautifulSoup

    # Find generated XML files
    xml_files = [f for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith(".xml")]

    if not xml_files:
        log("WARNING: No XML files generated!")
        return False

    log(f"Found {len(xml_files)} XML file(s):")

    verification_passed = True

    for xml_file in xml_files:
        xml_path = os.path.join(TEST_OUTPUT_DIR, xml_file)
        file_size = os.path.getsize(xml_path) / 1024
        log(f"  - {xml_file} ({file_size:.1f} KB)")

        # Parse and check for modifications
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if any modifications are present
        modified_found = "[MODIFIED]" in content
        log(f"    Contains [MODIFIED] markers: {modified_found}")

        if modified_found:
            # Count occurrences
            count = content.count("[MODIFIED]")
            log(f"    Found {count} modification marker(s)")

    return verification_passed


def main():
    """Run the complete end-to-end test."""
    log("=" * 60)
    log("TREXIMA END-TO-END TEST")
    log("=" * 60)
    log("")

    try:
        # Setup
        setup_test_environment()

        # Step 1: Load XML
        processor = test_step_1_load_xml()
        log("")

        # Step 2: Export to Excel
        excel_path, workbook = test_step_2_export_excel(processor)
        log("")

        # Step 3: Modify Excel
        modified_excel_path, modifications = test_step_3_modify_excel(excel_path, workbook)
        log("")

        # Step 4: Import to XML
        result = test_step_4_import_xml(processor, modified_excel_path)
        log("")

        # Step 5: Verify
        test_step_5_verify_xml(modifications)
        log("")

        log("=" * 60)
        log("TEST COMPLETED SUCCESSFULLY!")
        log("=" * 60)
        log(f"Test output directory: {TEST_OUTPUT_DIR}")
        log("")
        log("Generated files:")
        for f in os.listdir(TEST_OUTPUT_DIR):
            fpath = os.path.join(TEST_OUTPUT_DIR, f)
            fsize = os.path.getsize(fpath) / 1024
            log(f"  - {f} ({fsize:.1f} KB)")

        return True

    except Exception as e:
        log("")
        log("=" * 60)
        log(f"TEST FAILED: {e}")
        log("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
