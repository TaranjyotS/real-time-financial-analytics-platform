from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "viewer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PortfolioCreate(BaseModel):
    user_id: int
    name: str
    base_currency: str = "USD"


class PortfolioRead(BaseModel):
    id: int
    user_id: int
    name: str
    base_currency: str
    created_at: datetime
    model_config = {"from_attributes": True}


class AssetCreate(BaseModel):
    symbol: str
    asset_type: str = "equity"
    exchange: str = "SIM"
    currency: str = "USD"


class HoldingCreate(BaseModel):
    asset_id: int
    quantity: float
    average_price: float


class TransactionCreate(BaseModel):
    id: str
    user_id: int
    portfolio_id: int
    asset_id: int | None = None
    transaction_type: str
    quantity: float = 0
    price: float = 0
    amount: float
    currency: str = "USD"


class TransactionRead(TransactionCreate):
    status: str
    anomaly_score: float
    created_at: datetime
    model_config = {"from_attributes": True}


class MarketPriceCreate(BaseModel):
    symbol: str
    price: float
    source: str = "simulator"


class AlertRead(BaseModel):
    id: int
    alert_type: str
    severity: str
    message: str
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class AnomalyScoreRequest(BaseModel):
    amount: float
    quantity: float = 0
    price: float = 0
    hour_of_day: int = 12
    account_age_days: int = 365


class AnomalyScoreResponse(BaseModel):
    anomaly_score: float
    is_anomaly: bool
