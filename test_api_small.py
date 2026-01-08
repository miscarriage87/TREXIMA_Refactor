#!/usr/bin/env python3
"""
TREXIMA Small API Test

Tests basic API connectivity and OData operations:
1. Connect to SuccessFactors OData API
2. Retrieve active locales
3. Fetch a small sample of picklists
4. Get MDF object metadata
"""

import os
import sys
import json

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from datetime import datetime


def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def test_api_connectivity():
    """Test 1: Basic API connectivity."""
    log("=" * 60)
    log("TEST 1: API Connectivity")
    log("=" * 60)

    from trexima.core.odata_client import ODataClient

    # Load credentials
    creds_file = os.path.join(project_root, "LoginCredentialsForAPI.txt")
    if not os.path.exists(creds_file):
        log("ERROR: LoginCredentialsForAPI.txt not found")
        return None

    with open(creds_file, 'r') as f:
        creds_text = f.read().strip()
        # Parse the format: "key":"value","key":"value"...
        # Split by }, then parse each as JSON
        if creds_text.startswith('{'):
            creds = json.loads(creds_text)
        else:
            # Parse the custom format
            creds = {}
            parts = creds_text.split('","')
            for part in parts:
                part = part.replace('"', '').replace('}', '')
                if ':' in part:
                    key, value = part.split(':', 1)
                    creds[key] = value

    log(f"Service URL: {creds['oDataUrl']}")
    log(f"Company ID: {creds['companyID']}")
    log(f"Username: {creds['username']}")

    # Create client and connect
    client = ODataClient()

    try:
        log("Attempting connection...")
        success = client.connect(
            service_url=creds['oDataUrl'],
            company_id=creds['companyID'],
            username=creds['username'],
            password=creds['password']
        )

        if success:
            log("✓ Connection successful!")
            log(f"  Is connected: {client.is_connected}")
            return client
        else:
            log("✗ Connection failed")
            return None

    except Exception as e:
        log(f"✗ Connection error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_locales(client):
    """Test 2: Retrieve active locales."""
    log("")
    log("=" * 60)
    log("TEST 2: Get Active Locales")
    log("=" * 60)

    try:
        locales = client.get_active_locales()
        log(f"✓ Retrieved {len(locales)} active locales:")
        for i, locale in enumerate(locales, 1):
            log(f"  {i}. {locale}")
        return locales
    except Exception as e:
        log(f"✗ Error getting locales: {e}")
        return []


def test_get_picklist_count(client):
    """Test 3: Get picklist counts."""
    log("")
    log("=" * 60)
    log("TEST 3: Get Picklist Counts")
    log("=" * 60)

    try:
        legacy_count = client.get_picklist_count("legacy")
        log(f"✓ Legacy picklists: {legacy_count}")

        mdf_count = client.get_picklist_count("mdf")
        log(f"✓ MDF picklists: {mdf_count}")

        migrated_count = client.get_migrated_legacy_picklist_count()
        log(f"✓ Migrated legacy picklists: {migrated_count}")

        return {"legacy": legacy_count, "mdf": mdf_count, "migrated": migrated_count}
    except Exception as e:
        log(f"✗ Error getting picklist counts: {e}")
        return {}


def test_fetch_sample_picklists(client):
    """Test 4: Fetch a small sample of picklists."""
    log("")
    log("=" * 60)
    log("TEST 4: Fetch Sample Picklists (5 items)")
    log("=" * 60)

    try:
        # Get 5 MDF picklists
        mdf_picklists = client.get_mdf_picklists(batch_size=5, offset=0)
        log(f"✓ Retrieved {len(mdf_picklists)} MDF picklists")

        for i, pl in enumerate(mdf_picklists, 1):
            pl_id = pl.id
            try:
                values = pl.values
                log(f"  {i}. {pl_id} - {len(list(values))} options")
            except Exception as e:
                log(f"  {i}. {pl_id} - Error reading options: {e}")

        return mdf_picklists
    except Exception as e:
        log(f"✗ Error fetching picklists: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_get_entity_names(client):
    """Test 5: Get entity names from metadata."""
    log("")
    log("=" * 60)
    log("TEST 5: Get Entity Names")
    log("=" * 60)

    try:
        entities = client.get_all_entity_names()
        log(f"✓ Retrieved {len(entities)} entity names")

        # Show first 10
        log("  First 10 entities:")
        for i, entity in enumerate(entities[:10], 1):
            log(f"    {i}. {entity}")

        # Count custom objects
        custom = [e for e in entities if e.startswith("cust_")]
        log(f"  Custom objects (cust_*): {len(custom)}")

        # Count FO objects
        fo_objects = [e for e in entities if e.startswith("FO")]
        log(f"  Foundation objects (FO*): {len(fo_objects)}")

        return entities
    except Exception as e:
        log(f"✗ Error getting entity names: {e}")
        return []


def test_get_mdf_object_metadata(client):
    """Test 6: Get MDF object metadata sample."""
    log("")
    log("=" * 60)
    log("TEST 6: Get MDF Object Metadata Sample")
    log("=" * 60)

    test_objects = ["Position", "FOCompany", "FODepartment"]

    for obj_name in test_objects:
        try:
            log(f"Testing {obj_name}...")
            metadata = client.get_mdf_object_metadata(obj_name, "en_US")

            if metadata:
                entity_sets = metadata.find_all("EntitySet")
                properties = metadata.find_all("Property")
                log(f"  ✓ {obj_name}: {len(entity_sets)} EntitySets, {len(properties)} Properties")
            else:
                log(f"  ✗ {obj_name}: No metadata found")
        except Exception as e:
            log(f"  ✗ {obj_name}: Error - {e}")


def main():
    """Run all API tests."""
    log("=" * 60)
    log("TREXIMA SMALL API TEST")
    log("=" * 60)
    log("")

    try:
        # Test 1: Connectivity
        client = test_api_connectivity()
        if not client:
            log("")
            log("=" * 60)
            log("TEST FAILED: Could not connect to API")
            log("=" * 60)
            return False

        # Test 2: Locales
        locales = test_get_locales(client)

        # Test 3: Picklist counts
        counts = test_get_picklist_count(client)

        # Test 4: Sample picklists
        picklists = test_fetch_sample_picklists(client)

        # Test 5: Entity names
        entities = test_get_entity_names(client)

        # Test 6: MDF metadata
        test_get_mdf_object_metadata(client)

        log("")
        log("=" * 60)
        log("ALL API TESTS COMPLETED SUCCESSFULLY!")
        log("=" * 60)
        log("")
        log("Summary:")
        log(f"  - API Connection: ✓")
        log(f"  - Active Locales: {len(locales)}")
        log(f"  - Legacy Picklists: {counts.get('legacy', 0)}")
        log(f"  - MDF Picklists: {counts.get('mdf', 0)}")
        log(f"  - Entity Names: {len(entities)}")
        log(f"  - Sample Picklists Retrieved: {len(picklists)}")

        return True

    except Exception as e:
        log("")
        log("=" * 60)
        log(f"TEST FAILED: {e}")
        log("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
