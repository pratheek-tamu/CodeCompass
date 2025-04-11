FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt /app/
COPY config.yaml /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src /app/src
COPY data /app/data
COPY scripts /app/scripts

ENV PYTHONPATH=/app

WORKDIR /app

CMD ["sh", "scripts/entrypoint.sh"]

# CMD ["python", "scripts/initial_indexing.py"]
