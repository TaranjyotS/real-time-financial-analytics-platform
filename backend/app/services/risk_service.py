from sqlalchemy.orm import Session
from app.models.entities import Alert, AlertSeverity, Holding, RiskMetric


class RiskService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def calculate_portfolio_risk(self, portfolio_id: int) -> RiskMetric:
        holdings = self.db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
        total_exposure = sum(h.quantity * h.average_price for h in holdings)
        largest = max((h.quantity * h.average_price for h in holdings), default=0)
        concentration_score = largest / total_exposure if total_exposure else 0
        volatility_score = min(1.0, 0.15 + concentration_score * 0.6)
        drawdown_score = min(1.0, volatility_score * 0.75)
        metric = RiskMetric(
            portfolio_id=portfolio_id,
            volatility_score=volatility_score,
            concentration_score=concentration_score,
            drawdown_score=drawdown_score,
            total_exposure=total_exposure,
        )
        self.db.add(metric)
        if concentration_score > 0.6:
            self.db.add(Alert(portfolio_id=portfolio_id, alert_type="risk", severity=AlertSeverity.high, message="Portfolio concentration risk exceeds threshold"))
        self.db.commit()
        self.db.refresh(metric)
        return metric
