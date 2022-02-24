"""Contains shared datastructures."""
# pylint: disable=no-member, unused-import, ungrouped-imports
import multiprocessing as _multiprocessing
import warnings as _warnings
import logging
from multiprocessing import Lock as lock
from multiprocessing import RLock as rlock

try:
    import numpy as _np

    _NP_AVAILABLE = True
except ImportError:  # pragma: no cover
    _NP_AVAILABLE = False

_MANAGER = None
_NUM_PROCS = _multiprocessing.Value("i", 1, lock=False)  # pylint: disable=no-member
_LOCK = lock()
_PRINT_LOCK = lock()
_LOGGER = logging.getLogger(__name__)


def _get_manager():
    global _MANAGER, _LOCK
    if _MANAGER is None:
        with _LOCK:
            if _MANAGER is None:
                try:
                    _MANAGER = _multiprocessing.Manager()
                except RuntimeError as err:
                    _LOGGER.error(
                        "Could not create a multiprocessing manager. "
                        "This is likely because you are calling a function "
                        "using PyMP directly from the main script, without "
                        "guarding it with a `if __name__ == '__main__':`. "
                        "This is not supported. Just in case, we'll raise "
                        "the original exception."
                    )
                    raise err
    return _MANAGER


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
    return _get_manager().list(*args, **kwargs)


def dict(*args, **kwargs):  # pylint: disable=redefined-builtin
    """Create a shared dict."""
    return _get_manager().dict(*args, **kwargs)


def queue(*args, **kwargs):
    """Create a shared queue."""
    return _get_manager().Queue(*args, **kwargs)
