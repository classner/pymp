import subprocess
from os import path
import sys
import unittest


class RunTest(unittest.TestCase):
    """
    This wraps the unit test module in it's own process. The reason
    is that the Python test runner is not multiprocessing-safe and
    is calling the tests directly from the main thread (that means that
    subprocesses each try to run the entire test suite again, resulting
    in a recursive re-execution loop). We avoid this by wrapping the
    actual tests in their own process.
    """

    def test_run(self):
        subprocess.check_call(
            [
                sys.executable,
                path.abspath(path.join(path.dirname(__file__), "unittests.py")),
            ]
        )
