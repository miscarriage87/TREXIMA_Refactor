"""
TREXIMA v2.0 - Constants and Configuration

Contains all static configuration data including:
- SuccessFactors API endpoints
- ODATA object definitions
- FO Translation types
- Application limits
"""

# =============================================================================
# APPLICATION LIMITS
# =============================================================================

MAX_PROJECTS_PER_USER = 3
FILE_RETENTION_DAYS = 90
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {'xml', 'xlsx', 'csv'}

DATA_MODEL_TYPES = ['sdm', 'cdm', 'ec_sdm', 'ec_cdm', 'picklist']

PROJECT_STATUSES = ['draft', 'configured', 'exported', 'imported']


# =============================================================================
# SUCCESSFACTORS API ENDPOINTS
# =============================================================================

SF_ENDPOINTS = {
    "production": {
        "label": "Production Datacenters",
        "endpoints": [
            {"id": "dc2", "name": "DC2 - US West (Chandler)", "url": "https://api2.successfactors.com/odata/v2", "region": "US"},
            {"id": "dc4", "name": "DC4 - US East (Ashburn)", "url": "https://api4.successfactors.com/odata/v2", "region": "US"},
            {"id": "dc5", "name": "DC5 - US East (Ashburn)", "url": "https://api5.successfactors.com/odata/v2", "region": "US"},
            {"id": "dc8", "name": "DC8 - US East (Sterling)", "url": "https://api8.successfactors.com/odata/v2", "region": "US"},
            {"id": "dc10", "name": "DC10 - EU Central (Amsterdam)", "url": "https://api10.successfactors.eu/odata/v2", "region": "EU"},
            {"id": "dc12", "name": "DC12 - EU Central (Frankfurt)", "url": "https://api12.successfactors.eu/odata/v2", "region": "EU"},
            {"id": "dc15", "name": "DC15 - EU West (London)", "url": "https://api15.successfactors.eu/odata/v2", "region": "EU"},
            {"id": "dc16", "name": "DC16 - EU Central (Frankfurt)", "url": "https://api16.successfactors.eu/odata/v2", "region": "EU"},
            {"id": "dc17", "name": "DC17 - APAC (Sydney)", "url": "https://api17.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc18", "name": "DC18 - APAC (Singapore)", "url": "https://api18.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc19", "name": "DC19 - APAC (Tokyo)", "url": "https://api19.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc22", "name": "DC22 - APAC (Seoul)", "url": "https://api22.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc23", "name": "DC23 - APAC (Osaka)", "url": "https://api23.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc24", "name": "DC24 - Middle East (Dubai)", "url": "https://api24.successfactors.com/odata/v2", "region": "MEA"},
            {"id": "dc25", "name": "DC25 - South America (São Paulo)", "url": "https://api25.successfactors.com/odata/v2", "region": "LATAM"},
            {"id": "dc27", "name": "DC27 - India (Mumbai)", "url": "https://api27.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc28", "name": "DC28 - Canada (Toronto)", "url": "https://api28.successfactors.com/odata/v2", "region": "NA"},
            {"id": "dc33", "name": "DC33 - Australia (Sydney)", "url": "https://api33.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc35", "name": "DC35 - US Gov Cloud", "url": "https://api35.successfactors.com/odata/v2", "region": "US-GOV"},
            {"id": "dc40", "name": "DC40 - China (Shanghai)", "url": "https://api40.successfactors.cn/odata/v2", "region": "CHINA"},
            {"id": "dc45", "name": "DC45 - Saudi Arabia (Riyadh)", "url": "https://api45.successfactors.com/odata/v2", "region": "MEA"},
            {"id": "dc55", "name": "DC55 - Switzerland (Zurich)", "url": "https://api55.successfactors.eu/odata/v2", "region": "EU"},
            {"id": "dc56", "name": "DC56 - India (Hyderabad)", "url": "https://api56.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc58", "name": "DC58 - South Korea (Seoul)", "url": "https://api58.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc61", "name": "DC61 - Hong Kong", "url": "https://api61.successfactors.com/odata/v2", "region": "APAC"},
            {"id": "dc68", "name": "DC68 - EU Central (Frankfurt)", "url": "https://api68.successfactors.eu/odata/v2", "region": "EU"},
            {"id": "dc69", "name": "DC69 - US East (Virginia)", "url": "https://api69.successfactors.com/odata/v2", "region": "US"},
            {"id": "dc70", "name": "DC70 - Indonesia (Jakarta)", "url": "https://api70.successfactors.com/odata/v2", "region": "APAC"}
        ]
    },
    "preview": {
        "label": "Preview/Sandbox Datacenters",
        "endpoints": [
            {"id": "dc2-preview", "name": "DC2 Preview (US West)", "url": "https://api2preview.sapsf.com/odata/v2", "region": "US"},
            {"id": "dc4-preview", "name": "DC4 Preview (US East)", "url": "https://api4preview.sapsf.com/odata/v2", "region": "US"},
            {"id": "dc10-preview", "name": "DC10 Preview (EU)", "url": "https://api10preview.sapsf.eu/odata/v2", "region": "EU"},
            {"id": "dc12-preview", "name": "DC12 Preview (EU)", "url": "https://api12preview.sapsf.eu/odata/v2", "region": "EU"},
            {"id": "dc17-preview", "name": "DC17 Preview (APAC)", "url": "https://api17preview.sapsf.com/odata/v2", "region": "APAC"},
            {"id": "dc18-preview", "name": "DC18 Preview (APAC)", "url": "https://api18preview.sapsf.com/odata/v2", "region": "APAC"}
        ]
    },
    "salesdemo": {
        "label": "Salesdemo Instances",
        "endpoints": [
            {"id": "salesdemo2", "name": "Salesdemo 2 (EU)", "url": "https://apisalesdemo2.successfactors.eu/odata/v2", "region": "EU"},
            {"id": "salesdemo4", "name": "Salesdemo 4 (US)", "url": "https://apisalesdemo4.successfactors.com/odata/v2", "region": "US"},
            {"id": "salesdemo8", "name": "Salesdemo 8 (APAC)", "url": "https://apisalesdemo8.successfactors.com/odata/v2", "region": "APAC"}
        ]
    },
    "custom": {
        "label": "Custom URL",
        "endpoints": [
            {"id": "custom", "name": "Enter custom endpoint URL", "url": "", "region": "CUSTOM"}
        ]
    }
}


