#!/usr/bin/env python3
"""Install bundled skills into a project or a specified skills directory."""

import argparse
import difflib
import hashlib
import re
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"


def discover(*, include_experimental=False):
    skills = {}
    for entry in sorted(SKILLS_ROOT.glob("*/*/SKILL.md")):
        if entry.parent.parent.name in {"baw-authoring", "baw-operations"} and not include_experimental:
            continue
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


def show_changes(source, target, old, new):
    print(f"\nОтличия для {target.name}: установленная версия → версия из набора")
    for name in sorted(old.keys() | new.keys()):
        if name in old and name in new and old[name] == new[name]:
            continue
        status = "Добавлен" if name not in old else "Удалён" if name not in new else "Изменён"
        print(f"  {status}: {name}")
        before, after = target / name, source / name
        try:
            before_text = before.read_text(encoding="utf-8") if before.is_file() else ""
            after_text = after.read_text(encoding="utf-8") if after.is_file() else ""
            if "\0" in before_text or "\0" in after_text:
                raise UnicodeError()
        except UnicodeError:
            print("    Двоичный файл или текст не в UTF-8; содержимое не показано.")
            continue
        for line in difflib.unified_diff(
            before_text.splitlines(), after_text.splitlines(),
            fromfile=f"установлено/{name}", tofile=f"новая-версия/{name}", lineterm="",
        ):
            print(line)


def confirm_update(name):
    while True:
        answer = input(f"Заменить {name} с резервной копией? [да/Нет]: ").strip().lower()
        if answer in {"да", "д", "yes", "y"}:
            return True
        if answer in {"", "нет", "н", "no", "n", "отмена", "q"}:
            return False
        print("Введите 'да' для обновления или 'нет' для отмены установки.")


def publish_skill(source, target, old):
    destination = target.parent
    with tempfile.TemporaryDirectory(prefix=".skill-install-", dir=destination) as tmp:
        staged = Path(tmp) / source.name
        shutil.copytree(source, staged)
        if manifest(staged) != manifest(source):
            raise ValueError(f"Не удалось проверить копию навыка: {source.name}")
        if old is None:
            if target.exists() or target.is_symlink():
                raise ValueError(f"Destination appeared during installation: {target}")
            staged.rename(target)
            print(f"Установлен: {target}")
            return
        # Recheck after the dialog and staging, before moving the installed version.
        if target.is_symlink() or not target.is_dir() or manifest(target) != old:
            raise ValueError(f"Навык изменился во время установки: {target}. Повторите сравнение.")
        backup_root = destination.parent / f"{destination.name}-backups"
        if backup_root.is_symlink():
            raise ValueError(f"Каталог резервных копий является символической ссылкой: {backup_root}")
        backup_root.mkdir(parents=True, exist_ok=True)
        backup_dir = Path(tempfile.mkdtemp(prefix=f"{target.name}-", dir=backup_root))
        backup = backup_dir / target.name
        # Verify both move endpoints remain inside their intended directories.
        if target.resolve().parent != destination.resolve() or backup.resolve().parent.parent != backup_root.resolve():
            raise ValueError("Путь замены выходит за пределы каталога установки или резервных копий.")
        print(f"Резервная копия: {backup}", flush=True)
        target.rename(backup)
        try:
            staged.rename(target)
        except BaseException:
            if not target.exists() and not target.is_symlink():
                backup.rename(target)
                print(f"Восстановлена предыдущая версия: {target}", file=sys.stderr)
            else:
                print(f"Предыдущая версия сохранена в: {backup}", file=sys.stderr)
            raise
        print(f"Обновлён: {target}")


def install(skills, names, destination, *, update=False, interactive=False):
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
            if not target.is_dir():
                raise ValueError(f"Путь навыка занят файлом: {target}")
            old = manifest(target)
            if old != source_files:
                pending.append((source, target, old))
            else:
                unchanged.append(target)
        else:
            pending.append((source, target, None))

    updates = [(source, target, old) for source, target, old in pending if old is not None]
    for source, target, old in updates:
        show_changes(source, target, old, manifest(source))
    if updates:
        print(f"\nРезервные копии будут сохранены в: {destination.parent / (destination.name + '-backups')}")
        if interactive:
            for _, target, _ in updates:
                if not confirm_update(target.name):
                    print("Установка отменена. Навыки не изменены.")
                    return
        elif not update:
            raise ValueError(
                "Установленные навыки отличаются. Для замены с резервной копией "
                "повторите команду с --update или запустите без аргументов. Навыки не изменены."
            )

    if pending:
        destination.mkdir(parents=True, exist_ok=True)
        for source, target, old in pending:
            publish_skill(source, target, old)
    for target in unchanged:
        print(f"Уже установлен: {target}")


