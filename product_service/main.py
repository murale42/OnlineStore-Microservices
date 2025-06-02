from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, List

DATABASE_URL = "postgresql://postgres:Qweras.1@db:5432/product_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Сервис товаров", description="Каталог товаров, поиск, фильтрация", version="1.0.0")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    manufacturer = Column(String, index=True)

Base.metadata.create_all(bind=engine)

class ProductCreate(BaseModel):
    name: str
    price: float
    manufacturer: str

class ProductOut(ProductCreate):
    id: int

    class Config:
        orm_mode = True  

class ProductUpdate(BaseModel):
    name: Optional[str]
    price: Optional[float]
    manufacturer: Optional[str]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/products/", response_model=ProductOut)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[ProductOut])
def list_products(
    manufacturer: Optional[str] = None,
    search: Optional[str] = None,
    sort_by_price: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if manufacturer:
        query = query.filter(Product.manufacturer == manufacturer)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if sort_by_price == "asc":
        query = query.order_by(Product.price.asc())
    elif sort_by_price == "desc":
        query = query.order_by(Product.price.desc())
    return query.all()

@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict(exclude_unset=True).items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted"}
