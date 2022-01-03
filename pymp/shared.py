"""Contains shared datastructures."""
# pylint: disable=no-member, unused-import, ungrouped-imports
import multiprocessing as _multiprocessing
import warnings as _warnings
from multiprocessing import Lock as lock

try:
    import numpy as _np

    _NP_AVAILABLE = True
except ImportError:  # pragma: no cover
    _NP_AVAILABLE = False

_MANAGER = _multiprocessing.Manager()  # pylint: disable=no-member
_NUM_PROCS = _multiprocessing.Value("i", 1, lock=False)  # pylint: disable=no-member
_LOCK = lock()
_PRINT_LOCK = lock()


def array(shape, dtype=None, autolock=False):
    """
    Factory method for shared memory arrays supporting all numpy dtypes.

    By default the dtype will be set to float64 (if dtype is None).
    """
    assert _NP_AVAILABLE, "To use the shared array object, numpy must be available!"
    if dtype is None:
        dtype = _np.float64
    if not isinstance(dtype, _np.dtype):
        dtype = _np.dtype(dtype)
    # Not bothering to translate the numpy dtypes to ctype types directly,
    # because they're only partially supported. Instead, create a byte ctypes
    # array of the right size and use a view of the appropriate datatype.
    shared_arr = _multiprocessing.Array(
        "b", int(_np.prod(shape) * dtype.itemsize), lock=autolock
    )
    with _warnings.catch_warnings():
        # For more information on why this is necessary, see
        # https://www.reddit.com/r/Python/comments/j3qjb/parformatlabpool_replacement
        _warnings.simplefilter("ignore", RuntimeWarning)
        data = _np.ctypeslib.as_array(shared_arr).view(dtype).reshape(shape)
    return data


def list(*args, **kwargs):  # pylint: disable=redefined-builtin
    """Create a shared list."""
    return _MANAGER.list(*args, **kwargs)


def dict(*args, **kwargs):  # pylint: disable=redefined-builtin
    """Create a shared dict."""
    return _MANAGER.dict(*args, **kwargs)


def queue(*args, **kwargs):
    """Create a shared queue."""
    return _MANAGER.Queue(*args, **kwargs)
