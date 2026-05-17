FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs

EXPOSE 8000

# Default: run the API server
# Override with: CMD ["python", "run_worker.py"] for the consumer worker
CMD ["python", "run_api.py"]
