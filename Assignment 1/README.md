# Producer–Consumer Pattern (Python)

A thread-safe implementation of the classic Producer–Consumer pattern in Python with support for multiple producers and consumers (N:M). The system uses an **explicit condition-based bounded buffer** (`SharedBuffer`) built on `threading.Condition`, a poison-pill shutdown, and a focused unit test suite plus optional integration tests.

## Features

* Explicit wait/notify via `threading.Condition`
* Full N:M topology (any number of producers and consumers)
* Blocking semantics: producers block when the buffer is full, consumers block when the buffer is empty
* Graceful shutdown using poison pills (one per consumer) with deterministic drain
* Shared destination guarded by a lock for safe concurrent appends
* Modular architecture with clear separation of concerns
* Unit tests for the bounded buffer (as requested in the assignment)
* Optional integration tests that exercise full system behavior, including a high-contention stress scenario
* Extensive docstrings and runnable examples

## Project Structure

```text
Assignment 1/
├── src/
│   ├── __init__.py
│   ├── shared_buffer.py          # Condition-based bounded buffer
│   ├── producer.py               # Producer thread
│   ├── consumer.py               # Consumer thread
│   └── system.py                 # Orchestrator (graceful/forceful shutdown)
├── tests/
│   ├── run_tests.py          # Test runner (unit tests by default)
│   ├── test_shared_buffer.py     # REQUIRED unit tests for SharedBuffer
│   └── integration_producer_consumer.py  # OPTIONAL integration tests (1:1, N:1, 1:M, N:M, contention)
└── README.md
```

## Requirements

* Python 3.8+
* No external dependencies

## Quick Start

```bash
# Run the REQUIRED unit tests for SharedBuffer (per assignment prompt)
python tests/run_tests.py
# or explicitly
python -m unittest tests.test_shared_buffer -v
```

### Running Optional Integration Tests

To also run the integration tests that exercise the full Producer–Consumer system with multiple producers and consumers:

```bash
# Run only the integration tests
python -m unittest tests.integration_producer_consumer -v

```

### Sample Unit Test Output (abbreviated)

```text

test_blocking_get_timeout (test_shared_buffer.TestSharedBuffer.test_blocking_get_timeout)
get() should respect timeout when buffer is empty. ... ok
test_blocking_put_timeout (test_shared_buffer.TestSharedBuffer.test_blocking_put_timeout)
put() should respect timeout when buffer is full. ... ok
test_buffer_initialization (test_shared_buffer.TestSharedBuffer.test_buffer_initialization)
Buffer starts empty and not full. ... ok
test_fifo_order (test_shared_buffer.TestSharedBuffer.test_fifo_order)
Queue maintains FIFO ordering. ... ok
test_get_until_empty (test_shared_buffer.TestSharedBuffer.test_get_until_empty)
After removing all items, buffer reports empty. ... ok
test_put_get_single_item (test_shared_buffer.TestSharedBuffer.test_put_get_single_item)
Single put/get roundtrip updates size correctly. ... ok
test_put_until_full (test_shared_buffer.TestSharedBuffer.test_put_until_full)
Buffer reports full at capacity. ... ok

----------------------------------------------------------------------
Ran 7 tests in 1.007s

OK

======================================================================
TEST SUMMARY
======================================================================
Start directory: /Users/jay/Desktop/Intuit Build Challenge/Assignment 1/tests
Pattern:         test_shared_buffer.py
Verbosity:       2
Elapsed:         1.01s
----------------------------------------------------------------------
Tests run:       7
Successes:       7
Failures:        0
Errors:          0

 All tests passed!
======================================================================

```

## Usage

### Basic (1:1)

```python
from src import ProducerConsumerSystem

source = [f"Item-{i}" for i in range(20)]
destination = []

system = ProducerConsumerSystem(buffer_size=5)
system.add_producer(producer_id=1, source=source)
system.add_consumer(consumer_id=1, destination=destination)

system.start()
system.shutdown_gracefully()

print(f"Transferred: {len(destination)} items")
```

### Advanced (N:M)

