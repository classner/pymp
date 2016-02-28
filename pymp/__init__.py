"""Main package."""
# pylint: disable=invalid-name
from __future__ import print_function

import os as _os
import sys as _sys
import logging as _logging
import warnings as _warnings

import multiprocessing as _multiprocessing
import numpy as _np

import pymp.config as _config
# pylint: disable=no-name-in-module
from multiprocessing import Lock


_LOGGER = _logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
class Parallel(object):

    """A parallel region."""

    _instances = []

    def __init__(self,
                 num_threads=None):  # pylint: disable=redefined-outer-name
        if num_threads is None:
            self._num_threads = _config.num_threads
        else:
            self._num_threads = num_threads
        self._is_fork = False
        _LOGGER.debug("Constructed `Parallel` object for %d threads.",
                      self._num_threads)
        self._pids = []
        self._thread_num = 0

    def __enter__(self):
        assert len(self._pids) == 0, (
            "A `Parallel` object may only be used once!"
        )
        if not _config.nested:
            assert len(Parallel._instances) == 0, (
                "No nested parallel contexts allowed!")
        else:
            raise NotImplementedError("No nested support yet...")
        _LOGGER.debug("Entering `Parallel` context. Forking...")
        Parallel._instances.append(self)
        for thread_num in range(1, self._num_threads):
            pid = _os.fork()
            if pid == 0:
                # Forked process.
                self._is_fork = True
                self._thread_num = thread_num
                break
            else:
                self._pids.append(pid)
        if not self._is_fork:
            _LOGGER.debug("Forked to processes: %s.",
                          str(self._pids))
        return self

    def __exit__(self, exc_t, exc_val, exc_tb):
        if self._is_fork:
            _os._exit(1)  # pylint: disable=protected-access
        else:
            for pid in self._pids:
                _LOGGER.debug("Waiting for process %d...",
                              pid)
                _os.waitpid(pid, 0)
        Parallel._instances = [inst for inst in self._instances
                               if not inst is self]
        _LOGGER.debug("Parallel region left.")

    @property
    def thread_num(self):
        """The worker index."""
        return self._thread_num

    def range(self, start, stop=None, step=1):
        """Get the correctly distributed parallel chunks in a `Parallel` context."""
        if stop is None:
            start, stop = 0, start
        full_list = range(start, stop, step)
        per_worker = len(full_list) // self._num_threads
        rem = len(full_list) % self._num_threads
        schedule = [per_worker + 1
                    if thread_idx < rem else per_worker
                    for thread_idx in range(self._num_threads)]
        # pylint: disable=undefined-variable
        start_idx = reduce(lambda x, y: x+y, schedule[:self.thread_num], 0)
        end_idx = start_idx + schedule[self._thread_num]
        return full_list[start_idx:end_idx]


"""
See https://docs.python.org/2/library/array.html#module-array.
"""
_TYPE_ASSOC_TABLE = {'uint8': 'B',
                     'int8': 'b',
                     'uint16': 'H',
                     'int16': 'h',
                     'uint32': 'I',
                     'int32': 'i',
                     'uint64': 'l',
                     'int64': 'L',
                     'float32': 'f',
                     'float64': 'd'}

def SharedArray(shape, dtype='float64'):
    """Factory method for shared memory arrays."""
    # pylint: disable=no-member
    shared_arr = _multiprocessing.Array(
        _TYPE_ASSOC_TABLE[dtype],
        _np.zeros(_np.prod(shape), dtype=dtype),
        lock=False)
    with _warnings.catch_warnings():
        # For more information on why this is necessary, see
        # https://www.reddit.com/r/Python/comments/j3qjb/parformatlabpool_replacement
        _warnings.simplefilter('ignore', RuntimeWarning)
        data = _np.ctypeslib.as_array(shared_arr)
    return data.reshape(shape)
