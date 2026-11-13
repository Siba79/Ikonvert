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

Get the latest release from the `releases` folder or the release page:

- `Ikonvert_v<version>_portable_win64.zip`: unzip and run `Ikonvert.exe`
- `Ikonvert_v<version>_source.zip`: the full source code

## Run from source

```
pip install -r requirements.txt
python ikonvert.py
```

## Build

Double-click `build.bat`. It:

1. creates a private `.venv` in the project folder, so nothing is installed system-wide
2. builds the portable app with PyInstaller (onedir, no console window)
3. adds the license documents
4. creates both zips in `releases\`

The version number is set in `version.py`.

To change the app icon, replace `assets/app_icon.png` (square, ideally 1024 px) and run
`python tools/update_icon.py`.

## Project layout

| Path | What it is |
|---|---|
| `ikonvert.py` | The app (PySide6 GUI) |
| `ico_core.py` | Conversion logic (no GUI) |
| `version.py` | App name and version |
| `assets/` | App icon (`app.ico`, `app_icon.png`) |
| `tools/update_icon.py` | Rebuilds `app.ico` from `app_icon.png` |
| `tools/build_helper.py` | Used by `build.bat`: version info, licenses and zips |

## License

Ikonvert is released under the [MIT License](LICENSE).
Copyright (c) 2026 Stefan Karlsson.

Third-party components and their licenses are listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
