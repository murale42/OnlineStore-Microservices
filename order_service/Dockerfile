FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

COPY . .

CMD ["./wait-for-it.sh", "db:5432", "--", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
