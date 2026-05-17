from prometheus_client import Gauge, Histogram

active_cars_gauge = Gauge(
    "autorent_active_cars_total",
    "Number of cars currently in use",
)
available_cars_gauge = Gauge(
    "autorent_available_cars_total",
    "Number of cars available for rental",
)
maintenance_cars_gauge = Gauge(
    "autorent_maintenance_cars_total",
    "Number of cars under maintenance",
)
ongoing_rentals_gauge = Gauge(
    "autorent_ongoing_rentals_total",
    "Number of ongoing rentals",
)
request_duration_histogram = Histogram(
    "autorent_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


def update_car_metrics(active: int, available: int, maintenance: int) -> None:
    active_cars_gauge.set(active)
    available_cars_gauge.set(available)
    maintenance_cars_gauge.set(maintenance)


def update_rental_metrics(ongoing: int) -> None:
    ongoing_rentals_gauge.set(ongoing)
