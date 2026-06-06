import random
from datetime import datetime, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import Session
import hashlib
import secrets
from app import models


# Local-demo password hashing intentionally avoids bcrypt/passlib version issues in Docker.
# Format: pbkdf2_sha256$<salt_hex>$<hash_hex>
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = stored_hash.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 120_000
        )
        return secrets.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def anomaly_score(amount: float, quantity: float, price: float, freq: int = 1) -> float:
    score = 0.0
    if amount > 25000:
        score += 0.35
    if amount > 100000:
        score += 0.25
    if freq > 8:
        score += 0.20
    if quantity > 1000:
        score += 0.10
    if price <= 0:
        score += 0.10
    return min(round(score + random.uniform(0.01, 0.08), 3), 0.99)


def fraud_flags(tx: models.Transaction) -> list[tuple[str, str]]:
    flags = []
    if tx.amount >= 100000:
        flags.append(("critical", f"High-value transaction ${tx.amount:,.2f}"))
    elif tx.amount >= 25000:
        flags.append(("high", f"Large transaction ${tx.amount:,.2f}"))
    if tx.anomaly_score >= 0.75:
        flags.append(("high", f"ML anomaly score {tx.anomaly_score}"))
    return flags


def latest_price(db: Session, asset_id: int, fallback: float = 100.0) -> float:
    row = (
        db.query(models.MarketPrice)
        .filter_by(asset_id=asset_id)
        .order_by(desc(models.MarketPrice.event_time))
        .first()
    )
    return row.price if row else fallback


def portfolio_value(db: Session, portfolio_id: int) -> float:
    total = 0.0
    for h in db.query(models.Holding).filter_by(portfolio_id=portfolio_id).all():
        total += h.quantity * latest_price(db, h.asset_id, h.average_price)
    return round(total, 2)


def calculate_risk(db: Session, portfolio_id: int) -> models.RiskMetric:
    holdings = db.query(models.Holding).filter_by(portfolio_id=portfolio_id).all()
    values = [
        h.quantity * latest_price(db, h.asset_id, h.average_price) for h in holdings
    ]
    total = sum(values) or 1.0
    concentration = max(values) / total if values else 0
    volatility = min(0.95, 0.10 + concentration * 0.55 + random.random() * 0.12)
    drawdown = min(0.80, volatility * 0.45 + random.random() * 0.05)
    metric = models.RiskMetric(
        portfolio_id=portfolio_id,
        volatility_score=round(volatility, 3),
        concentration_score=round(concentration, 3),
        drawdown_score=round(drawdown, 3),
        total_exposure=round(total, 2),
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    if concentration > 0.55:
        db.add(
            models.Alert(
                user_id=1,
                portfolio_id=portfolio_id,
                alert_type="RISK",
                severity="medium",
                message=f"Portfolio concentration risk is {concentration:.0%}",
            )
        )
        db.commit()
    return metric


def seed_demo(db: Session):
    if db.query(models.User).first():
        return
    user = models.User(
        email="demo@finanalytics.local",
        hashed_password=hash_password("demo123"),
        role="admin",
    )
    db.add(user)
    db.flush()
    assets = [
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft"),
        ("NVDA", "NVIDIA"),
        ("AMZN", "Amazon"),
        ("TSLA", "Tesla"),
        ("JPM", "JPMorgan Chase"),
    ]
    objs = []
    for sym, name in assets:
        a = models.Asset(symbol=sym, name=name)
        db.add(a)
        objs.append(a)
    db.flush()
    pf = models.Portfolio(
        user_id=user.id, name="Growth & Risk Analytics Portfolio", base_currency="USD"
    )
    db.add(pf)
    db.flush()
    prices = {
        "AAPL": 192.4,
        "MSFT": 421.1,
        "NVDA": 1105.2,
        "AMZN": 186.7,
        "TSLA": 178.4,
        "JPM": 204.6,
    }
    for a in objs:
        db.add(
            models.MarketPrice(asset_id=a.id, symbol=a.symbol, price=prices[a.symbol])
        )
        db.add(
            models.Holding(
                portfolio_id=pf.id,
                asset_id=a.id,
                quantity=random.randint(20, 130),
                average_price=prices[a.symbol] * random.uniform(0.75, 0.95),
            )
        )
    db.commit()
    for _ in range(35):
        a = random.choice(objs)
        price = prices[a.symbol] * random.uniform(0.96, 1.04)
        qty = random.randint(1, 80)
        amount = qty * price
        sc = anomaly_score(amount, qty, price, random.randint(1, 12))
        tx = models.Transaction(
            user_id=user.id,
            portfolio_id=pf.id,
            asset_id=a.id,
            transaction_type=random.choice(["BUY", "SELL"]),
            quantity=qty,
            price=round(price, 2),
            amount=round(amount, 2),
            status="processed",
            anomaly_score=sc,
            created_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 360)),
        )
        db.add(tx)
        db.flush()
        for sev, msg in fraud_flags(tx):
            db.add(
                models.Alert(
                    user_id=user.id,
                    portfolio_id=pf.id,
                    alert_type="FRAUD",
                    severity=sev,
                    message=msg,
                )
            )
    db.commit()
    calculate_risk(db, pf.id)
