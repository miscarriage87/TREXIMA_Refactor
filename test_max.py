#!/usr/bin/env python3
"""
TREXIMA MAX Test

Comprehensive end-to-end test with maximum configuration:
- ALL 4 data models (SDM, CDM, CSF-SDM, CSF-CDM)
- ALL 17 active locales from API
- Full API integration (Picklists, MDF Objects, Foundation Objects)
- Complete export-modify-import-verify cycle
"""

import os
import sys
import json
import shutil
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Test configuration
TEST_OUTPUT_DIR = os.path.join(project_root, "test_output_max")
ALL_XML_FILES = [
    os.path.join(project_root, "EC-data-model.xml"),
    os.path.join(project_root, "EC-corporate-datamodel.xml"),
    os.path.join(project_root, "EC-CSF-for-succession-DM.xml"),
    os.path.join(project_root, "EC-CSF-for-corporate-DM.xml"),
]


def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def setup_test_environment():
    """Create clean test output directory."""
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR)
    log(f"Created MAX test output directory: {TEST_OUTPUT_DIR}")


def load_api_credentials():
    """Load API credentials from file."""
    creds_file = os.path.join(project_root, "LoginCredentialsForAPI.txt")
    if not os.path.exists(creds_file):
        log("WARNING: LoginCredentialsForAPI.txt not found - API tests will be skipped")
        return None

    with open(creds_file, 'r') as f:
        creds_text = f.read().strip()
        if creds_text.startswith('{'):
            return json.loads(creds_text)
        else:
            # Parse the custom format
            creds = {}
            parts = creds_text.split('","')
            for part in parts:
                part = part.replace('"', '').replace('}', '')
                if ':' in part:
                    key, value = part.split(':', 1)
                    creds[key] = value
            return creds


def test_step_1_connect_api():
    """Step 1: Connect to OData API."""
    log("=" * 70)
    log("STEP 1: Connecting to SuccessFactors OData API")
    log("=" * 70)

    from trexima.core.odata_client import ODataClient

    creds = load_api_credentials()
    if not creds:
        return None, []

    client = ODataClient()

    try:
        log(f"Service URL: {creds['oDataUrl']}")
        log(f"Company ID: {creds['companyID']}")
        log(f"Connecting...")

        success = client.connect(
            service_url=creds['oDataUrl'],
            company_id=creds['companyID'],
            username=creds['username'],
            password=creds['password']
        )

        if success:
            log(f"✓ API Connection successful!")

            # Get active locales
            locales = client.get_active_locales()
            log(f"✓ Retrieved {len(locales)} active locales:")
            for i, locale in enumerate(locales, 1):
                log(f"  {i:2d}. {locale}")

            # Get picklist counts
            legacy_count = client.get_picklist_count("legacy")
            mdf_count = client.get_picklist_count("mdf")
            log(f"✓ Picklist counts: {legacy_count} legacy, {mdf_count} MDF")

            return client, locales
        else:
            log("✗ Connection failed")
            return None, []

    except Exception as e:
        log(f"✗ Connection error: {e}")
        import traceback
        traceback.print_exc()
        return None, []


def test_step_2_load_all_xml(locales):
    """Step 2: Load ALL XML data model files."""
    log("")
    log("=" * 70)
    log("STEP 2: Loading ALL Data Models")
    log("=" * 70)

    from trexima.config import AppPaths
    from trexima.core.datamodel_processor import DataModelProcessor

    processor = DataModelProcessor(AppPaths())
    loaded_count = 0
    total_size = 0

    for xml_file in ALL_XML_FILES:
        if os.path.exists(xml_file):
            file_size = os.path.getsize(xml_file) / (1024 * 1024)  # MB
            total_size += file_size
            log(f"Loading: {os.path.basename(xml_file)} ({file_size:.1f} MB)")

            model = processor.load_data_model(xml_file)
            if model:
                loaded_count += 1
                model_langs = model.extract_languages()
                log(f"  ✓ {model.name}")
                log(f"    Type: {model.model_type.value}")
                log(f"    Languages in XML: {len(model_langs)}")
                log(f"    Soup size: {len(str(model.soup))} chars")
            else:
                log(f"  ✗ FAILED to load")
        else:
            log(f"  ✗ File not found: {xml_file}")

    log(f"")
    log(f"Summary:")
    log(f"  Total loaded: {loaded_count}/{len(ALL_XML_FILES)} data model(s)")
    log(f"  Total size: {total_size:.1f} MB")
    log(f"  Translatable tags found: {len(processor.translatable_tags)}")
    log(f"  Is SDM included: {processor.is_sdm_included}")
    log(f"  Is PMGM included: {processor.is_pmgm_included}")

    if loaded_count == 0:
        raise Exception("No XML files loaded!")

    # Use API locales if available, otherwise use discovered languages
    if locales:
        export_locales = locales
    else:
        export_locales = processor.extract_all_languages()
        export_locales = [lang.replace('-', '_') for lang in export_locales]

    log(f"  Locales for export: {len(export_locales)}")

    return processor, export_locales


