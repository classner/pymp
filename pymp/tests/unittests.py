"""Unittests for the pymp package."""
# pylint: disable=protected-access, invalid-name
from __future__ import print_function
import logging

import unittest

logging.basicConfig(level=logging.INFO)


class ParallelTest(unittest.TestCase):

    """Test the parallel context."""

    def test_init(self):
        """Initialization test."""
        import pymp
        pymp.config.nested = False
        pymp.config.thread_limit = 4
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

    def test_num_threads(self):
        """Test num threads property."""
        import pymp
        import os
        pymp.config.nested = False
        pymp.config.thread_limit = 4
        tlist = pymp.shared.list()
        with pymp.Parallel(2) as p:
            tlist.append(p.num_threads)
        self.assertEqual(list(tlist), [2, 2])
        pymp.config.nested = True
        tlist = pymp.shared.list()
        with pymp.Parallel(2) as p:
            with pymp.Parallel(2) as p2:
                tlist.append(p2.num_threads)
        self.assertEqual(list(tlist), [2, 2, 2, 2])

    def test_thread_num(self):
        """Test thread_num property."""
        import pymp
        pymp.config.nested = True
        pymp.config.thread_limit = 4
        tlist = pymp.shared.list()
        with pymp.Parallel(2) as p:
            tlist.append(p.thread_num)
        self.assertEqual(sorted(list(tlist)), [0, 1])
        tlist = pymp.shared.list()
        tlist2 = pymp.shared.list()
        tlist3 = pymp.shared.list()
        with pymp.Parallel(2) as p:
            with pymp.Parallel(2) as p2:
                if not p._is_fork:
                    tlist.append(p2.thread_num)
                else:
                    tlist2.append(p2.thread_num)
            tlist3.append(p.thread_num)
        self.assertEqual(sorted(list(tlist)), [0, 1])
        self.assertEqual(sorted(list(tlist2)), [0, 1])
        self.assertEqual(sorted(list(tlist3)), [0, 1])

    def test_range(self):
        """Range test."""
        import pymp
        pymp.config.nested = False
        pymp.config.thread_limit = 4
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
        pymp.config.nested = False
        pymp.config.thread_limit = 4
        try:
            import numpy as np
        except ImportError:
            return
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
        pymp.config.nested = False
        pymp.config.thread_limit = 4
        tlist = pymp.shared.list()
        with pymp.Parallel(2) as p:
            for _ in p.range(1000):
                tlist.append(1.)
        self.assertEqual(len(tlist), 1000)

    def test_dict(self):
        """Shared dict test."""
        import pymp
        pymp.config.nested = False
        pymp.config.thread_limit = 4
        tdict = pymp.shared.dict()
        with pymp.Parallel(2) as p:
            for iter_idx in p.range(400):
                tdict[iter_idx] = 1.
        self.assertEqual(len(tdict), 400)

    def test_queue(self):
        """Shared queue test."""
        import pymp
        pymp.config.nested = False
        pymp.config.thread_limit = 4
        tqueue = pymp.shared.queue()
        with pymp.Parallel(2) as p:
            for iter_idx in p.range(400):
                tqueue.put(iter_idx)
        self.assertEqual(tqueue.qsize(), 400)

    def test_rlock(self):
        """Shared rlock test."""
        import pymp
        pymp.config.nested = False
        pymp.config.thread_limit = 4
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
            with pymp.Parallel(2) as p2:
                thread_list.append(p2.thread_num)
        thread_list = list(thread_list)
        thread_list.sort()
        self.assertTrue(thread_list == [0, 0, 1] or
                        thread_list == [0, 0, 1, 1])
        # Second case if the first two threads were exiting already.

    def test_xrange(self):
        """Test the dynamic schedule."""
        import pymp
        pymp.config.thread_limit = 4
        pymp.config.nested = True
        tlist = pymp.shared.list()
        with pymp.Parallel(2):
            with pymp.Parallel(2) as p:
                for idx in p.xrange(5):
                    tlist.append(idx)
        self.assertEqual(len(tlist), 10)

    def test_exceptions(self):
        """Test raising behavior."""
        import pymp
        pymp.config.thread_limit = 4
        pymp.config.nested = True
        def exc_context():
            """Creates a context with an Exception in a subthread."""
            with pymp.Parallel(2) as p:
                if p.thread_num == 1:
                    raise Exception()
        self.assertRaises(Exception, exc_context)

    def test_print(self):  # pylint: disable=no-self-use
        """Test the print method."""
        import pymp
        pymp.config.thread_limit = 3
        pymp.config.nested = True
        with pymp.Parallel(2):
            with pymp.Parallel(2) as p:
                p.print("Hi from thread {}.".format(p.thread_num))

    def test_safety_check(self):
        """Test that the methods can only be used within their context."""
        import pymp
        pymp.config.thread_limit = 3
        pymp.config.nested = True
        p = pymp.Parallel(2)
        # Exception before use.
        self.assertRaises(AssertionError, lambda: p.thread_num)
        self.assertRaises(AssertionError, lambda: p.num_threads)
        self.assertRaises(AssertionError, lambda: p.lock)
        self.assertRaises(AssertionError, lambda: p.range(10))
        self.assertRaises(AssertionError, lambda: p.xrange(10))
        with p:
            pass
        # Exception after use.
        self.assertRaises(AssertionError, lambda: p.thread_num)
        self.assertRaises(AssertionError, lambda: p.num_threads)
        self.assertRaises(AssertionError, lambda: p.lock)
        self.assertRaises(AssertionError, lambda: p.range(10))
        self.assertRaises(AssertionError, lambda: p.xrange(10))

    def test_if(self):
        """Test the if_ deactivation."""
        import pymp
        pymp.config.thread_limit = 3
        pymp.config.nested = True
        with pymp.Parallel(if_=False) as p:
            self.assertEqual(p.num_threads, 1)

    def test_noreshape(self):
        """Test if reshaping is effectively prevented."""
        import pymp
        sa = pymp.shared.array((3, 3))
        self.assertRaises(ValueError, lambda: sa.reshape((4, 4)))
        sa.reshape((1, 3, 3))


if __name__ == '__main__':
    unittest.main()
