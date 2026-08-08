# arw2png-converter

Konvertiert RAW-Dateien im **.ARW**-Format zu **PNG** über die Kommandozeile.

## Verwendung

```bash
python convert_arw_to_png.py --source "D:\\DCIM\\100MSDCF"
```

oder mit anderem Zielordner:

```bash
python convert_arw_to_png.py --source "D:\\DCIM\\100MSDCF" --destination "D:\\export\\png"
```

## Optionen

- `--source` (Pflicht): Ordner mit ARW-Dateien
- `--destination`: Zielordner, Standard `~/Desktop/SonyA6100/`
- `--backend`: `auto` (Standard), `rawpy`, `magick`
- `--recursive` / `--no-recursive`: Unterordner einbeziehen (Standard: einbeziehen)
- `--overwrite`: Bestehende PNG-Dateien überschreiben

## Voraussetzungen

- Variante A (empfohlen): Python-Pakete `rawpy` und `Pillow`
- Variante B: ImageMagick (`magick` im PATH)

Installation:

```bash
pip install -r requirements.txt
```
