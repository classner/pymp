"""Configuration."""
# pylint: disable=invalid-name
from __future__ import print_function

import os as _os
import logging as _logging

import multiprocessing as _multiprocessing


_LOGGER = _logging.getLogger(__name__)

def _get_conf_value(suffix):
    """Get configuration value from PYMP/OMP env variables."""
    pymp_name = 'PYMP_' + suffix
    omp_name = 'OMP_' + suffix
    value = None
    for env_name in [pymp_name, omp_name]:
        # pylint: disable=no-member
        if env_name in _os.environ:
            _LOGGER.debug("Using %s environment variable: %s.",
                          env_name, _os.environ[env_name])
            value = _os.environ[env_name]
            break
    return value

# Initialize configuration.
_nested_env = _get_conf_value('NESTED')
if _nested_env is None:
    nested = False
else:  # pragma: no cover
    assert _nested_env.lower() in ['true', 'false'], (
        'The configuration for PYMP_NESTED/OMP_NESTED must be either '
        'TRUE or FALSE. Is %s.', _nested_env)
    nested = _nested_env.lower() == 'true'

_num_threads_env = _get_conf_value('NUM_THREADS')
if _num_threads_env is None:  # pragma: no cover
    # pylint: disable=no-member
    num_threads = [_multiprocessing.cpu_count()]
else:
    _num_threads_env = [int(_val) for _val in _num_threads_env.split(",")]
    for _val in _num_threads_env:
        assert _val > 0, (
            'The PYMP_NUM_THREADS/OMP_NUM_THREADS variable must be a comma '
            'separated list of positive integers, specifying the number '
            'of threads to use in each nested level.')
    num_threads = _num_threads_env[:]

_thread_limit_env = _get_conf_value("THREAD_LIMIT")
if _thread_limit_env is None:  # pragma: no cover
    thread_limit = None
else:
    thread_limit = int(_thread_limit_env)
    assert thread_limit > 0, (
        'The PYMP_THREAD_LIMIT/OMP_THREAD_LIMIT variable must be an intereger '
        'greater zero!')
