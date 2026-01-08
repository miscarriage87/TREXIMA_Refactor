"""
XML Handler Module

Handles reading and writing of XML configuration files.
"""

import os
from typing import List, Optional, Dict, Any, Tuple
from bs4 import BeautifulSoup, NavigableString

from ..config import (
    KEYWORD_SAP_STANDARD,
    SYSTEM_DEFAULT_LANG,
    EMPLOYEE_PROFILE_TAGS,
    TAGS_TO_BE_IGNORED,
    CHILD_CHAR
)
from ..models.datamodel import DataModel, DataModelType


class XMLHandler:
    """Handles XML file operations for SF data models."""

    def __init__(self):
        self.parser_xml = "xml"
        self.parser_html = "html.parser"

    def read_xml_file(self, file_path: str) -> Tuple[Optional[BeautifulSoup], str]:
        """
        Read an XML file and return BeautifulSoup object.

        Args:
            file_path: Path to the XML file

        Returns:
            Tuple of (BeautifulSoup object, parser used)
        """
        with open(file_path, encoding="utf8") as f:
            xml_content = f.read()

        # Choose parser based on CDATA presence
        if "<![CDATA[" not in xml_content:
            soup = BeautifulSoup(xml_content, self.parser_xml)
            parser = self.parser_xml
        else:
            soup = BeautifulSoup(xml_content, self.parser_html)
            parser = self.parser_html

        return soup, parser

    def write_xml_file(self, soup: BeautifulSoup, file_path: str) -> bool:
        """
        Write BeautifulSoup object to XML file.

        Args:
            soup: BeautifulSoup object to write
            file_path: Output file path

        Returns:
            True if successful
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        return True

    def detect_data_model_name(
        self,
        soup: BeautifulSoup,
        is_standard: bool = False,
        file_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Detect the name/type of the data model from soup content.

        Args:
            soup: BeautifulSoup object of the XML
            is_standard: Whether this is a standard SAP data model
            file_path: Original file path (for PM templates)

        Returns:
            Data model name string or None
        """
        special_name = None

        if soup.find("succession-data-model") is not None:
            if soup.find("hris-element") is not None:
                special_name = "SFEC Succession Data Model"
            else:
                special_name = "SF Succession Data Model"

        elif soup.find("country-specific-fields") is not None:
            if soup.find("format-group") is not None:
                special_name = "SFEC CSF Succession Data Model"
            else:
                special_name = "SFEC CSF Corporate Data Model"

        elif soup.find("corporate-data-model") is not None:
            special_name = "SFEC Corporate Data Model"

        elif soup.find("sf-form") is not None and soup.find("sf-pmreview") is not None:
            special_name = "PM Form Template"
            # For PM templates, use filename as identifier
            if file_path:
                filename = os.path.basename(file_path)
                if filename.endswith(".xml"):
                    special_name = filename[:-4]

        elif soup.find("obj-plan-template") is not None:
            plan_name = soup.find("obj-plan-name")
            plan_id = soup.find("obj-plan-id")
            if plan_name and plan_id:
                default_title = self.get_default_title(plan_name)
                special_name = f"{default_title} ({plan_id.string})"

        if is_standard and special_name:
            special_name = f"{KEYWORD_SAP_STANDARD} {special_name}"

        return special_name

    def get_default_title(
        self,
        tag,
        en_us: bool = False,
        label_on_parent: bool = False
    ) -> str:
        """
        Get the default label/title for a tag.

        Args:
            tag: BeautifulSoup tag
            en_us: Prefer en_US label
            label_on_parent: Look for label on parent tag

        Returns:
            Default label string
        """
        tag_label = ""
        tag_label_def = ""
        tag_label_eng = ""
        tag_name = ""

        if label_on_parent:
            children_tags = tag.parent.children
            tag_name = tag.name
        else:
            children_tags = tag.children

        for child_tag in children_tags:
            if isinstance(child_tag, NavigableString):
                continue

            child_tag_name = child_tag.name
            if (tag_name != "" and child_tag_name == tag_name) or tag_name == "":
                # Check for default label (no lang attribute)
                if (not child_tag.has_attr("xml:lang")
                        and not child_tag.has_attr("lang")
                        and not child_tag.has_attr("id")
                        and not child_tag.has_attr("rule")):
                    tag_label_def = child_tag.string

                # Check for en-US/en_US label
                if (child_tag.get("xml:lang") == "en-US"
                        or child_tag.get("lang") == "en_US"):
                    tag_label_eng = child_tag.string

                # Determine which label to use
                if not en_us:
                    if tag_label_def:
                        tag_label = tag_label_def
                        break
                    elif tag_label_eng:
                        tag_label = tag_label_eng
                        break
                else:
                    if tag_label_eng:
                        tag_label = tag_label_eng
                        break
                    elif tag_label_def:
                        tag_label = tag_label_def
                        break

                # Fallback to system default language
                if not tag_label:
                    if (child_tag.get("xml:lang") == SYSTEM_DEFAULT_LANG
                            or child_tag.get("lang") == SYSTEM_DEFAULT_LANG):
                        tag_label = child_tag.string

                # Special handling for mapto-desc
                if tag_name == "mapto-desc":
                    for_score = tag.parent.find("mapto-score")
                    if for_score:
                        tag_label = f"{tag_label} (for score={for_score.string})"

        # Fallback to ID or for attribute
        if not tag_label:
            if tag.get("id"):
                tag_label = f"{tag_name} ({tag.get('id')})"
            elif tag.get("for"):
                tag_label = f"{tag_name} ({tag.get('for')})"

        return tag_label or ""

    def get_readable_name(self, tag_name: str, include_tag_name: bool = False) -> str:
        """
        Convert a hyphenated tag name to readable format.

        Args:
            tag_name: Tag name like "obj-plan-name"
            include_tag_name: Include original tag name in parentheses

        Returns:
            Readable name like "Obj Plan Name (obj-plan-name)"
        """
        readable_name = ""
        words = tag_name.split("-")

        for word in words:
            if word == "sect":
                word = "Section"
            elif word == "intro":
                word = "Introduction"
            elif word == "comp":
                word = "Competency"
            elif word == "fm":
                word = " "
            readable_name += word.capitalize() + " "

        readable_name = readable_name.strip()
        if include_tag_name:
            readable_name = f"{readable_name} ({tag_name})"

        return readable_name

    def get_module_specific_name(self, parent_tag) -> str:
        """
        Get section/module name for a parent tag.

        Args:
            parent_tag: BeautifulSoup tag

        Returns:
            Section name string
        """
        parent_tag_name = parent_tag.name
        section_name = parent_tag_name

        if parent_tag_name == "obj-plan-template":
            section_name = "General Settings"
        elif parent_tag_name == "text-replacement":
            section_name = f"{self.get_readable_name(parent_tag_name)} (for={parent_tag.get('for')})"
        elif parent_tag_name == "permission":
            section_name = f"Permission (for={parent_tag.get('for')})"
        elif parent_tag_name == "field-permission":
            section_name = f"Field Permission (type={parent_tag.get('type')})"
        elif parent_tag_name == "field-definition":
            section_name = f"Field Definition (id={parent_tag.get('id')})"
        elif parent_tag_name == "table-column":
            section_name = f"{CHILD_CHAR}Table Column (id={parent_tag.get('id')})"
        elif "category" in parent_tag_name:
            section_name = f"{self.get_readable_name(parent_tag_name)} (id={parent_tag.get('id')})"
        elif parent_tag_name == "enum-value":
            section_name = f"{CHILD_CHAR}Field Option (value={parent_tag.get('value')})"
        elif parent_tag_name.endswith("-sect"):
            index = parent_tag.get("index")
            sect_tag_name = parent_tag_name
            if parent_tag_name == "fm-sect":
                sect_tag_name = parent_tag.parent.name

            section_name_from_tag = sect_tag_name[:sect_tag_name.find("-")]
            section_name = f"Form Section: {section_name_from_tag.capitalize()} (index={index})"

            if sect_tag_name == "objective-sect":
                obj_plan_id_tag = parent_tag.find("obj-sect-plan-id")
                if obj_plan_id_tag:
                    section_name = f"Form Section: {section_name_from_tag.capitalize()} (plan-id={obj_plan_id_tag.string})(index={index})"
            elif sect_tag_name == "objcomp-summary-sect":
                xaxis = parent_tag.find("x-axis")
                yaxis = parent_tag.find("y-axis")
                if xaxis and yaxis:
                    section_name = f"Form Section: {xaxis.string.capitalize()}(x) vs {yaxis.string.capitalize()}(y) Summary (index={index})"
                else:
                    section_name = f"Form Section: Objective vs Competency Summary (index={index})"
            elif sect_tag_name == "perfpot-summary-sect":
                section_name = f"Form Section: Performance-Potential Summary (index={index})"

        elif parent_tag_name == "fm-competency":
            comp_id_tag = parent_tag.find("fm-comp-id")
            if comp_id_tag:
                section_name = f"{CHILD_CHAR}Competency (id={comp_id_tag.string})"
        elif parent_tag_name == "fm-sect-config":
            section_name = f"{CHILD_CHAR}Section Configuration"
        elif parent_tag_name == "scale-map-value":
            section_name = "Scale Adjusted Calculation Mapping"
        else:
            section_name = self.get_readable_name(parent_tag_name)

        return section_name

    def derive_section_tag_name(self, section_name: str) -> str:
        """
        Derive tag name from section name.

        Args:
            section_name: Section display name

        Returns:
            Tag name string
        """
        if section_name.find("Form Section:") != -1:
            section_name = section_name[section_name.find(":") + 1:]
            section_name = section_name.lower().strip() + "-sect"
        elif section_name.find(CHILD_CHAR) != -1:
            section_name = section_name[section_name.find(CHILD_CHAR) + 1:]

        section_name = section_name.strip()

        if section_name == "Field Option":
            return "enum-value"
        elif section_name == "Competency":
            return "fm-competency"
        elif section_name == "Form Section: Performance-Potential Summary":
            return "perfpot-summary-sect"
        elif section_name.find("(x) vs ") > -1:
            return "objcomp-summary-sect"
        elif section_name == "Scale Adjusted Calculation Mapping":
            return "scale-map-value"
        elif section_name == "Section Configuration":
            return "fm-sect-config"
        else:
            words = section_name.casefold().split(" ")
            return "-".join(words)

    def get_missing_langs(self, label_tag, all_lang_ids: List[str]) -> List[str]:
        """
        Get languages missing translations for a tag.

        Args:
            label_tag: Label tag
            all_lang_ids: All language IDs to check

        Returns:
            List of missing language IDs
        """
        missing_langs = []
        parent_tag = label_tag.parent

        for lang in all_lang_ids:
            if parent_tag.find(attrs={"xml:lang": lang}, recursive=False) is None:
                missing_langs.append(lang)

        return missing_langs

    def get_lang_tag_of(
        self,
        tag,
        lang: str,
        lang_tag_name: str = "label"
    ):
        """
        Get the language-specific label tag for a given tag.

        Args:
            tag: Parent tag
            lang: Language code
            lang_tag_name: Name of the label tag

        Returns:
            Language label tag or None
        """
        for child_tag in tag.children:
            if (child_tag.name == lang_tag_name
                    and child_tag.has_attr("xml:lang")
                    and child_tag.get("xml:lang") == lang):
                return child_tag
        return None

    def create_data_model(
        self,
        file_path: str,
        is_standard: bool = False
    ) -> Optional[DataModel]:
        """
        Create a DataModel object from an XML file.

        Args:
            file_path: Path to XML file
            is_standard: Whether this is a standard SAP model

        Returns:
            DataModel object or None
        """
        soup, parser = self.read_xml_file(file_path)
        if soup is None:
            return None

        model_type = DataModel.detect_type(soup)
        name = self.detect_data_model_name(soup, is_standard, file_path)

        if name is None:
            return None

        return DataModel(
            name=name,
            soup=soup,
            model_type=model_type,
            is_standard=is_standard,
            file_path=file_path
        )

    def extract_tag_names_with_counts(self, soup: BeautifulSoup) -> Dict[str, int]:
        """
        Extract all tag names with their occurrence counts.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary of tag names to counts
        """
        tag_counts = {}
        tag_names = []

        for tag in soup.find_all():
            tag_name = tag.name
            if tag_name not in tag_names:
                count = len(soup.find_all(tag_name))
                tag_names.append(tag_name)
                tag_counts[tag_name] = count

        return tag_counts

    def find_translatable_tag_names(self, soup: BeautifulSoup) -> List[str]:
        """
        Find all translatable tag names in the soup.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of translatable tag names
        """
        translatable_tags = []

        for tag in soup.find_all():
            tag_name = tag.name
            if tag_name == "role-name" or tag_name == "meta-grp-label":
                continue

            if (tag_name in ["instruction", "label", "text", "default-rating", "unrated-rating"]
                    or "-name" in tag_name
                    or "-label" in tag_name
                    or "-intro" in tag_name
                    or "-desc" in tag_name):
                if tag_name not in translatable_tags:
                    translatable_tags.append(tag_name)

        return translatable_tags
