import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    portfolio_manager = "portfolio_manager"
    viewer = "viewer"


class TransactionType(str, enum.Enum):
    buy = "buy"
    sell = "sell"
    deposit = "deposit"
    withdrawal = "withdrawal"


class AlertSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.viewer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    portfolios = relationship("Portfolio", back_populates="user")


class Portfolio(Base):
    __tablename__ = "portfolios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    base_currency: Mapped[str] = mapped_column(String(10), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio")


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    exchange: Mapped[str] = mapped_column(String(50), default="SIM")
    currency: Mapped[str] = mapped_column(String(10), default="USD")


class Holding(Base):
    __tablename__ = "holdings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    average_price: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    portfolio = relationship("Portfolio", back_populates="holdings")
    asset = relationship("Asset")


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    quantity: Mapped[float] = mapped_column(Float, default=0)
    price: Mapped[float] = mapped_column(Float, default=0)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    status: Mapped[str] = mapped_column(String(50), default="created")
    anomaly_score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketPrice(Base):
    __tablename__ = "market_prices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    price: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(50), default="simulator")
    event_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RiskMetric(Base):
    __tablename__ = "risk_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    volatility_score: Mapped[float] = mapped_column(Float)
    concentration_score: Mapped[float] = mapped_column(Float)
    drawdown_score: Mapped[float] = mapped_column(Float)
    total_exposure: Mapped[float] = mapped_column(Float)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    portfolio_id: Mapped[int | None] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EventAuditLog(Base):
    __tablename__ = "event_audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(100), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    topic: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
