from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.check_workspace import WorkspaceError, validate_workspace


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

    def test_rejects_agent_state_at_hub_level(self) -> None:
        workspace = self.make_workspace()
        (workspace / "agents" / "researcher" / "memory").mkdir()

        with self.assertRaises(WorkspaceError):
            validate_workspace(workspace)


if __name__ == "__main__":
    unittest.main()
