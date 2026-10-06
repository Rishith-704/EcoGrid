import time
from datetime import datetime

from ecogrid.meter_ingestion.ingestion import MeterIngestionService
from ecogrid.meter_ingestion.models import MeterReading
from ecogrid.meter_ingestion.publisher import ReadingPublisher
from ecogrid.shared.event_bus import EventBus
from ecogrid.shared.events import MeterReadingReceived

READING_COUNT = 10_000
MAX_P95_LATENCY_SECONDS = 0.005
MIN_READINGS_PER_SECOND = 5_000


def run_burst():
    """Ingest a burst of readings and return (latencies, total_seconds)."""
    bus = EventBus()
    received = []
    bus.subscribe(MeterReadingReceived, received.append)
    service = MeterIngestionService(ReadingPublisher(bus))

    latencies = []
    start = time.perf_counter()
    for i in range(READING_COUNT):
        reading = MeterReading(f"meter-{i}", f"house-{i}", 5.0, 2.0, datetime.now())
        before = time.perf_counter()
        service.ingest(reading)
        latencies.append(time.perf_counter() - before)
    total_seconds = time.perf_counter() - start

    assert service.accepted_count == READING_COUNT
    assert len(received) == READING_COUNT
    return latencies, total_seconds


def test_p95_ingestion_latency_is_under_limit():
    latencies, _ = run_burst()

    p95 = sorted(latencies)[int(len(latencies) * 0.95)]

    assert p95 < MAX_P95_LATENCY_SECONDS, f"p95 latency was {p95 * 1000:.3f} ms"


def test_ingestion_throughput_is_above_minimum():
    _, total_seconds = run_burst()

    readings_per_second = READING_COUNT / total_seconds

    assert readings_per_second >= MIN_READINGS_PER_SECOND, (
        f"throughput was {readings_per_second:.0f} readings/s"
    )