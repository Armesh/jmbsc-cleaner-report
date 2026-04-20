from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageOps


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SOURCE_ROOT = Path("MaintenancePics")
OUTPUT_ROOT = Path("Collages")
IMAGES_PER_ROW = 2
COUNT = 4
CELL_SIZE = (900, 900)
BACKGROUND_COLOR = (255, 255, 255)
PADDING = 1


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


def image_files(folder: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ],
        key=lambda path: (path.stat().st_size, path.name.lower()),
        reverse=True,
    )


def folders_with_images(root: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in root.rglob("*")
            if path.is_dir() and image_files(path)
        ],
        key=lambda path: str(path.relative_to(root)).lower(),
    )


def fit_image(path: Path, cell_size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        return ImageOps.contain(image, cell_size, Image.Resampling.LANCZOS)


def chunked(items: list[Path], size: int) -> list[list[Path]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def build_collage(
    folder: Path,
    output_root: Path,
    source_root: Path,
    *,
    images_per_row: int,
    cell_size: tuple[int, int],
    padding: int,
) -> Path:
    pictures = image_files(folder)[:COUNT]
    fitted_pictures = [(picture, fit_image(picture, cell_size)) for picture in pictures]
    rows = chunked(fitted_pictures, images_per_row)

    row_widths = []
    row_heights = []
    for row in rows:
        row_width = sum(image.width for _, image in row) + (max(len(row) - 1, 0) * padding)
        row_height = max(image.height for _, image in row)
        row_widths.append(row_width)
        row_heights.append(row_height)

    canvas_width = max(row_widths)
    canvas_height = sum(row_heights) + (max(len(rows) - 1, 0) * padding)

    collage = Image.new("RGB", (canvas_width, canvas_height), BACKGROUND_COLOR)

    current_y = 0
    for row, row_height in zip(rows, row_heights, strict=True):
        current_x = 0
        for _, fitted in row:
            collage.paste(fitted, (current_x, current_y))
            current_x += fitted.width + padding
        current_y += row_height + padding

    relative_folder = folder.relative_to(source_root)
    output_folder = output_root / relative_folder.parent
    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / f"{relative_folder.name}.jpg"
    collage.save(output_path, format="JPEG", quality=92)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build collage images from subfolders of a source folder."
    )
    parser.add_argument(
        "--source-root",
        default=str(SOURCE_ROOT),
        help=f"Source root folder. Defaults to {SOURCE_ROOT}",
    )
    parser.add_argument(
        "--output-root",
        default=str(OUTPUT_ROOT),
        help=f"Output root folder. Defaults to {OUTPUT_ROOT}",
    )
    parser.add_argument(
        "--images-per-row",
        type=int,
        default=IMAGES_PER_ROW,
        help=f"Maximum images per row. Defaults to {IMAGES_PER_ROW}",
    )
    parser.add_argument(
        "--cell-width",
        type=int,
        default=CELL_SIZE[0],
        help=f"Cell width used for fitting images. Defaults to {CELL_SIZE[0]}",
    )
    parser.add_argument(
        "--cell-height",
        type=int,
        default=CELL_SIZE[1],
        help=f"Cell height used for fitting images. Defaults to {CELL_SIZE[1]}",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=PADDING,
        help=f"Padding between images in pixels. Defaults to {PADDING}",
    )
    args = parser.parse_args()

    if args.images_per_row <= 0:
        raise SystemExit("--images-per-row must be greater than 0")
    if args.cell_width <= 0 or args.cell_height <= 0:
        raise SystemExit("--cell-width and --cell-height must be greater than 0")
    if args.padding < 0:
        raise SystemExit("--padding must be 0 or greater")

    source_root = resolve_case_insensitive(args.source_root)
    if not source_root.exists():
        raise SystemExit(f"Folder not found: {source_root}")

    output_root = resolve_case_insensitive(args.output_root)
    created = 0

    for folder in folders_with_images(source_root):
        output_path = build_collage(
            folder,
            output_root,
            source_root,
            images_per_row=args.images_per_row,
            cell_size=(args.cell_width, args.cell_height),
            padding=args.padding,
        )
        created += 1
        print(f"CREATED {output_path}")

    print()
    print(f"Collages created: {created}")
    print(f"Output folder:     {output_root}")


if __name__ == "__main__":
    main()
