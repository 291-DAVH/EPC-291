"""The development MASTER credential can never be versioned (so it can never reach main): the detector of the gate and the repository itself."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "tools" / "ci" / "check_dev_credentials.py"


def load():
    spec = importlib.util.spec_from_file_location("check_dev_credentials", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestDevCredentials(unittest.TestCase):
    def test_the_detector_flags_a_value_and_accepts_an_empty_one(self):
        rx = load().ASSIGNS
        for bad in ("EPC_DEV_MASTER_PASSWORD=master", 'EPC_DEV_MASTER_PASSWORD = "master"', "EPC_DEV_MASTER_USER: master", "$env:EPC_DEV_MASTER_PASSWORD = 'x'"):
            self.assertTrue(rx.search(bad), bad)
        for ok in ("EPC_DEV_MASTER_PASSWORD=", "EPC_DEV_MASTER_PASSWORD=                # DEVELOPMENT ONLY", "# set EPC_DEV_MASTER_PASSWORD in your environment", "settings.dev_master_password"):
            self.assertFalse(rx.search(ok), ok)

    @unittest.skipUnless((REPO / ".git").exists(), "needs the git checkout")
    def test_nothing_versioned_gives_the_master_a_credential(self):
        r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
