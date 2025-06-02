from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

DATABASE_URL = "postgresql://postgres:Qweras.1@db:5432/user_db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Сервис пользователей", description="Регистрация, авторизация, профиль",  version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserDB(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True, index=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    full_name = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserRegister(BaseModel):
    username: str
    password: str
    email: str
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserUpdate(BaseModel):
    email: Optional[str]
    full_name: Optional[str]

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# Регистрация
@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = UserDB(
        username=user.username,
        password=user.password,
        email=user.email,
        full_name=user.full_name
    )
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

# Авторизация
@app.post("/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    if not user or user.password != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = f"token-{user.username}"
    return TokenResponse(access_token=token)

# Личный кабинет (GET)
@app.get("/users/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name
    }

# Обновление личных данных
@app.put("/users/{username}")
def update_user(username: str, update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if update.email is not None:
        user.email = update.email
    if update.full_name is not None:
        user.full_name = update.full_name
    db.commit()
    return {"message": "User updated"}

# Смена пароля
@app.post("/users/{username}/change-password")
def change_password(username: str, data: PasswordChange, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if not user or user.password != data.old_password:
        raise HTTPException(status_code=403, detail="Invalid password")
    user.password = data.new_password
    db.commit()
    return {"message": "Password changed"}

# Выход из аккаунта 
invalid_tokens = set()

@app.post("/logout")
def logout(token: str = Body(..., embed=True)):
    invalid_tokens.add(token)
    return {"message": "Logged out"}
