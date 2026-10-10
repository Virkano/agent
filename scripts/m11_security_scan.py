"""Read-only dependency/image scan with explicit unknown and pending states."""

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CHECKLIST = ROOT / "docs" / "安全三同步M11-04检查表.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def secure_report(path):
    if path.is_file():
        os.chmod(path, 0o600)


def checklist_summary():
    config = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    controls = config["controls"]
    phases = {"PLANNING", "IMPLEMENTATION", "OPERATIONS"}
    if {item["phase"] for item in controls} != phases:
        raise ValueError("The security checklist must cover planning, implementation, and operations")
    ids = [item["id"] for item in controls]
    if len(ids) != len(set(ids)):
        raise ValueError("The security checklist contains duplicate IDs")
    for item in controls:
        if not item.get("owner_role") or item.get("status") not in {"DONE", "PARTIAL", "PENDING"}:
            raise ValueError(f"Incomplete checklist ownership/status: {item['id']}")
        evidence = item.get("evidence", "")
        if item["status"] in {"DONE", "PARTIAL"} and (not evidence or not (ROOT / evidence).is_file()):
            raise ValueError(f"Missing checklist evidence: {item['id']}")
    return {
        "counts": dict(Counter(item["status"] for item in controls)),
        "all_done": all(item["status"] == "DONE" for item in controls),
        "controls": controls,
    }


def run_command(args, cwd, timeout=600):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def scan_python(output_dir):
    report = output_dir / "python-audit.json"
    site_packages = ROOT / ".venv" / "lib" / "python3.11" / "site-packages"
    if not site_packages.is_dir():
        return {"state": "NOT_RUN", "reason": "Project virtualenv site-packages missing"}
    result = run_command([
        "uvx", "--from", "pip-audit", "pip-audit", "--path", str(site_packages),
        "--format", "json", "--output", str(report), "--progress-spinner", "off",
    ], ROOT)
    if result is None or not report.is_file():
        return {"state": "ERROR", "reason": "pip-audit did not produce a report"}
    secure_report(report)
    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
        vulnerable = sum(len(package.get("vulns", [])) for package in payload.get("dependencies", []))
        packages = len(payload.get("dependencies", []))
    except (ValueError, TypeError, AttributeError):
        return {"state": "ERROR", "reason": "pip-audit report could not be parsed"}
    if result.returncode not in {0, 1}:
        return {"state": "ERROR", "reason": "pip-audit exited without a valid vulnerability result", "exit_code": result.returncode}
    return {"state": "FINDINGS" if vulnerable else "CLEAN", "packages": packages, "findings": vulnerable, "report": str(report.relative_to(ROOT))}


def scan_frontend(output_dir):
    report = output_dir / "frontend-audit.json"
    result = run_command(["pnpm", "audit", "--json", "--registry=https://registry.npmjs.org/"], ROOT / "ui")
    if result is None:
        return {"state": "ERROR", "reason": "pnpm audit could not run"}
    report.write_text(result.stdout, encoding="utf-8")
    secure_report(report)
    try:
        payload = json.loads(result.stdout)
        counts = payload["metadata"]["vulnerabilities"]
        findings = sum(value for key, value in counts.items() if key != "total" and isinstance(value, int))
    except (ValueError, TypeError, KeyError, AttributeError):
        return {"state": "ERROR", "reason": "pnpm audit report could not be parsed"}
    if result.returncode not in {0, 1}:
        return {"state": "ERROR", "reason": "pnpm audit exited without a valid vulnerability result", "exit_code": result.returncode}
    return {"state": "FINDINGS" if findings else "CLEAN", "severities": counts, "findings": findings, "report": str(report.relative_to(ROOT))}


def scan_image(output_dir, image):
    if not image:
        return {"state": "NOT_RUN", "reason": "No image explicitly selected"}
    inspect = run_command(["docker", "image", "inspect", "--format", "{{.Id}}", image], ROOT, timeout=30)
    if inspect is None or inspect.returncode != 0:
        return {"state": "NOT_RUN", "reason": "Selected image is not present locally"}
    report = output_dir / "image-high-critical.sarif.json"
    result = run_command([
        "docker", "scout", "cves", "--only-severity", "critical,high",
        "--format", "sarif", "--output", str(report), image,
    ], ROOT, timeout=900)
    if result is None or result.returncode != 0 or not report.is_file():
        output = "" if result is None else f"{result.stdout}\n{result.stderr}".lower()
        auth_missing = "no credential found" in output
        return {
            "state": "ERROR",
            "reason": "Docker Scout authentication unavailable" if auth_missing else "Docker Scout did not produce a valid report",
            "image": image,
            "image_id": inspect.stdout.strip(),
            "source_match": "UNVERIFIED_OLD_IMAGE",
        }
    secure_report(report)
    try:
        payload = json.loads(report.read_text(encoding="utf-8"))
        findings = sum(len(run.get("results", [])) for run in payload.get("runs", []))
    except (ValueError, TypeError, AttributeError):
        return {"state": "ERROR", "reason": "Docker Scout SARIF could not be parsed"}
    return {
        "state": "FINDINGS" if findings else "CLEAN", "high_critical_findings": findings,
        "image": image, "image_id": inspect.stdout.strip(), "source_match": "UNVERIFIED_OLD_IMAGE",
        "report": str(report.relative_to(ROOT)),
    }


def main():
    parser = argparse.ArgumentParser(description="M11-04 read-only security baseline")
    parser.add_argument("--image", help="Exact pre-existing local image to scan; no image is built or pulled")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output" / "m11-04")
    parser.add_argument("--skip-scans", action="store_true", help="Validate checklist only")
    parser.add_argument("--report-only", action="store_true", help="Return success even with findings/pending checks")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    checklist = checklist_summary()
    scans = {"python": {"state": "NOT_RUN"}, "frontend": {"state": "NOT_RUN"}, "image": {"state": "NOT_RUN"}}
    if not args.skip_scans:
        scans["python"] = scan_python(output_dir)
        scans["frontend"] = scan_frontend(output_dir)
        scans["image"] = scan_image(output_dir, args.image)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "pyproject_sha256": digest(ROOT / "pyproject.toml"),
            "pnpm_lock_sha256": digest(ROOT / "ui" / "pnpm-lock.yaml"),
            "dockerfile_sha256": digest(ROOT / "docker" / "Dockerfile.app"),
            "checklist_sha256": digest(CHECKLIST),
        },
        "scans": scans,
        "security_three_sync": checklist,
        "all_clear": checklist["all_done"] and all(item["state"] == "CLEAN" for item in scans.values()),
    }
    report = output_dir / "summary.json"
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    secure_report(report)
    for name, value in scans.items():
        print(f"{name}: {value['state']} ({value.get('findings', value.get('high_critical_findings', 'n/a'))})")
    print(f"three-sync: {checklist['counts']}; all_clear={summary['all_clear']}")
    print(f"report: {report}")
    return 0 if args.report_only or summary["all_clear"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
