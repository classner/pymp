"""Main package."""
# pylint: disable=invalid-name
from __future__ import print_function

import os as _os
import sys as _sys
import logging as _logging
import multiprocessing as _multiprocessing
import functools

import pymp.shared as _shared
import pymp.config as _config

_LOGGER = _logging.getLogger(__name__)


# pylint: disable=too-few-public-methods, too-many-instance-attributes
class Parallel(object):

    """A parallel region."""

    _level = 0
    _global_master = None

    def __init__(self,
                 num_threads=None,
                 if_=True):  # pylint: disable=redefined-outer-name
        self._num_threads = num_threads
        self._enabled = if_
        if not self._enabled:
            self._num_threads = 1
        self._is_fork = False
        self._pids = []
        self._thread_num = 0
        self._lock = None
        if Parallel._global_master is None:
            Parallel._global_master = _os.getpid()
        # Dynamic schedule management.
        self._dynamic_queue = _shared.queue()
        self._thread_loop_ids = None
        self._queuelock = _shared.lock()
        # Exception management.
        self._exception_queue = _shared.queue()
        self._exception_lock = _shared.lock()
        # Allows for self-checks.
        self._entered = False
        self._disposed = False

    def __enter__(self):
        _LOGGER.debug("Entering `Parallel` context (level %d). Forking...",
                      Parallel._level)
        # pylint: disable=global-statement
        assert len(self._pids) == 0, (
            "A `Parallel` object may only be used once!"
        )
        self._lock = _shared.lock()
        # pylint: disable=protected-access
        if self._num_threads is None:
            assert (len(_config.num_threads) == 1 or
                    len(_config.num_threads) > Parallel._level), (
                        "The value of PYMP_NUM_THREADS/OMP_NUM_THREADS must be "
                        "either a single positive number or a comma-separated "
                        "list of number per nesting level.")
            if len(_config.num_threads) == 1:
                self._num_threads = _config.num_threads[0]
            else:
                self._num_threads = _config.num_threads[Parallel._level]
        if not _config.nested:
            assert Parallel._level == 0, (
                "No nested parallel contexts allowed!")
        Parallel._level += 1
        # pylint: disable=protected-access
        with _shared._LOCK:
            # Make sure that max threads is not exceeded.
            if _config.thread_limit is not None:
                # pylint: disable=protected-access
                num_active = _shared._NUM_PROCS.value
                self._num_threads = min(self._num_threads,
                                        _config.thread_limit - num_active + 1)
            _shared._NUM_PROCS.value += self._num_threads - 1
        self._thread_loop_ids = _shared.list([-1] * self._num_threads)
        for thread_num in range(1, self._num_threads):
            pid = _os.fork()
            if pid == 0:  # pragma: no cover
                # Forked process.
                self._is_fork = True
                self._thread_num = thread_num
                break
            else:
                # pylint: disable=protected-access
                self._pids.append(pid)
        if not self._is_fork:
            _LOGGER.debug("Forked to processes: %s.",
                          str(self._pids))
        self._entered = True
        return self

    def __exit__(self, exc_t, exc_val, exc_tb):
        _LOGGER.debug("Leaving parallel region (%d)...", _os.getpid())
        if exc_t is not None:
            with self._exception_lock:
                self._exception_queue.put((exc_t, exc_val, self._thread_num))
        if self._is_fork:  # pragma: no cover
            _LOGGER.debug("Process %d done. Shutting down.",
                          _os.getpid())
            _os._exit(1)  # pylint: disable=protected-access
        for pid in self._pids:
            _LOGGER.debug("Waiting for process %d...",
                          pid)
            _os.waitpid(pid, 0)
        # pylint: disable=protected-access
        with _shared._LOCK:
            _shared._NUM_PROCS.value -= len(self._pids)
        Parallel._level -= 1
        if _os.getpid() == Parallel._global_master:
            # Reset the manager object.
            # pylint: disable=protected-access, no-member
            _shared._MANAGER = _multiprocessing.Manager()
        self._disposed = True
        # Take care of exceptions if necessary.
        if self._enabled:
            while not self._exception_queue.empty():
                exc_t, exc_val, thread_num = self._exception_queue.get()
                _LOGGER.critical("An exception occured in thread %d: (%s, %s).",
                                 thread_num, exc_t, exc_val)
                raise exc_t(exc_val)
        else:
            if not self._exception_queue.empty():
                raise
        _LOGGER.debug("Parallel region left (%d).", _os.getpid())

    def _assert_active(self):
        """Assert that the parallel region is active."""
        assert self._entered and not self._disposed, (
            "The parallel context of this object is not active!"
        )

    @property
    def thread_num(self):
        """The worker index."""
        self._assert_active()
        return self._thread_num

    @property
    def num_threads(self):
        """The number of threads in this context."""
        self._assert_active()
        return self._num_threads

    @property
    def lock(self):
        """Get a convenient, context specific lock."""
        self._assert_active()
        return self._lock

    @classmethod
    def print(cls, *args, **kwargs):
        """Print synchronized."""
        # pylint: disable=protected-access
        with _shared._PRINT_LOCK:
            print(*args, **kwargs)
            _sys.stdout.flush()

    def range(self, start, stop=None, step=1):
        """
        Get the correctly distributed parallel chunks.

        This corresponds to using the OpenMP 'static' schedule.
        """
        self._assert_active()
        if stop is None:
            start, stop = 0, start
        full_list = range(start, stop, step)
        per_worker = len(full_list) // self._num_threads
        rem = len(full_list) % self._num_threads
        schedule = [per_worker + 1
                    if thread_idx < rem else per_worker
                    for thread_idx in range(self._num_threads)]
        # pylint: disable=undefined-variable
        start_idx = functools.reduce(lambda x, y: x+y, schedule[:self.thread_num], 0)
        end_idx = start_idx + schedule[self._thread_num]
        return full_list[start_idx:end_idx]

    def xrange(self, start, stop=None, step=1):
        """
        Get an iterator for this threads chunk of work.

        This corresponds to using the OpenMP 'dynamic' schedule.
        """
        self._assert_active()
        if stop is None:
            start, stop = 0, start
        with self._queuelock:
            pool_loop_reached = max(self._thread_loop_ids)
            # Get this loop id.
            self._thread_loop_ids[self._thread_num] += 1
            loop_id = self._thread_loop_ids[self._thread_num]
            if pool_loop_reached < loop_id:
                # No thread reached this loop yet. Set up the queue.
                for idx in range(start, stop, step):
                    self._dynamic_queue.put(idx)
            # Iterate.
            return _QueueIterator(self._dynamic_queue,
                                  loop_id,
                                  self)


class _QueueIterator(object):

    """Iterator to create the dynamic schedule."""

    def __init__(self,
                 queue,
                 loop_id,
                 pcontext):
        self._queue = queue
        self._loop_id = loop_id
        self._pcontext = pcontext

    # pylint: disable=non-iterator-returned
    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """Iterator implementation."""
        # pylint: disable=protected-access
        with self._pcontext._queuelock:
            # Check that the pool still deals with this loop.
            # pylint: disable=protected-access
            pool_loop_reached = max(self._pcontext._thread_loop_ids)
            if (pool_loop_reached > self._loop_id or
                    self._queue.empty()):
                raise StopIteration()
            else:
                return self._queue.get()
