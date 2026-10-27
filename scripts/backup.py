#!/usr/bin/env python3
"""
TimAI Backup Script
Backs up the PostgreSQL database and the workspaces/ directory into a single timestamped ZIP archive.
Cross-platform (Windows, Linux, macOS) and Docker-aware.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BACKUP_VERSION = "1.0.0"


def run_command(cmd: list[str], input_bytes: bytes | None = None) -> tuple[int, bytes, bytes]:
    """Execute command safely and capture output."""
    try:
        proc = subprocess.run(
            cmd,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, b"", b"Executable not found"


def dump_database(temp_dir: Path) -> Path | None:
    """Attempts to dump PostgreSQL database using docker compose or pg_dump."""
    sql_path = temp_dir / "database.sql"
    print("Dumping PostgreSQL database...")

    # Method 1: Docker compose exec
    docker_cmds = [
        ["docker", "compose", "exec", "-T", "postgres", "pg_dump", "-U", "postgres", "-d", "timai"],
        ["docker-compose", "exec", "-T", "postgres", "pg_dump", "-U", "postgres", "-d", "timai"],
    ]

    for cmd in docker_cmds:
        ret, stdout, stderr = run_command(cmd)
        if ret == 0 and len(stdout) > 50:
            sql_path.write_bytes(stdout)
            print(f" Database dumped successfully via Docker ({len(stdout):,} bytes).")
            return sql_path

    # Method 2: Local pg_dump CLI
    pg_user = os.environ.get("POSTGRES_USER", "postgres")
    pg_db = os.environ.get("POSTGRES_DB", "timai")
    pg_host = os.environ.get("POSTGRES_HOST", "localhost")
    pg_port = os.environ.get("POSTGRES_PORT", "5432")

    ret, stdout, stderr = run_command(["pg_dump", "-h", pg_host, "-p", pg_port, "-U", pg_user, "-d", pg_db])
    if ret == 0 and len(stdout) > 50:
        sql_path.write_bytes(stdout)
        print(f" Database dumped successfully via local pg_dump ({len(stdout):,} bytes).")
        return sql_path

    print(" Warning: Unable to dump PostgreSQL database via docker compose or local pg_dump.")
    print("           Database portion will be skipped or saved as empty marker.")
    sql_path.write_text("-- PostgreSQL dump not available at backup creation\n", encoding="utf-8")
    return sql_path


def backup(
    output_path: Path | None = None,
    workspaces_dir: Path = Path("workspaces"),
    include_db: bool = True,
    include_workspaces: bool = True,
) -> Path:
    """Creates a full backup archive."""
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backups_dir = Path("backups")
    backups_dir.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = backups_dir / f"timai_backup_{now_str}.zip"

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Creating TimAI backup archive: {output_path}")

    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)

        # 1. Metadata
        metadata = {
            "version": BACKUP_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "include_db": include_db,
            "include_workspaces": include_workspaces,
        }
        meta_path = temp_dir / "metadata.json"
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # 2. Database Dump
        if include_db:
            dump_database(temp_dir)

        # 3. Create ZIP archive
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(meta_path, arcname="metadata.json")

            db_sql = temp_dir / "database.sql"
            if db_sql.exists():
                zip_file.write(db_sql, arcname="database.sql")

            if include_workspaces and workspaces_dir.exists():
                print(f"Packaging workspaces from: {workspaces_dir}...")
                count = 0
                for root, _, files in os.walk(workspaces_dir):
                    for f in files:
                        fp = Path(root) / f
                        try:
                            rel_path = fp.relative_to(workspaces_dir.parent)
                            zip_file.write(fp, arcname=str(rel_path).replace("\\", "/"))
                            count += 1
                        except Exception as exc:
                            print(f"Skipping {fp}: {exc}")
                print(f" Packaged {count} workspace files.")

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f" Backup complete! Archive saved at: {output_path} ({size_mb:.2f} MB)")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="TimAI Backup Utility")
    parser.add_argument("-o", "--output", type=str, help="Output archive path (.zip)")
    parser.add_argument("--workspaces", type=str, default="workspaces", help="Workspaces directory path")
    parser.add_argument("--no-db", action="store_true", help="Skip database dump")
    parser.add_argument("--no-workspaces", action="store_true", help="Skip workspaces directory")
    args = parser.parse_args()

    out = Path(args.output) if args.output else None
    ws = Path(args.workspaces)
    backup(
        output_path=out,
        workspaces_dir=ws,
        include_db=not args.no_db,
        include_workspaces=not args.no_workspaces,
    )


if __name__ == "__main__":
    main()
