from datetime import date
from httpx import AsyncClient


async def test_metrics_returns_prometheus_format(client: AsyncClient):
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "autorent_active_cars_total" in response.text
    assert "autorent_available_cars_total" in response.text
    assert "autorent_ongoing_rentals_total" in response.text


async def test_metrics_reflects_current_fleet_state(client: AsyncClient):
    car = (await client.post("/cars", json={"model": "Tesla", "year": 2023})).json()
    await client.post("/cars", json={"model": "BMW", "year": 2022, "status": "maintenance"})
    await client.post("/rentals", json={
        "car_id": car["id"], "customer_name": "Alice", "start_date": str(date.today()),
    })

    response = await client.get("/metrics")
    assert "autorent_active_cars_total 1.0" in response.text
    assert "autorent_available_cars_total 0.0" in response.text
    assert "autorent_maintenance_cars_total 1.0" in response.text
    assert "autorent_ongoing_rentals_total 1.0" in response.text
