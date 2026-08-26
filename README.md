# Cleaners Report Generator

This project turns pictures from structured folders into collages, builds a
Word report, and converts the report to PDF.

## Daily How to Use Steps
1. Make sure `pics` folder exist in this `jmbsc-cleaner-report` folder.
2. Put pictures inside `pics` folder.
3. Arrange the pictures as follows in `pics` folder:

   ```text
   pics/
     20260825/
       SC01/
         photo1.jpg
         photo2.jpg

4. Open PowerShell (shift+right click) in this `jmbsc-cleaner-report` project folder  
5. Type below command and hit Enter

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

6. PDF Report `cleaners_report_{date}.pdf` will be generated.







## First-Time Setup

These steps are only needed once on a Windows computer.

### 1. Install uv

Open PowerShell and install `uv` with Windows Package Manager:

```powershell
winget install --id=astral-sh.uv -e
```

Close and reopen PowerShell, then confirm that it is available:

```powershell
uv --version
```

Other official installation methods are available in the
[uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Create the project environment

Open PowerShell in this `jmbsc-cleaner-report` project folder.

Run this command from the project folder in PowerShell:

```powershell
uv sync --locked
```

This installs the Python version and package versions required by the project. After it finishes, follow the **Daily
Use** instructions above.

## Configuration files

The application reads settings in this order:

1. `config.toml` provides the tracked project defaults.
2. `config.local.toml`, when present, overrides selected defaults.
3. Command-line arguments override the merged configuration for that run.

`config.toml` must exist and should contain the complete default
configuration. Commit shared changes to this file.

`config.local.toml` is optional and ignored by Git. Use it for settings that
apply only to one user or computer. It is not created automatically.

### Creating a local override

Create `config.local.toml` beside `config.toml` and include only the settings
you want to change. For example:

```toml
[paths]
pics_dir = "D:/Cleaner Photos"

[collage]
count = 6
background_color = [240, 240, 240]

[report]
title = "Weekly Cleaners Report"

[pdf]
compress_after_export = false
delete_docx_after_success = false
```

The merge is recursive. In the example, `collage.count` changes, while the
other `[collage]` defaults still come from `config.toml`. Scalar values and
arrays in `config.local.toml` replace their corresponding defaults.

Use TOML syntax:

- Strings require quotes: `title = "Cleaners Report"`.
- Booleans are lowercase: `true` or `false`.
- Arrays use square brackets: `cell_size = [900, 900]`.
- Section names use brackets: `[collage]`.

### `[paths]`

| Setting | Default | Purpose |
|---|---|---|
| `pics_dir` | `"pics"` | Folder containing source pictures. |
| `collages_dir` | `"Collages"` | Generated collage folder. It must be a child of the project folder because the pipeline can delete it. |
| `template_file` | `"template.docx"` | Word template used for report styling. |

Relative paths are resolved from the project folder when using `run.ps1`.
Absolute paths may be used for pictures and the template. For cleanup safety,
`collages_dir` cannot point to the project root or an external directory.

### `[images]`

| Setting | Default | Purpose |
|---|---|---|
| `supported_extensions` | `[".jpg", ".jpeg", ".png", ".webp"]` | Image types recognized throughout the pipeline. |

Changing this array replaces the complete default extension list.

### `[collage]`

| Setting | Default | Purpose |
|---|---:|---|
| `images_per_row` | `2` | Maximum number of pictures placed in each row. |
| `count` | `4` | Maximum pictures selected from each source folder. |
| `cell_size` | `[900, 900]` | Maximum width and height used to fit each picture, in pixels. |
| `background_color` | `[255, 255, 255]` | RGB collage background color. Each value must be from 0 to 255. |
| `padding` | `1` | Space between pictures, in pixels. |
| `jpeg_quality` | `92` | JPEG quality used when initially saving collages. Valid values are 1 to 95. |

Pictures are selected by file size, largest first, up to `count`.

### `[compression]`

| Setting | Default | Purpose |
|---|---:|---|
| `target_size_ratio` | `0.5` | Desired compressed size as a fraction of the original size. |
| `min_jpeg_quality` | `20` | Lowest JPEG quality considered. |
| `max_jpeg_quality` | `95` | Highest JPEG quality considered. |
| `optimize` | `true` | Enables Pillow's optimized JPEG encoder. |
| `progressive` | `true` | Creates progressive JPEG output. |
| `subsampling` | `0` | JPEG chroma-subsampling setting. |
| `dry_run` | `false` | Reports expected compression without changing collage files. |

The quality values must satisfy:

```text
1 <= min_jpeg_quality <= max_jpeg_quality <= 95
```

`target_size_ratio` must be greater than 0 and no greater than 1.

### `[report]`

| Setting | Default | Purpose |
|---|---:|---|
| `title` | `"Cleaners Report"` | Heading shown at the beginning of the report. |
| `filename_prefix` | `"cleaners_report_"` | Prefix for generated DOCX and PDF filenames. |
| `folder_date_format` | `"%Y%m%d"` | Format used to recognize date folder names. |
| `filename_date_format` | `"%d%b%Y"` | Date format used in generated filenames. |
| `heading_month_year_format` | `"%b %Y"` | Month and year format used in date headings. |
| `max_image_width_cm` | `12` | Maximum report image width in centimetres. |
| `max_image_height_cm` | `22` | Maximum report image height in centimetres. |
| `page_width_cm` | `21` | Report page width in centimetres. |
| `page_height_cm` | `29.7` | Report page height in centimetres. |

If valid date folders exist, the filename date is the Monday of the earliest
date. If every top-level folder is text, today's date is used instead.

## Command-line overrides

Individual scripts retain command-line options for temporary changes. These
options do not modify either TOML file. Examples:

```powershell
uv run python .\collage_pictures.py --images-per-row 3
uv run python .\compress_pics.py --dry-run
uv run python .\word_docx_gen.py --title "Special Cleaners Report"
uv run python .\docx_to_pdf.py --no-compress
```

Run a script with `--help` to see all supported overrides.