# =============================================================================
# ODATA OBJECT CATEGORIES
# =============================================================================

EC_CORE_OBJECTS = [
    {"id": "PerPersonal", "name": "Personal Information", "description": "Basic personal data (name, DOB, gender, etc.)"},
    {"id": "PerEmail", "name": "Email Information", "description": "Email addresses"},
    {"id": "PerPhone", "name": "Phone Information", "description": "Phone numbers"},
    {"id": "PerAddressDeflt", "name": "Address Information", "description": "Physical addresses"},
    {"id": "PerEmergencyContacts", "name": "Emergency Contacts", "description": "Emergency contact details"},
    {"id": "PerNationalId", "name": "National ID", "description": "National identification numbers"},
    {"id": "EmpJob", "name": "Job Information", "description": "Employment and job data"},
    {"id": "EmpCompensation", "name": "Compensation Information", "description": "Salary and pay data"},
    {"id": "EmpPayCompRecurring", "name": "Recurring Pay Components", "description": "Recurring payments"},
    {"id": "EmpPayCompNonRecurring", "name": "Non-Recurring Pay Components", "description": "One-time payments"},
    {"id": "EmpWorkPermit", "name": "Work Permits", "description": "Work authorization documents"},
    {"id": "EmpGlobalAssignment", "name": "Global Assignments", "description": "International assignments"},
    {"id": "EmpJobRelationships", "name": "Job Relationships", "description": "Reporting relationships"},
    {"id": "PerGlobalInfoCHE", "name": "Switzerland Specific", "description": "CH country-specific fields"},
    {"id": "PerGlobalInfoDEU", "name": "Germany Specific", "description": "DE country-specific fields"},
    {"id": "PerGlobalInfoFRA", "name": "France Specific", "description": "FR country-specific fields"},
    {"id": "PerGlobalInfoGBR", "name": "UK Specific", "description": "GB country-specific fields"},
    {"id": "PerGlobalInfoUSA", "name": "USA Specific", "description": "US country-specific fields"},
    {"id": "PerGlobalInfoAUT", "name": "Austria Specific", "description": "AT country-specific fields"},
    {"id": "PerGlobalInfoNLD", "name": "Netherlands Specific", "description": "NL country-specific fields"},
    {"id": "PerGlobalInfoBEL", "name": "Belgium Specific", "description": "BE country-specific fields"},
    {"id": "PerGlobalInfoITA", "name": "Italy Specific", "description": "IT country-specific fields"},
    {"id": "PerGlobalInfoESP", "name": "Spain Specific", "description": "ES country-specific fields"}
]

