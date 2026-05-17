from datetime import date
from httpx import AsyncClient


async def test_create_car_returns_201(client: AsyncClient):
    response = await client.post("/cars", json={"model": "Tesla Model 3", "year": 2023})
    assert response.status_code == 201
    body = response.json()
    assert body["model"] == "Tesla Model 3"
    assert body["year"] == 2023
    assert body["status"] == "available"
    assert "id" in body


async def test_create_car_defaults_to_available(client: AsyncClient):
    response = await client.post("/cars", json={"model": "BMW X5", "year": 2022})
    assert response.json()["status"] == "available"


async def test_list_cars_returns_all(client: AsyncClient):
    await client.post("/cars", json={"model": "BMW X5", "year": 2022})
    await client.post("/cars", json={"model": "Audi A4", "year": 2021})
    response = await client.get("/cars")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_cars_filter_by_status(client: AsyncClient):
    await client.post("/cars", json={"model": "BMW X5", "year": 2022})
    await client.post("/cars", json={"model": "Broken Car", "year": 2020, "status": "maintenance"})
    response = await client.get("/cars?status=available")
    assert response.status_code == 200
    cars = response.json()
    assert len(cars) == 1
    assert cars[0]["model"] == "BMW X5"


async def test_get_car_by_id(client: AsyncClient):
    car_id = (await client.post("/cars", json={"model": "Honda Civic", "year": 2023})).json()["id"]
    response = await client.get(f"/cars/{car_id}")
    assert response.status_code == 200
    assert response.json()["id"] == car_id
    assert response.json()["model"] == "Honda Civic"


async def test_get_nonexistent_car_returns_404(client: AsyncClient):
    response = await client.get("/cars/9999")
    assert response.status_code == 404


async def test_update_car_status(client: AsyncClient):
    car_id = (await client.post("/cars", json={"model": "Honda Civic", "year": 2023})).json()["id"]
    response = await client.patch(f"/cars/{car_id}", json={"status": "maintenance"})
    assert response.status_code == 200
    assert response.json()["status"] == "maintenance"


async def test_delete_car(client: AsyncClient):
    car_id = (await client.post("/cars", json={"model": "Ford Focus", "year": 2021})).json()["id"]
    assert (await client.delete(f"/cars/{car_id}")).status_code == 204
    assert len((await client.get("/cars")).json()) == 0


async def test_delete_nonexistent_car_returns_404(client: AsyncClient):
    response = await client.delete("/cars/9999")
    assert response.status_code == 404


async def test_delete_car_with_active_rental_returns_409(client: AsyncClient):
    car_id = (await client.post("/cars", json={"model": "Rented Car", "year": 2022})).json()["id"]
    await client.post("/rentals", json={
        "car_id": car_id,
        "customer_name": "Active Renter",
        "start_date": str(date.today()),
    })
    response = await client.delete(f"/cars/{car_id}")
    assert response.status_code == 409


async def test_update_nonexistent_car_returns_404(client: AsyncClient):
    response = await client.patch("/cars/9999", json={"status": "maintenance"})
    assert response.status_code == 404


async def test_update_car_model_and_year(client: AsyncClient):
    car_id = (await client.post("/cars", json={"model": "Old Model", "year": 2018})).json()["id"]
    response = await client.patch(f"/cars/{car_id}", json={"model": "New Model", "year": 2024})
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "New Model"
    assert body["year"] == 2024


async def test_update_car_empty_body_returns_car_unchanged(client: AsyncClient):
    car_id = (await client.post("/cars", json={"model": "Honda Civic", "year": 2023})).json()["id"]
    response = await client.patch(f"/cars/{car_id}", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "Honda Civic"
    assert body["year"] == 2023


async def test_delete_car_with_closed_rental_returns_409(client: AsyncClient):
    car_id = (await client.post("/cars", json={"model": "Old Car", "year": 2019})).json()["id"]
    rental = (await client.post("/rentals", json={
        "car_id": car_id, "customer_name": "Past Renter", "start_date": str(date.today()),
    })).json()
    await client.post(f"/rentals/{rental['id']}/end")
    response = await client.delete(f"/cars/{car_id}")
    assert response.status_code == 409