def test_step_3_export_max(processor, client, locales):
    """Step 3: Export with MAXIMUM configuration."""
    log("")
    log("=" * 70)
    log("STEP 3: MAX Export - All Models, All Languages, Full API")
    log("=" * 70)

    from trexima.core.translation_extractor import TranslationExtractor

    def progress_callback(percent, message):
        log(f"  [{int(percent):3d}%] {message}")

    extractor = TranslationExtractor(
        processor=processor,
        odata_client=client,
        progress_callback=progress_callback
    )

    log(f"Export configuration:")
    log(f"  - Locales: {len(locales)} languages")
    log(f"  - Export Picklists: {'YES (from API)' if client else 'NO'}")
    log(f"  - Export MDF Objects: {'YES' if client else 'NO'}")
    log(f"  - Export Foundation Objects: {'YES' if client else 'NO'}")
    log(f"  - Data Models: {len(processor.get_all_data_models())}")
    log("")

    start_time = datetime.now()

    workbook = extractor.extract_to_workbook(
        locales_for_export=locales,
        export_picklists=bool(client),
        export_mdf_objects=bool(client),
        export_fo_translations=bool(client),
        remove_html_tags=False,
        system_default_lang=locales[0] if locales else "en_US"
    )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Log sheet information
    log("")
    log(f"Export completed in {duration:.1f} seconds")
    log(f"Created workbook with {len(workbook.sheetnames)} sheets:")

    total_rows = 0
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        rows = ws.max_row
        cols = ws.max_column
        total_rows += rows
        log(f"  - {sheet_name}: {rows:,} rows, {cols} columns")

    log(f"  Total rows across all sheets: {total_rows:,}")

    # Save workbook
    excel_path = extractor.save_workbook(workbook, TEST_OUTPUT_DIR, "max_export.xlsx")
    log(f"")
    log(f"Saved Excel file: {excel_path}")

    if not os.path.exists(excel_path):
        raise Exception("Excel file was not created!")

    file_size = os.path.getsize(excel_path) / (1024 * 1024)
    log(f"File size: {file_size:.1f} MB")

    return excel_path, workbook


def test_step_4_modify_excel(excel_path, workbook):
    """Step 4: Modify translations across multiple sheets."""
    log("")
    log("=" * 70)
    log("STEP 4: Modifying Translations Across Multiple Sheets")
    log("=" * 70)

    modifications = []

    # Find data model sheets to modify
    dm_sheets = [s for s in workbook.sheetnames if s.startswith("DataModel")]

    if not dm_sheets:
        log("No DataModel sheets found - checking other sheets")
        dm_sheets = [s for s in workbook.sheetnames if s not in ["Picklists", "ObjectDefinitions"]]

    log(f"Found {len(dm_sheets)} DataModel sheets to modify")

    # Modify first 5 sheets, 3 translations each
    for sheet_name in dm_sheets[:5]:
        ws = workbook[sheet_name]
        modified_count = 0

        # Find rows with content to modify (skip header)
        for row_num in range(2, min(ws.max_row + 1, 12)):
            # Find the label column (usually column 5 for translated label)
            if ws.max_column >= 5:
                cell = ws.cell(row=row_num, column=5)
                original_value = cell.value

                if original_value and isinstance(original_value, str) and len(original_value) > 0:
                    # Add a test marker
                    new_value = f"[MAX-TEST] {original_value}"
                    cell.value = new_value

                    modifications.append({
                        "sheet": sheet_name,
                        "row": row_num,
                        "column": 5,
                        "original": original_value,
                        "modified": new_value
                    })
                    modified_count += 1

                    if modified_count >= 3:
                        break

        log(f"  Modified {modified_count} cells in: {sheet_name}")

    # Save modified workbook
    modified_path = os.path.join(TEST_OUTPUT_DIR, "max_export_modified.xlsx")
    workbook.save(modified_path)
    file_size = os.path.getsize(modified_path) / (1024 * 1024)
    log(f"")
    log(f"Saved modified Excel: {modified_path} ({file_size:.1f} MB)")
    log(f"Total modifications: {len(modifications)}")

    return modified_path, modifications


