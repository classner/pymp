
# pymp

[![Build Status](https://travis-ci.org/classner/pymp.svg?branch=master)](https://travis-ci.org/classner/pymp)
[![Coverage Status](https://coveralls.io/repos/github/classner/pymp/badge.svg?branch=master)](https://coveralls.io/github/classner/pymp?branch=master)
[![PyPI version](https://badge.fury.io/py/pymp-pypi.png)](https://badge.fury.io/py/pymp-pypi)
[![Python support](https://img.shields.io/badge/python-2.6%2C2.7%2C3.4%2C3.5%2C3.6%2C3.7-blue.svg)](https://travis-ci.org/classner/pymp)
[![Documentation Status](https://readthedocs.org/projects/pymp/badge/?version=latest)](http://pymp.readthedocs.io/en/latest/?badge=latest)

This package brings OpenMP-like functionality to Python. It takes the good
qualities of OpenMP such as minimal code changes and high efficiency and
combines them with the Python Zen of code clarity and ease-of-use.

## Usage

For-loops, such as:

```
from __future__ import print_function

ex_array = np.zeros((100,), dtype='uint8')
for index in range(0, 100):
    ex_array[index] = 1
    print('Yay! {} done!'.format(index))
```

become:

```
from __future__ import print_function

import pymp
ex_array = pymp.shared.array((100,), dtype='uint8')
with pymp.Parallel(4) as p:
    for index in p.range(0, 100):
        ex_array[index] = 1
        # The parallel print function takes care of asynchronous output.
        p.print('Yay! {} done!'.format(index))
```

The GIL (global interpreter lock) is circumvented by using the operating
system's fork method. Due to the copy-on-write strategy, this causes
only a minimal overhead and results in the expected semantics. On the
other hand, the package will only work on systems with fork support (sorry,
not on Windows).

## Installation

The package is available from pypi. Due to a name clash, it is
available as ``pymp-pypi``:

```
pip install pymp-pypi
```

To get the cutting edge version from github, do:

```
git clone https://github.com/classner/pymp.git
cd pymp
python setup.py develop
```

In theory, Python 3.2 and Python 3.3 should be supported as well. For some
reason, the travis-ci builds hangs AFTER completing the test runs. If someone
confirms successful testing on these versions, please let me know so that I
include them in the compatibility list.

## Features

### Environment variables and configuration

The module is configurable by environment variables as well as at runtime.
It respects the environment variables:
* `PYMP_NESTED` / `OMP_NESTED`: 'TRUE' or 'FALSE' (default: 'FALSE'),
* `PYMP_THREAD_LIMIT` / `OMP_THREAD_LIMIT`: int > 0 (default: unset),
* `PYMP_NUM_THREADS` / `OMP_NUM_THREADS`: comma-separated list of int > 0,
the number of threads to use per nesting level. If only one value is provided,
it is used for all levels. Default: number of cores.

The `PYMP` variables are used with preference. At runtime, the configuration
values can be set at any time by using: `pymp.config.nested`,
`pymp.config.thread_limit` and `pymp.config.num_threads`.

### OpenMP variables

Every parallel context provides its number of threads and the current thread's
`thread_num` in the same way OpenMP does:

```
with pymp.Parallel(4) as p:
    p.print(p.num_threads, p.thread_num)
```

The original thread entering the parallel context always has `thread_num` 0.

### Schedules

The basic OpenMP scheduling types map directly to the classical Python ranges:
using `pymp.range` corresponds to the `static` schedule by returning a complete
list of indices, while `pymp.xrange` returns an iterator and corresponds to
dynamic scheduling.

You can use `p.iterate` to iterate over arbitrary
list elements. However, bearing efficiency in mind you should create complex or
large objects *before* the parallel section. Otherwise, they
have to be serialized and forwarded through the iterator to the
consuming process.

### Variable scopes

The only implemented variable scopes are `firstprivate`, `shared` and
`private`. All variables that are declared before the `pymp.Parallel` call
are implicitly `firstprivate`, all variables from the `pymp.shared`
module are shared, and all variables created within a `pymp.Parallel` context
are private.

The package `pymp.shared` provides a numpy array wrapper accepting the standard
datatype strings, as well as shared `list`, `dict`, `queue`, `lock` and `rlock`
objects wrapped from multiprocessing. High performance shared memory (ctypes)
datastructues are `array`, `lock` and `rlock`, the other datastructures are
synchronized via a `multiprocessing.Manager` and hence a little slower.

All datastructures must be synchronized manually, if required, by using a
`lock`. The parallel context offers one for your convenience:

```
ex_array = pymp.shared.array((1,), dtype='uint8')
with pymp.Parallel(4) as p:
    for index in p.range(0, 100):
        with p.lock:
            ex_array[0] += 1
```

### Nested loops

When `pymp.config.nested` is `True`, it is possible to nest parallel contexts
with the expected semantics:

```
with pymp.Parallel(2) as p1:
    with pymp.Parallel(2) as p2:
        p.print(p1.thread_num, p2.thread_num)
```

### Parallel sections

There is no special context for parallel sections. Please use a `pymp.range` or
`pymp.xrange` and `if-else` to achieve the expected behavior:

```
with pymp.Parallel(4) as p:
    for sec_idx in p.xrange(4):
        if sec_idx == 0:
            p.print('Section 0')
        elif sec_idx == 1:
            p.print('Section 1')
        ...
```

### Exceptions

Exceptions will be raised in the main program. However, there can be as many
fatal Exceptions as sub-processes at the end of a parallel context. They are
logged by the logger as `critical`, so you can always redirect their output.

All exceptions will be re-raised in the main program at the end of the parallel
section with their proper exception type and error message. It is unavoidable
that their stack-traces are lost, unfortunately. For easy debugging, use the
``pymp.Parallel(..., if_=False)`` flag to temporarily disable parallelism.

### Conditional parallelism

As mentioned in the preceding paragraph, parallel execution can be disabled
regardless of other settings by passing ``if_=False`` to the parallel region
constructor.

### Reductions

There is on purpose no method for reductions implemented for four reasons:

1. due to the higher level of the Python language compared to C++, it is very
easy to create a shared list and do the reduction after the loop, which,
2. corresponds more to the `explicit is better than implicit` Zen of Python and
3. can be realized cleanly with the language means that are available, while it is
4. perfectly deterministic.

The last point is not necessarily true for OpenMP reductions.

### Iterables

Additional to these more traditional OpenMP functionalities, ``pymp`` provides
a more Pythonic way of parallelization: parallel iterators. This is a
powerful paradigm, since iterators can be stacked. ``pymp`` uses a producer-
consumer pattern with the main thread as producer always and the rest of the
threads as consumers of the iterable. This is as easy as

```
with pymp.Parallel(4) as p:
    for iter_item in p.iterate(xrange(4)):
        p.print(iter_item)
```

The iteration items must be picklable to be transferred through a queue.


## How does it work?

When entering a parallel context, processes are forked as necessary. That means
that child processes are started, which are in (nearly) exactly the same state
as the creating process. The memory is not copied, but referenced. Only when a
process writes into a part of the memory it gets its own copy of the
corresponding memory region. This keeps the processing overhead low (but of
course not as low as for OpenMP threads).

Once the parallel region is left, child processes exit and only the original
process 'survives'. The 'shared' datastructures from the corresponding submodule
are synchronized either via shared memory or using a manager process and the
pickle protocol (see the documentation of the multiprocessing module for more
information).
