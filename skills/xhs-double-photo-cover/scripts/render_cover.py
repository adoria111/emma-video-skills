#!/usr/bin/env python3
"""Local, two-stage cover layout. Requires Pillow; never uploads or downloads."""
import argparse
import hashlib
import json
import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError:
    raise SystemExit("Pillow is unavailable in this Python environment. Reuse an environment with Pillow>=10, or install it within your authorization.")

SIZE = (1080, 1440)
HALF = (1080, 720)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def box(value, width, height, label):
    if (not isinstance(value, list) or len(value) != 4
            or any(type(v) is not int for v in value)):
        raise ValueError(f"{label}: expected four integer pixels [left, top, right, bottom]")
    left, top, right, bottom = value
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError(f"{label}: outside image or empty")
    return value


def contains(outer, inner):
    return (outer[0] <= inner[0] and outer[1] <= inner[1]
            and outer[2] >= inner[2] and outer[3] >= inner[3])


def overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def new_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(config_path, output):
    config_path = Path(config_path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source = (config_path.parent / config["source"]).resolve()
    with Image.open(source) as original:
        frame = ImageOps.exif_transpose(original).convert("RGB")
    crop = box(config["crop"], *frame.size, "crop")
    subject = box(config["subject_box"], *frame.size, "subject_box")
    if not contains(crop, subject):
        raise ValueError("Crop cuts the marked head/shoulder region; reframe or select another source")
    width, height = crop[2] - crop[0], crop[3] - crop[1]
    if width * 2 != height * 3:
        raise ValueError("Crop must be 3:2; do not stretch or silently center-crop a portrait frame")
    protected = config["face_boxes"]
    if not isinstance(protected, list) or not protected:
        raise ValueError("Mark at least one region covering eyes, nose and mouth")
    transformed = []
    for value in protected:
        value = box(value, *frame.size, "face_boxes")
        if not contains(crop, value):
            raise ValueError("Crop cuts a protected face region")
        transformed.append([(value[i] - crop[i % 2]) * HALF[i % 2] / (width, height)[i % 2]
                            for i in range(4)])
    panel = frame.crop(crop).resize(HALF, Image.Resampling.LANCZOS)
    preview = Image.new("RGB", SIZE)
    preview.paste(panel, (0, 0))
    preview.paste(panel, (0, 720))
    marked = panel.copy()
    draw = ImageDraw.Draw(marked)
    for value in transformed:
        draw.rectangle(value, outline="#ff7058", width=4)
    font = (config_path.parent / config["font"]).resolve()
    # Check the selected font can load; CJK coverage and actual weight need visual review.
    ImageFont.truetype(str(font), 100, index=config.get("font_index", 0))
    output = new_directory(output)
    panel.save(output / "panel.png")
    marked.save(output / "face-regions.png")
    preview.save(output / "plain-cover.png")
    config.update(source=str(source), font=str(font))
    plan = {"config": config, "source_sha256": digest(source), "font_sha256": digest(font),
            "panel_sha256": digest(output / "panel.png"), "face_boxes": transformed,
            "visual_review": "pending: inspect panel, marked face regions and reference before rendering"}
    write_json(output / "plan.json", plan)
    return plan


def number(config, key, default, minimum, maximum):
    value = config.get(key, default)
    if type(value) not in (float, int) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{key}: expected a number between {minimum} and {maximum}")
    return value


def render(prepared, output):
    prepared = Path(prepared)
    plan = json.loads((prepared / "plan.json").read_text(encoding="utf-8"))
    config = plan["config"]
    if digest(prepared / "panel.png") != plan["panel_sha256"]:
        raise ValueError("Prepared panel changed; prepare again before rendering")
    if digest(config["font"]) != plan["font_sha256"]:
        raise ValueError("Selected font changed; prepare again")
    titles = config["titles"]
    if (not isinstance(titles, list) or len(titles) != 2
            or any(not isinstance(t, str) or not t.strip() or any(c in t for c in "\n\r\t") for t in titles)):
        raise ValueError("titles: exactly two nonempty single-line strings required")
    centers = config.get("line_centers", [585, 795])
    if (not isinstance(centers, list) or len(centers) != 2
            or any(type(c) not in (int, float) or not math.isfinite(c) for c in centers)
            or not 0 < centers[0] < 720 < centers[1] < 1440):
        raise ValueError("line_centers: one center above seam 720, one below")
    darkness = number(config, "darkness", 0.48, 0, 0.8)
    minimum = int(number(config, "min_font_size", 130, 100, 220))
    maximum = int(number(config, "max_font_size", 190, minimum, 260))
    margin = 60
    # Same size for both lines; no anisotropic scaling or artificial outline.
    for size in range(maximum, minimum - 1, -1):
        font = ImageFont.truetype(config["font"], size, index=config.get("font_index", 0))
        bounds = [font.getbbox(t) for t in titles]
        if all(b[2] - b[0] <= SIZE[0] - margin * 2 for b in bounds):
            break
    else:
        raise ValueError("Title too long at readable size; revise unlocked wording or choose another layout")
    rectangles = []
    positions = []
    for center, bound in zip(centers, bounds):
        width, height = bound[2] - bound[0], bound[3] - bound[1]
        left, top = round((1080 - width) / 2), round(center - height / 2)
        rectangle = [left, top, left + width, top + height]
        if not (left >= margin and rectangle[2] <= 1080 - margin and 24 <= top and rectangle[3] <= 1416):
            raise ValueError("Text outside safe margins")
        rectangles.append(rectangle)
        positions.append((left - bound[0], top - bound[1]))
    if overlaps(rectangles[0], rectangles[1]):
        raise ValueError("Title lines overlap")
    # Boxes are supplied by the operator, not detected faces. Use padding for shadow/clearance.
    protected = [[b[0] - 12, b[1] + offset - 12, b[2] + 12, b[3] + offset + 12]
                 for offset in (0, 720) for b in plan["face_boxes"]]
    if any(overlaps(text, face) for text in rectangles for face in protected):
        raise ValueError("Title overlaps marked eyes/nose/mouth; adjust crop or line_centers and prepare again")
    with Image.open(prepared / "panel.png") as original:
        panel = original.convert("RGB")
    if panel.size != HALF:
        raise ValueError("Unexpected panel size")
    panel = Image.blend(panel, Image.new("RGB", HALF, "black"), darkness)
    background = Image.new("RGB", SIZE)
    background.paste(panel, (0, 0))
    background.paste(panel, (0, 720))
    mask = Image.new("L", SIZE)
    draw = ImageDraw.Draw(mask)
    for title, position in zip(titles, positions):
        draw.text(position, title, font=font, fill=255)
    shadow_mask = Image.new("L", SIZE)
    shadow_mask.paste(mask, (0, 4))
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(7)).point(lambda v: round(v * 0.6))
    cover = background.copy()
    cover.paste("black", (0, 0), shadow_mask)
    cover.paste("white", (0, 0), mask)
    thumb = cover.resize((270, 360), Image.Resampling.LANCZOS)
    output = new_directory(output)
    background.save(output / "background.png")
    cover.save(output / "cover.png")
    thumb.save(output / "thumbnail.png")
    report = {"size": list(SIZE), "font_size": size, "font_name": list(font.getname()),
              "titles": titles, "text_boxes": rectangles, "darkness": darkness,
              "geometry_checks": {"safe_margins": True, "marked_face_overlap": False,
                                  "same_source_panel": True},
              "visual_review": "pending: inspect cover and thumbnail beside approved reference; check glyphs and composition",
              "limits": "Face regions are manually marked; geometry checks cannot certify design quality or complete head/shoulders",
              "prepared_plan": plan}
    write_json(output / "render.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="stage", required=True)
    first = sub.add_parser("prepare", help="Create unlettered crop previews for actual visual review")
    first.add_argument("--config", required=True)
    first.add_argument("--out", required=True)
    second = sub.add_parser("render", help="Render after inspecting prepared previews")
    second.add_argument("--prepared", required=True)
    second.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.config, args.out) if args.stage == "prepare" else render(args.prepared, args.out)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(json.dumps({"output": str(Path(args.out).resolve()), "visual_review": result["visual_review"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
