from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from project_config import CONFIG


PATHS_CONFIG = CONFIG["paths"]
PIPELINE_CONFIG = CONFIG["pipeline"]
SCRIPT_SEQUENCE = tuple(PIPELINE_CONFIG["scripts"])
COLLAGES_DIR = PATHS_CONFIG["collages_dir"]
DELETE_COLLAGES_BEFORE_RUN = PIPELINE_CONFIG["delete_collages_before_run"]
DELETE_COLLAGES_AFTER_RUN = PIPELINE_CONFIG["delete_collages_after_run"]


def delete_collages(workdir: Path) -> None:
    collages_dir = (workdir / COLLAGES_DIR).resolve()
    if collages_dir == workdir or workdir not in collages_dir.parents:
        raise SystemExit(
            "paths.collages_dir in config.toml must be a child of the project folder"
        )
    if collages_dir.exists():
        shutil.rmtree(collages_dir)
        print(f"DELETED {collages_dir}")


def run_script(script_name: str, workdir: Path) -> None:
    script_path = workdir / script_name
    print(f"RUNNING {script_name}")
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=workdir,
        check=True,
    )


def main() -> None:
    workdir = Path(__file__).resolve().parent

    if DELETE_COLLAGES_BEFORE_RUN:
        delete_collages(workdir)

    for script_name in SCRIPT_SEQUENCE:
        run_script(script_name, workdir)

    if DELETE_COLLAGES_AFTER_RUN:
        delete_collages(workdir)

    print("Report generation pipeline completed.")


if __name__ == "__main__":
    main()