```python
from src import ProducerConsumerSystem

sources = [
    [f"P1-{i}" for i in range(15)],
    [f"P2-{i}" for i in range(15)],
    [f"P3-{i}" for i in range(15)],
]
destination = []

system = ProducerConsumerSystem(buffer_size=10)
for i, src in enumerate(sources, 1):
    system.add_producer(producer_id=i, source=src)

for cid in range(1, 3):
    system.add_consumer(consumer_id=cid, destination=destination)

system.start()
system.shutdown_gracefully()

print(f"Transferred: {len(destination)} items")
print(f"Statistics: {system.get_statistics()}")
```

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
│                  (examples, tests)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Orchestration Layer                    │
│              ProducerConsumerSystem                     │
│  - Lifecycle management                                 │
│  - Shutdown coordination                                │
│  - Statistics tracking                                  │
└──────────────┬────────────────────┬─────────────────────┘
               │                    │
       ┌───────▼────────┐   ┌──────▼────────┐
       │   Producer     │   │   Consumer    │
       │   (Thread)     │   │   (Thread)    │
       └───────┬────────┘   └──────┬────────┘
               │                    │
               └──────────┬─────────┘
                          ▼
                 ┌──────────────────────────────┐
                 │ SharedBuffer (Condition-based)│
                 │  - Lock + Condition          │
                 │  - Blocking put/get          │
                 │  - Timeouts & close()        │
                 └──────────────────────────────┘
```

## Components

**SharedBuffer (`src/shared_buffer.py`)**
Condition-based bounded buffer providing blocking `put` and `get`, timeouts, `close`, and size/introspection helpers. Uses a lock and condition variables to implement wait/notify explicitly.

**Producer (`src/producer.py`)**
Thread that reads from a per-producer source list and pushes items into the shared buffer. Retries `put` with a timeout until accepted to avoid data loss under contention.

**Consumer (`src/consumer.py`)**
Thread that reads from the shared buffer and appends to a shared destination list guarded by a shared lock. Recognizes a poison-pill sentinel for clean shutdown and calls `task_done` for both data and sentinel items.

**ProducerConsumerSystem (`src/system.py`)**
Orchestrates lifecycle: adds producers and consumers, starts them, performs deterministic graceful shutdown (wait for producers, use `join` to drain work, enqueue one poison pill per consumer with retries, call `join` again to ensure pills are processed, then join consumers), and aggregates statistics.

## Synchronization Strategy

* `SharedBuffer.put` blocks while the buffer is full; `get` blocks while the buffer is empty, using explicit wait/notify.
* A single shared `threading.Lock` serializes writes to the shared destination list.
* Poison pill pattern: after all producers finish and the buffer drains (`join`), the system enqueues one sentinel per consumer, waits again for all pills to be processed, and only then joins the consumers.

## Testing Strategy

* **Required unit tests** (`tests/test_shared_buffer.py`)

  * Cover initialization, FIFO ordering, blocking semantics, and timeouts.
  * These tests are what the assignment prompt refers to when it asks for "unit tests".

* **Optional integration tests** (`tests/integration_producer_consumer.py`)

  * Cover 1:1, N:1, 1:M, and N:M topologies.
  * Include a high-contention scenario (many producers and consumers with a very small buffer).
  * Verify that no items are duplicated or lost and that statistics remain consistent.



## Design Decisions and Trade-offs

* **Explicit `Condition` vs `queue.Queue`**: this implementation demonstrates the primitives directly, reinforcing understanding of wait/notify and timeouts while maintaining correctness.
* **Poison-pill shutdown with double `join`**: ensures a deterministic barrier so no items (or pills) are left unaccounted for.
* **Destination lock**: Python lists are not thread-safe; a shared lock ensures correctness with minimal overhead.
* **Clarity over micro-optimizations**: prioritize correctness, readability, and testability for a take-home setting.

## Performance Notes

* **Buffer size**: small buffers increase contention (useful for stress testing). Medium buffers (for example 10 to 20) are balanced for most scenarios.
* **Thread counts**: for I/O-bound work you can exceed CPU cores; for CPU-bound tasks consider multiprocessing.
* `put` and `get` are amortized O(1). Memory footprint is O(buffer_size) plus O(1) per thread.

## FAQ

**Does the system ever drop items?**
No. Producers retry `put` on timeout and the system drains the buffer with `join` before sending poison pills. It then waits again until pills are processed.

**Is the destination write safe with multiple consumers?**
Yes. A shared `threading.Lock` guards the destination list append.

**Which Python versions are supported?**
Python 3.8 and newer.
