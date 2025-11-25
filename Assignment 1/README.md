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
├── main.py
└── README.md
```

## Requirements

* Python 3.8+
* No external dependencies

## Quick Start

## How to Run

From the project root:

```bash
python main.py
```

This script will:

* Initialize a `ProducerConsumerSystem` with a bounded buffer of size 5
* Register **3 producers**, each generating 10 items (`P1-*`, `P2-*`, `P3-*`) with a small production delay
* Register **2 consumers** with a small consumption delay
* Start all producer and consumer threads
* Perform a **graceful shutdown** after producers finish (buffer is drained, then poison pills sent)
* Print:

  * Total items consumed
  * Aggregated per-thread statistics

## Sample Output
```text

Starting producer-consumer system
Consumer 1 started
Consumer 2 started
Producer 1 started
Producer 2 started
Producer 3 started
Initiating graceful shutdown
Producer 1 produced: 'P1-0' (total: 1)
Producer 2 produced: 'P2-0' (total: 1)
Producer 3 produced: 'P3-0' (total: 1)
Producer 1 produced: 'P1-1' (total: 2)
Producer 2 produced: 'P2-1' (total: 2)
Producer 3 produced: 'P3-1' (total: 2)
Consumer 2 consumed: 'P2-0' (total: 1)
Producer 1 produced: 'P1-2' (total: 3)
Producer 3 produced: 'P3-2' (total: 3)
Consumer 1 consumed: 'P1-0' (total: 1)
Producer 2 produced: 'P2-2' (total: 3)
Consumer 2 consumed: 'P3-0' (total: 2)
Consumer 1 consumed: 'P1-1' (total: 2)
Producer 1 produced: 'P1-3' (total: 4)
Producer 3 produced: 'P3-3' (total: 4)
Consumer 2 consumed: 'P2-1' (total: 3)
Producer 2 produced: 'P2-3' (total: 4)
Consumer 1 consumed: 'P3-1' (total: 3)
Producer 1 produced: 'P1-4' (total: 5)
Consumer 2 consumed: 'P1-2' (total: 4)
Consumer 1 consumed: 'P3-2' (total: 4)
Producer 3 produced: 'P3-4' (total: 5)
Producer 2 produced: 'P2-4' (total: 5)
Consumer 1 consumed: 'P1-3' (total: 5)
Producer 1 produced: 'P1-5' (total: 6)
Consumer 2 consumed: 'P2-2' (total: 5)
Producer 2 produced: 'P2-5' (total: 6)
Consumer 1 consumed: 'P3-3' (total: 6)
Consumer 2 consumed: 'P2-3' (total: 6)
Producer 1 produced: 'P1-6' (total: 7)
Producer 3 produced: 'P3-5' (total: 6)
Consumer 2 consumed: 'P3-4' (total: 7)
Consumer 1 consumed: 'P1-4' (total: 7)
Producer 2 produced: 'P2-6' (total: 7)
Producer 1 produced: 'P1-7' (total: 8)
Consumer 2 consumed: 'P2-4' (total: 8)
Producer 3 produced: 'P3-6' (total: 7)
Consumer 1 consumed: 'P1-5' (total: 8)
Producer 1 produced: 'P1-8' (total: 9)
Consumer 2 consumed: 'P2-5' (total: 9)
Producer 2 produced: 'P2-7' (total: 8)
Consumer 1 consumed: 'P1-6' (total: 9)
Producer 3 produced: 'P3-7' (total: 8)
Consumer 2 consumed: 'P3-5' (total: 10)
Consumer 1 consumed: 'P2-6' (total: 10)
Producer 2 produced: 'P2-8' (total: 9)
Producer 1 produced: 'P1-9' (total: 10)
Producer 1 finished. Total items produced: 10
Consumer 2 consumed: 'P1-7' (total: 11)
Consumer 1 consumed: 'P3-6' (total: 11)
Producer 2 produced: 'P2-9' (total: 10)
Producer 2 finished. Total items produced: 10
Producer 3 produced: 'P3-8' (total: 9)
Consumer 2 consumed: 'P1-8' (total: 12)
Producer 3 produced: 'P3-9' (total: 10)
Producer 3 finished. Total items produced: 10
Consumer 1 consumed: 'P2-7' (total: 12)
All producers finished
Consumer 2 consumed: 'P3-7' (total: 13)
Consumer 1 consumed: 'P2-8' (total: 13)
Consumer 2 consumed: 'P1-9' (total: 14)
Consumer 1 consumed: 'P2-9' (total: 14)
Consumer 1 consumed: 'P3-9' (total: 15)
Consumer 2 consumed: 'P3-8' (total: 15)
Consumer 1 received poison pill
Consumer 1 finished. Total items consumed: 15
Consumer 2 received poison pill
Consumer 2 finished. Total items consumed: 15
System shutdown complete
Total items consumed: 30
Stats: {'num_producers': 3, 'num_consumers': 2, 'total_produced': 30, 'total_consumed': 30, 'buffer_size': 0, 'items_in_transit': 0}

```

### Running  Unit Tests

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

### Sample Unit Test Output

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
