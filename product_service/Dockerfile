FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
 && apt-get install -y gcc libpq-dev netcat-openbsd \
 && apt-get clean


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-it.sh entrypoint.sh ./
COPY . .

RUN chmod +x wait-for-it.sh entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
