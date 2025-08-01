FROM python:3.12.4-slim

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app ./app

CMD ["python", "-m", "app.main"]