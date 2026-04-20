from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_SEQUENCE = [
    "collage_pictures.py",
    "compress_pics.py",
    "word_docx_gen.py",
    "docx_to_pdf.py",
]
COLLAGES_DIR = "Collages"
DELETE_COLLAGES_AFTER_RUN = True


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

    for script_name in SCRIPT_SEQUENCE:
        run_script(script_name, workdir)

    collages_dir = workdir / COLLAGES_DIR
    if DELETE_COLLAGES_AFTER_RUN and collages_dir.exists():
        shutil.rmtree(collages_dir)
        print(f"DELETED {collages_dir}")

    print("Report generation pipeline completed.")


if __name__ == "__main__":
    main()
