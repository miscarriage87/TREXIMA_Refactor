"""
Data Model Processor Module

Processes SF data model XML files.
"""

from typing import List, Optional, Dict, Any, Tuple
from bs4 import BeautifulSoup

from ..config import (
    EMPLOYEE_PROFILE_TAGS,
    TAGS_TO_BE_IGNORED,
    CHILD_CHAR,
    AppPaths
)
from ..models.datamodel import DataModel, DataModelType, TranslatableTag
from ..io.xml_handler import XMLHandler


class DataModelProcessor:
    """Processes SuccessFactors data model XML files."""

    def __init__(self, app_paths: Optional[AppPaths] = None):
        self.app_paths = app_paths or AppPaths()
        self.xml_handler = XMLHandler()
        self.data_models: Dict[str, DataModel] = {}
        self.translatable_tags: List[str] = []
        self.is_pmgm_included = False
        self.is_sdm_included = False

    def load_data_model(
        self,
        file_path: str,
        is_standard: bool = False
    ) -> Optional[DataModel]:
        """
        Load a data model from an XML file.

        Args:
            file_path: Path to the XML file
            is_standard: Whether this is a standard SAP model

        Returns:
            DataModel object or None
        """
        data_model = self.xml_handler.create_data_model(file_path, is_standard)

        if data_model:
            # Update flags based on model type
            if data_model.model_type in [
                DataModelType.PM_FORM_TEMPLATE,
                DataModelType.GOAL_PLAN_TEMPLATE,
                DataModelType.DEVELOPMENT_PLAN_TEMPLATE
            ]:
                self.is_pmgm_included = True

            if data_model.model_type in [
                DataModelType.SUCCESSION_DATA_MODEL,
                DataModelType.SFEC_SUCCESSION_DATA_MODEL,
                DataModelType.SFEC_CSF_SUCCESSION_DATA_MODEL
            ]:
                self.is_sdm_included = True

            # Extract translatable tags
            tag_names = self.xml_handler.find_translatable_tag_names(data_model.soup)
            for tag in tag_names:
                if tag not in self.translatable_tags:
                    self.translatable_tags.append(tag)

            # Store in dictionary
            self.data_models[data_model.name] = data_model

        return data_model

    def load_standard_data_models(self) -> List[DataModel]:
        """
        Load all standard SAP data models.

        Returns:
            List of loaded DataModel objects
        """
        models = []
        for path in self.app_paths.get_standard_dm_paths():
            model = self.load_data_model(path, is_standard=True)
            if model:
                models.append(model)
        return models

    def get_data_model(self, name: str) -> Optional[DataModel]:
        """Get a data model by name."""
        return self.data_models.get(name)

    def get_all_data_models(self, include_standard: bool = False) -> List[DataModel]:
        """
        Get all loaded data models.

        Args:
            include_standard: Include standard SAP models

        Returns:
            List of DataModel objects
        """
        if include_standard:
            return list(self.data_models.values())
        return [dm for dm in self.data_models.values() if not dm.is_standard]

    def find_references_of_tag(
        self,
        tag_name: str,
        tags_to_ignore: Optional[List[str]] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Find all references of a specific tag type.

        Args:
            tag_name: Tag name to search for
            tags_to_ignore: Tags to skip

        Returns:
            Tuple of (tag IDs, references)
        """
        if tags_to_ignore is None:
            tags_to_ignore = TAGS_TO_BE_IGNORED

        references = []
        tag_ids = []

        for data_model in self.get_all_data_models():
            matching_tags = data_model.soup.find_all(tag_name)

            for matching_tag in matching_tags:
                tag_id = matching_tag.get("id")
                if tag_name == "trigger-rule":
                    tag_id = f"{matching_tag.get('rule')}({matching_tag.get('event')})"

                parent_tag = matching_tag.parent
                parent_tag_id = parent_tag.get("id")
                parent_tag_name = parent_tag.name
                visibility = parent_tag.get("visibility")

                if visibility == "none" or parent_tag_name in tags_to_ignore:
                    continue

                section_name = ""
                field_name = self.xml_handler.get_default_title(parent_tag)

                if parent_tag_name in EMPLOYEE_PROFILE_TAGS:
                    section_name = "Employee Profile -> "
                    ep_parent = parent_tag.parent
                    bg_element_id = ep_parent.get("id")
                    if ep_parent.name == "background-element":
                        section_name += f"Background Element -> {field_name} ({bg_element_id})"
                    elif parent_tag_name == "userinfo-element":
                        section_name += "User-Info Element"

                elif parent_tag_name.startswith("hris"):
                    section_name = "Employee Central (GLOBAL) -> "
                    hris_parent = parent_tag.parent

                    if hris_parent.name == "hris-section":
                        ec_section_name = self.xml_handler.get_default_title(hris_parent)
                        ec_portlet = hris_parent.parent
                        ec_portlet_name = self.xml_handler.get_default_title(ec_portlet)

                        if ec_portlet.name == "country":
                            section_name = f"Employee Central ({hris_parent.parent.parent.get('id')}) -> "

                        section_name += f"{ec_portlet_name} (Portlet) -> "
                        section_name += f"{ec_section_name} (Section)"

                    elif hris_parent.name == "hris-element":
                        if hris_parent.parent.name == "country":
                            section_name = f"Employee Central ({hris_parent.parent.get('id')}) -> "
                        section_name += f"{self.xml_handler.get_default_title(hris_parent)} (Portlet)"

                reference = f"{section_name} -> {field_name} | "
                tag_ids.append(tag_id)
                references.append(reference)

        return tag_ids, references

    def find_picklist_references(self) -> Tuple[List[str], List[str]]:
        """
        Find all picklist references in data models.

        Returns:
            Tuple of (picklist IDs, references)
        """
        return self.find_references_of_tag("picklist")

    def find_rule_references(self) -> Tuple[List[str], List[str]]:
        """
        Find all trigger rule references in data models.

        Returns:
            Tuple of (rule IDs, references)
        """
        return self.find_references_of_tag("trigger-rule")

    def extract_all_languages(self) -> List[str]:
        """
        Extract all unique languages from all data models.

        Returns:
            List of language codes
        """
        all_langs = []
        for data_model in self.get_all_data_models():
            langs = data_model.extract_languages()
            for lang in langs:
                if lang not in all_langs:
                    all_langs.append(lang)
        return all_langs

    def get_section_info(
        self,
        tag,
        config_name: str,
        active_countries: List[str] = None
    ) -> Tuple[str, str, str, bool]:
        """
        Get section information for a translatable tag.

        Args:
            tag: BeautifulSoup tag
            config_name: Configuration name
            active_countries: List of active country codes

        Returns:
            Tuple of (section_name, subsection_name, country_code, skip_country)
        """
        parent_tag = tag.parent
        parent_tag_name = parent_tag.name
        grand_parent = parent_tag.parent

        section_name = ""
        subsection_name = parent_tag_name
        country_code = ""
        skip_country = False

        if parent_tag_name in EMPLOYEE_PROFILE_TAGS:
            section_name = "Employee Profile"

        elif parent_tag_name.startswith("hris") or parent_tag_name == "format":
            if " CSF " in config_name:
                is_grand_child_of_country = False

                if grand_parent.name == "hris-section":
                    country_code = grand_parent.parent.parent.get("id")
                elif grand_parent.name in ["hris-element", "format-group"]:
                    country_code = grand_parent.parent.get("id")
                    is_grand_child_of_country = True
                elif parent_tag_name in ["hris-element", "format-group"]:
                    country_code = grand_parent.get("id")

                if active_countries and country_code not in active_countries:
                    skip_country = True

                section_name = f"{config_name} ({country_code})"
            else:
                section_name = config_name
        else:
            section_name = config_name
            subsection_name = self.xml_handler.get_module_specific_name(parent_tag)

        return section_name, subsection_name, country_code, skip_country

    def find_matching_tag_in_standard(
        self,
        data_model: DataModel,
        tag_name: str,
        tag_id: str
    ) -> Optional[Any]:
        """
        Find matching tag in standard data model.

        Args:
            data_model: Source data model
            tag_name: Tag name to find
            tag_id: Tag ID to match

        Returns:
            Matching tag or None
        """
        standard_name = f"Standard SAP {data_model.get_type_name()}"
        standard_model = self.data_models.get(standard_name)

        if standard_model:
            return standard_model.soup.find(name=tag_name, attrs={"id": tag_id})

        return None

    def reset(self):
        """Reset processor state."""
        self.data_models = {}
        self.translatable_tags = []
        self.is_pmgm_included = False
        self.is_sdm_included = False
