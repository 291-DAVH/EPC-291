"""The engine adapter builds the child-process command in one place and reports a failure from the end of what the process wrote; a test can replace the process."""
import subprocess
import sys
import unittest

from epc.core import engine
from epc.core.config import settings


class TestEngineAdapter(unittest.TestCase):
    def tearDown(self):
        engine.set_runner(None)

    def test_the_command_is_python_dash_m_with_text_arguments(self):
        seen = {}

        def fake(cmd, **kw):
            seen["cmd"], seen["kw"] = cmd, kw
            return subprocess.CompletedProcess(cmd, 0, "ok", "")

        engine.set_runner(fake)
        res = engine.run_module("epc_drawing.export.pdf", ["a.dxf", 3], timeout=7)
        self.assertEqual(seen["cmd"], [sys.executable, "-m", "epc_drawing.export.pdf", "a.dxf", "3"])
        env = seen["kw"].pop("env")
        self.assertEqual(seen["kw"], {"capture_output": True, "text": True, "timeout": 7})
        self.assertEqual(env["EPC_LAYERS_JSON"], str(settings.layers_file))                 # the engine delivers DXF with the global catalog of layers
        self.assertEqual(res.stdout, "ok")

    def test_tail_prefers_stderr_and_keeps_the_end(self):
        self.assertEqual(engine.tail(subprocess.CompletedProcess([], 1, "out", "x" * 10 + "END"), 3), "END")
        self.assertEqual(engine.tail(subprocess.CompletedProcess([], 1, "  only out \n", ""), 100), "only out")

    def test_the_real_process_runs_when_no_runner_is_set(self):
        res = engine.run_module("site", ["--user-base"], timeout=30)
        self.assertEqual(type(res), subprocess.CompletedProcess)


if __name__ == "__main__":
    unittest.main()
