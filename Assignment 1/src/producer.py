"""
Producer Module

Implements the producer thread that reads items from a source
and places them into a shared buffer.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, List

from .shared_buffer import SharedBuffer


class Producer(threading.Thread):
    """
    Producer thread that reads items from a source and enqueues them
    into a shared bounded buffer.

    Features:
        - Respects a cooperative stop_event for early shutdown.
        - Optional production_delay to simulate work per item.
        - Lossless under contention via retry loop on buffer.put().
        - Per-thread production statistics.

    Attributes:
        producer_id: Unique identifier for this producer.
        source: List of items to produce.
        shared_buffer: Shared buffer to place items into.
        stop_event: Event to signal thread shutdown.
        production_delay: Delay between producing items.
        items_produced: Counter for successfully produced items.
    """

    def __init__(
        self,
        producer_id: int,
        source: List[Any],
        shared_buffer: SharedBuffer,
        stop_event: threading.Event,
        production_delay: float = 0.01,
    ) -> None:
        """
        Initialize the producer thread.

        Args:
            producer_id: Unique identifier for this producer.
            source: List of items to produce.
            shared_buffer: Shared buffer to place items into.
            stop_event: Event to signal thread shutdown.
            production_delay: Delay between producing items (simulates work).
        """
        super().__init__(name=f"Producer-{producer_id}")
        self.producer_id = producer_id
        self.source = source
        self.shared_buffer = shared_buffer
        self.stop_event = stop_event
        self.production_delay = production_delay
        self.items_produced = 0

        self._log = logging.getLogger(__name__)

    def run(self) -> None:
        """
        Main execution loop for the producer thread.

        Iterates the source, optionally sleeps to simulate work, then attempts
        to enqueue each item. If the buffer is full, retries until successful
        or until stop_event is set (prevents data loss under contention).
        """
        self._log.info("Producer %s started", self.producer_id)

        try:
            for item in self.source:
                if self.stop_event.is_set():
                    self._log.info("Producer %s stopping early", self.producer_id)
                    break

                if self.production_delay > 0:
                    time.sleep(self.production_delay)

                while not self.stop_event.is_set():
                    if self.shared_buffer.put(item, timeout=0.5):
                        self.items_produced += 1
                        self._log.info(
                            "Producer %s produced: %r (total: %d)",
                            self.producer_id,
                            item,
                            self.items_produced,
                        )
                        break 

                    self._log.debug(
                        "Producer %s retrying put for: %r", self.producer_id, item
                    )

                if self.stop_event.is_set():
                    self._log.info(
                        "Producer %s stopping during retry loop", self.producer_id
                    )
                    break

        except Exception as exc:
            self._log.error(
                "Producer %s encountered an error: %s",
                self.producer_id,
                exc,
                exc_info=True,
            )
        finally:
            self._log.info(
                "Producer %s finished. Total items produced: %d",
                self.producer_id,
                self.items_produced,
            )
