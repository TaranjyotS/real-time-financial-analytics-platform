from sqlalchemy.orm import Session
from app.models.entities import Asset, Holding, MarketPrice, Portfolio
from app.schemas.schemas import PortfolioCreate, HoldingCreate


class PortfolioService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_portfolio(self, request: PortfolioCreate) -> Portfolio:
        portfolio = Portfolio(**request.model_dump())
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def add_holding(self, portfolio_id: int, request: HoldingCreate) -> Holding:
        holding = Holding(portfolio_id=portfolio_id, **request.model_dump())
        self.db.add(holding)
        self.db.commit()
        self.db.refresh(holding)
        return holding

    def calculate_value(self, portfolio_id: int) -> dict:
        holdings = self.db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
        total = 0.0
        details = []
        for holding in holdings:
            latest_price = (
                self.db.query(MarketPrice)
                .filter(MarketPrice.asset_id == holding.asset_id)
                .order_by(MarketPrice.event_time.desc())
                .first()
            )
            price = latest_price.price if latest_price else holding.average_price
            value = holding.quantity * price
            total += value
            asset = self.db.get(Asset, holding.asset_id)
            details.append({"symbol": asset.symbol if asset else holding.asset_id, "quantity": holding.quantity, "price": price, "value": value})
        return {"portfolio_id": portfolio_id, "total_value": round(total, 2), "holdings": details}
