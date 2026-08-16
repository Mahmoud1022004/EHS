#!/usr/bin/env python3
"""
Generate a WebP twin for every JPEG in assets/.

The original JPEGs are never modified or deleted — build.py wraps each <img>
in a <picture> element that offers the WebP first and falls back to the JPEG,
so browsers that do not support WebP still get an image.

Run:  python3 _build/optimize_images.py
Then: python3 _build/build.py     (to emit the <picture> markup)
"""
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip3 install --user Pillow")

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ROOT)
ASSETS = os.path.join(SITE, "assets")

QUALITY = 82      # visually indistinguishable from the source at normal viewing size
METHOD = 6        # slowest encoder setting = smallest file; only runs at build time


def convert(jpg_path):
    webp_path = os.path.splitext(jpg_path)[0] + ".webp"
    if (os.path.exists(webp_path)
            and os.path.getmtime(webp_path) >= os.path.getmtime(jpg_path)):
        return None  # already current
    with Image.open(jpg_path) as im:
        im = im.convert("RGB")
        im.save(webp_path, "WEBP", quality=QUALITY, method=METHOD)
    return webp_path


def main():
    jpgs = []
    for dirpath, _, filenames in os.walk(ASSETS):
        for name in filenames:
            if name.lower().endswith((".jpg", ".jpeg")):
                jpgs.append(os.path.join(dirpath, name))
    jpgs.sort()

    made, skipped, before, after = 0, 0, 0, 0
    for jpg in jpgs:
        jpg_size = os.path.getsize(jpg)
        result = convert(jpg)
        webp = os.path.splitext(jpg)[0] + ".webp"
        if result is None:
            skipped += 1
        else:
            made += 1
        if os.path.exists(webp):
            before += jpg_size
            after += os.path.getsize(webp)

    rel = lambda p: os.path.relpath(p, SITE)
    print(f"JPEGs found:   {len(jpgs)}")
    print(f"WebP written:  {made}   (up to date already: {skipped})")
    if before:
        saved = before - after
        print(f"JPEG total:    {before/1_048_576:.2f} MB")
        print(f"WebP total:    {after/1_048_576:.2f} MB")
        print(f"Saved:         {saved/1_048_576:.2f} MB  ({saved/before*100:.0f}% smaller)")


if __name__ == "__main__":
    main()
