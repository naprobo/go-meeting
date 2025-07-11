FROM python:3.12

RUN apt-get update && apt-get install -y libpq-dev gcc

WORKDIR /app/backend

COPY requirements.txt /app/backend/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082", "--reload"]

