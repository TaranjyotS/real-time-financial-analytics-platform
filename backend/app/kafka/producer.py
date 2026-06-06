import json
import uuid
from datetime import datetime
from confluent_kafka import Producer
from app.core.config import get_settings

settings = get_settings()


class EventProducer:
    def __init__(self) -> None:
        self._producer = Producer(
            {"bootstrap.servers": settings.kafka_bootstrap_servers}
        )

    def publish(self, topic: str, event_type: str, payload: dict) -> dict:
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "event_time": datetime.utcnow().isoformat(),
            "payload": payload,
        }
        self._producer.produce(topic, json.dumps(event).encode("utf-8"))
        self._producer.flush(5)
        return event