FOUNDATION_OBJECTS = [
    # Organizational Structure
    {"id": "FOBusinessUnit", "name": "Business Units", "translatable": True, "description": "Organizational business units"},
    {"id": "FOCompany", "name": "Companies", "translatable": True, "description": "Legal company entities"},
    {"id": "FOCorporateAddressDeflt", "name": "Corporate Addresses", "translatable": True, "description": "Corporate address definitions"},
    {"id": "FOCostCenter", "name": "Cost Centers", "translatable": True, "description": "Cost center definitions"},
    {"id": "FODepartment", "name": "Departments", "translatable": True, "description": "Organizational departments"},
    {"id": "FODivision", "name": "Divisions", "translatable": True, "description": "Company divisions"},
    {"id": "FOLegalEntity", "name": "Legal Entities", "translatable": True, "description": "Legal entity structures"},
    # Jobs & Positions
    {"id": "FOEmployeeClass", "name": "Employee Classes", "translatable": True, "description": "Employee classification types"},
    {"id": "FOJobClassification", "name": "Job Classifications", "translatable": True, "description": "Job classification categories"},
    {"id": "FOJobClassLocalDEU", "name": "Job Classes (DE)", "translatable": True, "description": "German job classifications"},
    {"id": "FOJobClassLocalESP", "name": "Job Classes (ES)", "translatable": True, "description": "Spanish job classifications"},
    {"id": "FOJobClassLocalFRA", "name": "Job Classes (FR)", "translatable": True, "description": "French job classifications"},
    {"id": "FOJobClassLocalGBR", "name": "Job Classes (UK)", "translatable": True, "description": "UK job classifications"},
    {"id": "FOJobClassLocalITA", "name": "Job Classes (IT)", "translatable": True, "description": "Italian job classifications"},
    {"id": "FOJobClassLocalUSA", "name": "Job Classes (US)", "translatable": True, "description": "US job classifications"},
    {"id": "FOJobCode", "name": "Job Codes", "translatable": True, "description": "Job code definitions"},
    {"id": "FOJobFunction", "name": "Job Functions", "translatable": True, "description": "Job function categories"},
    {"id": "FOPosition", "name": "Positions", "translatable": False, "description": "Position definitions"},
    # Locations
    {"id": "FOGeozone", "name": "Geo Zones", "translatable": True, "description": "Geographic zones"},
    {"id": "FOLocation", "name": "Locations", "translatable": True, "description": "Physical locations"},
    {"id": "FOLocationAddress", "name": "Location Addresses", "translatable": False, "description": "Physical address details for locations"},
    {"id": "FOLocationGroup", "name": "Location Groups", "translatable": True, "description": "Location group definitions"},
    # Compensation
    {"id": "FOEventReason", "name": "Event Reasons", "translatable": True, "description": "HR event reasons"},
    {"id": "FOFrequency", "name": "Frequencies", "translatable": True, "description": "Pay frequencies"},
    {"id": "FOPayComponent", "name": "Pay Components", "translatable": True, "description": "Pay component definitions"},
    {"id": "FOPayComponentGroup", "name": "Pay Component Groups", "translatable": True, "description": "Pay component groupings"},
    {"id": "FOPayGrade", "name": "Pay Grades", "translatable": True, "description": "Pay grade levels"},
    {"id": "FOPayRange", "name": "Pay Ranges", "translatable": True, "description": "Pay range definitions"},
    # Time Management
    {"id": "Holiday", "name": "Holidays", "translatable": True, "description": "Holiday definitions"},
    {"id": "TimeType", "name": "Time Types", "translatable": True, "description": "Time recording types"},
]


# =============================================================================
# FO TRANSLATION TYPES (User-selectable)
# =============================================================================