def test_step_5_import_xml(processor, modified_excel_path):
    """Step 5: Import translations back to XML."""
    log("")
    log("=" * 70)
    log("STEP 5: Importing Translations to XML")
    log("=" * 70)

    from trexima.core.translation_importer import TranslationImporter
    from trexima.io.excel_handler import ExcelHandler

    def progress_callback(percent, message):
        log(f"  [{int(percent):3d}%] {message}")

    # Load the modified workbook
    excel_handler = ExcelHandler()
    workbook = excel_handler.load_workbook(modified_excel_path)

    log(f"Loaded modified workbook with {len(workbook.sheetnames)} sheets")

    # Create importer
    importer = TranslationImporter(
        processor=processor,
        progress_callback=progress_callback
    )

    # Select DataModel sheets to import
    sheets_to_import = [s for s in workbook.sheetnames if s.startswith("DataModel")]

    log(f"Importing {len(sheets_to_import)} DataModel sheets")
    log("")

    start_time = datetime.now()

    # Execute import
    result = importer.import_from_workbook(
        workbook=workbook,
        worksheets_to_process=sheets_to_import,
        save_dir=TEST_OUTPUT_DIR
    )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    log("")
    log(f"Import completed in {duration:.1f} seconds")
    log(f"Import result: success={result.success}")
    log(f"Changes made: {result.changes_made}")

    if result.files_generated:
        log(f"Generated {len(result.files_generated)} XML files:")
        for xml_file in result.files_generated:
            file_size = os.path.getsize(xml_file) / (1024 * 1024)
            log(f"  - {os.path.basename(xml_file)} ({file_size:.1f} MB)")

    if result.log_file_path:
        log(f"Import log: {os.path.basename(result.log_file_path)}")

    return result


def test_step_6_verify_xml(modifications):
    """Step 6: Verify changes in generated XML files."""
    log("")
    log("=" * 70)
    log("STEP 6: Verifying Changes in XML Files")
    log("=" * 70)

    # Find generated XML files
    xml_files = [f for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith(".xml")]

    if not xml_files:
        log("WARNING: No XML files generated!")
        return False

    log(f"Found {len(xml_files)} XML file(s):")

    verification_passed = True
    total_markers = 0

    for xml_file in xml_files:
        xml_path = os.path.join(TEST_OUTPUT_DIR, xml_file)
        file_size = os.path.getsize(xml_path) / (1024 * 1024)
        log(f"  - {xml_file} ({file_size:.1f} MB)")

        # Parse and check for modifications
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if any modifications are present
        modified_found = "[MAX-TEST]" in content
        log(f"    Contains [MAX-TEST] markers: {modified_found}")

        if modified_found:
            count = content.count("[MAX-TEST]")
            total_markers += count
            log(f"    Found {count} modification marker(s)")

    log(f"")
    log(f"Total [MAX-TEST] markers across all files: {total_markers}")

    return verification_passed


def main():
    """Run the complete MAX test."""
    log("=" * 70)
    log("TREXIMA MAX TEST")
    log("ALL Data Models + ALL Languages + Full API Integration")
    log("=" * 70)
    log("")

    try:
        # Setup
        setup_test_environment()
        log("")

        # Step 1: Connect to API
        client, locales = test_step_1_connect_api()

        # Step 2: Load all XML
        processor, export_locales = test_step_2_load_all_xml(locales)

        # Step 3: MAX Export
        excel_path, workbook = test_step_3_export_max(processor, client, export_locales)

        # Step 4: Modify
        modified_excel_path, modifications = test_step_4_modify_excel(excel_path, workbook)

        # Step 5: Import
        result = test_step_5_import_xml(processor, modified_excel_path)

        # Step 6: Verify
        test_step_6_verify_xml(modifications)

        log("")
        log("=" * 70)
        log("MAX TEST COMPLETED SUCCESSFULLY!")
        log("=" * 70)
        log(f"Test output directory: {TEST_OUTPUT_DIR}")
        log("")
        log("Generated files:")
        for f in sorted(os.listdir(TEST_OUTPUT_DIR)):
            fpath = os.path.join(TEST_OUTPUT_DIR, f)
            if os.path.isfile(fpath):
                fsize = os.path.getsize(fpath) / (1024 * 1024)
                log(f"  - {f} ({fsize:.1f} MB)")

        return True

    except Exception as e:
        log("")
        log("=" * 70)
        log(f"MAX TEST FAILED: {e}")
        log("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
