"""Offline checks for packaged upstream helpers; no BAW connection required."""
import ast
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORING = ROOT / "skills" / "baw-authoring"


class BawPackageTests(unittest.TestCase):
    def run_helper(self, script, *args):
        result = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(script), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_all_packages_include_workflow_license_and_connection_rules(self):
        packages = list((ROOT / "skills").glob("baw-*/*/SKILL.md"))
        self.assertEqual(len(packages), 22)
        for entry in packages:
            for relative in ("WORKFLOW.md", "LICENSE", "NOTICE", "references/CREDENTIAL_HANDLING.md"):
                self.assertTrue((entry.parent / relative).is_file(), str(entry.parent / relative))
            self.assertTrue((ROOT / "docs" / "baw" / (entry.parent.name + ".md")).is_file())
        for script in (ROOT / "skills").glob("baw-*/**/*.py"):
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))

    def test_bpmn_generator_produces_resolvable_flows_and_import_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            config = folder / "process.json"
            config.write_text(json.dumps({
                "process": {"name": "Offline Smoke"},
                "elements": [
                    {"id": "start", "type": "startEvent", "name": "Start"},
                    {"id": "end", "type": "endEvent", "name": "End"},
                ],
                "flows": [{"id": "flow", "sourceRef": "start", "targetRef": "end"}],
            }), encoding="utf-8")
            output = folder / "process.bpmn"
            self.run_helper(AUTHORING / "generate-baw-bpmn/scripts/generate_baw_bpmn.py", config, output)
            root = ET.parse(output).getroot()
            ids = {element.get("id") for element in root.iter() if element.get("id")}
            flows = root.findall(".//{http://www.omg.org/spec/BPMN/20100524/MODEL}sequenceFlow")
            self.assertEqual(len(flows), 1)
            for flow in flows:
                self.assertIn(flow.get("sourceRef"), ids)
                self.assertIn(flow.get("targetRef"), ids)
            with zipfile.ZipFile(output.with_suffix(".zip")) as archive:
                self.assertEqual(archive.read(output.name), output.read_bytes())

    def test_business_object_tools_find_template_from_another_directory(self):
        scripts = AUTHORING / "generate-baw-business-objects/scripts/twx-bo-tools"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "offline.twx"
            self.run_helper(scripts / "create_empty_twx.py", "--name", "Offline Test", "--acronym", "OFFLINE", "--out", output)
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                self.assertTrue(archive.namelist())
            result = self.run_helper(scripts / "list_bos.py", output, "--json")
            self.assertIsInstance(json.loads(result.stdout), list)


if __name__ == "__main__":
    unittest.main()
