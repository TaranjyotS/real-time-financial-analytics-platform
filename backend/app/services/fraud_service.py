from sqlalchemy.orm import Session
from app.models.entities import Alert, AlertSeverity, Transaction


class FraudService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def evaluate_transaction(self, transaction: Transaction) -> list[Alert]:
        alerts: list[Alert] = []
        if transaction.amount >= 10000:
            alerts.append(
                Alert(
                    user_id=transaction.user_id,
                    portfolio_id=transaction.portfolio_id,
                    alert_type="fraud",
                    severity=AlertSeverity.high,
                    message=f"High-value transaction detected: {transaction.amount}",
                )
            )
        recent_count = (
            self.db.query(Transaction)
            .filter(Transaction.user_id == transaction.user_id)
            .count()
        )
        if recent_count > 20:
            alerts.append(
                Alert(
                    user_id=transaction.user_id,
                    portfolio_id=transaction.portfolio_id,
                    alert_type="fraud",
                    severity=AlertSeverity.medium,
                    message="Elevated transaction frequency detected",
                )
            )
        for alert in alerts:
            self.db.add(alert)
        self.db.commit()
        return alerts
