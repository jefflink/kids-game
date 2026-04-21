"""
scale_covers.py
---------------
Scales all cover.png files found under a data/ directory to 600x400,
using cover-fit logic: the image is scaled to fill the frame, centred,
and any remaining space is padded with a blurred/darkened version of
itself (no ugly black bars).

Requirements:
    pip install Pillow

Usage:
    python scale_covers.py                  # looks for ./data/
    python scale_covers.py /path/to/data    # explicit path
"""

from pathlib import Path
from PIL import Image, ImageFilter
import sys


TARGET_W, TARGET_H = 600, 400


def scale_cover(src: Path, dst: Path | None = None, *, backup: bool = True) -> Path:
    """
    Scale a single PNG to 600x400 with smart letterbox fill.

    The image is resized to COVER the target canvas (no distortion),
    centred, then cropped to 600x400. If the aspect ratio differs from
    3:2, a blurred version of the image fills the background so there
    are no black bars.

    Args:
        src:    Path to the source PNG.
        dst:    Output path. Defaults to overwriting src in-place.
        backup: If True and dst == src, save a .bak copy before overwriting.

    Returns:
        Path to the saved output file.
    """
    dst = dst or src

    img = Image.open(src).convert("RGBA")
    orig_w, orig_h = img.size

    # ── 1. Build blurred background (fills any letterbox areas) ──────────
    bg = img.copy().convert("RGB")
    # Scale background to fill the entire target, ignoring aspect ratio
    bg = bg.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=18))
    # Darken so the real image pops
    bg = bg.point(lambda p: int(p * 0.45))

    # ── 2. Scale the real image to COVER the target ───────────────────────
    scale = max(TARGET_W / orig_w, TARGET_H / orig_h)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)
    fg = img.convert("RGB").resize((new_w, new_h), Image.LANCZOS)

    # ── 3. Centre-crop to target ──────────────────────────────────────────
    left = (new_w - TARGET_W) // 2
    top  = (new_h - TARGET_H) // 2
    fg   = fg.crop((left, top, left + TARGET_W, top + TARGET_H))

    # ── 4. Composite fg over blurred bg ──────────────────────────────────
    result = Image.new("RGB", (TARGET_W, TARGET_H))
    result.paste(bg, (0, 0))
    result.paste(fg, (0, 0))

    # ── 5. Save ───────────────────────────────────────────────────────────
    if backup and dst.resolve() == src.resolve() and src.exists():
        src.rename(src.with_suffix(".bak.png"))

    dst.parent.mkdir(parents=True, exist_ok=True)
    result.save(dst, format="PNG", optimize=True)
    return dst


def scale_all_covers(data_dir: str | Path = "./data") -> None:
    """
    Walk *data_dir* and scale every cover.png found to 600x400.

    Expected layout:
        data/
          game-name/
            cover.png   ← processed in-place (original saved as cover.bak.png)
            main.html

    Args:
        data_dir: Root directory to search. Defaults to ./data
    """
    data_dir = Path(data_dir)

    if not data_dir.is_dir():
        print(f"[error] Directory not found: {data_dir}")
        sys.exit(1)

    covers = sorted(data_dir.rglob("cover.png"))

    if not covers:
        print(f"[info] No cover.png files found under '{data_dir}'.")
        return

    print(f"Found {len(covers)} cover(s) — scaling to {TARGET_W}×{TARGET_H}...\n")

    ok = failed = skipped = 0

    for cover in covers:
        try:
            with Image.open(cover) as probe:
                w, h = probe.size

            if (w, h) == (TARGET_W, TARGET_H):
                print(f"  [skip]  {cover}  (already {TARGET_W}×{TARGET_H})")
                skipped += 1
                continue

            out = scale_cover(cover)
            print(f"  [ok]    {cover}  ({w}×{h} → {TARGET_W}×{TARGET_H})")
            ok += 1

        except Exception as exc:
            print(f"  [fail]  {cover}  — {exc}")
            failed += 1

    print(f"\nDone: {ok} scaled, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "./data"
    scale_all_covers(root)
