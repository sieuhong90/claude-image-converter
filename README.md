# claude-image-converter

A [Claude Code](https://claude.ai/claude-code) skill that converts images between **JPG**, **JPEG**, **PNG**, and **HEIC** formats — single file or entire batch. No configuration needed on macOS.

---

## Features

- **Batch or single file** — point it at a file or a whole folder
- **Zero setup on macOS** — uses the built-in `sips` tool by default
- **Cross-platform fallback chain** — sips → Pillow → ImageMagick
- **Alpha channel handling** — transparent PNGs are flattened to white before saving as JPG
- **Near-lossless quality** — JPG at quality 95 (4:4:4), PNG at compress_level 0
- **Clean output** — all converted files land in an `Output/` subfolder, originals untouched

---

## Installation

Copy the skill into your Claude Code skills directory:

```bash
git clone https://github.com/sieuhong90/claude-image-converter ~/.claude/skills/image-converter
```

Restart Claude Code and the `/image-converter` skill is available.

---

## Usage

Just describe what you want in plain language inside Claude Code:

```
convert all images in this folder to jpg
turn my heic photos into pngs
convert /path/to/photo.heic to jpg
```

Or use the bundled script directly:

```bash
# Single file
python3 ~/.claude/skills/image-converter/scripts/convert_images.py photo.heic --to jpg

# Multiple files
python3 ~/.claude/skills/image-converter/scripts/convert_images.py a.heic b.png --to jpg

# Entire folder
python3 ~/.claude/skills/image-converter/scripts/convert_images.py /path/to/photos/ --to png
```

Output is always saved to an `Output/` subfolder next to the source files.

---

## Supported Formats

| Format | Read | Write |
|--------|------|-------|
| JPG / JPEG | Yes | Yes |
| PNG | Yes | Yes |
| HEIC | Yes | Yes (macOS / with pillow-heif) |

---

## Tool Priority

The script automatically selects the best available tool:

| Priority | Tool | Platform | Install |
|----------|------|----------|---------|
| 1 | **sips** | macOS only | Built-in (no install needed) |
| 2 | **Pillow** | Cross-platform | `pip install Pillow pillow-heif` |
| 3 | **ImageMagick** | Cross-platform | `brew install imagemagick` / `apt install imagemagick` |

---

## Quality Settings

| Target Format | Setting |
|---------------|---------|
| PNG | Lossless (`compress_level=0`) |
| JPG / JPEG | Highest quality (`quality=95`, `subsampling=0` — 4:4:4 chroma) |
| HEIC | Default export via sips or ImageMagick |

> Note: converting from a lossy source (e.g. JPEG → PNG) preserves existing quality but cannot recover already-lost detail.

---

## Performance Benchmarks

The skill is validated against 3 automated eval cases covering the most common real-world scenarios.

### Eval Results

| # | Test Case | Assertions | Result |
|---|-----------|------------|--------|
| 1 | Single file: JPG → PNG | Output file exists · Placed in `Output/` · Valid PNG · Success reported | **PASS** |
| 2 | RGBA PNG → JPG (alpha channel) | Output file exists · Valid JPEG · No alpha-mode error | **PASS** |
| 3 | Batch folder → PNG | `Output/` folder created · All files converted · Count reported | **PASS** |

### Real-world Run (10 HEIC files, macOS)

Tested on 10 iPhone photos (`IMG_7897.HEIC` – `IMG_8210.HEIC`) using `sips` on macOS:

| Metric | Result |
|--------|--------|
| Files processed | 10 / 10 |
| Failures | 0 |
| Tool used | sips (built-in) |
| HEIC → JPG | All succeeded |
| HEIC → PNG | All succeeded |
| Output location | `Output/` subfolder |

### Assertion Coverage

```
output_file_exists          ✓  Output lands in Output/ with correct name
output_in_correct_folder    ✓  Output/ is always alongside source, never in-place
correct_format              ✓  Output file is a valid image of the target format
reports_success             ✓  Claude confirms success and states output location
output_is_valid_jpeg        ✓  Alpha channels flattened cleanly, no mode errors
no_error_about_alpha        ✓  RGBA → JPG handled without exceptions
output_folder_created       ✓  Batch mode creates Output/ automatically
jpg_converted_to_png        ✓  Mixed-format folders processed correctly
all_files_processed         ✓  Batch reports all files, not just the first
reports_count               ✓  Final summary always includes succeeded/failed count
```

---

## Sharing with Colleagues

Colleagues using Claude Code can install this skill with one command:

```bash
git clone https://github.com/sieuhong90/claude-image-converter ~/.claude/skills/image-converter
```

---

## Requirements

- Python 3.7+
- macOS (recommended — zero install) or any OS with Pillow / ImageMagick installed

---

## License

MIT
