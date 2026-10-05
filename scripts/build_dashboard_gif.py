"""Create an animated walkthrough from the real browser dashboard captures."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "screenshots"
OUTPUT = SCREENSHOT_DIR / "dashboard_walkthrough.gif"
SCREENSHOTS = [
    "executive_overview.png",
    "sales_performance.png",
    "customer_analytics.png",
    "product_analytics.png",
    "inventory_operations.png",
    "returns_profitability.png",
]


def build_gif() -> Path:
    paths = [SCREENSHOT_DIR / name for name in SCREENSHOTS]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        names = ", ".join(str(path.relative_to(ROOT)) for path in missing)
        raise FileNotFoundError(f"Dashboard screenshots are missing: {names}")

    rgb_frames = []
    for path in paths:
        with Image.open(path) as image:
            if image.size != (1280, 720):
                raise ValueError(
                    f"{path.name} is {image.width}x{image.height}; "
                    "expected a 1280x720 browser capture."
                )
            rgb_frames.append(image.convert("RGB"))

    palette = rgb_frames[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    frames = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE)
        for frame in rgb_frames
    ]
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=1200,
        loop=0,
        disposal=2,
        optimize=True,
    )
    for frame in rgb_frames:
        frame.close()
    for frame in frames:
        frame.close()
    palette.close()
    return OUTPUT


if __name__ == "__main__":
    print(f"Dashboard walkthrough saved to {build_gif()}")
