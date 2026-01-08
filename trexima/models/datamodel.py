"""
Data Model Classes for TREXIMA

Contains domain models representing SF configuration structures.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup


class DataModelType(Enum):
    """Types of SuccessFactors data models."""

    SUCCESSION_DATA_MODEL = auto()
    SFEC_SUCCESSION_DATA_MODEL = auto()
    SFEC_CSF_SUCCESSION_DATA_MODEL = auto()
    SFEC_CORPORATE_DATA_MODEL = auto()
    SFEC_CSF_CORPORATE_DATA_MODEL = auto()
    PM_FORM_TEMPLATE = auto()
    GOAL_PLAN_TEMPLATE = auto()
    DEVELOPMENT_PLAN_TEMPLATE = auto()
    UNKNOWN = auto()


@dataclass
class TranslationEntry:
    """Represents a single translation entry for a language."""

    language: str
    value: str
    is_default: bool = False

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "value": self.value,
            "is_default": self.is_default
        }


@dataclass
class TranslatableTag:
    """Represents a translatable XML tag with its translations."""

    tag_name: str
    tag_id: Optional[str] = None
    parent_tag_name: Optional[str] = None
    parent_tag_id: Optional[str] = None
    section_name: str = ""
    subsection_name: str = ""
    default_label: str = ""
    translations: Dict[str, str] = field(default_factory=dict)
    visibility: Optional[str] = None
    msg_key: Optional[str] = None

    def get_translation(self, language: str) -> Optional[str]:
        """Get translation for a specific language."""
        return self.translations.get(language)

    def set_translation(self, language: str, value: str):
        """Set translation for a specific language."""
        self.translations[language] = value

    def to_excel_row(self, languages: List[str]) -> List[str]:
        """Convert to Excel row data."""
        row = [
            self.section_name,
            self.subsection_name,
            self.tag_id or "",
            self.default_label
        ]
        for lang in languages:
            row.append(self.translations.get(lang, ""))
        return row


@dataclass
class PicklistOption:
    """Represents a picklist option with translations."""

    external_code: str
    option_id: str
    labels: Dict[str, str] = field(default_factory=dict)
    status: str = "A"

    def get_label(self, language: str) -> Optional[str]:
        """Get label for a specific language."""
        return self.labels.get(language)


@dataclass
class PicklistItem:
    """Represents a picklist with its options."""

    picklist_id: str
    options: List[PicklistOption] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    is_mdf_picklist: bool = False

    def add_reference(self, reference: str):
        """Add a reference to this picklist."""
        if reference not in self.references:
            self.references.append(reference)

    def get_references_string(self) -> str:
        """Get all references as a single string."""
        return " | ".join(self.references)


@dataclass
class LabelKeyEntry:
    """Represents a form label key entry."""

    label_key: str
    default_lang: str
    translations: Dict[str, str] = field(default_factory=dict)

    def to_csv_dict(self, headers: List[str]) -> dict:
        """Convert to CSV dictionary format."""
        result = {
            "label_key": self.label_key,
            "default": self.default_lang
        }
        for header in headers:
            if header not in ["label_key", "default"]:
                result[header] = self.translations.get(header, "")
        return result


@dataclass
class DataModel:
    """Represents a SuccessFactors data model configuration."""

    name: str
    soup: BeautifulSoup
    model_type: DataModelType
    is_standard: bool = False
    file_path: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    translatable_tags: List[TranslatableTag] = field(default_factory=list)

    def get_full_name(self) -> str:
        """Get the full display name including standard prefix if applicable."""
        if self.is_standard:
            return f"Standard SAP {self.name}"
        return self.name

    @classmethod
    def detect_type(cls, soup: BeautifulSoup) -> DataModelType:
        """Detect the data model type from BeautifulSoup object."""
        if soup.find("succession-data-model") is not None:
            if soup.find("hris-element") is not None:
                return DataModelType.SFEC_SUCCESSION_DATA_MODEL
            return DataModelType.SUCCESSION_DATA_MODEL

        if soup.find("country-specific-fields") is not None:
            if soup.find("format-group") is not None:
                return DataModelType.SFEC_CSF_SUCCESSION_DATA_MODEL
            return DataModelType.SFEC_CSF_CORPORATE_DATA_MODEL

        if soup.find("corporate-data-model") is not None:
            return DataModelType.SFEC_CORPORATE_DATA_MODEL

        if soup.find("sf-form") is not None and soup.find("sf-pmreview") is not None:
            return DataModelType.PM_FORM_TEMPLATE

        if soup.find("obj-plan-template") is not None:
            obj_plan_type = soup.find("obj-plan-type")
            if obj_plan_type and obj_plan_type.string == "Development":
                return DataModelType.DEVELOPMENT_PLAN_TEMPLATE
            return DataModelType.GOAL_PLAN_TEMPLATE

        return DataModelType.UNKNOWN

    def get_type_name(self) -> str:
        """Get human-readable type name."""
        type_names = {
            DataModelType.SUCCESSION_DATA_MODEL: "SF Succession Data Model",
            DataModelType.SFEC_SUCCESSION_DATA_MODEL: "SFEC Succession Data Model",
            DataModelType.SFEC_CSF_SUCCESSION_DATA_MODEL: "SFEC CSF Succession Data Model",
            DataModelType.SFEC_CORPORATE_DATA_MODEL: "SFEC Corporate Data Model",
            DataModelType.SFEC_CSF_CORPORATE_DATA_MODEL: "SFEC CSF Corporate Data Model",
            DataModelType.PM_FORM_TEMPLATE: "PM Form Template",
            DataModelType.GOAL_PLAN_TEMPLATE: "Goal Plan Template",
            DataModelType.DEVELOPMENT_PLAN_TEMPLATE: "Development Plan Template",
            DataModelType.UNKNOWN: "Unknown"
        }
        return type_names.get(self.model_type, "Unknown")

    def extract_languages(self) -> List[str]:
        """Extract all languages present in the data model."""
        languages = []
        label_tags = self.soup.find_all("label")
        for label_tag in label_tags:
            lang_id = label_tag.get("xml:lang")
            if lang_id and lang_id not in languages:
                languages.append(lang_id)
        self.languages = languages
        return languages

    def find_tag_by_id(self, tag_name: str, tag_id: str) -> Optional[Any]:
        """Find a tag by name and ID."""
        return self.soup.find(name=tag_name, attrs={"id": tag_id})

    def find_all_translatable_tags(self, translatable_tag_names: List[str]) -> List[Any]:
        """Find all translatable tags in the data model."""
        return self.soup.find_all(translatable_tag_names)


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    sheets_created: int = 0
    rows_exported: int = 0


@dataclass
class ImportResult:
    """Result of an import operation."""

    success: bool
    files_generated: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    changes_made: int = 0
    log_file_path: Optional[str] = None
