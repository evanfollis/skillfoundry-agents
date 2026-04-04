from __future__ import annotations

import json
import subprocess
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_workspace import WorkspaceError, validate_workspace
from scripts.project_agent import ProjectionError, write_projection
from scripts.resolve_profiles import resolve_agent_profiles


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "valid_workspace"


class WorkspaceValidationTests(unittest.TestCase):
    def make_workspace(self) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        workspace_root = Path(tmpdir.name) / "workspace"
        shutil.copytree(FIXTURE_ROOT, workspace_root)
        return workspace_root

    def test_valid_planned_workspace(self) -> None:
        validate_workspace(self.make_workspace())

    def test_active_agent_requires_context_checkout(self) -> None:
        workspace = self.make_workspace()
        manifest = workspace / "agents" / "researcher" / "agent.toml"
        manifest.write_text(manifest.read_text().replace('status = "planned"', 'status = "active"'))

        with self.assertRaises(WorkspaceError):
            validate_workspace(workspace)

    def test_active_agent_accepts_plain_git_context_checkout(self) -> None:
        workspace = self.make_workspace()
        manifest = workspace / "agents" / "researcher" / "agent.toml"
        manifest.write_text(manifest.read_text().replace('status = "planned"', 'status = "active"'))
        self.make_context_repo_at(workspace / "agents" / "researcher" / "context")

        validate_workspace(workspace)

    def test_rejects_agent_state_at_hub_level(self) -> None:
        workspace = self.make_workspace()
        (workspace / "agents" / "researcher" / "memory").mkdir()

        with self.assertRaises(WorkspaceError):
            validate_workspace(workspace)

    def test_resolves_agent_profile_stack(self) -> None:
        workspace = self.make_workspace()
        snapshot = resolve_agent_profiles(workspace, workspace / "agents" / "researcher" / "agent.toml")

        self.assertEqual(snapshot["requested_profiles"], ["researcher"])
        self.assertEqual(snapshot["requested_skills"], [])
        self.assertEqual(snapshot["resolved_profile_stack"], ["default", "researcher"])
        self.assertIn("Detect and clarify bottlenecks.", snapshot["frontdoor"]["mission"])
        self.assertIn("canon-safe", snapshot["policy"]["promotion_validation_kinds"])
        self.assertIn("research-grounded", snapshot["policy"]["promotion_validation_kinds"])

    def test_resolves_composed_profile_stack_in_declared_order(self) -> None:
        workspace = self.make_workspace()
        manifest = workspace / "agents" / "researcher" / "agent.toml"
        manifest.write_text(manifest.read_text().replace('profiles = ["researcher"]', 'profiles = ["researcher", "pricing"]'))
        pricing_dir = workspace / "profiles" / "pricing"
        pricing_dir.mkdir(parents=True)
        (pricing_dir / "profile.toml").write_text(
            "\n".join(
                [
                    'schema_version = "1"',
                    'profile_id = "pricing"',
                    'name = "Pricing"',
                    'extends = ["default"]',
                    "",
                    "[persona]",
                    'summary = "Price and package validated utility."',
                    "",
                    "[frontdoor]",
                    'mission = ["Convert utility into pricing tests."]',
                    'focus = ["Differentiate installs from real value."]',
                    'deliverables = ["Pricing recommendations."]',
                    "",
                    "[policy]",
                    'promotion_validation_kinds = ["pricing-grounded"]',
                    "preferred_bundle_ids = []",
                    "",
                    "[handoff]",
                    'expected_outputs = ["A pricing experiment plan."]',
                    "downstream_profiles = []",
                ]
            )
        )

        validate_workspace(workspace)
        snapshot = resolve_agent_profiles(workspace, manifest)
        self.assertEqual(snapshot["resolved_profile_stack"], ["default", "researcher", "pricing"])
        self.assertEqual(snapshot["persona"]["summary"], "Price and package validated utility.")
        self.assertIn("research-grounded", snapshot["policy"]["promotion_validation_kinds"])
        self.assertIn("pricing-grounded", snapshot["policy"]["promotion_validation_kinds"])

    def test_rejects_unknown_profile_reference(self) -> None:
        workspace = self.make_workspace()
        manifest = workspace / "agents" / "researcher" / "agent.toml"
        manifest.write_text(manifest.read_text().replace('profiles = ["researcher"]', 'profiles = ["missing"]'))

        with self.assertRaises(WorkspaceError):
            validate_workspace(workspace)

    def test_rejects_profile_inheritance_cycle(self) -> None:
        workspace = self.make_workspace()
        profile = workspace / "profiles" / "default" / "profile.toml"
        profile.write_text(profile.read_text() + '\nextends = ["researcher"]\n')

        with self.assertRaises(WorkspaceError):
            validate_workspace(workspace)

    def test_projects_agent_profiles_into_context_repo(self) -> None:
        workspace = self.make_workspace()
        context_repo = self.make_context_repo()

        result = write_projection(
            workspace / "agents" / "researcher" / "agent.toml",
            context_repo,
        )

        self.assertEqual(result["memory_profile_path"], "memory/profiles/researcher.md")
        self.assertEqual(result["bundle_profile_path"], "bundles/profiles/researcher.json")
        memory_file = context_repo / "memory" / "profiles" / "researcher.md"
        bundle_file = context_repo / "bundles" / "profiles" / "researcher.json"
        self.assertTrue(memory_file.exists())
        self.assertTrue(bundle_file.exists())
        self.assertIn("resolved_profile_stack: default, researcher", memory_file.read_text())
        self.assertIn("requested_skills: (none declared)", memory_file.read_text())
        bundle_payload = json.loads(bundle_file.read_text())
        self.assertEqual(bundle_payload["bundle_id"], "researcher-profile")
        self.assertEqual(bundle_payload["promotion"]["status"], "promoted")

    def test_projection_requires_frontdoor_pin_when_configured(self) -> None:
        workspace = self.make_workspace()
        context_repo = self.make_context_repo(include_profile_pin=False)

        with self.assertRaises(ProjectionError):
            write_projection(workspace / "agents" / "researcher" / "agent.toml", context_repo)

    def make_context_repo(self, *, include_profile_pin: bool = True) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        context_root = Path(tmpdir.name) / "context"
        return self.make_context_repo_at(context_root, include_profile_pin=include_profile_pin)

    def make_context_repo_at(self, context_root: Path, *, include_profile_pin: bool = True) -> Path:
        (context_root / "bundles").mkdir(parents=True)
        (context_root / "memory").mkdir(parents=True)
        (context_root / "artifacts").mkdir(parents=True)
        (context_root / "runs").mkdir(parents=True)
        (context_root / "README.md").write_text("Context repo\n")
        (context_root / "memory" / "mission.md").write_text("Mission\n")
        pinned = ['"README.md"', '"memory/mission.md"']
        if include_profile_pin:
            pinned.append('"memory/profiles/researcher.md"')
        (context_root / "skillfoundry.toml").write_text(
            "\n".join(
                [
                    "[repository]",
                    'schema_version = "1"',
                    'name = "Researcher Context"',
                    'agent_id = "researcher"',
                    "",
                    "[frontdoor]",
                    f"pinned_paths = [{', '.join(pinned)}]",
                    'discoverable_paths = ["bundles", "memory", "artifacts"]',
                    "",
                    "[promotion_policy]",
                    'promotable_memory_roots = ["notes", "plans"]',
                    'required_validation_kinds = ["canon-safe", "frontdoor-reviewed"]',
                ]
            )
        )
        subprocess.run(["git", "init", str(context_root)], check=True, capture_output=True)
        return context_root


if __name__ == "__main__":
    unittest.main()
