import random, uuid
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.db import Base, engine, get_db, SessionLocal
from app import models, schemas
from app.services import seed_demo, verify_password, hash_password, anomaly_score, fraud_flags, calculate_risk, portfolio_value
from app.kafka_client import publish

app=FastAPI(title="real-time-financial-analytics-platform", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
REQUESTS=Counter("finanalytics_api_requests_total","API request count",["endpoint"])
LATENCY=Histogram("finanalytics_api_latency_seconds","API latency")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal(); seed_demo(db); db.close()

@app.get("/health")
def health(): REQUESTS.labels("health").inc(); return {"status":"healthy","service":"finanalytics-api"}
@app.get("/ready")
def ready(db:Session=Depends(get_db)): db.execute(models.User.__table__.select().limit(1)); return {"status":"ready"}
@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/auth/register")
def register(req:schemas.RegisterRequest, db:Session=Depends(get_db)):
    if db.query(models.User).filter_by(email=req.email).first(): raise HTTPException(409,"email exists")
    u=models.User(email=req.email, hashed_password=hash_password(req.password), role=req.role); db.add(u); db.commit(); db.refresh(u)
    return {"id":u.id,"email":u.email,"role":u.role}
@app.post("/api/v1/auth/login")
def login(req:schemas.LoginRequest, db:Session=Depends(get_db)):
    u=db.query(models.User).filter_by(email=req.email).first()
    if not u or not verify_password(req.password,u.hashed_password): raise HTTPException(401,"invalid credentials")
    return {"access_token":"demo-local-token","token_type":"bearer","user":{"id":u.id,"email":u.email,"role":u.role}}

@app.post("/api/v1/assets")
def create_asset(req:schemas.AssetCreate, db:Session=Depends(get_db)):
    a=models.Asset(**req.model_dump()); db.add(a); db.commit(); db.refresh(a); return a
@app.get("/api/v1/assets")
def list_assets(db:Session=Depends(get_db)): return db.query(models.Asset).order_by(models.Asset.symbol).all()
@app.post("/api/v1/portfolios")
def create_portfolio(req:schemas.PortfolioCreate, db:Session=Depends(get_db)):
    p=models.Portfolio(**req.model_dump()); db.add(p); db.commit(); db.refresh(p); return p
@app.post("/api/v1/portfolios/{portfolio_id}/holdings")
def add_holding(portfolio_id:int, req:schemas.HoldingCreate, db:Session=Depends(get_db)):
    h=models.Holding(portfolio_id=portfolio_id, **req.model_dump()); db.add(h); db.commit(); db.refresh(h); publish("portfolio.updated", {"portfolio_id":portfolio_id,"holding_id":h.id}); return h
@app.get("/api/v1/portfolios")
def portfolios(db:Session=Depends(get_db)): return db.query(models.Portfolio).all()
@app.get("/api/v1/portfolios/{portfolio_id}/performance")
def performance(portfolio_id:int, db:Session=Depends(get_db)):
    value=portfolio_value(db,portfolio_id); risk=db.query(models.RiskMetric).filter_by(portfolio_id=portfolio_id).order_by(desc(models.RiskMetric.calculated_at)).first()
    return {"portfolio_id":portfolio_id,"current_value":value,"daily_change_pct":round(random.uniform(-2.2,2.8),2),"risk":risk}

@app.post("/api/v1/transactions")
def create_transaction(req:schemas.TransactionCreate, db:Session=Depends(get_db)):
    amount=req.quantity*req.price; sc=anomaly_score(amount,req.quantity,req.price,random.randint(1,12))
    tx=models.Transaction(**req.model_dump(), amount=round(amount,2), anomaly_score=sc, status="processed")
    db.add(tx); db.commit(); db.refresh(tx)
    payload={"event_id":str(uuid.uuid4()),"transaction_id":tx.id,"amount":tx.amount,"anomaly_score":sc,"created_at":tx.created_at.isoformat()}
    db.add(models.EventAuditLog(event_id=payload["event_id"], event_type="transactions.created", topic="transactions.created", payload=payload))
    for sev,msg in fraud_flags(tx): db.add(models.Alert(user_id=tx.user_id,portfolio_id=tx.portfolio_id,alert_type="FRAUD",severity=sev,message=msg))
    db.commit(); publish("transactions.created", payload); return tx
@app.get("/api/v1/transactions")
def list_transactions(db:Session=Depends(get_db)): return db.query(models.Transaction).order_by(desc(models.Transaction.created_at)).limit(100).all()

@app.post("/api/v1/market/prices")
def price(req:schemas.MarketPriceCreate, db:Session=Depends(get_db)):
    mp=models.MarketPrice(**req.model_dump()); db.add(mp); db.commit(); db.refresh(mp); publish("market.prices.updated", req.model_dump()); return mp
@app.post("/api/v1/market/simulate")
def simulate_market_events(count:int=10, db:Session=Depends(get_db)):
    assets=db.query(models.Asset).all(); out=[]
    for _ in range(count):
        a=random.choice(assets); last=db.query(models.MarketPrice).filter_by(asset_id=a.id).order_by(desc(models.MarketPrice.event_time)).first(); new=round((last.price if last else 100)*random.uniform(.985,1.018),2)
        mp=models.MarketPrice(asset_id=a.id,symbol=a.symbol,price=new); db.add(mp); out.append({"symbol":a.symbol,"price":new})
    db.commit(); publish("market.prices.updated", {"count":count,"prices":out}); return {"generated":count,"prices":out}
@app.get("/api/v1/market/prices")
def prices(db:Session=Depends(get_db)):
    assets=db.query(models.Asset).all(); res=[]
    for a in assets:
        p=db.query(models.MarketPrice).filter_by(asset_id=a.id).order_by(desc(models.MarketPrice.event_time)).first(); res.append({"symbol":a.symbol,"price":p.price if p else None})
    return res

@app.get("/api/v1/risk/portfolio/{portfolio_id}")
def risk(portfolio_id:int, db:Session=Depends(get_db)): return calculate_risk(db,portfolio_id)
@app.get("/api/v1/alerts")
def alerts(db:Session=Depends(get_db)): return db.query(models.Alert).order_by(desc(models.Alert.created_at)).limit(50).all()
@app.post("/api/v1/anomaly/score")
def score(req:schemas.AnomalyScoreRequest): return {"anomaly_score": anomaly_score(req.amount,req.quantity,req.price,req.transaction_frequency_1h)}
@app.post("/api/v1/demo/generate-events")
def demo_events(count:int=15, db:Session=Depends(get_db)):
    assets=db.query(models.Asset).all(); p=db.query(models.Portfolio).first(); generated=[]
    for _ in range(count):
        a=random.choice(assets); price=round(random.uniform(80,1100),2); qty=random.randint(1,150); amount=qty*price
        tx=models.Transaction(user_id=1,portfolio_id=p.id,asset_id=a.id,transaction_type=random.choice(["BUY","SELL"]),quantity=qty,price=price,amount=round(amount,2),status="processed",anomaly_score=anomaly_score(amount,qty,price,random.randint(1,15)))
        db.add(tx); db.flush(); generated.append(tx.id)
        for sev,msg in fraud_flags(tx): db.add(models.Alert(user_id=1,portfolio_id=p.id,alert_type="FRAUD",severity=sev,message=msg))
    db.commit(); calculate_risk(db,p.id); return {"generated_transaction_ids":generated}
@app.get("/api/v1/dashboard/summary")
def dashboard(db:Session=Depends(get_db)):
    p=db.query(models.Portfolio).first(); txs=db.query(models.Transaction).order_by(desc(models.Transaction.created_at)).limit(10).all(); alerts=db.query(models.Alert).order_by(desc(models.Alert.created_at)).limit(10).all(); risk=db.query(models.RiskMetric).order_by(desc(models.RiskMetric.calculated_at)).first()
    return {"status":"online","portfolio_value": portfolio_value(db,p.id) if p else 0,"portfolio_id":p.id if p else None,"transactions":txs,"alerts":alerts,"risk":risk,"prices":prices(db)}
