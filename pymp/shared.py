"""Contains shared datastructures."""
import multiprocessing as _multiprocessing
# pylint: disable=unused-import
from multiprocessing import Lock as lock, RLock as rlock

import warnings as _warnings
try:
    import numpy as _np
    _NP_AVAILABLE = True
except ImportError:
    _NP_AVAILABLE = False

_MANAGER = _multiprocessing.Manager()
_NUM_PROCS = _multiprocessing.Value('i', 1, lock=False)
_LOCK = lock()
_PRINT_LOCK = lock()


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

def array(shape, dtype='float64', autolock=False):
    """Factory method for shared memory arrays."""
    assert _NP_AVAILABLE, (
        "To use the shared array object, numpy must be available!")
    # pylint: disable=no-member
    shared_arr = _multiprocessing.Array(
        _TYPE_ASSOC_TABLE[dtype],
        _np.zeros(_np.prod(shape), dtype=dtype),
        lock=autolock)
    with _warnings.catch_warnings():
        # For more information on why this is necessary, see
        # https://www.reddit.com/r/Python/comments/j3qjb/parformatlabpool_replacement
        _warnings.simplefilter('ignore', RuntimeWarning)
        data = _np.ctypeslib.as_array(shared_arr)
    return data.reshape(shape)


def list(*args, **kwargs):  # pylint: disable=redefined-builtin
    """Create a shared list."""
    return _MANAGER.list(*args, **kwargs)

def dict(*args, **kwargs):  # pylint: disable=redefined-builtin
    """Create a shared dict."""
    return _MANAGER.dict(*args, **kwargs)

def queue():
    """Create a shared queue."""
    return _MANAGER.Queue()
