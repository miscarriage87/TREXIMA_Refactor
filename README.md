# TREXIMA - SuccessFactors Translation Export & Import Management Accelerator

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

TREXIMA is a powerful tool for managing translations in SAP SuccessFactors configurations. It provides seamless export and import workflows for translating Employee Central data models, form templates, and other SuccessFactors objects.

## ✨ Features

- **📤 Translation Export**: Extract translations from SF data models to Excel workbooks
- **📥 Translation Import**: Update SF configuration files from translated Excel workbooks
- **🌍 Multi-Language Support**: Handle 17+ languages including RTL (Arabic, Hebrew)
- **🔗 OData API Integration**:
  - Picklists (Legacy and MDF)
  - MDF Object Definitions
  - Foundation Objects
- **📊 Multiple Data Model Types**:
  - Succession Data Model (SDM)
  - Corporate Data Model (CDM)
  - Country-Specific Fields (CSF)
  - PM/GM Form Templates
- **🖥️ Dual Interface**:
  - Desktop GUI (Tkinter)
  - Web Application (Flask)
- **🔄 Change Tracking**: Detailed import logs with before/after values

## 🏗️ Architecture

TREXIMA follows a clean, modular architecture with clear separation of concerns:

```
trexima/
├── config.py                # Configuration and settings
├── orchestrator.py          # Workflow coordination
├── models/                  # Data models
├── io/                      # Input/Output handlers
├── core/                    # Business logic
├── ui/                      # Desktop GUI
└── web/                     # Web application
```

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements_new.txt
```

## 🚀 Usage

### Desktop Application (Tkinter)

```bash
python run_trexima.py
```

### Web Application (Flask)

```bash
python run_web.py

# With custom port
python run_web.py --port 8080 --debug
```

Then open http://127.0.0.1:5000 in your browser.

### Programmatic Usage

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
    export_mdf_objects=True
)

# Execute export
output_path = orch.export_translations(config)
print(f"Exported to: {output_path}")
```

## 📊 Performance

Tested with maximum configuration:

| Metric | Value |
|--------|-------|
| **Data Models** | 4 (SDM, CDM, CSF-SDM, CSF-CDM) |
| **Languages** | 17 (all active locales) |
| **Input Size** | 8.4 MB XML |
| **Output Size** | 6.4 MB Excel |
| **Rows Processed** | 98,327 across 36 sheets |
| **Export Time** | ~3.7 minutes |
| **Import Time** | ~7.6 minutes |

## 🧪 Testing

### End-to-End Tests

```bash
# Small test (2 data models, 3 languages)
python test_e2e.py

# MAX test (all 4 data models, 17 languages, full API)
python test_max.py

# API connectivity test
python test_api_small.py
```

## 🔒 Security

- **Credentials**: Never commit `LoginCredentialsForAPI.txt`
- **Workbook Protection**: Excel workbooks are password-protected
- **API Authentication**: Uses SAML authentication for SuccessFactors

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Original monolithic script: 2173 lines
- Refactored modular code: 24+ files with clean architecture
- Built with ❤️ for the SAP community

---

**Note**: This tool is designed to work with SAP SuccessFactors configurations. Ensure you have proper authorization and backup your data before using in production environments.

