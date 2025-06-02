from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from uuid import uuid4
from typing import List

DATABASE_URL = "postgresql://postgres:Qweras.1@db:5432/product_db"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Сервис платежей", description="Обработка и проверка платежей", version="1.0.0")

class PaymentDB(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, unique=True, index=True)
    username = Column(String, index=True)
    amount = Column(Float)
    delivery_method = Column(String)
    status = Column(String)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PaymentRequest(BaseModel):
    username: str
    amount: float
    delivery_method: str

class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    amount: float
    delivery_method: str

@app.post("/pay/", response_model=PaymentResponse)
def pay(request: PaymentRequest, db: Session = Depends(get_db)):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    payment_id = str(uuid4())
    payment = PaymentDB(
        payment_id=payment_id,
        username=request.username,
        amount=request.amount,
        delivery_method=request.delivery_method,
        status="success"
    )
    db.add(payment)
    db.commit()
    return PaymentResponse(
        payment_id=payment_id,
        status="success",
        amount=request.amount,
        delivery_method=request.delivery_method
    )

@app.get("/payments/{username}", response_model=List[PaymentResponse])
def get_user_payments(username: str, db: Session = Depends(get_db)):
    payments = db.query(PaymentDB).filter(PaymentDB.username == username).all()
    return [
        PaymentResponse(
            payment_id=p.payment_id,
            status=p.status,
            amount=p.amount,
            delivery_method=p.delivery_method
        ) for p in payments
    ]
