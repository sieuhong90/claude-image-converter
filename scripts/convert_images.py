#!/usr/bin/env python3
"""
Image format converter: jpg/jpeg/png/heic
Tool priority: sips (macOS) → Pillow → ImageMagick
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}


def normalize_format(fmt: str) -> str:
    """Normalize format string to lowercase without leading dot."""
    return fmt.lower().lstrip(".")


def get_output_ext(target_format: str) -> str:
    """Return the file extension to use for the output file."""
    # Normalize jpeg → jpg for file naming consistency
    if target_format == "jpeg":
        return "jpg"
    return target_format


def try_sips(input_path: Path, output_path: Path, target_format: str) -> bool:
    """Convert using macOS built-in sips. Returns True on success."""
    if platform.system() != "Darwin":
        return False

    sips_format_map = {
        "jpg": "jpeg",
        "jpeg": "jpeg",
        "png": "png",
        "heic": "heic",
    }
    sips_fmt = sips_format_map.get(target_format)
    if not sips_fmt:
        return False

    try:
        result = subprocess.run(
            ["sips", "-s", "format", sips_fmt, str(input_path), "--out", str(output_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def try_pillow(input_path: Path, output_path: Path, target_format: str) -> bool:
    """Convert using Pillow. Returns True on success."""
    try:
        from PIL import Image
    except ImportError:
        return False

    # Register HEIF opener for HEIC support if available
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass

    try:
        img = Image.open(input_path)

        pil_format = target_format.upper()
        if pil_format in ("JPEG", "JPG"):
            pil_format = "JPEG"
            # JPEG does not support alpha — flatten to white background
            if img.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

        save_kwargs = {}
        if pil_format == "JPEG":
            save_kwargs["quality"] = 95
            save_kwargs["subsampling"] = 0  # 4:4:4 — best chroma quality
        elif pil_format == "PNG":
            save_kwargs["compress_level"] = 0  # lossless, no compression

        img.save(output_path, format=pil_format, **save_kwargs)
        return True
    except Exception:
        return False


def try_imagemagick(input_path: Path, output_path: Path, target_format: str) -> bool:
    """Convert using ImageMagick. Returns True on success."""
    for cmd in ["magick", "convert"]:
        try:
            args = [cmd]
            if target_format in ("jpg", "jpeg"):
                args += ["-quality", "95"]
            args += [str(input_path), str(output_path)]
            result = subprocess.run(args, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    return False


def convert_image(input_path: Path, output_path: Path, target_format: str) -> tuple:
    """Try each tool in priority order. Returns (success: bool, tool_used: str)."""
    if try_sips(input_path, output_path, target_format):
        return True, "sips"
    if try_pillow(input_path, output_path, target_format):
        return True, "Pillow"
    if try_imagemagick(input_path, output_path, target_format):
        return True, "ImageMagick"
    return False, "none"


def collect_input_files(inputs: list) -> list:
    """Resolve input paths to a flat list of supported image files."""
    files = []
    for raw in inputs:
        p = Path(raw).expanduser().resolve()
        if p.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(p.glob(f"*{ext}"))
                files.extend(p.glob(f"*{ext.upper()}"))
        elif p.is_file():
            if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(p)
            else:
                print(f"  Skipping {p.name}: unsupported format ({p.suffix})")
        else:
            print(f"  Not found: {raw}")
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def main():
    parser = argparse.ArgumentParser(
        description="Convert images between jpg/jpeg/png/heic formats."
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Input file(s) or directory containing images",
    )
    parser.add_argument(
        "--to",
        required=True,
        metavar="FORMAT",
        help="Target format: jpg, jpeg, png, or heic",
    )
    args = parser.parse_args()

    target_format = normalize_format(args.to)
    if target_format not in {"jpg", "jpeg", "png", "heic"}:
        print(f"Error: unsupported target format '{args.to}'. Choose from: jpg, jpeg, png, heic")
        sys.exit(1)

    input_files = collect_input_files(args.input)
    if not input_files:
        print("No supported image files found.")
        sys.exit(1)

    # Output folder alongside the source files
    output_dir = input_files[0].parent / "Output"
    output_dir.mkdir(exist_ok=True)

    out_ext = get_output_ext(target_format)
    success_count = 0
    fail_count = 0

    print(f"\nConverting {len(input_files)} file(s) → .{out_ext}")
    print(f"Output folder: {output_dir}\n")

    for input_file in input_files:
        out_name = input_file.stem + "." + out_ext
        output_path = output_dir / out_name

        # Skip if input and output are the same format
        if input_file.suffix.lower().lstrip(".") == target_format or (
            input_file.suffix.lower() in (".jpg", ".jpeg")
            and target_format in ("jpg", "jpeg")
        ):
            print(f"  ~ {input_file.name} — already in target format, copying as-is")
            import shutil
            shutil.copy2(input_file, output_path)
            success_count += 1
            continue

        ok, tool = convert_image(input_file, output_path, target_format)
        if ok:
            print(f"  ✓ {input_file.name}  →  {out_name}  (via {tool})")
            success_count += 1
        else:
            print(f"  ✗ {input_file.name}  —  conversion failed (no suitable tool found)")
            fail_count += 1

    print(f"\nDone: {success_count} succeeded, {fail_count} failed")
    if fail_count > 0:
        print("\nTip: install a fallback tool for your OS:")
        print("  macOS:   sips is built-in; or: brew install imagemagick")
        print("  Windows/Linux:  pip install Pillow pillow-heif")
        print("                  or: apt install imagemagick / choco install imagemagick")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
