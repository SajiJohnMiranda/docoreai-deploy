import csv
import os
import sys
from pathlib import Path

from docore_ai.config.db import get_connection, init_db


def read_config_file(path):
    """Read a CSV into a dictionary keyed by category and config_key."""
    settings = {}

    if not path.is_file():
        return settings

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            category = (row.get("category") or "").strip()
            key = (row.get("config_key") or "").strip()
            value = (row.get("config_value") or "").strip()

            if not category or not key or not value:
                raise ValueError(f"Invalid or incomplete configuration row in {path}")

            settings[(category, key)] = value

    return settings


def main():
    config_dir = Path(os.environ.get("DOCOREAI_CONFIG_DIR", "/app/configs"))

    client_env_id = os.environ.get("DOCOREAI_CLIENT_ENV_ID", "").strip()
    if not client_env_id or "_" not in client_env_id:
        print("ERROR: DOCOREAI_CLIENT_ENV_ID must be set in the format {client}_{env}, e.g. hsbc_prod")
        return 1

    parts = client_env_id.split("_", 1)
    client = parts[0]
    env = parts[1]

    defaults_path = config_dir / "defaults.csv"
    client_path = config_dir / "clients" / client / f"{client}-{env}.csv"

    if not defaults_path.is_file():
        print(f"ERROR: Defaults file not found: {defaults_path}")
        return 1

    if not client_path.is_file():
        print(f"ERROR: Client config not found: {client_path}")
        return 1

    # Client values override defaults for matching keys.
    settings = read_config_file(defaults_path)
    settings.update(read_config_file(client_path))

    init_db()
    conn = get_connection()
    applied = 0
    errors = 0

    try:
        for (category, key), value in settings.items():
            existing = conn.execute(
                """
                SELECT value_type
                FROM wp_docoreai_phase2_config
                WHERE category = ? AND config_key = ?
                """,
                (category, key),
            ).fetchone()

            if not existing:
                print(f"ERROR: Unknown config {category}.{key}; skipping")
                errors += 1
                continue

            value_type = existing[0]

            try:
                if value_type == "int":
                    int(value)
                elif value_type == "float":
                    float(value)
                elif value_type == "bool":
                    if value.lower() not in ("true", "false"):
                        raise ValueError("Expected true or false")
            except ValueError:
                print(
                    f"ERROR: Invalid value for {category}.{key}: "
                    f"{value!r} (expected {value_type}); skipping"
                )
                errors += 1
                continue

            conn.execute(
                """
                UPDATE wp_docoreai_phase2_config
                SET config_value = ?
                WHERE category = ? AND config_key = ?
                """,
                (value, category, key),
            )
            print(f"Applied {category}.{key} = {value}")
            applied += 1

        conn.commit()

    finally:
        conn.close()

    print(f"Configuration complete: {applied} applied, {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
