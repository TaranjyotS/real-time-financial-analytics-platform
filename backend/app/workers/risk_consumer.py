from app.core.database import SessionLocal
from app.kafka.consumer import EventConsumer
from app.kafka.topics import PORTFOLIO_UPDATED
from app.services.risk_service import RiskService


def handle(event: dict) -> None:
    db = SessionLocal()
    try:
        portfolio_id = event["payload"].get("portfolio_id")
        if portfolio_id:
            RiskService(db).calculate_portfolio_risk(int(portfolio_id))
    finally:
        db.close()


if __name__ == "__main__":
    EventConsumer("risk-service", [PORTFOLIO_UPDATED]).consume_forever(handle)
