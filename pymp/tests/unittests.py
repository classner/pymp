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
            with nested_parallel:
                pass
            pymp.config.nested = False
        self.assertRaises(AssertionError,
                          pinst.__enter__)
        self.assertEqual(pymp.shared._NUM_PROCS.value, 1)
        self.assertEqual(pymp.Parallel._level, 0)

    def test_range(self):
        """Range test."""
        import pymp
        try:
            import numpy as np
        except ImportError:
            return
        tarr = pymp.shared.array((5, 1))
        with pymp.Parallel(2) as p:
            for i in p.range(len(tarr)):
                tarr[i, 0] = 1.
        self.assertEqual(np.sum(tarr), 5.)


    def test_lock(self):
        """Lock test."""
        import pymp
        tarr = pymp.shared.array((1, 1))
        lock = pymp.shared.lock()
        with pymp.Parallel(2) as p:
            for _ in p.range(1000):
                with lock:
                    tarr[0, 0] += 1.
        self.assertEqual(tarr[0, 0], 1000.)

    def test_list(self):
        """Shared list test."""
        import pymp
        tlist = pymp.shared.list()
        with pymp.Parallel(2) as p:
            for _ in p.range(1000):
                tlist.append(1.)
        self.assertEqual(len(tlist), 1000)

    def test_dict(self):
        """Shared dict test."""
        import pymp
        tdict = pymp.shared.dict()
        with pymp.Parallel(2) as p:
            for iter_idx in p.range(400):
                tdict[iter_idx] = 1.
        self.assertEqual(len(tdict), 400)

    def test_queue(self):
        """Shared queue test."""
        import pymp
        tqueue = pymp.shared.queue()
        with pymp.Parallel(2) as p:
            for iter_idx in p.range(400):
                tqueue.put(iter_idx)
        self.assertEqual(tqueue.qsize(), 400)

    def test_rlock(self):
        """Shared rlock test."""
        import pymp
        rlock = pymp.shared.rlock()
        tlist = pymp.shared.list()
        with pymp.Parallel(2):
            with rlock:
                with rlock:
                    tlist.append(1.)
        self.assertEqual(len(tlist), 2)

    def test_thread_limit(self):
        """Thread limit test."""
        import pymp
        pymp.config.thread_limit = 3
        pymp.config.nested = True
        thread_list = pymp.shared.list()
        with pymp.Parallel(4) as p:
            thread_list.append(p.thread_num)
        thread_list = list(thread_list)
        thread_list.sort()
        self.assertEqual(list(thread_list), [0, 1, 2])
        thread_list = pymp.shared.list()
        with pymp.Parallel(2) as p:
            with pymp.Parallel(2) as p:
                thread_list.append(p.thread_num)
        thread_list = list(thread_list)
        thread_list.sort()
        self.assertTrue(thread_list == [0, 0, 1] or
                        thread_list == [0, 1, 1])


if __name__ == '__main__':
    unittest.main()
