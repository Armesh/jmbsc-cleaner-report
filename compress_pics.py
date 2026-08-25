from __future__ import annotations

import argparse
import io
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps

from project_config import CONFIG


PATHS_CONFIG = CONFIG["paths"]
IMAGES_CONFIG = CONFIG["images"]
COMPRESSION_CONFIG = CONFIG["compression"]
SUPPORTED_EXTENSIONS = {
    extension.lower() for extension in IMAGES_CONFIG["supported_extensions"]
}
DEFAULT_ROOT = Path(PATHS_CONFIG["collages_dir"])
TARGET_SIZE_RATIO = COMPRESSION_CONFIG["target_size_ratio"]
MIN_JPEG_QUALITY = COMPRESSION_CONFIG["min_jpeg_quality"]
MAX_JPEG_QUALITY = COMPRESSION_CONFIG["max_jpeg_quality"]
OPTIMIZE = COMPRESSION_CONFIG["optimize"]
PROGRESSIVE = COMPRESSION_CONFIG["progressive"]
SUBSAMPLING = COMPRESSION_CONFIG["subsampling"]
DRY_RUN = COMPRESSION_CONFIG["dry_run"]


def iter_images(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def encode_jpeg(
    image: Image.Image,
    quality: int,
    *,
    icc_profile: bytes | None,
    exif: bytes | None,
) -> bytes:
    buffer = io.BytesIO()
    save_kwargs = {
        "format": "JPEG",
        "quality": quality,
        "optimize": OPTIMIZE,
        "progressive": PROGRESSIVE,
        "subsampling": SUBSAMPLING,
    }
    if icc_profile is not None:
        save_kwargs["icc_profile"] = icc_profile
    if exif is not None:
        save_kwargs["exif"] = exif

    image.save(buffer, **save_kwargs)
    return buffer.getvalue()


def compress_image(path: Path, dry_run: bool = False) -> tuple[bool, int, int]:
    original_size = path.stat().st_size
    target_size = max(int(original_size * TARGET_SIZE_RATIO), 1)

    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        icc_profile = source.info.get("icc_profile")
        exif = source.info.get("exif")
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Search for the highest quality that still gets close to the target.
        best_data: bytes | None = None
        low = MIN_JPEG_QUALITY
        high = MAX_JPEG_QUALITY

        while low <= high:
            quality = (low + high) // 2
            candidate = encode_jpeg(
                image,
                quality,
                icc_profile=icc_profile,
                exif=exif,
            )
            candidate_size = len(candidate)

            if candidate_size <= target_size:
                best_data = candidate
                low = quality + 1
            else:
                high = quality - 1

        if best_data is None:
            best_data = encode_jpeg(
                image,
                MIN_JPEG_QUALITY,
                icc_profile=icc_profile,
                exif=exif,
            )

    new_size = len(best_data)

    if new_size >= original_size:
        return False, original_size, original_size

    if not dry_run:
        path.write_bytes(best_data)

    return True, original_size, new_size


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Compress images under the {DEFAULT_ROOT} folder."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=str(DEFAULT_ROOT),
        help=f"Root folder to scan. Defaults to ./{DEFAULT_ROOT}",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=DRY_RUN,
        help="Show planned savings without modifying files.",
    )
    args = parser.parse_args()

    if TARGET_SIZE_RATIO <= 0 or TARGET_SIZE_RATIO > 1:
        raise SystemExit(
            "compression.target_size_ratio in config.toml must be greater than 0 and at most 1"
        )
    if not 1 <= MIN_JPEG_QUALITY <= MAX_JPEG_QUALITY <= 95:
        raise SystemExit(
            "compression JPEG quality values in config.toml must satisfy "
            "1 <= min_jpeg_quality <= max_jpeg_quality <= 95"
        )

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Folder not found: {root}")

    total_original = 0
    total_new = 0
    changed = 0
    skipped = 0

    for image_path in iter_images(root):
        try:
            updated, before, after = compress_image(image_path, dry_run=args.dry_run)
        except Exception as exc:  # pragma: no cover
            skipped += 1
            print(f"SKIP  {image_path} ({exc})")
            continue

        total_original += before
        total_new += after

        if updated:
            changed += 1
            reduction = 100 - ((after / before) * 100)
            action = "WOULD" if args.dry_run else "DONE "
            print(
                f"{action} {image_path} | {before / 1024:.1f} KB -> "
                f"{after / 1024:.1f} KB ({reduction:.1f}% smaller)"
            )
        else:
            skipped += 1
            print(f"KEEP  {image_path}")

    if total_original == 0:
        print("No supported images found.")
        return

    overall_reduction = 100 - ((total_new / total_original) * 100)
    print()
    print(f"Processed: {changed + skipped}")
    print(f"Changed:   {changed}")
    print(f"Skipped:   {skipped}")
    print(
        f"Total:     {total_original / (1024 * 1024):.2f} MB -> "
        f"{total_new / (1024 * 1024):.2f} MB ({overall_reduction:.1f}% smaller)"
    )


if __name__ == "__main__":
    main()
