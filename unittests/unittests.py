"""Unittests for the pymp package."""
# pylint: disable=protected-access, invalid-name
import logging

import unittest

logging.basicConfig(level=logging.DEBUG)


class ParallelTest(unittest.TestCase):

    """Test the parallel context."""

    def test_init(self):
        """Initialization test."""
        import pymp
        pinst = pymp.Parallel(2)
        with pinst as parallel:
            if not parallel._is_fork:
                self.assertEqual(len(parallel._pids), 1)
            nested_parallel = pymp.Parallel(2)
            self.assertRaises(AssertionError,
                              nested_parallel.__enter__)
            pymp.config.nested = True
            self.assertRaises(NotImplementedError,
                              nested_parallel.__enter__)
            pymp.config.nested = False
        self.assertRaises(AssertionError,
                          pinst.__enter__)
        self.assertEqual(len(pymp.Parallel._instances), 0)

    def test_range(self):
        """Range test."""
        import pymp
        import numpy as np
        tarr = pymp.SharedArray((5, 1))
        with pymp.Parallel(2) as p:
            for i in p.range(len(tarr)):
                tarr[i, 0] = 1.
        self.assertEqual(np.sum(tarr), 5.)


    def test_lock(self):
        """Lock test."""
        import pymp
        tarr = pymp.SharedArray((1, 1))
        lock = pymp.Lock()
        with pymp.Parallel(2) as p:
            for _ in p.range(1000):
                with lock:
                    tarr[0, 0] += 1.
        self.assertEqual(tarr[0, 0], 1000.)


if __name__ == '__main__':
    unittest.main()
