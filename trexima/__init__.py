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

# Lazy import of Orchestrator to avoid importing UI dependencies in web mode
def _get_orchestrator():
    from .orchestrator import Orchestrator
    return Orchestrator

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
    Orchestrator = _get_orchestrator()
    orchestrator = Orchestrator()
    orchestrator.run()

# Export Orchestrator as a module-level attribute (lazy loaded)
def __getattr__(name):
    if name == 'Orchestrator':
        return _get_orchestrator()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


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
