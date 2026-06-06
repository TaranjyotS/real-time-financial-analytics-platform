import json, logging
from confluent_kafka import Producer
from app.core.config import settings
logger=logging.getLogger(__name__)

producer=None

def get_producer():
    global producer
    if producer is None:
        producer=Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    return producer

def publish(topic:str, payload:dict):
    try:
        p=get_producer(); p.produce(topic, json.dumps(payload).encode("utf-8")); p.poll(0)
    except Exception as exc:
        logger.warning("Kafka publish skipped: %s", exc)
