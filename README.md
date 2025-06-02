# Online store Microservices API
Этот проект — демонстрация микросервисной архитектуры для простого онлайн-магазина, реализованной на Python (FastAPI), PostgreSQL, RabbitMQ и Docker.

## Сервисы
- **Product Service** — управление товарами.
- **User Service** — регистрация, аутентификация, профиль пользователя.
- **Cart Service** — корзина пользователя (события заказов через RabbitMQ).
- **Order Service** — оформление заказов.
- **Payment Service** — имитация оплаты заказов.
### Дополнительно
- **RabbitMQ** — брокер сообщений для взаимодействия между сервисами.
- **PostgreSQL** — база данных.

## Стек технологий
- Python 3.13
- FastAPI
- Docker + Docker Compose
- PostgreSQL
- RabbitMQ
- Pydantic
- Uvicorn

## Структура проекта

-├── cart_service/

-├── order_service/

-├── payment_service/

-├── product_service/

-├── user_service/

-├── docker-compose.yml

-├── README.md

Каждый микросервис содержит:
- `main.py` — основной запуск приложения
- `requirements.txt` — зависимости
- `Dockerfile` — сборка образа

## Запуск проекта
1. Клонируйте репозиторий: 
- `git clone https://github.com/murale42/OnlineStore-Microservices.git`
- `cd OnlineStore-Microservices`

2. Соберите и запустите контейнеры: `docker compose up --build`

3. Доступ к сервисам:
   
- Product Service	http://localhost:8001/docs
- User Service	http://localhost:8002/docs
- Payment Service	http://localhost:8003/docs
- Cart Service	http://localhost:8004/docs
- Order Service	http://localhost:8005/docs
- RabbitMQ (UI)	http://localhost:15672/
