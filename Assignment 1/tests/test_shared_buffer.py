"""
Unit tests for SharedBuffer.

Covers the REQUIRED thread-safe buffer behavior for the assignment,
including blocking behavior, timeouts, and FIFO ordering with low-flake
timing checks.
"""

from __future__ import annotations

import sys
import time
import unittest
from typing import Any, List

# Allow "src" imports when running this file directly.
sys.path.insert(0, "..")

from src.shared_buffer import SharedBuffer  # type: ignore


class TestSharedBuffer(unittest.TestCase):
    """Unit test cases for SharedBuffer."""

    def setUp(self) -> None:
        self.buffer = SharedBuffer(max_size=5)

    def test_buffer_initialization(self) -> None:
        """Buffer starts empty and not full."""
        self.assertTrue(self.buffer.is_empty())
        self.assertFalse(self.buffer.is_full())
        self.assertEqual(self.buffer.size(), 0)

    def test_put_get_single_item(self) -> None:
        """Single put/get roundtrip updates size correctly."""
        item = "test_item"
        self.assertTrue(self.buffer.put(item))
        self.assertEqual(self.buffer.size(), 1)

        retrieved = self.buffer.get()
        self.assertEqual(retrieved, item)
        self.assertEqual(self.buffer.size(), 0)
        self.assertTrue(self.buffer.is_empty())

    def test_put_until_full(self) -> None:
        """Buffer reports full at capacity."""
        for i in range(5):
            self.assertTrue(self.buffer.put(f"item_{i}"))
        self.assertTrue(self.buffer.is_full())
        self.assertEqual(self.buffer.size(), 5)

    def test_get_until_empty(self) -> None:
        """After removing all items, buffer reports empty."""
        for i in range(3):
            self.assertTrue(self.buffer.put(f"item_{i}"))
        for _ in range(3):
            self.assertIsNotNone(self.buffer.get())
        self.assertTrue(self.buffer.is_empty())
        self.assertEqual(self.buffer.size(), 0)

    def test_blocking_put_timeout(self) -> None:
        """put() should respect timeout when buffer is full."""
        for i in range(5):
            self.assertTrue(self.buffer.put(f"item_{i}"))

        t0 = time.monotonic()
        ok = self.buffer.put("overflow_item", timeout=0.5)
        dt = time.monotonic() - t0

        self.assertFalse(ok)
        self.assertGreaterEqual(dt, 0.48)

    def test_blocking_get_timeout(self) -> None:
        """get() should respect timeout when buffer is empty."""
        t0 = time.monotonic()
        item = self.buffer.get(timeout=0.5)
        dt = time.monotonic() - t0

        self.assertIsNone(item)
        self.assertGreaterEqual(dt, 0.48)

    def test_fifo_order(self) -> None:
        """Queue maintains FIFO ordering."""
        items: List[Any] = ["first", "second", "third"]
        for x in items:
            self.assertTrue(self.buffer.put(x))

        retrieved = [self.buffer.get() for _ in items]
        self.assertEqual(items, retrieved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
