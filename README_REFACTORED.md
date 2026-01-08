# TREXIMA - Refactored

SuccessFactors Translation Export & Import Management Accelerator

## Overview

This is the refactored, modular version of TREXIMA. The original monolithic script (SFConfigProcessor.py, 2173 lines) has been restructured into a clean, maintainable architecture with separation of concerns.

## Project Structure

```
trexima/
├── __init__.py              # Package entry point
├── app.py                   # Desktop app entry point
├── config.py                # Configuration and settings
├── orchestrator.py          # Workflow coordination
│
├── models/                  # Data models
│   ├── __init__.py
│   └── datamodel.py         # Domain models (DataModel, TranslatableTag, etc.)
│
├── io/                      # Input/Output handlers
│   ├── __init__.py
│   ├── xml_handler.py       # XML file operations
│   ├── excel_handler.py     # Excel workbook operations
│   └── csv_handler.py       # CSV file operations
│
├── core/                    # Business logic
│   ├── __init__.py
│   ├── odata_client.py      # SF OData API client
│   ├── datamodel_processor.py # Data model processing
│   ├── translation_extractor.py # Export functionality
│   └── translation_importer.py  # Import functionality
│
├── ui/                      # Desktop GUI (Tkinter)
│   ├── __init__.py
│   ├── main_window.py       # Main application window
│   ├── dialogs.py           # Dialog components
│   └── progress.py          # Progress tracking
│
├── utils/                   # Utilities
│   ├── __init__.py
│   └── helpers.py           # Helper functions
│
└── web/                     # Web application (Flask)
    ├── __init__.py
    ├── app.py               # Flask application factory
    ├── routes.py            # API routes and handlers
    ├── templates/           # HTML templates
    │   ├── base.html
    │   ├── index.html
    │   ├── export.html
    │   ├── import.html
    │   ├── settings.html
    │   └── error.html
    └── static/
        ├── css/style.css
        └── js/main.js
```

## Features

- **Export Translations**: Extract translations from SF data models to Excel
- **Import Translations**: Update SF configuration files from Excel workbooks
- **Multiple Data Model Support**:
  - Succession Data Model (SDM)
  - Corporate Data Model (CDM)
  - Country-Specific Fields (CSF)
  - PM/GM Form Templates
- **OData API Integration**: Picklists, MDF Objects, Foundation Objects
- **Two Interfaces**:
  - Desktop GUI (Tkinter)
  - Web Application (Flask)

## Installation

```bash
# Install dependencies
pip install -r requirements_new.txt
```

## Running the Application

### Desktop GUI (Tkinter)
```bash
python run_trexima.py
```

### Web Application (Flask)
```bash
python run_web.py

# With options
python run_web.py --port 8080 --debug
```

Then open http://127.0.0.1:5000 in your browser.

## Programmatic Usage

```python
from trexima import Orchestrator, ExportConfig

# Create orchestrator
orch = Orchestrator()

# Load XML files
orch.load_xml_files(['EC-data-model.xml'], include_standard=True)

# Configure export
config = ExportConfig(
    locales_for_export=['en_US', 'de_DE', 'fr_FR'],
    export_picklists=True,
    export_mdf_objects=False
)

# Execute export
output_path = orch.export_translations(config)
```

## Architecture Highlights

1. **Separation of Concerns**: Clear boundaries between UI, business logic, and I/O
2. **Modular Design**: Each module has a single responsibility
3. **Dual Interface**: Same core logic powers both desktop and web interfaces
4. **Type Hints**: Comprehensive type annotations for better IDE support
5. **Dataclasses**: Clean data models with minimal boilerplate
6. **No Global State**: State management through classes instead of globals

## Migration from Original

The original `SFConfigProcessor.py` remains in the project root for reference. The refactored code provides identical functionality with:

- Better maintainability
- Easier testing
- Cleaner architecture
- Web interface support
- Programmatic API access

## Dependencies

- beautifulsoup4 - XML parsing
- babel - Localization
- openpyxl - Excel processing
- ttkthemes - Tkinter theming
- requests - HTTP client
- pyodata - SAP OData client
- easygui - Simple dialogs
- flask - Web framework
- flask-cors - CORS support
