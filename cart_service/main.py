from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import threading
import pika
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time

DATABASE_URL = "postgresql://postgres:Qweras.1@db:5432/cart_db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class CartItemDB(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    product_id = Column(Integer)
    name = Column(String)
    price = Column(Float)
    quantity = Column(Integer)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Сервис корзины", description="Управление корзиной пользователя", version="1.0.0")
PRODUCT_SERVICE_URL = "http://product_service:8000"

class CartItem(BaseModel):
    product_id: int
    quantity: int

@app.post("/cart/{username}/add")
def add_to_cart(username: str, item: CartItem):
    db = SessionLocal()
    product_resp = requests.get(f"{PRODUCT_SERVICE_URL}/products/{item.product_id}")
    if product_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found")
    product = product_resp.json()

    db_item = db.query(CartItemDB).filter_by(username=username, product_id=item.product_id).first()
    if db_item:
        db_item.quantity += item.quantity
    else:
        db_item = CartItemDB(
            username=username,
            product_id=item.product_id,
            name=product["name"],
            price=product["price"],
            quantity=item.quantity
        )
        db.add(db_item)
    db.commit()
    db.close()
    return get_cart(username)

@app.get("/cart/{username}")
def get_cart(username: str):
    db = SessionLocal()
    items = db.query(CartItemDB).filter_by(username=username).all()
    result = [
        {"id": i.product_id, "name": i.name, "price": i.price, "quantity": i.quantity}
        for i in items
    ]
    db.close()
    return {"cart": result}

@app.delete("/cart/{username}/remove/{product_id}")
def remove_from_cart(username: str, product_id: int):
    db = SessionLocal()
    db.query(CartItemDB).filter_by(username=username, product_id=product_id).delete()
    db.commit()
    db.close()
    return get_cart(username)

@app.put("/cart/{username}/update")
def update_quantity(username: str, item: CartItem):
    db = SessionLocal()
    db_item = db.query(CartItemDB).filter_by(username=username, product_id=item.product_id).first()
    if db_item:
        db_item.quantity = item.quantity
        db.commit()
    db.close()
    return get_cart(username)


def consume_order_events():
    def callback(ch, method, properties, body):
        data = json.loads(body)
        username = data["username"]
        db = SessionLocal()
        db.query(CartItemDB).filter_by(username=username).delete()
        db.commit()
        db.close()
        print(f"Cleared cart for user {username}")

    parameters = pika.ConnectionParameters(host="rabbitmq", heartbeat=30, blocked_connection_timeout=300)

    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange="order_events", exchange_type="fanout", durable=True)
            channel.queue_declare(queue="cart_clear_queue")
            channel.queue_bind(exchange="order_events", queue="cart_clear_queue")
            channel.basic_consume(queue="cart_clear_queue", on_message_callback=callback, auto_ack=True)
            print("Listening for order events to clear cart...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"[!] Lost connection to RabbitMQ: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

threading.Thread(target=consume_order_events, daemon=True).start()