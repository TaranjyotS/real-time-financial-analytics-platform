from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "analyst"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AssetCreate(BaseModel):
    symbol: str
    name: str
    asset_type: str = "equity"
    currency: str = "USD"


class PortfolioCreate(BaseModel):
    user_id: int = 1
    name: str
    base_currency: str = "USD"


class HoldingCreate(BaseModel):
    asset_id: int
    quantity: float
    average_price: float


class TransactionCreate(BaseModel):
    user_id: int = 1
    portfolio_id: int = 1
    asset_id: int
    transaction_type: str = "BUY"
    quantity: float
    price: float


class MarketPriceCreate(BaseModel):
    asset_id: int
    symbol: str
    price: float


class AnomalyScoreRequest(BaseModel):
    amount: float
    quantity: float
    price: float
    transaction_frequency_1h: int = 1
