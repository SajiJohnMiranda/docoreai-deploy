import csv
import os
import sys
from pathlib import Path

from docore_ai.config.db import get_connection, init_db

init_db()


def read_config_file(path):
    settings = {}
    if not path.is_file():
        return settings
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "").strip()
            key = (row.get("config_key") or "").strip()
            value = (row.get("config_value") or "").strip()
            if not category or not key or not value:
                raise ValueError(f"Invalid row in {path}: {row}")
            settings[(category, key)] = value
    return settings


def main():
    config_dir = Path(os.environ.get("DOCOREAI_CONFIG_DIR", "/app/configs"))
    client_env_id = os.environ.get("DOCOREAI_CLIENT_ENV_ID", "").strip()

    if not client_env_id:
        print("ERROR: DOCOREAI_CLIENT_ENV_ID is not set", file=sys.stderr)
        return 1

    parts = client_env_id.split("_", 1)
    if len(parts) != 2:
        print(f"ERROR: DOCOREAI_CLIENT_ENV_ID must be {{client}}_{{env}}, got: {client_env_id}", file=sys.stderr)
        return 1

    client, env = parts

    defaults_path = config_dir / "defaults.csv"
    client_path = config_dir / "clients" / client / f"{client}-{env}.csv"

    settings = read_config_file(defaults_path)
    client_settings = read_config_file(client_path)

    if not client_settings:
        print(f"WARNING: No client config found at {client_path}, using defaults only")

    settings.update(client_settings)

    if not settings:
        print("No configuration to apply.")
        return 0

    conn = get_connection()
    cur = conn.cursor()

    TABLE = "wp_docoreai_phase2_config"
    for (category, key), value in settings.items():
        cur.execute(
            f"UPDATE {TABLE} SET config_value = ? WHERE category = ? AND config_key = ?",
            (value, category, key),
        )
        if cur.rowcount == 0:
            cur.execute(
                f"INSERT INTO {TABLE} (category, config_key, config_value) VALUES (?, ?, ?)",
                (category, key, value),
            )

    conn.commit()
    conn.close()
    print(f"Config applied: {len(settings)} settings for client={client} env={env}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
