# AutoRent — Vehicle Management System

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-FF6600?logo=rabbitmq&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-metrics-E6522C?logo=prometheus&logoColor=white)

Internal fleet management API for a car rental company — manage vehicles, register rentals, and monitor fleet metrics.

---

## Quick Start

**Docker (recommended):**
```bash
cp .env.example .env
docker compose up --build
```

**Local:**
```bash
pip install -r requirements.txt
cp .env.example .env
python run_api.py        # terminal 1 — API server
python run_worker.py     # terminal 2 — event consumer
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| RabbitMQ UI | http://localhost:15672 &nbsp;`guest / guest` |
| Metrics | http://localhost:8000/metrics |

---

## Tests

```bash
docker compose up db -d   # PostgreSQL must be running
pytest tests/ -v
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/autorent` | PostgreSQL URL |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | RabbitMQ URL |
| `RABBITMQ_EXCHANGE` | `autorent.events` | Topic exchange name |
| `RABBITMQ_QUEUE` | `autorent.events.queue` | Durable queue name |
| `WORKER_CONCURRENCY` | `4` | Concurrent messages per worker |
| `LOG_FILE` | `logs/app.log` | Log file path |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `API_HOST` | `0.0.0.0` | Bind host |
| `API_PORT` | `8000` | Bind port |

---

## API

### Cars

| Method | Path | Description | Success | Error |
|---|---|---|:---:|:---:|
| `GET` | `/cars` | List all cars — filter: `?status=available` | 200 | — |
| `GET` | `/cars/{id}` | Get a car by ID | 200 | 404 |
| `POST` | `/cars` | Add a car `{"model": "...", "year": 2023}` | 201 | — |
| `PATCH` | `/cars/{id}` | Update car `{"status": "maintenance"}` | 200 | 404 |
| `DELETE` | `/cars/{id}` | Remove a car | 204 | 404 / 409 |

### Rentals

| Method | Path | Description | Success | Error |
|---|---|---|:---:|:---:|
| `GET` | `/rentals` | List all rentals | 200 | — |
| `GET` | `/rentals/{id}` | Get a rental by ID | 200 | 404 |
| `POST` | `/rentals` | Start rental `{"car_id": 1, "customer_name": "...", "start_date": "..."}` | 201 | 404 / 409 |
| `POST` | `/rentals/{id}/end` | End rental — returns car to `available` | 200 | 404 / 409 |

> `409` — renting a non-available car · ending a closed rental · deleting a car with rental history

### Events & Metrics

| Method | Path | Description |
|---|---|---|
| `GET` | `/events` | Audit log — filter: `?event_type=car.created&limit=50` |
| `GET` | `/metrics` | Prometheus exposition format |

---

## Architecture

```mermaid
flowchart TD
    Client([HTTP Client]) --> API

    subgraph app [FastAPI — run_api.py]
        API[API Layer\napp/api/] --> Service[Service Layer\napp/services/]
        Service --> Repo[Repository Layer\napp/repositories/]
        Service --> Pub[Event Publisher\napp/events/publisher.py]
    end

    Repo --> DB[(PostgreSQL)]
    Pub --> MQ([RabbitMQ\nautorent.events])
    MQ --> Worker([Worker\nrun_worker.py])
    Worker --> DB
```

Three strict layers — **API** validates input, **Service** owns business logic and transaction commits, **Repository** runs SQLAlchemy queries. `start_rental` uses `SELECT FOR UPDATE` to prevent concurrent overbooking.

### Why a message queue?

Every write publishes an event to RabbitMQ; a separate worker persists it to `event_log`. This keeps the audit log fully decoupled from the business transaction — if the worker is down, the API continues and events queue up for later. The worker uses `requeue=True` for transient failures (DB down) and discards malformed messages without requeuing.

### Why PostgreSQL?

Row-level locking (`SELECT FOR UPDATE`), JSONB for flexible event payloads, `asyncpg` for non-blocking I/O, and ACID transactions for atomic multi-step operations.

### Event routing keys

| Routing Key | Trigger | Payload |
|---|---|---|
| `car.created` | Car added | `{id, model, year, status}` |
| `car.updated` | Car updated | `{id, fields: {field: new_value}}` |
| `car.deleted` | Car removed | `{id}` |
| `rental.started` | Rental started | `{rental_id, car_id, customer_name}` |
| `rental.ended` | Rental ended | `{rental_id, car_id}` |

---

## Example Usage

```bash
# Add a car
curl -X POST http://localhost:8000/cars \
  -H "Content-Type: application/json" \
  -d '{"model": "Tesla Model 3", "year": 2023}'
# → {"id":1,"model":"Tesla Model 3","year":2023,"status":"available"}

# Start a rental
curl -X POST http://localhost:8000/rentals \
  -H "Content-Type: application/json" \
  -d '{"car_id": 1, "customer_name": "John Doe", "start_date": "2026-05-17"}'
# → {"id":1,"car_id":1,...,"end_date":null,"is_active":true}

# Car is now in_use — another rental attempt returns 409
# → {"detail":"Car 1 is not available (current status: in_use)"}

# End the rental
curl -X POST http://localhost:8000/rentals/1/end
# → {"id":1,...,"end_date":"2026-05-17","is_active":false}

# Check audit log
curl "http://localhost:8000/events?limit=5"

# Check fleet metrics
curl http://localhost:8000/metrics | grep autorent_
```

A full **Postman collection** is included — `autorent_postman_collection.json`.

---

## Screenshots

### Swagger UI — Interactive API docs

![Swagger UI](docs/screenshots/swagger.png)

### RabbitMQ Management UI

![RabbitMQ UI](docs/screenshots/rabbitmq.png)

### Audit Log — `GET /events`

```json
[
  { "id": 7, "event_type": "rental.ended",   "data": { "car_id": 1, "rental_id": 1 },                              "created_at": "2026-05-17T10:44:19Z" },
  { "id": 6, "event_type": "rental.started", "data": { "car_id": 1, "rental_id": 1, "customer_name": "John Doe" }, "created_at": "2026-05-17T10:44:18Z" },
  { "id": 4, "event_type": "car.updated",    "data": { "id": 2, "fields": { "status": "maintenance" } },           "created_at": "2026-05-17T10:44:18Z" },
  { "id": 1, "event_type": "car.created",    "data": { "id": 1, "year": 2023, "model": "Tesla Model 3", "status": "available" }, "created_at": "2026-05-17T10:44:18Z" }
]
```

### Prometheus Metrics — `GET /metrics`

```
autorent_active_cars_total       0.0
autorent_available_cars_total    1.0
autorent_maintenance_cars_total  1.0
autorent_ongoing_rentals_total   0.0

autorent_request_duration_seconds_count{endpoint="/cars",method="POST"}    3.0
autorent_request_duration_seconds_count{endpoint="/rentals",method="POST"} 2.0
```

### Test Suite — 32 passed

```
$ pytest tests/ -v
...
======================== 32 passed in 3.94s ========================
```

---

## Project Structure

```
├── run_api.py              # API server entry point
├── run_worker.py           # Event consumer entry point
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── app/
│   ├── api/                # FastAPI routers
│   ├── services/           # Business logic, transaction ownership
│   ├── repositories/       # SQLAlchemy async queries
│   ├── models/             # ORM models (Car, Rental, EventLog)
│   ├── schemas/            # Pydantic schemas
│   ├── events/             # RabbitMQ publisher + consumer
│   ├── logging_config.py
│   ├── metrics.py          # Prometheus definitions
│   ├── database.py
│   └── main.py
└── tests/                  # 32 async integration tests
```
