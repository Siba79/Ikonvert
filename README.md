# Ikonvert

Ikonvert is a free, open-source and portable Windows tool for working with icons.

- **Image → ICO:** drop any image (PNG, JPG, BMP, GIF, WebP, TIFF or TGA) to
  make a multi-size `.ico` with 16, 24, 32, 48, 64, 80, 96, 128, 160, 192
  and 256 px.
  Transparency is detected and kept automatically.
- **ICO → PNG:** drop an `.ico` to preview every size inside it and extract
  them as separate PNG files.

## Features

- Drag and drop files or folders, or browse
- Preview of every size with a checkerboard background and 100/200/400% zoom
- Light and dark mode (light by default)
- Batch conversion with **Convert all**
- Asks before replacing existing files
- Portable: the only file it writes is `settings.json`, next to `Ikonvert.exe`

## Download

Get the latest version from the
[Releases page](https://github.com/Siba79/Ikonvert/releases):

- `Ikonvert_v<version>_portable_win64.zip`: unzip and run `Ikonvert.exe`
- `Ikonvert_v<version>_source.zip`: the source code

Each release is scanned on VirusTotal, see
[VirusTotal_Ikonvert.md](VirusTotal_Ikonvert.md).

## Run from source

```
pip install -r requirements.txt
python ikonvert.py
```

## Project layout

| Path | What it is |
|---|---|
| `ikonvert.py` | The app (PySide6 GUI) |
| `ico_core.py` | Conversion logic (no GUI) |
| `version.py` | App name and version |
| `assets/app.ico` | App icon |

## License

Ikonvert is released under the [MIT License](LICENSE).
Copyright (c) 2026 Stefan Karlsson.

Third-party components and their licenses are listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
