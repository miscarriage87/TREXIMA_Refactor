"""
TREXIMA - SuccessFactors Translation Export & Import Management Accelerator

A tool for managing translations in SAP SuccessFactors configurations.

Features:
- Export translations from SF data models to Excel workbooks
- Import updated translations back to SF configuration files
- Support for multiple data model types (Succession, Corporate, CSF)
- Integration with SF OData API for picklists and MDF objects
- PM/GM form template translation support

Usage:
    # Run with GUI
    from trexima import run_app
    run_app()

    # Programmatic usage
    from trexima import Orchestrator
    orch = Orchestrator()
    orch.load_xml_files(['path/to/datamodel.xml'])
    orch.export_translations(config)
"""

from .config import (
    APP_NAME,
    VERSION,
    APP_TITLE,
    AppPaths,
    AppState,
    ODataConfig,
    ExportConfig,
    ImportConfig
)

from .orchestrator import Orchestrator

from .models import (
    DataModel,
    DataModelType,
    TranslatableTag,
    TranslationEntry,
    PicklistItem,
    PicklistOption,
    LabelKeyEntry,
    ExportResult,
    ImportResult
)

from .core import (
    ODataClient,
    TranslationExtractor,
    TranslationImporter,
    DataModelProcessor
)

from .io import (
    XMLHandler,
    ExcelHandler,
    CSVHandler
)


__version__ = str(VERSION)
__author__ = "TREXIMA Team"


def run_app():
    """Run the TREXIMA application with GUI."""
    orchestrator = Orchestrator()
    orchestrator.run()


__all__ = [
    # Main
    'run_app',
    'Orchestrator',

    # Config
    'APP_NAME',
    'VERSION',
    'APP_TITLE',
    'AppPaths',
    'AppState',
    'ODataConfig',
    'ExportConfig',
    'ImportConfig',

    # Models
    'DataModel',
    'DataModelType',
    'TranslatableTag',
    'TranslationEntry',
    'PicklistItem',
    'PicklistOption',
    'LabelKeyEntry',
    'ExportResult',
    'ImportResult',

    # Core
    'ODataClient',
    'TranslationExtractor',
    'TranslationImporter',
    'DataModelProcessor',

    # I/O
    'XMLHandler',
    'ExcelHandler',
    'CSVHandler',
]
