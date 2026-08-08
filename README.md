# arw2png-converter

Convert RAW files in **.ARW** format to **PNG** from the command line.

## Usage

```bash
python convert_arw_to_png.py --source "D:\\DCIM\\100MSDCF"
```

or with a custom destination:

```bash
python convert_arw_to_png.py --source "D:\\DCIM\\100MSDCF" --destination "D:\\export\\png"
```

## Options

- `--source` (required): folder containing `.arw` files
- `--destination`: output folder, default `~/Desktop/SonyA6100/`
- `--backend`: `auto` (default), `rawpy`, `magick`
- `--recursive` / `--no-recursive`: include subfolders (default: include)
- `--overwrite`: overwrite existing PNG files
- `--threads`: number of worker threads (`0` disables threading, default)
- `--bit-depth`: `8` or `16` bits per channel for rawpy backend; `16` is default (maximum quality)

### Parallel example

```bash
python convert_arw_to_png.py --source "D:\\DCIM\\100MSDCF" --threads 8
```

## Requirements

- Option A (recommended): Python packages `rawpy`, `Pillow`, and `pypng`
- Option B: ImageMagick (`magick` on PATH)

Install:

```bash
pip install -r requirements.txt
```