FO_TRANSLATION_TYPES = [
    {
        "id": "eventReason",
        "name": "Event Reasons",
        "object": "FOEventReason",
        "field": "name",
        "description": "Reasons for HR events (hire, termination, transfer, etc.)"
    },
    {
        "id": "frequency",
        "name": "Frequencies",
        "object": "FOFrequency",
        "field": "name",
        "description": "Pay frequencies (monthly, bi-weekly, etc.)"
    },
    {
        "id": "geozone",
        "name": "Geo Zones",
        "object": "FOGeozone",
        "field": "name",
        "description": "Geographic zones for assignment purposes"
    },
    {
        "id": "locationGroup",
        "name": "Location Groups",
        "object": "FOLocationGroup",
        "field": "name",
        "description": "Groups of related locations"
    },
    {
        "id": "location",
        "name": "Locations",
        "object": "FOLocation",
        "field": "name",
        "description": "Physical work locations"
    },
    {
        "id": "payComponent",
        "name": "Pay Components",
        "object": "FOPayComponent",
        "field": "name",
        "description": "Compensation pay components"
    },
    {
        "id": "payComponentGroup",
        "name": "Pay Component Groups",
        "object": "FOPayComponentGroup",
        "field": "name",
        "description": "Groupings of pay components"
    },
    {
        "id": "payGrade",
        "name": "Pay Grades",
        "object": "FOPayGrade",
        "field": "name",
        "description": "Pay grade levels"
    },
    {
        "id": "payRange",
        "name": "Pay Ranges",
        "object": "FOPayRange",
        "field": "name",
        "description": "Salary ranges for pay grades"
    }
]


# =============================================================================
# LANGUAGE/LOCALE MAPPING
# =============================================================================

LOCALE_NAMES = {
    "en_US": "English (US)",
    "en_GB": "English (UK)",
    "de_DE": "German (Germany)",
    "de_AT": "German (Austria)",
    "de_CH": "German (Switzerland)",
    "fr_FR": "French (France)",
    "fr_CA": "French (Canada)",
    "fr_BE": "French (Belgium)",
    "fr_CH": "French (Switzerland)",
    "es_ES": "Spanish (Spain)",
    "es_MX": "Spanish (Mexico)",
    "it_IT": "Italian (Italy)",
    "pt_PT": "Portuguese (Portugal)",
    "pt_BR": "Portuguese (Brazil)",
    "nl_NL": "Dutch (Netherlands)",
    "nl_BE": "Dutch (Belgium)",
    "pl_PL": "Polish",
    "cs_CZ": "Czech",
    "hu_HU": "Hungarian",
    "ro_RO": "Romanian",
    "ru_RU": "Russian",
    "uk_UA": "Ukrainian",
    "ja_JP": "Japanese",
    "zh_CN": "Chinese (Simplified)",
    "zh_TW": "Chinese (Traditional)",
    "ko_KR": "Korean",
    "th_TH": "Thai",
    "vi_VN": "Vietnamese",
    "id_ID": "Indonesian",
    "ms_MY": "Malay",
    "ar_SA": "Arabic (Saudi Arabia)",
    "he_IL": "Hebrew",
    "tr_TR": "Turkish",
    "el_GR": "Greek",
    "sv_SE": "Swedish",
    "no_NO": "Norwegian",
    "da_DK": "Danish",
    "fi_FI": "Finnish",
    "hi_IN": "Hindi",
    "bn_IN": "Bengali",
    "ta_IN": "Tamil",
    "te_IN": "Telugu"
}


def get_locale_name(locale_code: str) -> str:
    """Get human-readable name for a locale code."""
    return LOCALE_NAMES.get(locale_code, locale_code)


def get_all_endpoints_flat() -> list:
    """Get all endpoints as a flat list."""
    endpoints = []
    for category in SF_ENDPOINTS.values():
        endpoints.extend(category['endpoints'])
    return endpoints


def get_endpoint_by_id(endpoint_id: str) -> dict:
    """Get endpoint details by ID."""
    for category in SF_ENDPOINTS.values():
        for endpoint in category['endpoints']:
            if endpoint['id'] == endpoint_id:
                return endpoint
    return None


def get_endpoint_by_url(url: str) -> dict:
    """Get endpoint details by URL."""
    for category in SF_ENDPOINTS.values():
        for endpoint in category['endpoints']:
            if endpoint['url'] == url:
                return endpoint
    return None
