#!/usr/bin/env python3
"""Check package structure, local Markdown links and obvious private-file leaks."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"emma-video-workflow", "video-transcribe", "koubo-advisor",
            "video-edit-handoff", "xhs-double-photo-cover", "video-publish-pack"}


def validate(root: Path = ROOT) -> list[str]:
    errors = []
    skill_dirs = {p.name for p in (root / "skills").iterdir() if p.is_dir()}
    if skill_dirs != EXPECTED:
        errors.append("Unexpected or missing skill directories")
    for name in EXPECTED:
        path = root / "skills" / name / "SKILL.md"
        if not path.is_file():
            errors.append(f"Missing {path.relative_to(root)}")
            continue
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---\n") or "\n---\n" not in content[4:]:
            errors.append(f"Missing frontmatter: {name}")
            continue
        frontmatter = content.split("---", 2)[1]
        if not re.search(rf"^name: {re.escape(name)}$", frontmatter, re.M):
            errors.append(f"Skill name mismatch: {name}")
        if not re.search(r"^description: .+", frontmatter, re.M):
            errors.append(f"Missing description: {name}")
        if not (path.parent / "agents/openai.yaml").is_file():
            errors.append(f"Missing UI metadata: {name}")
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__", ".venv"} for part in relative.parts):
            continue
        if path.is_symlink():
            errors.append(f"Symlink in public package: {relative}")
        if not path.is_file():
            continue
        if path.suffix.lower() in {".mp4", ".mov", ".wav", ".mp3", ".png", ".jpg", ".jpeg", ".db"}:
            errors.append(f"Unexpected private/media artifact: {relative}")
        if path.name.startswith(".env"):
            errors.append(f"Environment file must not ship: {relative}")
        if path.suffix.lower() not in {".md", ".py", ".yaml", ".txt", ".yml"}:
            continue
        content = path.read_text(encoding="utf-8")
        # Match concrete home-directory paths, not generic /path/to examples.
        if re.search(r"/(?:Users|home)/[^\s/]+/", content):
            errors.append(f"Concrete home path in {relative}")
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
                target = target.strip("<>").split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (path.parent / target).resolve()
                if root.resolve() not in resolved.parents or not resolved.exists():
                    errors.append(f"Broken/outside local link in {relative}: {target}")
                if relative.parts[0] == "skills" and not resolved.is_relative_to(root / "skills" / relative.parts[1]):
                    errors.append(f"Installed skill depends on files outside its folder: {relative}: {target}")
    return errors


if __name__ == "__main__":
    issues = validate()
    for issue in issues:
        print("ERROR:", issue)
    if issues:
        sys.exit(1)
    print("Validated six Skills, UI metadata, local links and public package boundaries.")
