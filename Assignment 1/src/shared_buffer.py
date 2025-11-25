"""
Shared Buffer Module

Thread-safe bounded buffer implemented with an explicit mutex and
condition variables (wait/notify). Supports blocking put/get with
optional timeouts and join/task_done coordination.
"""

from __future__ import annotations

from time import monotonic
from typing import Deque, Generic, Optional, TypeVar
from collections import deque
import threading

T = TypeVar("T")


class QueueClosed(RuntimeError):
    """Raised when operations are attempted on a closed buffer."""
    pass


class SharedBuffer(Generic[T]):
    """
    Bounded, thread-safe buffer.

    - put(item, timeout): blocks when full; returns False on timeout.
    - get(timeout): blocks when empty; returns None on timeout.
    - task_done(): marks a retrieved item as fully processed.
    - join(): blocks until all put items have a matching task_done().
    """

    def __init__(self, max_size: int = 10) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be positive")

        self._max: int = max_size
        self._q: Deque[T] = deque()

        self._lock = threading.Lock()

        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        self._all_tasks_done = threading.Condition(self._lock)

        self._unfinished_tasks: int = 0

        self._closed: bool = False

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _wait_until(self, predicate, timeout: Optional[float]) -> bool:
        """
        Wait (under self._lock) until predicate() becomes True or timeout elapses.
        Returns True if predicate became True; False on timeout.
        """
        if timeout is None:
            while not predicate():
                
                self._not_empty.wait()
            return True

        deadline = monotonic() + timeout
        remaining = timeout
        while not predicate():
            if remaining <= 0:
                return False
            self._not_empty.wait(timeout=remaining)
            remaining = deadline - monotonic()
        return True



    def put(self, item: T, timeout: Optional[float] = None) -> bool:
        """
        Enqueue an item. Blocks while the buffer is full.
        Returns True if enqueued, or False if the timeout elapsed.
        Raises QueueClosed if the buffer was closed before/while waiting.
        """
        with self._lock:
            if self._closed:
                raise QueueClosed("Buffer is closed")

            def can_put() -> bool:
                return (not self._closed) and (len(self._q) < self._max)

            if not can_put():
                if not self._wait_until(can_put, timeout):
                    return False
                if self._closed:
                    raise QueueClosed("Buffer is closed")

            self._q.append(item)
            self._unfinished_tasks += 1
            self._not_empty.notify()
            return True

    def get(self, timeout: Optional[float] = None) -> Optional[T]:
        """
        Dequeue and return an item. Blocks while the buffer is empty.
        Returns None if the timeout elapsed.
        Raises QueueClosed if the buffer is closed and empty.
        """
        with self._lock:
            def can_get() -> bool:
            
                if self._closed and not self._q:
                    return True  
                return bool(self._q)

            if not can_get():
                if not self._wait_until(can_get, timeout):
                    return None

            if self._closed and not self._q:
                raise QueueClosed("Buffer is closed")

            item = self._q.popleft()
            
            self._not_full.notify()
            return item

    def task_done(self) -> None:
        """
        Indicate that a previously enqueued task is complete.
        Must be called once for each item removed by get().
        """
        with self._lock:
            if self._unfinished_tasks <= 0:
                raise ValueError("task_done() called too many times")
            self._unfinished_tasks -= 1
            if self._unfinished_tasks == 0:
                self._all_tasks_done.notify_all()

    def join(self) -> None:
        """
        Block until all items put into the buffer have been processed
        (i.e., until unfinished_tasks drops to zero).
        """
        with self._lock:
            while self._unfinished_tasks:
                self._all_tasks_done.wait()

    def close(self) -> None:
        """
        Close the buffer. After closing:
          - put() raises QueueClosed
          - get() raises QueueClosed once the buffer becomes empty
          - waiting threads are notified
        """
        with self._lock:
            if not self._closed:
                self._closed = True
           
                self._not_empty.notify_all()
                self._not_full.notify_all()
                self._all_tasks_done.notify_all()


    def size(self) -> int:
        with self._lock:
            return len(self._q)

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._q) == 0

    def is_full(self) -> bool:
        with self._lock:
            return len(self._q) >= self._max

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        with self._lock:
            return (
                f"{self.__class__.__name__}(max_size={self._max}, "
                f"size={len(self._q)}, closed={self._closed}, "
                f"unfinished_tasks={self._unfinished_tasks})"
            )
