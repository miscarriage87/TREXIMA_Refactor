"""
Orchestrator Module

Coordinates workflows between UI and core logic.
"""

import os
from typing import Optional, List

from .config import AppPaths, AppState, ODataConfig, ExportConfig, SYSTEM_DEFAULT_LANG
from .core.odata_client import ODataClient
from .core.datamodel_processor import DataModelProcessor
from .core.translation_extractor import TranslationExtractor
from .core.translation_importer import TranslationImporter
from .io.csv_handler import CSVHandler
from .io.excel_handler import ExcelHandler
from .ui.main_window import MainWindow
from .ui.dialogs import DialogManager
from .utils.helpers import open_file, open_directory


class Orchestrator:
    """Coordinates the application workflow."""

    def __init__(self):
        self.app_paths = AppPaths()
        self.state = AppState()

        # Initialize components
        self.dialog_manager = DialogManager()
        self.odata_client = ODataClient()
        self.processor = DataModelProcessor(self.app_paths)
        self.csv_handler = CSVHandler()
        self.excel_handler = ExcelHandler()

        # UI (optional - for headless mode)
        self.main_window: Optional[MainWindow] = None

        # Extractors and importers
        self.extractor: Optional[TranslationExtractor] = None
        self.importer: Optional[TranslationImporter] = None

    def initialize_ui(self) -> MainWindow:
        """Initialize the UI components."""
        self.main_window = MainWindow(self.app_paths)

        # Set up callbacks
        self.main_window.set_on_export(self._on_export_start)
        self.main_window.set_on_import(self._on_import_start)
        self.main_window.set_on_open_files(self._on_open_files)
        self.main_window.set_on_connect_api(self._on_connect_api)
        self.main_window.set_on_execute_export(self._on_execute_export)
        self.main_window.set_on_execute_import(self._on_execute_import)

        return self.main_window

    def run(self):
        """Run the application with UI."""
        if self.main_window is None:
            self.initialize_ui()
        self.main_window.run()

    def _log_progress(self, percent: int, message: str):
        """Log progress through UI if available."""
        if self.main_window:
            self.main_window.progress_tracker.update(percent, message)

    def _on_export_start(self):
        """Handle export workflow start."""
        self.state.is_export_action = True
        self.state.reset()

    def _on_import_start(self):
        """Handle import workflow start."""
        self.state.is_export_action = False
        self.state.reset()

        # Select translations workbook
        workbook_path = self.dialog_manager.select_excel_file(
            "Browse to the updated Translations Workbook"
        )

        if not workbook_path:
            return

        # Load and validate workbook
        workbook = self.excel_handler.load_workbook(workbook_path)
        if not self.excel_handler.validate_translations_workbook(workbook):
            self.dialog_manager.show_error(
                "Invalid Translations Workbook",
                "The selected file is not a valid Translations workbook."
            )
            return

        self.state.translations_wb = workbook
        self.state.file_save_dir = os.path.dirname(workbook_path)
        self.dialog_manager.set_default_directory(self.state.file_save_dir)

        # Determine button text based on sheet contents
        dm_sheets = self.excel_handler.get_datamodel_sheets(workbook)
        has_pm = "Performance_Review_Templates" in workbook.sheetnames

        if has_pm and not dm_sheets:
            btn_text = "1. Browse to Latest PMGM Template File(s)"
        elif has_pm and dm_sheets:
            btn_text = "1. Browse to Latest PMGM Template & Data Model File(s)"
        else:
            btn_text = "1. Browse to Latest EC Data Model File(s)"

        if self.main_window:
            self.main_window.setup_import_buttons(btn_text)

    def _on_open_files(self):
        """Handle open files action."""
        # Select XML files
        xml_files = self.dialog_manager.select_xml_files(
            "Open XML Configuration Files"
        )

        if not xml_files:
            return

        # Ask about standard data models
        include_standard = self.dialog_manager.ask_yes_no(
            "Process Standard Data Models",
            "Do you want to add Standard translations from SAP for missing labels?"
        )

        self._log_progress(1, "Extracting content of XML files...")

        # Load files
        for xml_file in xml_files:
            self._log_progress(10, f"Loading {os.path.basename(xml_file)}...")
            model = self.processor.load_data_model(xml_file)
            if model:
                self.state.xml_files.append(xml_file)
                self.state.file_save_dir = os.path.dirname(xml_file)

        # Load standard models if requested
        if include_standard:
            self._log_progress(50, "Loading standard SAP data models...")
            self.processor.load_standard_data_models()

        # Check for PMGM templates and load label keys if needed
        if self.processor.is_pmgm_included:
            self._handle_label_keys_file()

        # Check for CSF models and load country list if needed
        if self.processor.is_sdm_included:
            self._handle_country_list()

        self._log_progress(
            100,
            f"Loaded {len(self.state.xml_files)} configuration files. Connect to SF OData Service."
        )

        if self.main_window:
            self.main_window.mark_step_complete(self.main_window.file_open_btn)

    def _handle_label_keys_file(self):
        """Handle label keys file for PM templates."""
        if self.state.label_keys_file:
            reload = self.dialog_manager.ask_ok_cancel(
                "Browse to FormLabelKeys file",
                f"File '{self.state.label_keys_file}' already uploaded. Upload new file?"
            )
            if not reload:
                return

        self.dialog_manager.show_info(
            "Useful Info for the Next Step",
            "On the next screen, browse to the 'FormLabelKeys' (csv) file. "
            "This is required for extracting translations from PM Form Templates."
        )

        label_keys_path = self.dialog_manager.select_csv_file(
            "Browse to FormLabelKeys CSV file"
        )

        if label_keys_path:
            self.state.label_keys_file = label_keys_path
            self.state.label_keys_dict, self.state.label_keys_file_headers = (
                self.csv_handler.read_label_keys_file(label_keys_path)
            )

    def _handle_country_list(self):
        """Handle country list for CSF models."""
        if self.state.active_countries:
            return

        proceed = self.dialog_manager.ask_ok_cancel(
            "INFO about choice on the next prompted screen",
            "Browse to a CSV file with enabled country codes. "
            "If not specified, all countries from CSF models will be included."
        )

        if proceed:
            country_file = self.dialog_manager.select_csv_file(
                "Browse to Country List CSV file"
            )
            if country_file:
                self.state.active_countries = self.csv_handler.read_country_list(country_file)

    def _on_connect_api(self):
        """Handle connect to OData API action."""
        if not self.state.xml_files:
            self.dialog_manager.show_error(
                "ERROR - Process Order Incorrect",
                "Complete Step 1 before proceeding with this step."
            )
            return

        # Check for existing connection
        if self.odata_client.is_connected:
            use_existing = self.dialog_manager.ask_yes_no(
                "Already an active OData connection",
                "Use existing connection?"
            )
            if use_existing:
                self._complete_api_connection()
                return

        # Ask if API connection is needed
        connect = self.dialog_manager.ask_yes_no(
            "Connect to SF OData API or Skip",
            "Connection to OData API is needed for Picklists, Object Definitions, "
            "and Org Objects. Do you want to connect?"
        )

        if not connect:
            self._complete_api_connection()
            return

        # Get credentials
        credentials = self.dialog_manager.get_odata_credentials()
        if not credentials:
            return

        self._log_progress(10, "Establishing connection to SF OData Service...")

        try:
            self.odata_client.connect(
                service_url=credentials["service_url"],
                company_id=credentials["company_id"],
                username=credentials["username"],
                password=credentials["password"]
            )
            self._log_progress(80, "Connection established!")
            self._complete_api_connection()

        except Exception as e:
            self.dialog_manager.show_error(
                "Connection Failed",
                f"Could not connect to OData service: {str(e)}"
            )
            self._log_progress(100, "Connection failed. Please retry.")

    def _complete_api_connection(self):
        """Complete the API connection step."""
        if self.main_window:
            self.main_window.mark_step_complete(self.main_window.connect_api_btn)
            self.main_window.show_execute_button()

    def _on_execute_export(self):
        """Execute the export operation."""
        # Get export options
        export_picklists = self.dialog_manager.ask_yes_no(
            "Export Picklists' Translations?",
            "Do you want to export translations for all Picklists?"
        )

        picklist_from_csv = None
        if export_picklists:
            use_csv = self.dialog_manager.ask_yes_no(
                "Export Picklists from latest export?",
                "Export from Picklist-Values CSV? (No = use API)"
            )
            if use_csv:
                picklist_from_csv = self.dialog_manager.select_csv_file(
                    "Open Picklist CSV file"
                )

        # Get active locales
        active_locales = []
        if self.odata_client.is_connected:
            active_locales = self.odata_client.get_active_locales()

        if not active_locales:
            active_locales = ["en_US", "de_DE", "fr_FR", "es_ES"]

        # Add from label keys if available
        if self.state.label_keys_file_headers:
            for header in self.state.label_keys_file_headers:
                if header not in ["label_key", "default"] and header not in active_locales:
                    active_locales.append(header)

        locales_for_export = self.dialog_manager.select_locales(active_locales)

        # Get default language
        default_lang = self.dialog_manager.select_default_language(
            locales_for_export,
            self.state.system_default_lang
        )
        self.state.system_default_lang = default_lang

        # Ensure default is first
        if default_lang in locales_for_export:
            locales_for_export.remove(default_lang)
            locales_for_export.insert(0, default_lang)

        # Get other options
        export_mdf = False
        export_fo = True

        if self.odata_client.is_connected:
            export_mdf = self.dialog_manager.ask_yes_no(
                "Export MDF Objects' Definitions?",
                "Export translations from MDF Objects' Definitions?"
            )

            export_fo = self.dialog_manager.ask_yes_no(
                "Export Foundation Objects?",
                "Export translations for Foundation Objects (EC Relevant)?"
            )

        remove_html = False
        if self.processor.is_pmgm_included:
            remove_html = self.dialog_manager.ask_yes_no(
                "Remove HTML tags?",
                "Remove HTML tags from translations?"
            )

        # Create extractor and execute
        self.extractor = TranslationExtractor(
            self.processor,
            self.odata_client,
            self._log_progress
        )

        if self.state.label_keys_dict:
            self.extractor.set_label_keys(
                self.state.label_keys_dict,
                self.state.label_keys_file_headers
            )

        if self.state.active_countries:
            self.extractor.set_active_countries(self.state.active_countries)

        workbook = self.extractor.extract_to_workbook(
            locales_for_export=locales_for_export,
            export_picklists=export_picklists,
            export_mdf_objects=export_mdf,
            export_fo_translations=export_fo,
            picklist_from_csv=picklist_from_csv,
            remove_html_tags=remove_html,
            system_default_lang=default_lang
        )

        # Save workbook
        file_path = self.extractor.save_workbook(workbook, self.state.file_save_dir)
        self.state.excel_filename = file_path

        self._log_progress(100, "Export complete! Opening file...")

        # Mark complete and open file
        if self.main_window:
            self.main_window.mark_step_complete(self.main_window.export_execute_btn)

        open_file(file_path)

    def _on_execute_import(self):
        """Execute the import operation."""
        if not self.state.translations_wb:
            self.dialog_manager.show_error(
                "No Workbook Loaded",
                "Please load a translations workbook first."
            )
            return

        # Get worksheets to process
        sheet_names = self.state.translations_wb.sheetnames
        worksheets = self.dialog_manager.multi_choice(
            "Choose Worksheets to process",
            "Choose Worksheets",
            sheet_names,
            list(range(len(sheet_names)))
        )

        if not worksheets:
            return

        # Create importer
        self.importer = TranslationImporter(
            self.processor,
            self._log_progress
        )

        if self.state.label_keys_dict:
            self.importer.set_label_keys(
                self.state.label_keys_dict,
                self.state.label_keys_file_headers
            )

        # Execute import
        result = self.importer.import_from_workbook(
            self.state.translations_wb,
            worksheets,
            self.state.file_save_dir
        )

        # Show results
        if result.success:
            self._log_progress(100, "Import complete!")

            if self.main_window:
                self.main_window.mark_step_complete(self.main_window.import_execute_btn)

            # Open output directory
            open_directory(self.state.file_save_dir)
        else:
            self.dialog_manager.show_error(
                "Import Failed",
                result.error_message or "An error occurred during import."
            )

    # Headless mode methods for programmatic use

    def load_xml_files(
        self,
        file_paths: List[str],
        include_standard: bool = False
    ) -> int:
        """
        Load XML files programmatically.

        Args:
            file_paths: List of XML file paths
            include_standard: Include standard SAP models

        Returns:
            Number of files loaded
        """
        count = 0
        for path in file_paths:
            model = self.processor.load_data_model(path)
            if model:
                self.state.xml_files.append(path)
                count += 1

        if include_standard:
            self.processor.load_standard_data_models()

        if self.state.xml_files:
            self.state.file_save_dir = os.path.dirname(self.state.xml_files[0])

        return count

    def connect_to_odata(self, config: ODataConfig) -> bool:
        """
        Connect to OData service programmatically.

        Args:
            config: OData configuration

        Returns:
            True if connected
        """
        try:
            return self.odata_client.connect(
                service_url=config.service_url,
                company_id=config.company_id,
                username=config.username,
                password=config.password
            )
        except Exception:
            return False

    def export_translations(
        self,
        config: ExportConfig,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Export translations programmatically.

        Args:
            config: Export configuration
            output_path: Optional output file path

        Returns:
            Path to exported file or None
        """
        self.extractor = TranslationExtractor(
            self.processor,
            self.odata_client
        )

        workbook = self.extractor.extract_to_workbook(
            locales_for_export=config.locales_for_export,
            export_picklists=config.export_picklists,
            export_mdf_objects=config.export_mdf_objects,
            export_fo_translations=config.export_fo_translations,
            remove_html_tags=config.remove_html_tags
        )

        save_dir = output_path or self.state.file_save_dir
        return self.extractor.save_workbook(workbook, save_dir)
