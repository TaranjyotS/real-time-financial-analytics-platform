from sqlalchemy.orm import Session
from app.kafka.producer import EventProducer
from app.kafka.topics import TRANSACTIONS_CREATED
from app.models.entities import Transaction
from app.schemas.schemas import TransactionCreate


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.producer = EventProducer()

    def create_transaction(self, request: TransactionCreate) -> Transaction:
        existing = self.db.get(Transaction, request.id)
        if existing:
            return existing
        transaction = Transaction(**request.model_dump(), status="created")
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        self.producer.publish(TRANSACTIONS_CREATED, "transaction.created", request.model_dump())
        return transaction
