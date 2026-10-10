"""Export the M11-02 data and API inventory without reading business rows."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from common.asset_inventory import build_inventory, validate_inventory


class Command(BaseCommand):
    help = "Validate and optionally export metadata-only data and API asset inventory"

    def add_arguments(self, parser):
        parser.add_argument("--output", type=Path, help="JSON output path; omitted for read-only validation")

    def handle(self, *args, **options):
        inventory = build_inventory()
        issues = validate_inventory(inventory)
        if issues:
            raise CommandError("\n".join(issues[:30]))
        output = options["output"]
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(
            f"PASS: {len(inventory['models'])} models, {len(inventory['api_routes'])} API routes; "
            f"SHA-256 {inventory['sha256']}"
        ))
