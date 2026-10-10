#!/usr/bin/env python3
"""Run a secret-safe deployment gate before starting the container."""

import argparse
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps"))

from django.core.exceptions import ImproperlyConfigured  # noqa: E402
from telecom_ai_agent.deployment import deployment_settings  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="M11 deployment security preflight")
    parser.add_argument("--production", action="store_true", help="require production settings")
    args = parser.parse_args()

    dockerfile = (ROOT / "docker" / "Dockerfile.app").read_text(encoding="utf-8")
    compose_file = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    if "/.env*" not in dockerignore:
        print("FAIL: Docker build context does not exclude root environment files", file=sys.stderr)
        return 1
    if re.search(r"(?m)^\s*JB_(?:DB|REDIS)_PASSWORD\s*=", dockerfile):
        print("FAIL: Docker image embeds a database or Redis password default", file=sys.stderr)
        return 1
    if re.search(r"(?m)^  (?:postgres|redis):\s*$", compose_file):
        print("FAIL: application Compose file must not define PostgreSQL or Redis services", file=sys.stderr)
        return 1
    exposed_ports = re.findall(r"(?m)^EXPOSE\s+(.+)$", dockerfile)
    if exposed_ports != ["8080"]:
        print("FAIL: business image must expose only port 8080", file=sys.stderr)
        return 1
    if "JB_START_LOCAL_MODEL=true" not in dockerfile or "JB_LOCAL_MODEL_HOST=127.0.0.1" not in dockerfile:
        print("FAIL: business image must start the internal vector service", file=sys.stderr)
        return 1
    if "/docker/initdb.sql" not in dockerignore:
        print("FAIL: database dump must not be copied into the business image", file=sys.stderr)
        return 1
    config_source = (ROOT / "apps" / "telecom_ai_agent" / "conf.py").read_text(encoding="utf-8")
    if re.search(r'(?m)^\s*["\'](?:DB|REDIS)_PASSWORD["\']\s*:', config_source):
        print("FAIL: common configuration embeds a database or Redis password default", file=sys.stderr)
        return 1

    env = dict(os.environ)
    if args.production:
        env["JB_DEPLOYMENT_MODE"] = "production"
    is_production = env.get("JB_DEPLOYMENT_MODE", "local").strip().lower() == "production"
    try:
        resolved = deployment_settings({}, env)
    except ImproperlyConfigured as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if is_production and not resolved["SESSION_COOKIE_SECURE"]:
        print("FAIL: secure cookies are disabled", file=sys.stderr)
        return 1
    print("PASS: Dockerfile and common config have no service password defaults; deployment settings gate passed")
    if not is_production:
        print("INFO: local mode checked; use --production for the full production gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
