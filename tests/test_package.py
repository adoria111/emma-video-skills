import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("installer", ROOT / "scripts/install.py")
transcriber = load("transcriber", ROOT / "skills/video-transcribe/scripts/transcribe_local.py")
validator = load("validator", ROOT / "scripts/validate.py")


class PackageTests(unittest.TestCase):
    def test_package_structure_and_links(self):
        self.assertEqual(validator.validate(), [])

    def test_install_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "skills"
            result = installer.install(dest)
            self.assertEqual(len(result["skills"]), 6)
            marker = dest / "koubo-advisor" / "my-notes.txt"
            marker.write_text("keep my private customization")
            with self.assertRaises(ValueError):
                installer.install(dest)
            self.assertEqual(marker.read_text(), "keep my private customization")

    def test_replace_retains_recoverable_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "skills"
            installer.install(dest, ["koubo-advisor"])
            marker = dest / "koubo-advisor" / "custom.txt"
            marker.write_text("old version")
            result = installer.install(dest, ["koubo-advisor"], replace=True)
            self.assertFalse(marker.exists())
            self.assertEqual((Path(result["backup"]) / "koubo-advisor/custom.txt").read_text(), "old version")

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "new-parent" / "skills"
            installer.install(dest, dry_run=True)
            self.assertFalse(dest.parent.exists())

    def test_symlink_target_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "skills"
            dest.mkdir()
            protected = Path(tmp) / "protected"
            protected.mkdir()
            try:
                (dest / "koubo-advisor").symlink_to(protected, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks unavailable on this system")
            with self.assertRaises(ValueError):
                installer.install(dest, ["koubo-advisor"], replace=True)
            self.assertEqual(list(protected.iterdir()), [])

    def test_transcript_unicode_timing_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "transcript"
            segments = [{"start": 1.125, "end": 3.5, "text": "示例：如何整理素材？", "words": []}]
            transcriber.write_outputs(output, Path(tmp) / "sample.mp4", "small", "zh", segments)
            srt = (output / "transcript.srt").read_text()
            self.assertIn("00:00:01,125 --> 00:00:03,500", srt)
            self.assertIn("如何整理素材", srt)
            with self.assertRaises(FileExistsError):
                transcriber.write_outputs(output, Path(tmp) / "sample.mp4", "small", "zh", segments)
            self.assertEqual((output / "transcript.srt").read_text(), srt)

    def test_invalid_transcription_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "transcript"
            with self.assertRaises(ValueError):
                transcriber.write_outputs(output, Path(tmp) / "sample.mp4", "small", "zh",
                                          [{"start": 2, "end": 1, "text": "bad"}])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
