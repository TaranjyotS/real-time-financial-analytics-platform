from app.core.database import SessionLocal
from app.kafka.consumer import EventConsumer
from app.kafka.topics import TRANSACTIONS_CREATED
from app.models.entities import Transaction
from app.services.fraud_service import FraudService


def handle(event: dict) -> None:
    db = SessionLocal()
    try:
        tx_id = event["payload"]["id"]
        tx = db.get(Transaction, tx_id)
        if tx:
            FraudService(db).evaluate_transaction(tx)
    finally:
        db.close()


if __name__ == "__main__":
    EventConsumer("fraud-service", [TRANSACTIONS_CREATED]).consume_forever(handle)
