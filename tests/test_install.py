import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install.py"


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="skills installer test ")
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.destination = self.project / ".agents" / "skills"

    def run_install(self, *args, input_text=""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            cwd=self.project, capture_output=True, text=True, input=input_text, timeout=10,
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
        self.assertIn("Already up to date:", result.stdout)
        self.assertEqual(sorted(p.name for p in self.destination.iterdir()), ["feature-trace", "project-todo"])

    def test_conflict_prevents_entire_selection_and_preserves_local_changes(self):
        existing = self.destination / "project-todo"
        existing.mkdir(parents=True)
        local = existing / "SKILL.md"
        local.write_text("local modifications", encoding="utf-8")
        result = self.run_install("--all", "--project", self.project)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Existing skill differs", result.stderr)
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
        self.assertEqual(result.stdout.count("Installed:"), 2)

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


if __name__ == "__main__":
    unittest.main()
