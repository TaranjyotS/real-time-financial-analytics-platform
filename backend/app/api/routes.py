from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.ml.anomaly_model import AnomalyDetector
from app.models.entities import Alert, Asset, MarketPrice, Transaction, User
from app.schemas.schemas import (
    AnomalyScoreRequest,
    AnomalyScoreResponse,
    AssetCreate,
    HoldingCreate,
    MarketPriceCreate,
    PortfolioCreate,
    PortfolioRead,
    TokenResponse,
    TransactionCreate,
    TransactionRead,
    UserCreate,
)
from app.services.fraud_service import FraudService
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/v1")
anomaly_detector = AnomalyDetector()


@router.post("/auth/register")
def register(request: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        role=request.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/auth/login", response_model=TokenResponse)
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user.email, str(user.role.value))
    )


@router.post("/assets")
def create_asset(request: AssetCreate, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.symbol == request.symbol).first()
    if asset:
        return asset
    asset = Asset(**request.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.post("/portfolios", response_model=PortfolioRead)
def create_portfolio(request: PortfolioCreate, db: Session = Depends(get_db)):
    return PortfolioService(db).create_portfolio(request)


@router.post("/portfolios/{portfolio_id}/holdings")
def add_holding(
    portfolio_id: int, request: HoldingCreate, db: Session = Depends(get_db)
):
    return PortfolioService(db).add_holding(portfolio_id, request)


@router.get("/portfolios/{portfolio_id}/performance")
def get_portfolio_performance(portfolio_id: int, db: Session = Depends(get_db)):
    return PortfolioService(db).calculate_value(portfolio_id)


@router.post("/transactions", response_model=TransactionRead)
def create_transaction(request: TransactionCreate, db: Session = Depends(get_db)):
    transaction = TransactionService(db).create_transaction(request)
    FraudService(db).evaluate_transaction(transaction)
    return transaction


@router.get("/transactions")
def list_transactions(db: Session = Depends(get_db)):
    return (
        db.query(Transaction).order_by(Transaction.created_at.desc()).limit(100).all()
    )


@router.post("/market/prices")
def create_market_price(request: MarketPriceCreate, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.symbol == request.symbol).first()
    if not asset:
        asset = Asset(
            symbol=request.symbol, asset_type="equity", exchange="SIM", currency="USD"
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
    price = MarketPrice(asset_id=asset.id, price=request.price, source=request.source)
    db.add(price)
    db.commit()
    db.refresh(price)
    return {
        "symbol": request.symbol,
        "price": request.price,
        "event_time": price.event_time,
    }


@router.get("/risk/portfolio/{portfolio_id}")
def get_risk(portfolio_id: int, db: Session = Depends(get_db)):
    return RiskService(db).calculate_portfolio_risk(portfolio_id)


@router.get("/alerts")
def list_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.created_at.desc()).limit(100).all()


@router.post("/anomaly/score", response_model=AnomalyScoreResponse)
def score_anomaly(request: AnomalyScoreRequest):
    score, is_anomaly = anomaly_detector.score(
        [
            request.amount,
            request.quantity,
            request.price,
            request.hour_of_day,
            request.account_age_days,
        ]
    )
    return AnomalyScoreResponse(anomaly_score=score, is_anomaly=is_anomaly)
