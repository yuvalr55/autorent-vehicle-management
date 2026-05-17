from datetime import date
from httpx import AsyncClient


TODAY = str(date.today())


async def _add_car(client: AsyncClient, model: str = "Toyota Camry", year: int = 2022) -> dict:
    return (await client.post("/cars", json={"model": model, "year": year})).json()


async def test_start_rental_for_available_car(client: AsyncClient):
    car = await _add_car(client)
    response = await client.post("/rentals", json={
        "car_id": car["id"],
        "customer_name": "Alice Smith",
        "start_date": TODAY,
    })
    assert response.status_code == 201
    body = response.json()
    assert body["is_active"] is True
    assert body["car_id"] == car["id"]


async def test_start_rental_marks_car_as_in_use(client: AsyncClient):
    car = await _add_car(client)
    await client.post("/rentals", json={"car_id": car["id"], "customer_name": "Bob", "start_date": TODAY})
    cars = (await client.get("/cars?status=in_use")).json()
    assert any(c["id"] == car["id"] for c in cars)


async def test_prevent_rental_for_in_use_car(client: AsyncClient):
    car = await _add_car(client)
    await client.post("/rentals", json={"car_id": car["id"], "customer_name": "Alice", "start_date": TODAY})
    response = await client.post("/rentals", json={
        "car_id": car["id"],
        "customer_name": "Bob",
        "start_date": TODAY,
    })
    assert response.status_code == 409


async def test_prevent_rental_for_maintenance_car(client: AsyncClient):
    car = (await client.post("/cars", json={"model": "Old Car", "year": 2010, "status": "maintenance"})).json()
    response = await client.post("/rentals", json={
        "car_id": car["id"],
        "customer_name": "Charlie",
        "start_date": TODAY,
    })
    assert response.status_code == 409


async def test_end_rental_sets_car_available(client: AsyncClient):
    car = await _add_car(client)
    rental = (await client.post("/rentals", json={
        "car_id": car["id"], "customer_name": "Diana", "start_date": TODAY,
    })).json()

    end_response = await client.post(f"/rentals/{rental['id']}/end")
    assert end_response.status_code == 200
    assert end_response.json()["is_active"] is False

    available = (await client.get("/cars?status=available")).json()
    assert any(c["id"] == car["id"] for c in available)


async def test_end_already_closed_rental_returns_409(client: AsyncClient):
    car = await _add_car(client)
    rental = (await client.post("/rentals", json={
        "car_id": car["id"], "customer_name": "Eve", "start_date": TODAY,
    })).json()
    await client.post(f"/rentals/{rental['id']}/end")
    response = await client.post(f"/rentals/{rental['id']}/end")
    assert response.status_code == 409


async def test_list_rentals(client: AsyncClient):
    car = await _add_car(client)
    await client.post("/rentals", json={"car_id": car["id"], "customer_name": "Frank", "start_date": TODAY})
    response = await client.get("/rentals")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_rental_by_id(client: AsyncClient):
    car = await _add_car(client)
    rental_id = (await client.post("/rentals", json={
        "car_id": car["id"], "customer_name": "Grace", "start_date": TODAY,
    })).json()["id"]
    response = await client.get(f"/rentals/{rental_id}")
    assert response.status_code == 200
    assert response.json()["id"] == rental_id
    assert response.json()["customer_name"] == "Grace"


async def test_get_nonexistent_rental_returns_404(client: AsyncClient):
    response = await client.get("/rentals/9999")
    assert response.status_code == 404


async def test_start_rental_for_nonexistent_car_returns_404(client: AsyncClient):
    response = await client.post("/rentals", json={
        "car_id": 9999,
        "customer_name": "Harry",
        "start_date": TODAY,
    })
    assert response.status_code == 404


async def test_end_nonexistent_rental_returns_404(client: AsyncClient):
    response = await client.post("/rentals/9999/end")
    assert response.status_code == 404
