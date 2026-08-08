#!/usr/bin/env python3
"""Convert all .ARW files from a source folder to PNG."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable

try:
    import rawpy
    from PIL import Image
except ImportError:  # pragma: no cover
    rawpy = None
    Image = None


def parse_args() -> argparse.Namespace:
    home = Path.home()
    default_dest = home / "Desktop" / "SonyA6100"

    parser = argparse.ArgumentParser(
        description="Konvertiere alle ARW-Dateien eines Ordners in PNG.",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Pfad zu einem Ordner mit ARW-Dateien (Pflichtargument)",
    )
    parser.add_argument(
        "--destination",
        default=str(default_dest),
        help="Zielordner für PNGs. Default: ~/Desktop/SonyA6100/",
    )
    parser.add_argument(
        "--backend",
        choices=("rawpy", "magick", "auto"),
        default="auto",
        help="Konvertierungs-Backend: rawpy (Python), magick (ImageMagick), auto",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Rekursiv in Unterordnern suchen (Standard)",
    )
    parser.add_argument(
        "--recursive",
        dest="recursive",
        action="store_false",
        help="Nur im angegebenen Verzeichnis suchen (kein Unterordner)",
    )
    parser.set_defaults(recursive=True)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Bestehende PNG-Dateien überschreiben",
    )
    return parser.parse_args()


def command_available(cmd: str) -> bool:
    return (
        subprocess.run(["where.exe", cmd], capture_output=True, text=True).returncode == 0
        if sys.platform == "win32"
        else subprocess.run(["which", cmd], capture_output=True, text=True).returncode == 0
    )


def collect_arw_files(folder: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        iterator = folder.rglob("*")
    else:
        iterator = folder.iterdir()

    for path in iterator:
        if path.is_file() and path.suffix.lower() == ".arw":
            yield path


def convert_with_rawpy(src: Path, dst: Path) -> None:
    if rawpy is None or Image is None:
        raise RuntimeError("Python-Pakete nicht installiert: rawpy, Pillow")

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
        ["magick", str(src), str(dst)], check=True, capture_output=True, text=True
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
            "Kein Konvertierungs-Backend gefunden. Installiere rawpy+Pillow oder ImageMagick (magick)."
        )
    if selected == "rawpy":
        if rawpy is None or Image is None:
            raise RuntimeError("Auswahl 'rawpy' gewählt, aber rawpy/Pillow nicht installiert.")
        return "rawpy"
    if selected == "magick":
        if not command_available("magick"):
            raise RuntimeError("Auswahl 'magick' gewählt, aber 'magick' nicht gefunden.")
        return "magick"
    return selected


def main() -> int:
    args = parse_args()

    source = Path(args.source).expanduser().resolve()
    destination = Path(args.destination).expanduser().resolve()

    if not source.exists() or not source.is_dir():
        print(f"[FEHLER] Source ist kein Ordner: {source}", file=sys.stderr)
        return 1

    backend = choose_backend(args.backend)

    ensure_destination(destination)

    arw_files = sorted(collect_arw_files(source, recursive=args.recursive), key=lambda p: str(p).lower())
    if not arw_files:
        print(f"Keine ARW-Dateien gefunden in: {source}")
        return 0

    converted = 0
    failed = 0

    for src in arw_files:
        out = resolve_output_name(destination, src, overwrite=args.overwrite)
        try:
            if backend == "rawpy":
                convert_with_rawpy(src, out)
            else:
                convert_with_magick(src, out)
            converted += 1
            print(f"OK: {src.name} -> {out.name}")
        except Exception as exc:  # pragma: no cover
            failed += 1
            print(f"FEHLER: {src.name}: {exc}", file=sys.stderr)

    print(f"Fertig: {converted} konvertiert, {failed} Fehler")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
