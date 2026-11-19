#!/usr/bin/env python3
"""Install bundled skills into a project or a specified skills directory."""

import argparse
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"


def discover():
    skills = {}
    for entry in sorted(SKILLS_ROOT.glob("*/*/SKILL.md")):
        name = entry.parent.name
        if name in skills:
            raise ValueError(f"Duplicate skill name: {name}")
        skills[name] = entry.parent
    if not skills:
        raise ValueError(f"No skills found in {SKILLS_ROOT}")
    return skills


def manifest(root):
    """Compare all packaged files and directories, including extra local files."""
    result = {}
    if root.is_symlink():
        raise ValueError(f"Symbolic links are not supported: {root}")
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symbolic links are not supported: {path}")
        key = path.relative_to(root).as_posix()
        if path.is_file():
            result[key] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif path.is_dir():
            result[key] = None
        else:
            raise ValueError(f"Unsupported file type: {path}")
    return result


def install(skills, names, destination):
    pending = []
    unchanged = []
    # Validate the entire selection before copying any skill.
    for name in names:
        source = skills[name]
        target = destination / name
        source_files = manifest(source)
        if target.is_symlink():
            raise ValueError(f"Destination is a symbolic link: {target}")
        if target.exists():
            if not target.is_dir() or manifest(target) != source_files:
                raise ValueError(
                    f"Existing skill differs: {target}\n"
                    "Compare it with the source and move the old directory to a "
                    "backup location before retrying. No skills were installed."
                )
            unchanged.append(target)
        else:
            pending.append((source, target))

    if pending:
        destination.mkdir(parents=True, exist_ok=True)
        for source, target in pending:
            # Publish only a complete copy; a copy failure leaves no partial skill.
            with tempfile.TemporaryDirectory(prefix=".skill-install-", dir=destination) as tmp:
                staged = Path(tmp) / source.name
                shutil.copytree(source, staged)
                if target.exists() or target.is_symlink():
                    raise ValueError(f"Destination appeared during installation: {target}")
                staged.rename(target)
            print(f"Installed: {target}")
    for target in unchanged:
        print(f"Already up to date: {target}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--list", action="store_true", help="List bundled skill names")
    selection.add_argument("--all", action="store_true", help="Install all bundled skills")
    selection.add_argument("--skill", action="append", metavar="NAME", help="Install a skill; repeat to select several")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--project", type=Path, help="Existing project; installs into .agents/skills")
    target.add_argument("--dest", type=Path, help="Explicit skills directory for another agent environment")
    args = parser.parse_args(argv)

    try:
        skills = discover()
        if args.list:
            if args.project or args.dest:
                parser.error("--list does not take --project or --dest")
            for name, source in skills.items():
                print(f"{name}\t{source.relative_to(SKILLS_ROOT.parent).as_posix()}")
            return 0
        if args.project is None and args.dest is None:
            parser.error("installation requires --project or --dest")
        names = sorted(skills) if args.all else list(dict.fromkeys(args.skill))
        unknown = sorted(set(names) - skills.keys())
        if unknown:
            raise ValueError(f"Unknown skills: {', '.join(unknown)}. Use --list.")
        if args.project is not None:
            project = args.project.expanduser().resolve()
            if not project.is_dir():
                raise ValueError(f"Project directory does not exist: {project}")
            destination = project / ".agents" / "skills"
        else:
            destination = args.dest.expanduser().resolve()
        # Installing into the source collection could alter the distributable bundle.
        source_root = SKILLS_ROOT.resolve()
        resolved = destination.resolve()
        if resolved == source_root or source_root in resolved.parents:
            raise ValueError("Choose a destination outside the source skills directory.")
        install(skills, names, destination)
        return 0
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
