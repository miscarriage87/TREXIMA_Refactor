"""
OData Client Module

Handles communication with SAP SuccessFactors OData API.
"""

from typing import List, Optional, Dict, Any
import requests
import pyodata
from bs4 import BeautifulSoup

from ..config import ODataConfig


class ODataClient:
    """Client for SAP SuccessFactors OData API."""

    def __init__(self, config: Optional[ODataConfig] = None):
        self.config = config
        self.service = None
        self.session = None
        self._connected = False

    def connect(
        self,
        service_url: str = None,
        company_id: str = None,
        username: str = None,
        password: str = None
    ) -> bool:
        """
        Connect to the OData service.

        Args:
            service_url: OData service URL
            company_id: SF company ID
            username: API username
            password: API password

        Returns:
            True if connection successful

        Raises:
            pyodata.exceptions.HttpError: If connection fails
        """
        if self.config and not service_url:
            service_url = self.config.service_url
            company_id = self.config.company_id
            username = self.config.username
            password = self.config.password

        self.session = requests.Session()
        self.session.auth = (f"{username}@{company_id}", password)

        self.service = pyodata.Client(service_url, self.session)
        self._connected = True
        return True

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self.service is not None

    def disconnect(self):
        """Disconnect from the OData service."""
        if self.session:
            self.session.close()
        self.service = None
        self.session = None
        self._connected = False

    def get_active_locales(self) -> List[str]:
        """
        Get list of active locales from the SF instance.

        Returns:
            List of locale codes (e.g., ['en_US', 'de_DE'])
        """
        if not self.is_connected:
            return []

        default_langs = ["defaultValue", "localized", "en_DEBUG"]
        checklist = [f"label_{lang}" for lang in default_langs]

        try:
            properties = self.service.schema.entity_type("PickListValueV2").proprties()
            active_locales = []

            for prop in properties:
                prop_name = prop.name
                if prop_name.startswith("label_") and prop_name not in checklist:
                    active_locales.append(prop_name[6:])

            return active_locales
        except Exception:
            return []

    def get_all_entity_names(self) -> List[str]:
        """Get list of all entity set names."""
        if not self.is_connected:
            return []

        try:
            return [es.name for es in self.service.schema.entity_sets]
        except Exception:
            return []

    def get_mdf_object_metadata(
        self,
        object_name: str,
        language: str = None
    ) -> Optional[BeautifulSoup]:
        """
        Get metadata for an MDF object.

        Args:
            object_name: Entity name
            language: Language code for labels

        Returns:
            BeautifulSoup object of metadata XML
        """
        if not self.is_connected:
            return None

        try:
            lang_param = f"?sap-language={language}" if language else ""
            response = self.service.http_get(
                f"/{object_name}/$metadata{lang_param}"
            )
            return BeautifulSoup(response.text, "xml")
        except Exception:
            return None

    def get_picklist_count(self, picklist_type: str = "mdf") -> int:
        """
        Get count of picklists.

        Args:
            picklist_type: 'mdf' or 'legacy'

        Returns:
            Count of picklists
        """
        if not self.is_connected:
            return 0

        try:
            if picklist_type == "mdf":
                return self.service.entity_sets.PickListV2.get_entities().count().execute()
            else:
                return self.service.entity_sets.Picklist.get_entities().count().execute()
        except Exception:
            return 0

    def get_migrated_legacy_picklist_count(self) -> int:
        """Get count of migrated legacy picklists."""
        if not self.is_connected:
            return 0

        try:
            return (self.service.entity_sets.PickListV2
                    .get_entities()
                    .count()
                    .filter("legacyPickListId ne null")
                    .execute())
        except Exception:
            return 0

    def get_mdf_picklists(
        self,
        top: int = 10,
        skip: int = 0
    ) -> List[Any]:
        """
        Get MDF picklists with values.

        Args:
            top: Number of items to fetch
            skip: Number of items to skip

        Returns:
            List of picklist entities
        """
        if not self.is_connected:
            return []

        try:
            return (self.service.entity_sets.PickListV2
                    .get_entities()
                    .top(top)
                    .skip(skip)
                    .expand("values")
                    .execute())
        except Exception:
            return []

    def get_legacy_picklists(
        self,
        top: int = 10,
        skip: int = 0
    ) -> List[Any]:
        """
        Get legacy picklists with options.

        Args:
            top: Number of items to fetch
            skip: Number of items to skip

        Returns:
            List of picklist entities
        """
        if not self.is_connected:
            return []

        try:
            return (self.service.entity_sets.Picklist
                    .get_entities()
                    .top(top)
                    .skip(skip)
                    .expand("picklistOptions/picklistLabels")
                    .execute())
        except Exception:
            return []

    def get_foundation_objects(
        self,
        entity_name: str,
        expand: Optional[List[str]] = None
    ) -> List[Any]:
        """
        Get foundation objects.

        Args:
            entity_name: Entity set name
            expand: List of navigation properties to expand

        Returns:
            List of entities
        """
        if not self.is_connected:
            return []

        try:
            entity_sets = self.service.entity_sets.__dict__["_entity_sets"]
            query = entity_sets[entity_name].get_entities()

            if expand:
                query = query.expand(",".join(expand))

            return query.execute()
        except Exception:
            return []

    def get_entity_metadata(self, entity_name: str) -> Optional[Any]:
        """
        Get entity type metadata.

        Args:
            entity_name: Entity name

        Returns:
            Entity type metadata or None
        """
        if not self.is_connected:
            return None

        try:
            return self.service.schema.entity_type(entity_name)
        except Exception:
            return None

    def get_translatable_properties(
        self,
        entity_name: str,
        system_langs: List[str]
    ) -> tuple[List[str], List[str]]:
        """
        Get translatable properties for an entity.

        Args:
            entity_name: Entity name
            system_langs: List of system languages

        Returns:
            Tuple of (translatable properties, translatable fields)
        """
        metadata = self.get_entity_metadata(entity_name)
        if not metadata:
            return [], []

        translatable_props = []
        translatable_fields = []

        all_properties = [prop.name for prop in metadata.proprties()]

        for prop in all_properties:
            for lang in system_langs:
                if prop.endswith(f"_{lang}"):
                    translatable_props.append(prop)
                    field_name = prop[:prop.find("_")]
                    if field_name not in translatable_fields:
                        translatable_fields.append(field_name)

        return translatable_props, translatable_fields

    def has_name_translation_nav(self, entity_name: str) -> bool:
        """Check if entity has nameTranslationNav property."""
        metadata = self.get_entity_metadata(entity_name)
        if not metadata:
            return False

        nav_properties = [prop.name for prop in metadata.nav_proprties]
        return "nameTranslationNav" in nav_properties
