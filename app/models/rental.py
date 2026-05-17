from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.database import Base


class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False, index=True)
    customer_name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # passive_deletes=True tells SQLAlchemy not to NULL-out car_id before deleting
    # the Car row. The service checks for existing rentals first and returns 409,
    # so the FK constraint at the DB level acts as a safety net only.
    car = relationship("Car", backref=backref("rentals", passive_deletes=True))
