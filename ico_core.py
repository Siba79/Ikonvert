"""
ico_core.py - Image <-> ICO conversion logic used by Ikonvert.

Copyright (c) 2026 Stefan Karlsson
Licensed under the MIT License (see LICENSE).

No GUI code here, so it can be tested and reused on its own.
"""

import os
from collections import Counter

from PIL import Image, ImageOps

SIZES = [16, 24, 32, 48, 64, 80, 96, 128, 160, 192, 256]

IMAGE_EXTS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp",
    ".tif", ".tiff", ".tga", ".ico",
}


def is_supported(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS


def is_ico(path: str) -> bool:
    return os.path.splitext(path)[1].lower() == ".ico"


# ----------------------------------------------------------------------------
# Image -> ICO
# ----------------------------------------------------------------------------
def _normalize_mode(img: Image.Image) -> Image.Image:
    """Bring 16-bit / float images down to 8-bit so colours convert correctly."""
    if img.mode in ("I;16", "I;16B", "I;16L", "I"):
        return img.convert("I").point(lambda v: v / 256).convert("L")
    if img.mode == "F":
        return img.point(lambda v: v * 255).convert("L")
    return img


def load_image(path: str) -> dict:
    """
    Load any supported image and return:
        image      RGBA image (opaque if the source has no transparency)
        has_alpha  True if real transparency was found
        size       original (w, h)
        format     source format name (PNG, JPEG, ...)
    """
    with Image.open(path) as src:
        fmt = src.format or os.path.splitext(path)[1][1:].upper()
        try:
            src.seek(0)  # first frame of animated GIF/WebP
        except EOFError:
            pass
        img = ImageOps.exif_transpose(src)  # respect camera rotation
        img = _normalize_mode(img)

        has_alpha = False
        if img.mode in ("RGBA", "LA", "PA", "RGBa", "La") or "transparency" in img.info:
            rgba = img.convert("RGBA")
            has_alpha = rgba.getchannel("A").getextrema()[0] < 255
        else:
            rgba = img.convert("RGBA")  # fully opaque

    return {"image": rgba, "has_alpha": has_alpha, "size": rgba.size, "format": fmt}


def make_square(img: Image.Image) -> Image.Image:
    """Center the image on a transparent square canvas (no stretching)."""
    w, h = img.size
    if w == h:
        return img
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2))
    return canvas


def build_frames(rgba: Image.Image, sizes=SIZES) -> list:
    """Return one high-quality resized frame per size (smallest first)."""
    square = make_square(rgba)
    return [square.resize((s, s), Image.LANCZOS) for s in sorted(sizes)]


def ico_path_for(src_path: str) -> str:
    return os.path.splitext(src_path)[0] + ".ico"


def save_ico(frames: list, ico_path: str) -> str:
    """Save frames (smallest first) as one multi-size .ico file."""
    frames = sorted(frames, key=lambda f: f.width)
    frames[-1].save(
        ico_path,
        format="ICO",
        sizes=[f.size for f in frames],
        append_images=frames[:-1],
    )
    return ico_path


def image_to_ico(src_path: str, ico_path: str | None = None) -> str:
    data = load_image(src_path)
    return save_ico(build_frames(data["image"]), ico_path or ico_path_for(src_path))


# ----------------------------------------------------------------------------
# ICO -> PNGs
# ----------------------------------------------------------------------------
def read_ico(path: str) -> list:
    """
    Read every image inside an .ico.
    Returns a list of dicts (largest first): image (RGBA), width, height, bpp.
    """
    frames = []
    with Image.open(path) as im:
        if im.format != "ICO":
            raise ValueError("Not a valid ICO file")
        for i, entry in enumerate(im.ico.entry):
            img = im.ico.frame(i).convert("RGBA")
            frames.append({
                "image": img,
                "width": img.width,
                "height": img.height,
                "bpp": getattr(entry, "bpp", 32) or 32,
            })
    frames.sort(key=lambda f: (f["width"] * f["height"], f["bpp"]), reverse=True)
    return frames


def png_dir_for(ico_path: str) -> str:
    base = os.path.splitext(os.path.basename(ico_path))[0]
    return os.path.join(os.path.dirname(ico_path), f"{base}_png")


def png_names(ico_path: str, frames: list) -> list:
    """File names for each frame; bit depth is added when a size repeats."""
    base = os.path.splitext(os.path.basename(ico_path))[0]
    count = Counter((f["width"], f["height"]) for f in frames)
    names = []
    for f in frames:
        name = f"{base}_{f['width']}x{f['height']}"
        if count[(f["width"], f["height"])] > 1:
            name += f"_{f['bpp']}bit"
        names.append(name + ".png")
    return names


def save_pngs(ico_path: str, frames: list, out_dir: str | None = None) -> list:
    out_dir = out_dir or png_dir_for(ico_path)
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for f, name in zip(frames, png_names(ico_path, frames)):
        out = os.path.join(out_dir, name)
        f["image"].save(out, "PNG")
        saved.append(out)
    return saved


def ico_to_pngs(ico_path: str, out_dir: str | None = None) -> list:
    return save_pngs(ico_path, read_ico(ico_path), out_dir)
