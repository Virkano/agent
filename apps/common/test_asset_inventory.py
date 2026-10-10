import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import SimpleTestCase

from common.asset_inventory import build_inventory, validate_inventory


class AssetInventoryTests(SimpleTestCase):
    def test_registered_models_and_routes_have_owners(self):
        inventory = build_inventory()
        self.assertFalse(validate_inventory(inventory))
        self.assertGreater(len(inventory["models"]), 100)
        self.assertGreater(len(inventory["api_routes"]), 500)
        self.assertTrue(all(item["owner_role"] != "待指定" for item in inventory["models"]))

    def test_master_data_read_audit_is_marked_partial(self):
        inventory = build_inventory()
        masters = {item["model"]: item for item in inventory["models"] if item["master_data"]}
        self.assertEqual(set(masters), {"users.User", "marketing.MarketingCustomer"})
        self.assertTrue(all(item["read_access_audit_status"] == "DIRECT_API_PARTIAL" for item in masters.values()))

    def test_inventory_is_stable_and_metadata_only(self):
        first = build_inventory()
        second = build_inventory()
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(first, second)
        self.assertTrue(all("sensitive_field_names" in item for item in first["models"]))
        self.assertTrue(all(item["lake_mapping_status"] == "PROPOSED_NOT_CONNECTED" for item in first["models"]))
        self.assertTrue(all("eop_registration_status" in item for item in first["api_routes"]))
        self.assertTrue(all("interface_layer" in item for item in first["api_routes"]))

    def test_management_command_exports_matching_snapshot(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            call_command("export_asset_inventory", output=output)
            exported = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(exported["sha256"], build_inventory()["sha256"])
