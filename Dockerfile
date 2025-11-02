FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic.ini .
COPY alembic alembic
COPY src/fastbg fastbg
RUN alembic upgrade head

EXPOSE 8000

CMD ["uvicorn", "fastbg.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
