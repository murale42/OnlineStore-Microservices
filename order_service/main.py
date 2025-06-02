from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Float, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import pika
import json
import os
import httpx

DATABASE_URL = "postgresql://postgres:Qweras.1@db:5432/product_db"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Сервис заказов", description="Управление заказами пользователей", version="1.0.0")

USER_SERVICE = os.getenv("USER_SERVICE", "http://user_service:8000")
CART_SERVICE = os.getenv("CART_SERVICE", "http://cart_service:8000")
PRODUCT_SERVICE = os.getenv("PRODUCT_SERVICE", "http://product_service:8000")
PAYMENT_SERVICE = os.getenv("PAYMENT_SERVICE", "http://payment_service:8000")

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    items = Column(JSON)
    total = Column(Float)
    status = Column(String)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def publish_order_created(username: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    channel = connection.channel()
    channel.exchange_declare(exchange="order_events", exchange_type="fanout", durable=True)
    message = json.dumps({"username": username})
    channel.basic_publish(exchange="order_events", routing_key="", body=message)
    connection.close()

@app.post("/order/{username}")
async def create_order(username: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(f"{USER_SERVICE}/users/{username}")
        if user_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")

        cart_resp = await client.get(f"{CART_SERVICE}/cart/{username}")
        if cart_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Cart not found")

        cart = cart_resp.json().get("cart", [])
        if not cart:
            raise HTTPException(status_code=400, detail="Cart is empty")

        total = sum(item["price"] * item.get("quantity", 1) for item in cart)

        payment_resp = await client.post(
            f"{PAYMENT_SERVICE}/pay/",
            json={"username": username, "amount": total, "delivery_method": "courier"}
        )
        if payment_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Payment failed")

    order = OrderDB(username=username, items=cart, total=total, status="created")
    db.add(order)
    db.commit()
    db.refresh(order)

    publish_order_created(username)

    return {
        "id": order.id,
        "username": order.username,
        "items": order.items,
        "total": order.total,
        "status": order.status
    }

@app.get("/orders/{username}")
def user_orders(username: str, db: Session = Depends(get_db)):
    orders = db.query(OrderDB).filter(OrderDB.username == username).all()
    return orders

@app.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    return db.query(OrderDB).all()

@app.put("/orders/{order_id}")
def update_order(order_id: int, status: str, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    db.commit()
    return order

@app.delete("/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {"message": "Order deleted"}
