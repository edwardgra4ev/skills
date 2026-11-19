import subprocess
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install.py"
SPEC = importlib.util.spec_from_file_location("installer", SCRIPT)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="skills installer test ")
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.destination = self.project / ".agents" / "skills"

    def run_install(self, *args, input_text=""):
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), *map(str, args)],
            cwd=self.project, capture_output=True, text=True, encoding="utf-8", input=input_text, timeout=10,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_list_does_not_create_destination(self):
        result = self.run_install("--list")
        self.assert_success(result)
        self.assertIn("feature-trace", result.stdout)
        self.assertIn("project-todo", result.stdout)
        self.assertFalse(self.destination.exists())

    def test_install_all_copies_complete_packages_and_is_repeatable(self):
        self.assert_success(self.run_install("--all", "--project", self.project))
        for source in (ROOT / "skills").glob("*/*"):
            target = self.destination / source.name
            source_files = {p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()}
            target_files = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            self.assertEqual(source_files, target_files)
        result = self.run_install("--all", "--project", self.project)
        self.assert_success(result)
        self.assertIn("Уже установлен:", result.stdout)
        self.assertEqual(sorted(p.name for p in self.destination.iterdir()), ["feature-trace", "project-todo"])

    def test_conflict_prevents_entire_selection_and_preserves_local_changes(self):
        existing = self.destination / "project-todo"
        existing.mkdir(parents=True)
        local = existing / "SKILL.md"
        local.write_text("local modifications", encoding="utf-8")
        result = self.run_install("--all", "--project", self.project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--update", result.stderr)
        self.assertEqual(local.read_text(encoding="utf-8"), "local modifications")
        self.assertFalse((self.destination / "feature-trace").exists())

    def test_custom_destination_and_selected_skill(self):
        target = self.project / "custom skills"
        self.assert_success(self.run_install("--skill", "project-todo", "--dest", target))
        self.assertTrue((target / "project-todo" / "references" / "workflow.md").is_file())
        self.assertFalse((target / "feature-trace").exists())

    def test_invalid_requests_do_not_write(self):
        for args in [
            ("--skill", "../escape", "--project", self.project),
            ("--all", "--project", self.project / "missing"),
            ("--all",),
            ("--all", "--dest", ROOT / "skills"),
        ]:
            with self.subTest(args=args):
                self.assertNotEqual(self.run_install(*args).returncode, 0)
        self.assertFalse(self.destination.exists())

    def test_interactive_selects_multiple_skills_and_quoted_project(self):
        result = self.run_install(input_text=f'1, project-todo, 1\n"{self.project}"\n')
        self.assert_success(result)
        self.assertEqual(sorted(p.name for p in self.destination.iterdir()), ["feature-trace", "project-todo"])
        self.assertEqual(result.stdout.count("Установлен:"), 2)

    def test_interactive_retries_invalid_selection_and_project(self):
        result = self.run_install(input_text=f'\n0\n1,unknown\n2\n\nmissing\n{self.project}\n')
        self.assert_success(result)
        self.assertEqual([p.name for p in self.destination.iterdir()], ["project-todo"])

    def test_interactive_all_with_relative_project(self):
        target = self.project / "target project"
        target.mkdir()
        result = self.run_install(input_text="all\ntarget project\n")
        self.assert_success(result)
        self.assertEqual(len(list((target / ".agents" / "skills").iterdir())), 2)

    def test_interactive_russian_menu_descriptions_and_commands(self):
        result = self.run_install(input_text="отмена\n")
        self.assert_success(result)
        self.assertIn("Выберите навыки для установки:", result.stdout)
        # Every bundled skill's description must be visible before selection.
        visible = " ".join(result.stdout.split())
        for source in (ROOT / "skills").glob("*/*/SKILL.md"):
            description = next(line.removeprefix("description: ") for line in
                               source.read_text(encoding="utf-8").splitlines()
                               if line.startswith("description: "))
            self.assertIn(description, visible)
        self.assertFalse(self.destination.exists())
        cancelled = self.run_install(input_text="все\nотмена\n")
        self.assert_success(cancelled)
        self.assertIn("Путь к проекту:", cancelled.stdout)
        self.assertFalse(self.destination.exists())
        self.assert_success(self.run_install(input_text=f"все\n{self.project}\n"))
        self.assertEqual(len(list(self.destination.iterdir())), 2)

    def test_interactive_cancel_and_eof_leave_project_untouched(self):
        for answers, code in [("q\n", 0), ("all\nq\n", 0), ("", 130), ("all\n", 130)]:
            with self.subTest(answers=answers):
                result = self.run_install(input_text=answers)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertFalse(self.destination.exists())

    def test_interactive_conflict_preserves_existing_skill(self):
        existing = self.destination / "project-todo"
        existing.mkdir(parents=True)
        local = existing / "SKILL.md"
        local.write_text("local modifications", encoding="utf-8")
        result = self.run_install(input_text=f"all\n{self.project}\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(local.read_text(encoding="utf-8"), "local modifications")
        self.assertFalse((self.destination / "feature-trace").exists())

    def prepare_old_version(self):
        target = self.destination / "feature-trace"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("old local instructions\n", encoding="utf-8")
        (target / "extra.bin").write_bytes(b"\x00\xff\x01")
        (target / "empty").mkdir()
        return target

    def test_update_backs_up_entire_old_directory_and_shows_diff(self):
        target = self.prepare_old_version()
        original = installer.manifest(target)
        result = self.run_install("--skill", "feature-trace", "--project", self.project, "--update")
        self.assert_success(result)
        self.assertIn("-old local instructions", result.stdout)
        self.assertIn("+name: feature-trace", result.stdout)
        self.assertIn("Удалён: extra.bin", result.stdout)
        self.assertIn("Двоичный файл", result.stdout)
        backups = list((self.destination.parent / "skills-backups").glob("*/feature-trace"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(installer.manifest(backups[0]), original)
        source = ROOT / "skills" / "engineering" / "feature-trace"
        self.assertEqual(installer.manifest(target), installer.manifest(source))
        self.assert_success(self.run_install("--skill", "feature-trace", "--project", self.project, "--update"))
        self.assertEqual(len(list(backups[0].parent.parent.iterdir())), 1)

    def test_interactive_update_requires_yes(self):
        target = self.prepare_old_version()
        original = installer.manifest(target)
        for response in ("нет", "", "отмена"):
            result = self.run_install(input_text=f"all\n{self.project}\n{response}\n")
            self.assert_success(result)
            self.assertEqual(installer.manifest(target), original)
            self.assertFalse((self.destination / "project-todo").exists())
            self.assertFalse((self.destination.parent / "skills-backups").exists())
        result = self.run_install(input_text=f"feature-trace\n{self.project}\nда\n")
        self.assert_success(result)
        self.assertIn("Обновлён:", result.stdout)
        self.assertTrue(list((self.destination.parent / "skills-backups").glob("*/feature-trace")))

    def test_custom_destination_keeps_separate_unique_backups(self):
        target = self.prepare_old_version()
        for text in ("first version", "second version"):
            (target / "SKILL.md").write_text(text, encoding="utf-8")
            self.assert_success(self.run_install("--skill", "feature-trace", "--dest", self.destination, "--update"))
        contents = sorted(p.read_text(encoding="utf-8") for p in
                          (self.destination.parent / "skills-backups").glob("*/feature-trace/SKILL.md"))
        self.assertEqual(contents, ["first version", "second version"])

    def test_failed_publish_restores_old_version(self):
        target = self.prepare_old_version()
        original = installer.manifest(target)
        source = ROOT / "skills" / "engineering" / "feature-trace"
        rename = Path.rename

        def fail_publish(path, dest):
            if path.parent.name.startswith(".skill-install-"):
                raise OSError("simulated publish failure")
            return rename(path, dest)

        with mock.patch.object(Path, "rename", fail_publish):
            with self.assertRaisesRegex(OSError, "simulated publish failure"):
                installer.publish_skill(source, target, original)
        self.assertEqual(installer.manifest(target), original)
        self.assertFalse(list(self.destination.glob(".skill-install-*")))

    def test_backup_failure_leaves_old_version_untouched(self):
        target = self.prepare_old_version()
        original = installer.manifest(target)
        source = ROOT / "skills" / "engineering" / "feature-trace"
        with mock.patch.object(Path, "rename", side_effect=PermissionError("backup denied")):
            with self.assertRaises(PermissionError):
                installer.publish_skill(source, target, original)
        self.assertEqual(installer.manifest(target), original)

    def test_changed_target_is_not_replaced_after_review(self):
        target = self.prepare_old_version()
        reviewed = installer.manifest(target)
        (target / "SKILL.md").write_text("edited after review", encoding="utf-8")
        source = ROOT / "skills" / "engineering" / "feature-trace"
        with self.assertRaisesRegex(ValueError, "изменился"):
            installer.publish_skill(source, target, reviewed)
        self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "edited after review")


if __name__ == "__main__":
    unittest.main()
