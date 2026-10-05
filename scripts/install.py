#!/usr/bin/env python3
"""Install only this repository's Skills, with opt-in replacement and backups."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]


def available_skills() -> dict[str, Path]:
    return {p.name: p for p in sorted((ROOT / "skills").iterdir())
            if p.is_dir() and (p / "SKILL.md").is_file()}


def ensure_plain_tree(path: Path) -> None:
    if path.is_symlink() or any(p.is_symlink() for p in path.rglob("*")):
        raise ValueError(f"Symbolic links are not supported: {path}")


def install(destination: Path, names: list[str] | None = None,
            replace: bool = False, dry_run: bool = False) -> dict:
    available = available_skills()
    selected = list(dict.fromkeys(names or available))
    if not selected or any(name not in available for name in selected):
        raise ValueError("Choose one or more names from the repository's skills directory")
    destination = destination.expanduser().resolve()
    source_root = (ROOT / "skills").resolve()
    if (destination == source_root or source_root in destination.parents
            or destination in source_root.parents):
        raise ValueError("Installation destination must not overlap the source skills directory")
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"Destination is not a directory: {destination}")
    conflicts = []
    for name in selected:
        ensure_plain_tree(available[name])
        target = destination / name
        if target.is_symlink():
            raise ValueError(f"Refusing to replace a symbolic link: {target}")
        if target.exists():
            if not target.is_dir():
                raise ValueError(f"Existing target is not a directory: {target}")
            conflicts.append(name)
    if conflicts and not replace:
        raise ValueError("Existing skills were not changed: " + ", ".join(conflicts)
                         + ". Compare them first; use --replace to back up and replace.")
    result = {"destination": str(destination), "skills": selected,
              "replacing": conflicts, "backup": None, "dry_run": dry_run}
    if dry_run:
        return result

    destination.parent.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    installed: list[str] = []
    backup = None
    with tempfile.TemporaryDirectory(prefix="emma-video-stage-", dir=destination.parent) as staging:
        stage = Path(staging)
        for name in selected:
            shutil.copytree(available[name], stage / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        destination.mkdir(parents=True, exist_ok=True)
        try:
            if conflicts:
                backup_parent = destination.parent / "skill-backups"
                backup_parent.mkdir(exist_ok=True)
                prefix = "emma-video-skills-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
                backup = Path(tempfile.mkdtemp(prefix=prefix, dir=backup_parent))
                result["backup"] = str(backup)
            for name in selected:
                target = destination / name
                if target.is_symlink():
                    raise ValueError(f"Target became a symbolic link: {target}")
                if target.exists():
                    if name not in conflicts or not target.is_dir():
                        raise ValueError(f"Target changed during installation: {target}")
                    target.rename(backup / name)
                    moved.append(name)
                elif name in conflicts:
                    raise ValueError(f"Existing target disappeared during installation: {target}")
                (stage / name).rename(target)
                installed.append(name)
        except Exception:
            for name in reversed(installed):
                shutil.rmtree(destination / name)
            for name in reversed(moved):
                (backup / name).rename(destination / name)
            raise
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--app", choices=("codex", "claude", "agents"))
    group.add_argument("--dest", type=Path)
    parser.add_argument("--skill", action="append", choices=tuple(available_skills()))
    parser.add_argument("--replace", action="store_true", help="Back up conflicting directories before replacement")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    defaults = {"codex": Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills",
                "claude": Path.home() / ".claude" / "skills",
                "agents": Path.home() / ".agents" / "skills"}
    try:
        result = install(args.dest or defaults[args.app], args.skill, args.replace, args.dry_run)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Installation stopped: {exc}\n")
    print(("Preview: " if args.dry_run else "Installed: ") + ", ".join(result["skills"]))
    print("Destination:", result["destination"])
    if result["backup"]:
        print("Previous versions:", result["backup"])


if __name__ == "__main__":
    main()
