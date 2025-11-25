"""
Integration tests for ProducerConsumerSystem.

These are OPTIONAL end-to-end tests and are NOT part of the required unit
test suite. They exercise complete system behavior across 1:1, N:1, 1:M,
and N:M topologies, including a high-contention case, and validate stats.
"""

from __future__ import annotations

import logging
import sys
import unittest
from typing import Any, List

# Allow "src" imports when running this file directly.
sys.path.insert(0, "..")

from src import ProducerConsumerSystem  # type: ignore


# Silence logs during tests to keep output clean.
logging.basicConfig(level=logging.CRITICAL)


class TestProducerConsumerSystem(unittest.TestCase):
    """Integration test cases for ProducerConsumerSystem."""

    def _assert_stats(
        self,
        system: ProducerConsumerSystem,
        *,
        num_producers: int,
        num_consumers: int,
        produced: int,
        consumed: int,
        items_in_transit: int = 0,
    ) -> None:
        stats = system.get_statistics()
        self.assertEqual(stats["num_producers"], num_producers)
        self.assertEqual(stats["num_consumers"], num_consumers)
        self.assertEqual(stats["total_produced"], produced)
        self.assertEqual(stats["total_consumed"], consumed)
        self.assertEqual(stats["items_in_transit"], items_in_transit)
        # Buffer should be empty at quiescence
        self.assertEqual(stats["buffer_size"], 0)

    def test_single_producer_single_consumer(self) -> None:
        """1 producer, 1 consumer; order preserved and counts match."""
        source = [f"item_{i}" for i in range(20)]
        destination: List[Any] = []

        system = ProducerConsumerSystem(buffer_size=5)
        system.add_producer(1, source, production_delay=0.001)
        system.add_consumer(1, destination, consumption_delay=0.001)

        system.start()
        system.shutdown_gracefully()

        self.assertEqual(destination, source)
        self._assert_stats(
            system,
            num_producers=1,
            num_consumers=1,
            produced=len(source),
            consumed=len(source),
        )

    def test_multiple_producers_single_consumer(self) -> None:
        """N producers, 1 consumer; all items delivered exactly once."""
        sources = [
            [f"P1-{i}" for i in range(10)],
            [f"P2-{i}" for i in range(10)],
            [f"P3-{i}" for i in range(10)],
        ]
        all_items = [x for src in sources for x in src]
        destination: List[Any] = []

        system = ProducerConsumerSystem(buffer_size=10)
        for i, src in enumerate(sources, start=1):
            system.add_producer(i, src, production_delay=0.001)
        system.add_consumer(1, destination, consumption_delay=0.001)

        system.start()
        system.shutdown_gracefully()

        self.assertEqual(len(destination), len(all_items))
        self.assertEqual(sorted(destination), sorted(all_items))
        self._assert_stats(
            system,
            num_producers=3,
            num_consumers=1,
            produced=30,
            consumed=30,
        )

    def test_single_producer_multiple_consumers(self) -> None:
        """1 producer, M consumers; all items delivered exactly once."""
        source = [f"item_{i}" for i in range(30)]
        destination: List[Any] = []

        system = ProducerConsumerSystem(buffer_size=10)
        system.add_producer(1, source, production_delay=0.001)
        for i in range(3):
            system.add_consumer(i + 1, destination, consumption_delay=0.001)

        system.start()
        system.shutdown_gracefully()

        self.assertEqual(len(destination), len(source))
        self.assertEqual(sorted(destination), sorted(source))
        self._assert_stats(
            system,
            num_producers=1,
            num_consumers=3,
            produced=30,
            consumed=30,
        )

    def test_multiple_producers_multiple_consumers(self) -> None:
        """N producers, M consumers; N:M with balanced throughput."""
        sources = [
            [f"P1-{i}" for i in range(15)],
            [f"P2-{i}" for i in range(15)],
            [f"P3-{i}" for i in range(15)],
        ]
        all_items = [x for src in sources for x in src]
        destination: List[Any] = []

        system = ProducerConsumerSystem(buffer_size=10)
        for i, src in enumerate(sources, start=1):
            system.add_producer(i, src, production_delay=0.001)
        for i in range(2):
            system.add_consumer(i + 1, destination, consumption_delay=0.001)

        system.start()
        system.shutdown_gracefully()

        self.assertEqual(len(destination), len(all_items))
        self.assertEqual(sorted(destination), sorted(all_items))
        self._assert_stats(
            system,
            num_producers=3,
            num_consumers=2,
            produced=45,
            consumed=45,
            items_in_transit=0,
        )

    def test_high_contention_scenario(self) -> None:
        """Stress case: many producers/consumers, tiny buffer; no loss/dup."""
        sources = [[f"P{i}-{j}" for j in range(20)] for i in range(5)]  # 100 items
        all_items = [x for src in sources for x in src]
        destination: List[Any] = []

        system = ProducerConsumerSystem(buffer_size=3)  # Deliberately small
        for i, src in enumerate(sources, start=1):
            system.add_producer(i, src, production_delay=0.001)
        for i in range(4):
            system.add_consumer(i + 1, destination, consumption_delay=0.001)

        system.start()
        system.shutdown_gracefully()

        self.assertEqual(len(destination), len(all_items))
        self.assertEqual(sorted(destination), sorted(all_items))
        self._assert_stats(
            system,
            num_producers=5,
            num_consumers=4,
            produced=100,
            consumed=100,
        )

    def test_empty_source(self) -> None:
        """Empty source yields empty destination and zero counts."""
        destination: List[Any] = []

        system = ProducerConsumerSystem(buffer_size=5)
        system.add_producer(1, [], production_delay=0.001)
        system.add_consumer(1, destination, consumption_delay=0.001)

        system.start()
        system.shutdown_gracefully()

        self.assertEqual(destination, [])
        self._assert_stats(
            system,
            num_producers=1,
            num_consumers=1,
            produced=0,
            consumed=0,
        )

    def test_no_lost_items(self) -> None:
        """Repeat small fast run; ensure every item appears exactly once."""
        for _ in range(3):
            source = list(range(50))
            destination: List[Any] = []

            system = ProducerConsumerSystem(buffer_size=5)
            system.add_producer(1, source, production_delay=0.0001)
            system.add_consumer(1, destination, consumption_delay=0.0001)

            system.start()
            system.shutdown_gracefully()

            self.assertEqual(len(destination), len(source))
            self.assertEqual(sorted(destination), sorted(source))
            self._assert_stats(
                system,
                num_producers=1,
                num_consumers=1,
                produced=50,
                consumed=50,
            )

    def test_no_duplicate_items(self) -> None:
        """Two consumers reading shared queue must not duplicate items."""
        source = list(range(50))
        destination: List[Any] = []

        system = ProducerConsumerSystem(buffer_size=10)
        system.add_producer(1, source, production_delay=0.001)
        system.add_consumer(1, destination, consumption_delay=0.001)
        system.add_consumer(2, destination, consumption_delay=0.001)

        system.start()
        system.shutdown_gracefully()

        self.assertEqual(len(destination), len(set(destination)))
        self.assertEqual(len(destination), len(source))
        self._assert_stats(
            system,
            num_producers=1,
            num_consumers=2,
            produced=50,
            consumed=50,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
