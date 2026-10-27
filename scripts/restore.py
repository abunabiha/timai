#!/usr/bin/env python3
"""
TimAI Restore Script
Restores PostgreSQL database and workspaces/ directory from a TimAI backup ZIP archive.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


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


def restore_database(sql_path: Path) -> bool:
    """Restores database from database.sql using docker compose or psql."""
    if not sql_path.exists():
        print(" No database.sql found in backup archive. Skipping DB restore.")
        return False

    sql_bytes = sql_path.read_bytes()
    if len(sql_bytes) < 20 or b"-- PostgreSQL dump not available" in sql_bytes:
        print(" Database dump was empty or skipped during backup. Nothing to restore.")
        return False

    print("Restoring database to PostgreSQL...")

    # Method 1: Docker compose exec
    docker_cmds = [
        ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "postgres", "-d", "timai"],
        ["docker-compose", "exec", "-T", "postgres", "psql", "-U", "postgres", "-d", "timai"],
    ]

    for cmd in docker_cmds:
        ret, stdout, stderr = run_command(cmd, input_bytes=sql_bytes)
        if ret == 0:
            print(" Database restored successfully via Docker.")
            return True

    # Method 2: Local psql
    pg_user = os.environ.get("POSTGRES_USER", "postgres")
    pg_db = os.environ.get("POSTGRES_DB", "timai")
    pg_host = os.environ.get("POSTGRES_HOST", "localhost")
    pg_port = os.environ.get("POSTGRES_PORT", "5432")

    ret, stdout, stderr = run_command(
        ["psql", "-h", pg_host, "-p", pg_port, "-U", pg_user, "-d", pg_db],
        input_bytes=sql_bytes,
    )
    if ret == 0:
        print(" Database restored successfully via local psql.")
        return True

    print(f" Failed to restore database: {stderr.decode('utf-8', errors='ignore')}")
    return False


def restore(
    backup_file: Path,
    target_workspaces: Path = Path("workspaces"),
    restore_db: bool = True,
    restore_workspaces: bool = True,
) -> bool:
    """Extracts backup archive and restores components."""
    if not backup_file.exists():
        print(f"Error: Backup archive '{backup_file}' does not exist.")
        return False

    print(f"Restoring TimAI from archive: {backup_file}")

    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        with zipfile.ZipFile(backup_file, "r") as zip_file:
            zip_file.extractall(temp_dir)

        # Read metadata
        meta_file = temp_dir / "metadata.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            print(f" Archive metadata: Version={meta.get('version')}, CreatedAt={meta.get('created_at')}")

        # 1. Restore Database
        if restore_db:
            db_sql = temp_dir / "database.sql"
            restore_database(db_sql)

        # 2. Restore Workspaces
        if restore_workspaces:
            extracted_ws = temp_dir / "workspaces"
            if extracted_ws.exists():
                print(f"Restoring workspaces into '{target_workspaces}'...")
                target_workspaces.mkdir(parents=True, exist_ok=True)
                for item in extracted_ws.iterdir():
                    dest = target_workspaces / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)
                print(" Workspaces restored successfully.")

    print(" Restore process completed successfully!")
    return True


def main():
    parser = argparse.ArgumentParser(description="TimAI Restore Utility")
    parser.add_argument("-i", "--input", type=str, required=True, help="Input backup archive path (.zip)")
    parser.add_argument("--workspaces", type=str, default="workspaces", help="Target workspaces directory")
    parser.add_argument("--no-db", action="store_true", help="Skip database restore")
    parser.add_argument("--no-workspaces", action="store_true", help="Skip workspaces restore")
    args = parser.parse_args()

    restore(
        backup_file=Path(args.input),
        target_workspaces=Path(args.workspaces),
        restore_db=not args.no_db,
        restore_workspaces=not args.no_workspaces,
    )


if __name__ == "__main__":
    main()
