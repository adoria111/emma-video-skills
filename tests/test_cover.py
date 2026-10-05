import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

try:
    from PIL import Image, ImageFont
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parents[1]
if Image is not None:
    spec = importlib.util.spec_from_file_location(
        "cover", ROOT / "skills/xhs-double-photo-cover/scripts/render_cover.py")
    cover = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cover)


@unittest.skipIf(Image is None, "Optional Pillow is not installed")
class CoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        candidates = [os.environ.get("COVER_TEST_FONT", ""), "DejaVuSans.ttf",
                      "/System/Library/Fonts/Supplemental/Arial.ttf",
                      "C:/Windows/Fonts/arial.ttf"]
        for candidate in candidates:
            try:
                self.font = str(Path(ImageFont.truetype(candidate, 20).path).resolve())
                break
            except (OSError, TypeError):
                continue
        else:
            self.skipTest("Provide COVER_TEST_FONT for render tests")
        source = Image.new("RGB", (600, 800), "#ad9380")
        source.paste("#334455", (0, 0, 300, 800))
        source.save(self.root / "frame.png")
        self.config = {"source": "frame.png", "crop": [0, 100, 600, 500],
                       "subject_box": [100, 130, 500, 450],
                       "face_boxes": [[200, 190, 350, 270]],
                       "font": self.font, "titles": ["HELLO", "WORLD"]}
        self.path = self.root / "config.json"

    def prepare(self):
        self.path.write_text(json.dumps(self.config))
        return cover.prepare(self.path, self.root / "preview")

    def test_render_and_identical_panels_visual_status_pending(self):
        self.prepare()
        report = cover.render(self.root / "preview", self.root / "output")
        self.assertTrue(report["visual_review"].startswith("pending"))
        with Image.open(self.root / "output/background.png") as image:
            self.assertEqual(image.crop((0, 0, 1080, 720)).tobytes(),
                             image.crop((0, 720, 1080, 1440)).tobytes())
        with Image.open(self.root / "output/thumbnail.png") as image:
            self.assertEqual(image.size, (270, 360))

    def test_invalid_crop_and_cut_subject_rejected_before_writing(self):
        for crop in [[0, 0, 700, 400], [0, 0, 600, 500], [0, 0, 600, 400]]:
            self.config["crop"] = crop
            with self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse((self.root / "preview").exists())

    def test_collision_rejected_before_writing(self):
        self.config["face_boxes"] = [[200, 350, 350, 480]]
        self.prepare()
        with self.assertRaisesRegex(ValueError, "overlaps marked"):
            cover.render(self.root / "preview", self.root / "output")
        self.assertFalse((self.root / "output").exists())

    def test_long_title_rejected_not_shrunk_to_unreadable(self):
        self.config["titles"][0] = "LONG TITLE " * 20
        self.prepare()
        with self.assertRaisesRegex(ValueError, "too long"):
            cover.render(self.root / "preview", self.root / "output")
        self.assertFalse((self.root / "output").exists())

    def test_existing_output_and_previews_preserved(self):
        self.prepare()
        panel = (self.root / "preview/panel.png").read_bytes()
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual((self.root / "preview/panel.png").read_bytes(), panel)
        cover.render(self.root / "preview", self.root / "output")
        original = (self.root / "output/cover.png").read_bytes()
        with self.assertRaises(FileExistsError):
            cover.render(self.root / "preview", self.root / "output")
        self.assertEqual((self.root / "output/cover.png").read_bytes(), original)

    def test_modified_panel_requires_new_prepare(self):
        self.prepare()
        (self.root / "preview/panel.png").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "panel changed"):
            cover.render(self.root / "preview", self.root / "output")


if __name__ == "__main__":
    unittest.main()
