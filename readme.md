# Find Luigi

> or else...

## Overview

This program is a recreation of the Wanted minigame from New Super Mario Bros for Windows. Your goal is to find and click on Luigi within 30 seconds. Should you fail, your PC won't boot anymore.

[A screenshot of the software running on top of a Windows desktop.](screenshot.jpg)

---

## Requirements

| Component  | Version                         |
| ---------- | ------------------------------- |
| **OS**     | Windows 10/11 (Win32 APIs used) |
| **Python** | 3.8 or newer                    |
| **PyQt5**  | 5.15 or newer                   |

You can download an exe from this projects' releases. Available are builds with or without the destructive payload.

Install dependencies:

```bash
pip -r requirements.txt
```

---

## Change Between Safe and Destructive mode

```python
# main.py — top of file
DANGEROUS_BUILD = False  # <— Safe
DANGEROUS_BUILD = True  # <— Destructive
```

Then simply run:

```bash
python main.py
```

---

## Building a Stand‑Alone EXE (PyInstaller)

```bash
pyinstaller --onefile --noconsole --add-data "assets;assets"  --icon assets/app.ico main.py
```

---

## Customization

| Constant              | Purpose                             | Default |
| --------------------- | ----------------------------------- | ------- |
| `FRAME_RATE`          | Animation FPS                       | `60`    |
| `IMAGE_SCALE_FACTOR`  | Size multiplier for sprites         | `4`     |
| `SPRITE_COUNT_FACTOR` | Density control (pixels per sprite) | `35000` |
| `SPEED_FACTOR`        | Initial velocity multiplier         | `2.0`   |

---

## License

Released under the MIT License.

---

## Disclaimer

This software is provided **“as is”** without warranty of any kind. By using or distributing the code you accept that **you** are solely responsible for any consequences.
