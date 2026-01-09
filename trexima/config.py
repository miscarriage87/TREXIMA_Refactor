"""
TREXIMA Configuration Module

Contains all configuration constants and settings.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


# Application Info
APP_NAME = "TREXIMA"
VERSION = 3.0
APP_TITLE = f"{APP_NAME} - Translation Export & Import Accelerator"

# File Names
APP_ICON_FILENAME = "appicon.png"
BACKGROUND_IMAGE_FILENAME = "bg.png"
DONE_ICON_FILENAME = "done.png"

# Standard Data Model Filenames
STD_SDM_FILENAME = "EC-data-model.xml"
STD_CSF_SDM_FILENAME = "EC-CSF-for-succession-DM.xml"
STD_CDM_FILENAME = "EC-corporate-datamodel.xml"
STD_CSF_CDM_FILENAME = "EC-CSF-for-corporate-DM.xml"

# Keywords
KEYWORD_SAP_STANDARD = "Standard SAP"
SYSTEM_DEFAULT_LANG = "en_US"

# Excel Sheet Names
SHEET_NAME_PM = "Performance_Review_Templates"
SHEET_NAME_GM = "Goal&Development_Plan_Templates"
SHEET_NAME_PL = "Picklists"

# Tags Configuration
EMPLOYEE_PROFILE_TAGS = [
    "standard-element", "background-element", "userinfo-element",
    "data-field", "rating-field", "tab-element", "view-template", "edit-template"
]

TAGS_TO_BE_IGNORED = [
    "tab-element", "view-template", "edit-template", "fm-competency", "permission"
]

HIGHLIGHT_TAGS = [
    "succession-data-model", "background-element", "userinfo-element",
    "hris-element", "hris-section"
]

# UI Configuration
CHILD_CHAR = " ↪ "
BG_COLOR = "#066b8d"
TROUGH_COLOR = "white"
BAR_COLOR = "#90ee90"

# Excel Styles
# Workbook password can be set via environment variable for protection
WORKBOOK_PASSWORD = os.environ.get('WORKBOOK_PASSWORD', '')


@dataclass
class AppPaths:
    """Application paths configuration."""

    app_dir: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(__file__)))

    @property
    def app_icon_path(self) -> str:
        return os.path.join(self.app_dir, APP_ICON_FILENAME)

    @property
    def background_image_path(self) -> str:
        return os.path.join(self.app_dir, BACKGROUND_IMAGE_FILENAME)

    @property
    def done_icon_path(self) -> str:
        return os.path.join(self.app_dir, DONE_ICON_FILENAME)

    @property
    def std_sdm_path(self) -> str:
        return os.path.join(self.app_dir, STD_SDM_FILENAME)

    @property
    def std_csf_sdm_path(self) -> str:
        return os.path.join(self.app_dir, STD_CSF_SDM_FILENAME)

    @property
    def std_cdm_path(self) -> str:
        return os.path.join(self.app_dir, STD_CDM_FILENAME)

    @property
    def std_csf_cdm_path(self) -> str:
        return os.path.join(self.app_dir, STD_CSF_CDM_FILENAME)

    def get_standard_dm_paths(self) -> List[str]:
        """Returns list of all standard data model paths."""
        return [
            self.std_sdm_path,
            self.std_csf_sdm_path,
            self.std_cdm_path,
            self.std_csf_cdm_path
        ]


@dataclass
class ODataConfig:
    """OData API configuration."""

    service_url: str = ""
    company_id: str = ""
    username: str = ""
    password: str = ""

    @property
    def auth_credentials(self) -> tuple:
        """Returns authentication tuple for requests."""
        return (f"{self.username}@{self.company_id}", self.password)

    def is_valid(self) -> bool:
        """Checks if configuration has all required fields."""
        return all([self.service_url, self.company_id, self.username, self.password])


@dataclass
class ExportConfig:
    """Export operation configuration."""

    locales_for_export: List[str] = field(default_factory=list)
    export_picklists: bool = True
    export_mdf_objects: bool = True
    export_fo_translations: bool = True
    remove_html_tags: bool = False
    picklist_from_csv: bool = False
    ask_to_choose_dm_langs: bool = True
    exclude_custom_label_std_fields: bool = True


@dataclass
class ImportConfig:
    """Import operation configuration."""

    worksheets_to_process: List[str] = field(default_factory=list)
    import_file_path: Optional[str] = None


@dataclass
class AppState:
    """Application runtime state."""

    soups: List = field(default_factory=list)
    soups_dict: dict = field(default_factory=dict)
    file_save_dir: str = "C:\\"
    xml_files: List[str] = field(default_factory=list)
    translatable_tags: List[str] = field(default_factory=list)
    is_pmgm_included: bool = False
    is_sdm_included: bool = False
    label_keys_dict: dict = field(default_factory=dict)
    label_keys_file_headers: List[str] = field(default_factory=list)
    active_countries: List[str] = field(default_factory=list)
    picklist_ids: List[str] = field(default_factory=list)
    picklist_references: List[str] = field(default_factory=list)
    sf_odata_service: Optional[object] = None
    excel_filename: Optional[str] = None
    translations_wb: Optional[object] = None
    label_keys_file: Optional[str] = None
    is_export_action: bool = False
    system_default_lang: str = SYSTEM_DEFAULT_LANG

    def reset(self):
        """Reset state for new operation."""
        self.soups = []
        self.soups_dict = {}
        self.xml_files = []
        self.translatable_tags = []
        self.is_pmgm_included = False
        self.is_sdm_included = False
        self.label_keys_dict = {}
        self.label_keys_file_headers = []
        self.active_countries = []
        self.picklist_ids = []
        self.picklist_references = []
        self.label_keys_file = None
