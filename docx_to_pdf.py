from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


WORD_FORMAT_PDF = 17
WORD_OPTIMIZE_FOR_ONSCREEN = 1
GHOSTSCRIPT_CANDIDATES = ("gswin64c", "gswin32c", "gs")
DELETE_DOCX_AFTER_SUCCESS = True


def newest_docx(workdir: Path) -> Path:
    docx_files = sorted(workdir.glob("*.docx"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not docx_files:
        raise SystemExit(f"No .docx files found in {workdir}")
    return docx_files[0]


def export_pdf_via_word(input_path: Path, output_path: Path) -> None:
    powershell_script = f"""
$word = $null
$document = $null
try {{
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $document = $word.Documents.Open("{input_path}")
    $document.ExportAsFixedFormat("{output_path}", {WORD_FORMAT_PDF}, $false, {WORD_OPTIMIZE_FOR_ONSCREEN})
}}
finally {{
    if ($document -ne $null) {{ $document.Close($false) }}
    if ($word -ne $null) {{ $word.Quit() }}
}}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", powershell_script],
        check=True,
    )


def ghostscript_executable() -> str | None:
    for candidate in GHOSTSCRIPT_CANDIDATES:
        if shutil.which(candidate):
            return candidate
    return None


def compress_pdf(path: Path) -> bool:
    gs = ghostscript_executable()
    if gs is None:
        print("SKIP PDF compression (Ghostscript not found)")
        return False

    compressed_path = path.with_name(f"{path.stem}_compressed.pdf")
    subprocess.run(
        [
            gs,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/screen",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={compressed_path}",
            str(path),
        ],
        check=True,
    )

    if compressed_path.stat().st_size < path.stat().st_size:
        compressed_path.replace(path)
        print(f"COMPRESSED {path}")
        return True

    compressed_path.unlink(missing_ok=True)
    print("KEEP PDF size (compressed output was not smaller)")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a Word .docx report to PDF and optionally compress it."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input .docx file. Defaults to the newest .docx in the current folder.",
    )
    parser.add_argument(
        "--output",
        help="Optional output .pdf filename. Defaults to the input filename with .pdf",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Skip PDF compression attempt after export.",
    )
    args = parser.parse_args()

    workdir = Path.cwd()
    input_path = Path(args.input).resolve() if args.input else newest_docx(workdir)
    if not input_path.exists():
        raise SystemExit(f"Input .docx not found: {input_path}")

    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".pdf")
    export_pdf_via_word(input_path, output_path)
    print(f"CREATED {output_path}")

    if not args.no_compress:
        compress_pdf(output_path)

    if DELETE_DOCX_AFTER_SUCCESS:
        input_path.unlink(missing_ok=True)
        print(f"DELETED {input_path}")


if __name__ == "__main__":
    main()
