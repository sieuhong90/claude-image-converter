---
name: image-converter
description: Convert image files between jpg, jpeg, png, and heic formats — single file or entire batch/folder. Invoke whenever the user wants to convert images, change image format, transform heic to jpg, convert png to jpeg, batch process a folder of images, or export photos in a different format. Use this skill for any combination of jpg/jpeg/png/heic conversions, even when phrased casually (e.g., "turn my heic photos into jpgs", "save this as a png", "convert all images in this folder").
---

# Image Converter

Convert images between **jpg**, **jpeg**, **png**, and **heic** formats — single file or batch. Outputs land in an `Output/` subfolder alongside the source files.

## Step 1: Gather inputs

Before running, confirm you have:
1. **Source** — a file path, multiple file paths, or a folder path
2. **Target format** — which format to convert to (jpg, jpeg, png, or heic)

If either is missing or ambiguous, ask. If the user provides a folder, the script will find all supported images inside it automatically.

## Step 2: Run the conversion

Use the bundled script for all conversions — don't write your own conversion code:

```bash
# Single file
python ~/.claude/skills/image-converter/scripts/convert_images.py photo.heic --to jpg

# Multiple specific files
python ~/.claude/skills/image-converter/scripts/convert_images.py a.heic b.png --to jpg

# Entire folder
python ~/.claude/skills/image-converter/scripts/convert_images.py /path/to/photos/ --to png
```

Always use absolute paths for input files to avoid working directory issues.

## Tool priority (handled automatically by the script)

The script tries tools in this order, falling back if one isn't available:

1. **sips** — macOS built-in, zero install required. Handles all four formats on macOS 10.13+.
2. **Pillow (Python)** — cross-platform. Works if Pillow is installed (`pip install Pillow`). For HEIC support on non-macOS, also needs `pip install pillow-heif`.
3. **ImageMagick** — cross-platform fallback. Works if installed (`brew install imagemagick` / `apt install imagemagick`).

## Quality settings

Conversions are lossless or near-lossless:

| Target format | Setting |
|---|---|
| PNG | Lossless (compress_level=0) |
| JPEG/JPG | Highest quality (quality=95, subsampling=0) |
| HEIC | Default export from sips/ImageMagick |

Note: converting from a lossy source (e.g. JPEG→PNG) preserves existing quality but cannot recover already-lost detail.

## Output

Converted files are saved to an `Output/` folder in the same directory as the source files. After the script finishes, report:
- How many files were converted successfully
- Where the Output folder is located
- Any files that failed, and why

## Handling failures

If a file fails to convert:
- Verify the extension is one of: `.jpg`, `.jpeg`, `.png`, `.heic` (case-insensitive)
- Check that at least one tool is available on the user's OS
- For HEIC on Windows/Linux with no sips: suggest `pip install pillow-heif` or install ImageMagick with libheif
- If all tools fail, tell the user which tool to install based on their platform
