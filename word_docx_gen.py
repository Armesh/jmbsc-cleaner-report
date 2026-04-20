from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm
from PIL import Image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_WIDTH_CM = 12
MAX_IMAGE_HEIGHT_CM = 22
A4_WIDTH_CM = 21
A4_HEIGHT_CM = 29.7
DEFAULT_TEMPLATE = "template.docx"
DEFAULT_TITLE = "Maintenance Report"
MAINTENANCE_PICS_DIR = "Maintenancepics"


def format_date_folder(name: str) -> str:
    date_value = datetime.strptime(name, "%Y%m%d")
    return f"{date_value.day} {date_value.strftime('%b %Y')}"


def date_directories(root: Path) -> list[Path]:
    return sorted(
        [path for path in root.iterdir() if path.is_dir()],
        key=lambda path: path.name,
    )


def image_files(root: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in root.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ],
        key=lambda path: path.name.lower(),
    )


def add_page_break(document: Document) -> None:
    document.add_page_break()


def resolve_case_insensitive(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path

    path = path.resolve(strict=False)
    if path.exists():
        return path

    anchor = Path(path.anchor) if path.anchor else Path.cwd().anchor
    current = Path(anchor) if isinstance(anchor, str) else anchor

    for part in path.parts[len(current.parts) :]:
        if not current.exists() or not current.is_dir():
            return path

        match = next(
            (child for child in current.iterdir() if child.name.lower() == part.lower()),
            None,
        )
        if match is None:
            return path
        current = match

    return current


def report_date_from_maintenancepics() -> datetime:
    maintenance_root = resolve_case_insensitive(MAINTENANCE_PICS_DIR)
    if not maintenance_root.exists():
        raise SystemExit(f"Folder not found: {maintenance_root}")

    date_values = []
    for path in maintenance_root.iterdir():
        if not path.is_dir():
            continue
        try:
            date_values.append(datetime.strptime(path.name, "%Y%m%d"))
        except ValueError:
            continue

    if not date_values:
        raise SystemExit(f"No YYYYMMDD folders found in {maintenance_root}")

    earliest = min(date_values)
    monday = earliest - timedelta(days=earliest.weekday())
    return monday


def default_output_filename() -> str:
    monday = report_date_from_maintenancepics()
    return f"maintenance_report_{monday.strftime('%d%b%Y')}.docx"


def configure_a4(document: Document) -> None:
    for section in document.sections:
        section.page_width = Cm(A4_WIDTH_CM)
        section.page_height = Cm(A4_HEIGHT_CM)


def add_page_numbers(document: Document) -> None:
    for section in document.sections:
        footer = section.footer
        paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        run = paragraph.add_run()
        fld_char_begin = OxmlElement("w:fldChar")
        fld_char_begin.set(qn("w:fldCharType"), "begin")

        instr_text = OxmlElement("w:instrText")
        instr_text.set(qn("xml:space"), "preserve")
        instr_text.text = "PAGE"

        fld_char_end = OxmlElement("w:fldChar")
        fld_char_end.set(qn("w:fldCharType"), "end")

        run._r.append(fld_char_begin)
        run._r.append(instr_text)
        run._r.append(fld_char_end)


def picture_size(picture: Path) -> tuple[Cm, Cm]:
    with Image.open(picture) as image:
        width_px, height_px = image.size

    scale = min(MAX_IMAGE_WIDTH_CM / width_px, MAX_IMAGE_HEIGHT_CM / height_px)
    width_cm = width_px * scale
    height_cm = height_px * scale
    return Cm(width_cm), Cm(height_cm)


def build_report(
    source_root: Path,
    output_path: Path,
    template_path: Path | None,
    title: str,
) -> None:
    document = Document(str(template_path)) if template_path else Document()
    configure_a4(document)
    add_page_numbers(document)
    document.add_heading(title, level=0)
    first_date = True
    first_picture_in_date = True

    for date_dir in date_directories(source_root):
        pictures = image_files(date_dir)
        if not pictures:
            continue

        if not first_date:
            add_page_break(document)
        first_date = False
        first_picture_in_date = True

        document.add_heading(format_date_folder(date_dir.name), level=1)

        for picture in pictures:
            if not first_picture_in_date:
                add_page_break(document)
            first_picture_in_date = False

            document.add_heading(picture.stem.upper(), level=2)

            width, height = picture_size(picture)
            document.add_picture(str(picture), width=width, height=height)

    document.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Word report from pictures in Collages."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="Collages",
        help="Root folder containing date folders. Defaults to ./Collages",
    )
    parser.add_argument(
        "--output",
        help="Optional output .docx filename. Defaults to a name derived from the title.",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_TITLE,
        help=f"Report title shown at the start of the document. Defaults to {DEFAULT_TITLE}.",
    )
    parser.add_argument(
        "--template",
        default=DEFAULT_TEMPLATE,
        help=(
            "Optional .docx template to start from. "
            "Use a template with the Gallery theme already applied."
        ),
    )
    args = parser.parse_args()

    source_root = Path(args.source).resolve()
    if not source_root.exists():
        raise SystemExit(f"Folder not found: {source_root}")

    output_name = args.output or default_output_filename()
    output_path = Path(output_name).resolve()
    template_path = Path(args.template).resolve()
    if not template_path.exists():
        template_path = None

    build_report(source_root, output_path, template_path, args.title)
    print(f"Created report: {output_path}")


if __name__ == "__main__":
    main()
