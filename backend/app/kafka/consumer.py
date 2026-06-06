import json
from confluent_kafka import Consumer, KafkaException
from app.core.config import get_settings

settings = get_settings()


class EventConsumer:
    def __init__(self, group_id: str, topics: list[str]) -> None:
        self.consumer = Consumer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        self.consumer.subscribe(topics)

    def consume_forever(self, handler):
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())
                event = json.loads(msg.value().decode("utf-8"))
                handler(event)
                self.consumer.commit(msg)
        finally:
            self.consumer.close()
