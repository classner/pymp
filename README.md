
# pymp

This package brings OpenMP-like functionality to Python. It takes the good
qualities of OpenMP such as minimal code changes and high efficiency and
combines them with the Python Zen of code clarity and ease-of-use.

## Usage

For loops, such as:

```
ex_array = np.zeros((100,), dtype='uint8')
for index in range(0, 100):
    ex_array[index] = 1
    print('Yay! {} done!'.format(index))
```

become:

```
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

For now, please install from github by doing:

```
git clone https://github.com/classner/pymp.git
cd pymp
python setup.py install
```

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

Other iterators, such as `enumerate`, or simply an iterator over arbitrary
list elements, have on purpose not been implemented to ensure efficient
operation of the package. Using only index lists forces the user to create
complex or large objects in memory *before* the fork. If this would not be the
case, they would have to be serialized and forwarded through the iterator to the
consuming process, which is not what is usually intended.

### Variable scopes

The only implemented variable scopes are `firstprivate`, `shared` and
`private`. All variables that are declared before the `pymp.Parallel` call
are explicitly `firstprivate`, all variables from the `pymp.shared`
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
            p.print('Secion 1')
        ...
```

### Exceptions

Exceptions will be noticed in the main program. However, there can be as many
fatal Exceptions as sub-processes at the end of a parallel context. They are
logged by the logger as `critical`, so you can always redirect their output.
If there was an exception in the parallel context, a plain `Exception` will
be raised in the main process, which can be handled.

### Reductions

There is no method for reductions implemented explicitly and on purpose for
two reasons:

1. due to the higher level of the Python language compared to C++, it is very
easy to create a shared list and do the reduction after the loop, which,
2. corresponds more to the `explicit is better than implicit` Zen of Python and
3. can be realized cleanly with the language means that are available, while it is
4. perfectly deterministic.

The last point is not necessarily true for OpenMP reductions.


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
