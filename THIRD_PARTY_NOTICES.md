# Third-party notices

Ikonvert is licensed under the MIT License (see `LICENSE`).
The portable Windows package also contains the third-party software listed
below. Each component keeps its own license. The full license texts are
included in the `licenses/` folder of the portable package (they are copied
from the installed packages when the app is built).

| Component | License | Website |
|---|---|---|
| Python | PSF License Agreement | https://www.python.org/ |
| Qt for Python (PySide6, Shiboken6) | LGPL-3.0 | https://www.qt.io/qt-for-python |
| Qt 6 libraries (bundled with PySide6) | LGPL-3.0 | https://www.qt.io/ |
| Pillow | MIT-CMU (HPND) | https://python-pillow.github.io/ |
| PyInstaller bootloader | GPL-2.0 with bootloader exception | https://pyinstaller.org/ |

## Qt / PySide6 (LGPL-3.0)

Ikonvert uses Qt and PySide6 under the GNU Lesser General Public License v3.

- Qt and PySide6 are **not modified** and are **dynamically linked**. They
  ship as separate library files (`.dll` / `.pyd`) inside the `_internal`
  folder of the portable package.
- You may replace these libraries with your own compatible (modified) builds.
- The source code for Qt and PySide6 is available at
  https://code.qt.io/ and https://download.qt.io/.
- The complete source code of Ikonvert is published in the source code zip,
  so the whole app can be rebuilt with `build.bat`.

## PyInstaller

The program launcher (`Ikonvert.exe`) is built with the PyInstaller
bootloader. Its license (GPL-2.0 with a special exception) allows the
bootloader to be distributed with programs under any license.

## App icon

The app icon artwork (`assets/app_icon.png`) is supplied by the author,
Stefan Karlsson. `assets/app.ico` is generated from it with
`tools/update_icon.py`.
