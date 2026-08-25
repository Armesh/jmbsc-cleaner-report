# SCJMB Report Project Memory

Start here before re-reading the project.

## Purpose

This project generates a cleaners report PDF from photos stored in dated folders.

## Main Entry Point

`run.ps1`

- Changes directory to the script folder.
- Runs `uv run python .\report_gen.py`.
- Waits for Enter before closing.

## Configuration

`config.toml` contains tracked default settings for the Python report pipeline.
An optional `config.local.toml` supplies user- or machine-specific overrides
and is ignored by git. `project_config.py` loads the default file first, then
recursively merges the local file on top. Nested tables merge by key, while
scalar and array values in the local file replace their defaults. Both paths
are relative to the project rather than the current working directory.

Configuration sections:

- `[paths]`: source pictures, generated collages, and Word template.
- `[images]`: supported image extensions shared by image-processing stages.
- `[collage]`: image count, grid, cell, background, padding, and JPEG quality.
- `[compression]`: target ratio, quality range, encoder options, and dry-run
  default.
- `[report]`: title, filename/date formats, page size, and image dimensions.
- `[pdf]`: Word export, Ghostscript, compression, and DOCX cleanup behavior.
- `[pipeline]`: stage order and collage cleanup behavior.

Individual script command-line options remain available as one-run overrides
where supported. The sample-data generator is a separate development utility;
its sample content and drawing settings remain inside its PowerShell script.

## Sample Data Generator

`generate_sample_pics.ps1`

- Creates a sample `pics` folder in the intended structure.
- Generates sample JPG files with PowerShell and `System.Drawing`.
- Uses random labels and background colors each time it creates sample images.
- Sample output:

```text
pics/
  20260622/
    SC01/
      a.JPG
      b.JPG
      c.JPG
  20260623/
    SC01/
      a.JPG
      b.JPG
      c.JPG
  20260624/
    SC01/
      a.JPG
      b.JPG
      c.JPG
```

## Pipeline

`report_gen.py` orchestrates the full report pipeline:

Before running the pipeline, it deletes the configured collages folder when
`pipeline.delete_collages_before_run = true`.

1. `collage_pictures.py`
2. `compress_pics.py`
3. `word_docx_gen.py`
4. `docx_to_pdf.py`

After all scripts complete, it deletes the configured collages folder when
`pipeline.delete_collages_after_run = true`.

## Expected Input Layout

The expected source folder defaults to `pics` and is configured by
`paths.pics_dir`.

Typical structure:

```text
pics/
  20260414/
    location-or-task-1/
      image1.jpg
      image2.jpg
    location-or-task-2/
      image1.jpg
```

Top-level folders may use `YYYYMMDD` names or plain text. Valid dates are shown
as formatted dates; other names are shown unchanged. The report filename is
derived from the Monday of the earliest valid date folder. If there are no
valid date folders, it uses today's date instead.

Supported image extensions are configured by `images.supported_extensions`:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`

## Script Responsibilities

### `collage_pictures.py`

- Source root defaults to `paths.pics_dir` (`pics`).
- Output root defaults to `paths.collages_dir` (`Collages`).
- Recursively finds folders containing supported images.
- For each image folder, sorts images by file size descending.
- Uses up to `collage.count` images (`4`).
- Fits images into `collage.cell_size` cells (`900 x 900`).
- Places `collage.images_per_row` images per row (`2`).
- Uses configurable background color, padding, and JPEG quality.
- Saves one JPG collage per source folder into the matching relative path under
  `Collages`.

### `compress_pics.py`

- Root defaults to `paths.collages_dir` (`Collages`).
- Recursively compresses supported image files in place.
- Uses Pillow to encode JPEGs.
- Binary-searches the configured JPEG quality range (`20` to `95`).
- Targets `compression.target_size_ratio` of the original file size (`0.5`).
- Reads optimize, progressive, subsampling, and dry-run defaults from
  `[compression]`.
- Keeps the original file if compression would not reduce size.

### `word_docx_gen.py`

- Source defaults to `paths.collages_dir` (`Collages`).
- Template defaults to `paths.template_file` (`template.docx`).
- Title defaults to `report.title` (`Cleaners Report`).
- Configures page size from `[report]` (A4 by default).
- Adds page numbers to the footer.
- Creates a heading for each top-level folder, formatting `YYYYMMDD` names as
  dates and preserving other names as plain text.
- Creates a heading for each collage image using `picture.stem.upper()`.
- Adds one collage image per page.
- Image size is capped by the configured report image dimensions (`12 cm` wide
  and `22 cm` tall by default).
- Default output filename is:

```text
cleaners_report_<ddMonYYYY>.docx
```

Example:

```text
cleaners_report_14Apr2026.docx
```

### `docx_to_pdf.py`

- Input defaults to the newest `.docx` file in the current folder.
- Output defaults to the same filename with `.pdf`.
- Uses Microsoft Word COM automation through PowerShell.
- Reads Word export codes and Ghostscript settings from `[pdf]`.
- Attempts Ghostscript compression when `pdf.compress_after_export = true`.
- Deletes the input DOCX after successful PDF export when
  `pdf.delete_docx_after_success = true`.

## Operational Requirements

- Windows is expected for the full pipeline.
- Microsoft Word must be installed for DOCX to PDF conversion.
- Ghostscript is optional. If unavailable, PDF compression is skipped.
- Python dependencies are managed by `uv`.
- `pyproject.toml` currently requires Python `>=3.14`.
- Dependencies:
  - `pillow`
  - `python-docx`

## Current Repo Notes

- `README.md` is the user guide for `config.toml`, optional local overrides,
  configuration precedence, and per-script CLI overrides.
- `main.py` is the default placeholder and is not part of the report pipeline.
- `template.docx` is used for document styling when present.
- `config.toml` contains user-editable pipeline settings.
- `config.local.toml` is an optional, git-ignored override file.
- `project_config.py` is the shared TOML loader.
- `project.zip` was observed as untracked in git.
- `Collages` is generated output and normally deleted after a pipeline run.

## Gotchas

- `collage_pictures.py` and `word_docx_gen.py` share `paths.pics_dir` as the
  source image folder.
- `docx_to_pdf.py` chooses the newest `.docx` in the folder when no input is
  provided, so extra DOCX files in the project root can affect conversion.
- `word_docx_gen.py` derives the default report filename from folders in `pics`,
  not from `Collages`. It prefers the earliest valid date and otherwise uses
  today's date.
- For cleanup safety, `paths.collages_dir` must resolve to a child of the
  project folder; it cannot be the project root or an external directory.
- The full pipeline deletes intermediate collages and the generated DOCX by
  default, leaving the PDF as the main final artifact.
