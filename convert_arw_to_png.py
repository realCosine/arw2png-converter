#!/usr/bin/env python3
"""Convert all .ARW files from a source folder to PNG."""

from __future__ import annotations

import argparse
import concurrent.futures
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional, Tuple

from tqdm import tqdm

try:
    import rawpy
    from PIL import Image
except ImportError:  # pragma: no cover
    rawpy = None
    Image = None


def parse_args() -> argparse.Namespace:
    default_dest = Path.home() / "Desktop" / "SonyA6100"

    parser = argparse.ArgumentParser(
        description="Convert all ARW files in a source folder to PNG.",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to a folder that contains ARW files (required)",
    )
    parser.add_argument(
        "--destination",
        default=str(default_dest),
        help="Destination folder for PNG files. Default: ~/Desktop/SonyA6100/",
    )
    parser.add_argument(
        "--backend",
        choices=("rawpy", "magick", "auto"),
        default="auto",
        help="Conversion backend: rawpy (Python), magick (ImageMagick), auto",
    )
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Search recursively in subfolders (default: enabled)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PNG files",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=0,
        help="Number of worker threads. 0 disables threading (default), 1 uses single-thread processing",
    )
    return parser.parse_args()


def command_available(cmd: str) -> bool:
    return (
        subprocess.run(["where.exe", cmd], capture_output=True, text=True).returncode == 0
        if sys.platform == "win32"
        else subprocess.run(["which", cmd], capture_output=True, text=True).returncode == 0
    )


def collect_arw_files(folder: Path, recursive: bool) -> Iterable[Path]:
    iterator = folder.rglob("*") if recursive else folder.iterdir()
    for path in iterator:
        if path.is_file() and path.suffix.lower() == ".arw":
            yield path


def convert_with_rawpy(src: Path, dst: Path) -> None:
    if rawpy is None or Image is None:
        raise RuntimeError("Missing dependencies: rawpy and Pillow must be installed")

    with rawpy.imread(str(src)) as raw:
        rgb = raw.postprocess(
            no_auto_bright=False,
            use_camera_wb=True,
            half_size=False,
            output_bps=8,
        )
    image = Image.fromarray(rgb)
    image.save(dst, format="PNG")


def convert_with_magick(src: Path, dst: Path) -> None:
    subprocess.run(
        ["magick", str(src), str(dst)],
        check=True,
        capture_output=True,
        text=True,
    )


def ensure_destination(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)


def resolve_output_name(destination: Path, src: Path, overwrite: bool) -> Path:
    candidate = destination / (src.stem + ".png")
    if overwrite or not candidate.exists():
        return candidate

    index = 1
    while True:
        alt = destination / f"{src.stem}_{index}.png"
        if not alt.exists():
            return alt
        index += 1


def choose_backend(selected: str) -> str:
    if selected == "auto":
        if rawpy is not None and Image is not None:
            return "rawpy"
        if command_available("magick"):
            return "magick"
        raise RuntimeError(
            "No conversion backend found. Install rawpy + Pillow or ImageMagick (magick)."
        )

    if selected == "rawpy":
        if rawpy is None or Image is None:
            raise RuntimeError("Backend 'rawpy' selected, but rawpy/Pillow are not installed.")
        return "rawpy"

    if selected == "magick":
        if not command_available("magick"):
            raise RuntimeError("Backend 'magick' selected, but 'magick' was not found in PATH.")
        return "magick"

    return selected


def main() -> int:
    args = parse_args()

    source = Path(args.source).expanduser().resolve()
    destination = Path(args.destination).expanduser().resolve()

    if not source.exists() or not source.is_dir():
        print(f"[ERROR] Source is not a directory: {source}", file=sys.stderr)
        return 1

    backend = choose_backend(args.backend)
    ensure_destination(destination)

    arw_files = sorted(
        collect_arw_files(source, recursive=args.recursive),
        key=lambda p: str(p).lower(),
    )
    if not arw_files:
        print(f"No ARW files found in: {source}")
        return 0

    def process_file(src: Path) -> Tuple[str, str, Optional[str]]:
        out = resolve_output_name(destination, src, overwrite=args.overwrite)
        try:
            if backend == "rawpy":
                convert_with_rawpy(src, out)
            else:
                convert_with_magick(src, out)
            return src.name, out.name, None
        except Exception as exc:
            return src.name, out.name, str(exc)

    converted = 0
    failed = 0
    use_threads = args.threads > 0
    max_workers = args.threads if args.threads > 0 else 1

    description = "Converting (parallel)" if use_threads else "Converting"
    with tqdm(total=len(arw_files), unit="file", desc=description) as progress:
        if use_threads:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_file, src) for src in arw_files]
                for future in concurrent.futures.as_completed(futures):
                    src_name, out_name, error = future.result()
                    progress.update(1)
                    if error is None:
                        converted += 1
                        tqdm.write(f"OK: {src_name} -> {out_name}")
                    else:
                        failed += 1
                        tqdm.write(f"ERROR: {src_name} -> {out_name}: {error}")
        else:
            for src in arw_files:
                src_name, out_name, error = process_file(src)
                progress.update(1)
                if error is None:
                    converted += 1
                    tqdm.write(f"OK: {src_name} -> {out_name}")
                else:
                    failed += 1
                    tqdm.write(f"ERROR: {src_name} -> {out_name}: {error}")

    print(f"Done: {converted} converted, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
