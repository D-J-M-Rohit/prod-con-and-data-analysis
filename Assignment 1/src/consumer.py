"""
Consumer Module

Implements the consumer thread that reads items from a shared buffer
and stores them in a destination container (thread-safe via a shared lock).
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, List

from .shared_buffer import SharedBuffer


class Consumer(threading.Thread):
    """
    Consumer thread that reads items from a shared buffer and appends them
    to a shared destination list.

    Features:
        - Graceful shutdown via a poison-pill sentinel (POISON_PILL).
        - Respect for a cooperative stop_event.
        - Destination writes protected by a shared lock to avoid races.
        - Per-thread consumption statistics.

    Attributes:
        consumer_id: Unique identifier for this consumer.
        destination: Shared list to store consumed items.
        destination_lock: Shared lock guarding writes to destination.
        shared_buffer: The shared bounded buffer to consume from.
        stop_event: Event used to signal cooperative shutdown.
        consumption_delay: Optional delay to simulate processing.
        items_consumed: Number of successfully consumed items.
    """

    # Poison pill sentinel to signal consumer shutdown.
    POISON_PILL = object()

    def __init__(
        self,
        consumer_id: int,
        destination: List[Any],
        destination_lock: threading.Lock,
        shared_buffer: SharedBuffer,
        stop_event: threading.Event,
        consumption_delay: float = 0.01,
    ) -> None:
        """
        Initialize the consumer thread.

        Args:
            consumer_id: Unique identifier for this consumer.
            destination: Shared list to store consumed items.
            destination_lock: Shared lock to protect destination writes.
            shared_buffer: Shared buffer to get items from.
            stop_event: Event to signal thread shutdown.
            consumption_delay: Delay between consuming items (simulates work).
        """
        super().__init__(name=f"Consumer-{consumer_id}")
        self.consumer_id = consumer_id
        self.destination = destination
        self.destination_lock = destination_lock  
        self.shared_buffer = shared_buffer
        self.stop_event = stop_event
        self.consumption_delay = consumption_delay
        self.items_consumed = 0

        self._log = logging.getLogger(__name__)

    def run(self) -> None:
        """
        Main execution loop for the consumer thread.

        Continuously retrieves items from the shared buffer and stores them
        in the destination list. Handles poison pills for graceful shutdown
        and respects the stop event. Uses a shared lock to ensure thread-safe
        writes to the destination list.
        """
        self._log.info("Consumer %s started", self.consumer_id)

        try:
            while not self.stop_event.is_set():
                item = self.shared_buffer.get(timeout=1.0)

                if item is None:
                    continue

                if item is self.POISON_PILL:
                    self._log.info("Consumer %s received poison pill", self.consumer_id)
                    self.shared_buffer.task_done()
                    break

                if self.consumption_delay > 0:
                    time.sleep(self.consumption_delay)

                with self.destination_lock:
                    self.destination.append(item)

                self.items_consumed += 1
                self._log.info(
                    "Consumer %s consumed: %r (total: %d)",
                    self.consumer_id,
                    item,
                    self.items_consumed,
                )

                self.shared_buffer.task_done()

        except Exception as exc:
            self._log.error(
                "Consumer %s encountered an error: %s",
                self.consumer_id,
                exc,
                exc_info=True,
            )
        finally:
            self._log.info(
                "Consumer %s finished. Total items consumed: %d",
                self.consumer_id,
                self.items_consumed,
            )