def skill_description(source):
    """Read the single-line description used by bundled SKILL.md files."""
    content = (source / "SKILL.md").read_text(encoding="utf-8-sig")
    header = re.match(r"\A---\n(.*?)\n---(?:\n|$)", content, re.DOTALL)
    if header:
        match = re.search(r"^description:[ \t]*(.+)$", header.group(1), re.MULTILINE)
        if match:
            return match.group(1).strip()
    return "Описание отсутствует."


def choose_interactively(skills):
    names = sorted(skills)
    print("Выберите навыки для установки:")
    for number, name in enumerate(names, start=1):
        print(f"  {number}. {name}")
        print(textwrap.fill(skill_description(skills[name]), width=88, break_on_hyphens=False,
                            initial_indent="     ", subsequent_indent="     "))
    print("Введите номера или имена через пробелы или запятые.")
    print("'все' (all) — установить весь набор; 'отмена' (q) — выйти.")
    while True:
        answer = input("Навыки: ").strip()
        if answer.lower() in {"q", "отмена"}:
            return None
        if answer.lower() in {"all", "все", "всё"}:
            selected = names
            break
        tokens = re.split(r"[\s,]+", answer) if answer else []
        selected = []
        for token in tokens:
            if token.isascii() and token.isdigit() and 1 <= int(token) <= len(names):
                selected.append(names[int(token) - 1])
            elif token in skills:
                selected.append(token)
            else:
                break
        else:
            if selected:
                selected = list(dict.fromkeys(selected))
                break
        print("Выберите хотя бы один навык из списка, введите 'все' или 'отмена'.")

    print(f"Выбраны: {', '.join(selected)}")
    print("Введите путь к существующему проекту или 'отмена' (q) для выхода.")
    print(f"Относительные пути считаются от: {Path.cwd()}")
    while True:
        answer = input("Путь к проекту: ").strip()
        if answer.lower() in {"q", "отмена"}:
            return None
        if len(answer) >= 2 and answer[0] == answer[-1] and answer[0] in "\"'":
            answer = answer[1:-1]
        if answer:
            try:
                project = Path(answer).expanduser().resolve()
                if project.is_dir():
                    return selected, project
            except (OSError, ValueError, RuntimeError):
                pass
        print("Каталог проекта не найден. Введите путь к существующему каталогу.")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Run without arguments to choose skills and a project interactively.",
    )
    selection = parser.add_mutually_exclusive_group(required=bool(argv))
    selection.add_argument("--list", action="store_true", help="List bundled skill names")
    selection.add_argument("--all", action="store_true", help="Install all bundled skills")
    selection.add_argument("--skill", action="append", metavar="NAME", help="Install a skill; repeat to select several")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--project", type=Path, help="Existing project; installs into .agents/skills")
    target.add_argument("--dest", type=Path, help="Explicit skills directory for another agent environment")
    parser.add_argument("--update", action="store_true", help="Заменить отличающиеся навыки с резервной копией без вопросов")
    parser.add_argument("--include-experimental", action="store_true",
                        help="Включить тестовые, непроверенные навыки BAW в список и выбор установки")
    args = parser.parse_args(argv)

    try:
        skills = discover(include_experimental=args.include_experimental)
        if args.include_experimental:
            print("Внимание: навыки BAW тестовые и непроверенные; результаты требуют сверки с исходниками.")
        if not argv:
            choice = choose_interactively(skills)
            if choice is None:
                print("Установка отменена.")
                return 0
            args.skill, args.project = choice
        if args.list:
            if args.project or args.dest or args.update:
                parser.error("--list does not take --project, --dest or --update")
            for name, source in skills.items():
                print(f"{name}\t{source.relative_to(SKILLS_ROOT.parent).as_posix()}")
            return 0
        if args.project is None and args.dest is None:
            parser.error("installation requires --project or --dest")
        names = sorted(skills) if args.all else list(dict.fromkeys(args.skill))
        unknown = sorted(set(names) - skills.keys())
        if unknown:
            experimental = set(unknown) & discover(include_experimental=True).keys()
            if experimental:
                raise ValueError(
                    f"Тестовые, непроверенные навыки: {', '.join(sorted(experimental))}. "
                    "Для их установки укажите --include-experimental."
                )
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
        install(skills, names, destination, update=args.update, interactive=not argv)
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nУстановка прервана.", file=sys.stderr)
        return 130
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
