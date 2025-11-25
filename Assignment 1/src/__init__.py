"""
Producer-Consumer Pattern Implementation

A thread-safe implementation of the producer-consumer pattern with support
for multiple producers and consumers (N:M pattern).
"""

from .shared_buffer import SharedBuffer
from .producer import Producer
from .consumer import Consumer
from .system import ProducerConsumerSystem

__all__ = [
    'SharedBuffer',
    'Producer',
    'Consumer',
    'ProducerConsumerSystem',
]
