from src.system import ProducerConsumerSystem
import logging


def main():
    # Enable simple, clean logs so we can see what is produced/consumed
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )

    destination = []

    # Create system with bounded buffer
    system = ProducerConsumerSystem(buffer_size=5)

    # Add producers
    system.add_producer(1, [f"P1-{i}" for i in range(10)], production_delay=0.01)
    system.add_producer(2, [f"P2-{i}" for i in range(10)], production_delay=0.01)
    system.add_producer(3, [f"P3-{i}" for i in range(10)], production_delay=0.01)

    # Add consumers
    system.add_consumer(1, destination, consumption_delay=0.02)
    system.add_consumer(2, destination, consumption_delay=0.02)
    
    # Start the system
    system.start()

    # Graceful shutdown after all producers finish
    system.shutdown_gracefully()

    print(f"Total items consumed: {len(destination)}")

    # Print final stats
    stats = system.get_statistics()
    print("Stats:", stats)

if __name__ == "__main__":
    main()
