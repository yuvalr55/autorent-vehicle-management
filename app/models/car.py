from sqlalchemy import Column, Integer, String, Enum as SAEnum
from app.database import Base
from app.enums import CarStatus


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(
        SAEnum(CarStatus, name="carstatus", create_constraint=True, native_enum=False),
        default=CarStatus.available,
        nullable=False,
    )
