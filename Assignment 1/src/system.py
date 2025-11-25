"""
Producer-Consumer System Module

Orchestrates the producer-consumer system, managing thread lifecycle
and providing clean shutdown mechanisms.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, List

from .shared_buffer import SharedBuffer
from .producer import Producer
from .consumer import Consumer

_log = logging.getLogger(__name__)


class ProducerConsumerSystem:
    """
    Orchestrates the producer-consumer system.

    Responsibilities:
        - Lifecycle management for producer/consumer threads
        - Coordinated, lossless shutdown (graceful mode)
        - Aggregated system statistics

    Attributes:
        shared_buffer: The shared bounded buffer instance.
        stop_event: Event to signal cooperative shutdown to all threads.
        destination_lock: Shared lock to guard the shared destination list.
        producers: List of producer threads.
        consumers: List of consumer threads.
    """

    def __init__(self, buffer_size: int = 10) -> None:
        """
        Initialize the producer-consumer system.

        Args:
            buffer_size: Maximum size of the shared buffer (must be > 0).
        """
        self.shared_buffer = SharedBuffer(max_size=buffer_size)
        self.stop_event = threading.Event()
        self.destination_lock = threading.Lock()  # Shared lock for destination list
        self.producers: List[Producer] = []
        self.consumers: List[Consumer] = []

    def add_producer(
        self,
        producer_id: int,
        source: List[Any],
        production_delay: float = 0.01,
    ) -> Producer:
        """
        Add a producer to the system.

        Args:
            producer_id: Unique identifier for the producer.
            source: Items for the producer to emit into the buffer.
            production_delay: Optional delay between productions (simulate work).

        Returns:
            The created Producer instance (not yet started).
        """
        producer = Producer(
            producer_id=producer_id,
            source=source,
            shared_buffer=self.shared_buffer,
            stop_event=self.stop_event,
            production_delay=production_delay,
        )
        self.producers.append(producer)
        return producer

    def add_consumer(
        self,
        consumer_id: int,
        destination: List[Any],
        consumption_delay: float = 0.01,
    ) -> Consumer:
        """
        Add a consumer to the system.

        Args:
            consumer_id: Unique identifier for the consumer.
            destination: Shared list to store consumed items.
            consumption_delay: Optional delay between consumptions (simulate work).

        Returns:
            The created Consumer instance (not yet started).
        """
        consumer = Consumer(
            consumer_id=consumer_id,
            destination=destination,
            destination_lock=self.destination_lock,
            shared_buffer=self.shared_buffer,
            stop_event=self.stop_event,
            consumption_delay=consumption_delay,
        )
        self.consumers.append(consumer)
        return consumer

    def start(self) -> None:
        """
        Start all producer and consumer threads.

        Note:
            Consumers are started first so they are ready to receive items.
        """
        _log.info("Starting producer-consumer system")

        # Start consumers first to be ready for items
        for consumer in self.consumers:
            consumer.start()

        # Start producers
        for producer in self.producers:
            producer.start()

    def wait_for_producers(self) -> None:
        """
        Block until all producers have finished emitting items.
        """
        for producer in self.producers:
            producer.join()
        _log.info("All producers finished")

    def shutdown_gracefully(self) -> None:
        """
        Gracefully shut down the system without losing items.

        Sequence:
            1) Wait for all producers to finish.
            2) Drain the buffer (wait until all produced items are processed).
            3) Send a poison pill per consumer to terminate them.
            4) Wait until all poison pills are consumed (prevents thread join from stalling)
            4) Wait for all consumers to finish.

        This guarantees no items are lost and all in-flight work completes.
        """
        _log.info("Initiating graceful shutdown")
        self.wait_for_producers()
        _log.debug("Waiting for buffer to drain via join()")
        self.shared_buffer.join()

        for _ in self.consumers:
            while not self.shared_buffer.put(Consumer.POISON_PILL, timeout=0.5):
                _log.debug("Retrying poison-pill enqueue...")
        
        self.shared_buffer.join()
        for consumer in self.consumers:
            consumer.join()

        _log.info("System shutdown complete")

    def shutdown_forcefully(self) -> None:
        """
        Forcefully shut down the system.

        Sets the stop event and joins threads with a timeout. This may result in
        some items not being processed and should be used only for emergencies.
        """
        _log.info("Initiating forceful shutdown")
        self.stop_event.set()

        timeout = 5.0
        for producer in self.producers:
            producer.join(timeout=timeout)

        for consumer in self.consumers:
            consumer.join(timeout=timeout)

        _log.info("Forceful shutdown complete")

    def get_statistics(self) -> dict:
        """
        Return aggregated system statistics.

        Returns:
            Dictionary containing:
                - num_producers: Number of producer threads.
                - num_consumers: Number of consumer threads.
                - total_produced: Total items produced across all producers.
                - total_consumed: Total items consumed across all consumers.
                - buffer_size: Current buffer occupancy.
                - items_in_transit: Produced minus consumed (>= 0 during runtime).
        """
        total_produced = sum(p.items_produced for p in self.producers)
        total_consumed = sum(c.items_consumed for c in self.consumers)

        return {
            "num_producers": len(self.producers),
            "num_consumers": len(self.consumers),
            "total_produced": total_produced,
            "total_consumed": total_consumed,
            "buffer_size": self.shared_buffer.size(),
            "items_in_transit": total_produced - total_consumed,
        }
