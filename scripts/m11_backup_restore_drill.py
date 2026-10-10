"""Exercise a local PostgreSQL restore without touching the source database."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "output" / "m11-05"
IDENTIFIER = re.compile(r"[a-z_][a-z0-9_]*\Z")
SQL_COUNTS = (
    "SELECT "
    "(SELECT count(*) FROM pg_tables WHERE schemaname=current_schema()),"
    "(SELECT count(*) FROM pg_largeobject_metadata),"
    "(SELECT count(*) FROM file),"
    "(SELECT count(*) FROM pg_largeobject),"
    "(SELECT coalesce(sum(length(data)),0) FROM pg_largeobject),"
    "(SELECT coalesce(md5(string_agg(encode(data,'hex'),'|' ORDER BY loid,pageno)),md5('')) FROM pg_largeobject)"
)


def validate_local_target(database, host, port):
    if not database or not IDENTIFIER.fullmatch(database):
        raise ValueError("DB_NAME must be a simple PostgreSQL identifier")
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("Only a local Docker-published PostgreSQL host may be used")
    if not port or not port.isdigit():
        raise ValueError("DB_PORT must be numeric")


def docker_pg(container, executable, database, *extra, interactive=False):
    if executable not in {"psql", "pg_dump", "pg_restore", "createdb", "dropdb"}:
        raise ValueError("Unsupported PostgreSQL command")
    if executable == "pg_restore":
        shell = 'export PGPASSWORD="$POSTGRES_PASSWORD"; db="$1"; shift; exec pg_restore -U "$POSTGRES_USER" -d "$db" "$@"'
        arguments = [database, *extra]
    else:
        shell = f'export PGPASSWORD="$POSTGRES_PASSWORD"; exec {executable} -U "$POSTGRES_USER" "$@"'
        arguments = [*extra, database]
    return ["docker", "exec", *(["-i"] if interactive else []), container, "sh", "-c", shell, "sh", *arguments]


def run_checked(args, *, stdin=None, stdout=None, stage, stderr_path=None):
    completed = subprocess.run(args, stdin=stdin, stdout=stdout or subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode:
        if stderr_path is not None:
            stderr_path.write_bytes(completed.stderr)
            os.chmod(stderr_path, 0o600)
        raise RuntimeError(f"{stage} failed (exit {completed.returncode}); inspect Docker/PostgreSQL privately")
    return completed.stdout.decode("utf-8").strip() if completed.stdout is not None else ""


def psql(container, database, query):
    args = docker_pg(container, "psql", database, "-v", "ON_ERROR_STOP=1", "-Atqc", query)
    return run_checked(args, stage="psql")


def collect_counts(container, database):
    values = psql(container, database, SQL_COUNTS).split("|")
    if len(values) != 6:
        raise RuntimeError("Unexpected verification result shape")
    labels = ("public_tables", "large_objects", "file_rows", "large_object_chunks", "large_object_bytes")
    return {**dict(zip(labels, (int(value) for value in values[:5]), strict=True)), "large_object_content_md5": values[5]}


def check_container(container, port):
    state = run_checked(["docker", "inspect", "--format", "{{.State.Running}}", container], stage="container inspect")
    if state != "true":
        raise RuntimeError("Selected PostgreSQL container is not running")
    ports = json.loads(run_checked(
        ["docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", container],
        stage="container ports",
    ))
    if not any(item.get("HostPort") == port for item in ports.get("5432/tcp") or []):
        raise RuntimeError("Container port mapping does not match Django DB_PORT")


def sha256_file(path):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def write_report(output_dir, report):
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = output_dir / "summary.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def drill(container, database, host, port, output_dir):
    validate_local_target(database, host, port)
    check_container(container, port)
    if psql(container, database, "SELECT current_database()") != database:
        raise RuntimeError("Source PostgreSQL database mismatch")

    restore_db = f"m11_restore_{uuid.uuid4().hex[:12]}"
    # Only a database created during this invocation may be dropped.
    if psql(container, "postgres", f"SELECT 1 FROM pg_database WHERE datname='{restore_db}'"):
        raise RuntimeError("Proposed temporary restore database already exists")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FAIL",
        "source_database": database,
        "container": container,
        "restore_database": restore_db,
        "backup_retained": False,
        "checks": {},
    }
    created = False
    error = None
    started = time.monotonic()
    try:
        source_before = collect_counts(container, database)
        with tempfile.TemporaryDirectory(prefix="drill-", dir=output_dir) as temporary:
            archive = Path(temporary) / "database.dump"
            backup_started = time.monotonic()
            with archive.open("wb") as destination:
                os.chmod(archive, 0o600)
                run_checked(
                    docker_pg(container, "pg_dump", database, "--format=custom", "--large-objects", "--no-owner", "--no-privileges"),
                    stdout=destination, stage="pg_dump",
                )
            report["backup_seconds"] = round(time.monotonic() - backup_started, 3)
            report["archive_bytes"] = archive.stat().st_size
            report["archive_sha256"] = sha256_file(archive)
            run_checked(docker_pg(container, "createdb", restore_db), stage="createdb")
            created = True
            restore_started = time.monotonic()
            with archive.open("rb") as source:
                run_checked(
                    docker_pg(container, "pg_restore", restore_db, "--exit-on-error", "--no-owner", "--no-privileges", interactive=True),
                    stdin=source, stage="pg_restore",
                    stderr_path=output_dir / f"{restore_db}-restore-stderr.log",
                )
            report["restore_seconds"] = round(time.monotonic() - restore_started, 3)
            restored = collect_counts(container, restore_db)
            source_after = collect_counts(container, database)
            report["checks"] = {
                "source_stable_during_drill": source_before == source_after,
                "restored_counts_match_source": restored == source_before,
                "source_before": source_before,
                "source_after": source_after,
                "restored": restored,
            }
            if not all((source_before == source_after, restored == source_before)):
                raise RuntimeError("Restore counts differ or source changed during drill")
    except (OSError, ValueError, RuntimeError) as exc:
        error = str(exc)
    finally:
        if created:
            try:
                run_checked(docker_pg(container, "dropdb", restore_db), stage="temporary database cleanup")
                report["temporary_database_removed"] = True
            except RuntimeError as exc:
                report["temporary_database_removed"] = False
                error = f"{error}; {exc}" if error else str(exc)
        else:
            report["temporary_database_removed"] = None
    if error:
        report["reason"] = error
    else:
        report["status"] = "PASS"
    report["total_seconds"] = round(time.monotonic() - started, 3)
    return report


def main():
    parser = argparse.ArgumentParser(description="Local PostgreSQL backup/restore drill")
    parser.add_argument("--container", default="telecom-ai-postgres")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--execute", action="store_true", help="Create and restore an isolated temporary database")
    args = parser.parse_args()
    database = os.environ.get("JB_DB_NAME") or os.environ.get("DB_NAME", "")
    host = os.environ.get("JB_DB_HOST") or os.environ.get("DB_HOST", "")
    port = os.environ.get("JB_DB_PORT") or os.environ.get("DB_PORT", "")
    validate_local_target(database, host, port)
    if not args.execute:
        print("Preflight only. Pass --execute to run an isolated backup/restore drill.")
        return 0
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    report = drill(args.container, database, host, port, output_dir)
    path = write_report(output_dir, report)
    print(f"M11-05: {report['status']}; temporary_database_removed={report['temporary_database_removed']}; report={path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
