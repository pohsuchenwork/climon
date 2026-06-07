"""Build cached terminal sprite art from PokeAPI PNGs using chafa.

Run with `make build-sprites` (or `uv run python tools/build_sprites.py`). For each
Pokemon this fetches a front and a back PNG, re-frames it (crops the empty border and
centers the Pokemon on a square canvas with a margin all around, so every sprite fills
the panel consistently and never looks cut off), renders it to truecolor half-block
ANSI at the battle-panel size, and writes ``src/climon/assets/sprites/<name>.<front|
back>.ans``. Those files are committed, so end users need neither chafa nor network.

Fronts come from Gen-3 FireRed/LeafGreen (the clean, classic look). Backs come from
Gen-4 HeartGold/SoulSilver, because the Gen-3 back sprites are a close-up cropped at
the bottom by the games, while the Gen-4 backs show the whole Pokemon.
"""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image

SPRITE_WIDTH = 28
SPRITE_HEIGHT = 14
FILL = 0.82
_REPO = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions"
FRONT_URL = f"{_REPO}/generation-iii/firered-leafgreen"
BACK_URL = f"{_REPO}/generation-iv/heartgold-soulsilver/back"
# The roster: name -> national dex id. All are Kanto (1-151), so both sources have them.
ROSTER: dict[str, int] = {
    "bulbasaur": 1,
    "charmander": 4,
    "squirtle": 7,
    "charizard": 6,
    "pikachu": 25,
    "machamp": 68,
    "gengar": 94,
    "gyarados": 130,
    "lapras": 131,
    "snorlax": 143,
    "dragonite": 149,
    "mewtwo": 150,
}
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "climon" / "assets" / "sprites"


def fetch_png(dex_id: int, *, back: bool) -> bytes:
    """Download one Pokemon PNG (front from Gen-3, back from Gen-4) over HTTPS."""
    url = f"{BACK_URL}/{dex_id}.png" if back else f"{FRONT_URL}/{dex_id}.png"
    with urllib.request.urlopen(url, timeout=30) as response:
        data: bytes = response.read()
    return data


def reframe(png: bytes) -> bytes:
    """Crop to the Pokemon and center it on a square canvas.

    Cropping the source's own padding makes the Pokemon fill the panel; the square
    canvas keeps the aspect ratio when chafa stretches it to the panel size; FILL
    leaves a margin all around so no edge looks cut off.
    """
    with Image.open(io.BytesIO(png)) as image:
        rgba = image.convert("RGBA")
    bbox = rgba.getbbox()
    if bbox is None:
        return png
    content = rgba.crop(bbox)
    width, height = content.size
    side = round(max(width, height) / FILL)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(content, ((side - width) // 2, (side - height) // 2))
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


def render_ansi(png: bytes) -> str:
    """Render a PNG to fixed-size truecolor half-block ANSI with chafa."""
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        tmp.write(png)
        tmp.flush()
        result = subprocess.run(
            [
                "chafa",
                "-f",
                "symbols",
                "--symbols",
                "half",
                "-c",
                "full",
                "--stretch",
                "-s",
                f"{SPRITE_WIDTH}x{SPRITE_HEIGHT}",
                tmp.name,
            ],
            capture_output=True,
            check=True,
        )
    return result.stdout.decode("utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, dex_id in ROSTER.items():
        for back in (False, True):
            view = "back" if back else "front"
            ansi = render_ansi(reframe(fetch_png(dex_id, back=back)))
            out = OUT_DIR / f"{name}.{view}.ans"
            out.write_text(ansi, encoding="utf-8")
            print(f"wrote {out.name}: {len(ansi)} bytes, {ansi.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
