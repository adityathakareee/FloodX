"""Environmental observation models for FLOOD-X (Rainfall, Weather, River Levels)."""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.models.base import Base, utc_now


class RainfallObservation(Base):
    """Stores satellite, ground telemetry, and derived rainfall observations."""
    __tablename__ = "rainfall_observations"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    station_name = Column(String(150), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observation_time = Column(DateTime(timezone=True), nullable=False, index=True)
    rainfall_value = Column(Float, nullable=False)
    rainfall_unit = Column(String(20), default="mm", nullable=False)
    measurement_type = Column(String(50), nullable=False, index=True)
    # Types: DAILY_ACCUMULATION, 5MIN_CUMULATIVE, INCREMENTAL, HOURLY_ACCUMULATION
    quality_flag = Column(String(30), default="VALID", nullable=False, index=True)
    # Flags: VALID, SUSPECT, MISSING, INVALID, DERIVED, INCOMPLETE
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("DataSource", back_populates="rainfall_observations")

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "station_name",
            "observation_time",
            "measurement_type",
            name="uq_rainfall_obs_record",
        ),
        Index("ix_rainfall_station_time", "station_name", "observation_time"),
        Index("ix_rainfall_source_time", "source_id", "observation_time"),
    )

    def __repr__(self) -> str:
        return f"<RainfallObs(st='{self.station_name}', time='{self.observation_time}', val={self.rainfall_value}{self.rainfall_unit}, type='{self.measurement_type}')>"


class WeatherObservation(Base):
    """Stores numerical weather model predictions and surface/soil observations."""
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    location_name = Column(String(150), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observation_time = Column(DateTime(timezone=True), nullable=False, index=True)
    data_category = Column(String(20), default="OBSERVED", nullable=False, index=True)
    # Categories: OBSERVED, FORECAST
    temperature = Column(Float, nullable=True)  # °C
    relative_humidity = Column(Float, nullable=True)  # %
    precipitation = Column(Float, nullable=True)  # mm
    wind_speed = Column(Float, nullable=True)  # km/h
    wind_direction = Column(Float, nullable=True)  # degrees
    soil_moisture = Column(Float, nullable=True)  # m³/m³ (0-7cm)
    quality_flag = Column(String(30), default="VALID", nullable=False, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("DataSource", back_populates="weather_observations")

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "location_name",
            "observation_time",
            "data_category",
            name="uq_weather_obs_record",
        ),
        Index("ix_weather_loc_time_cat", "location_name", "observation_time", "data_category"),
    )

    def __repr__(self) -> str:
        return f"<WeatherObs(loc='{self.location_name}', time='{self.observation_time}', cat='{self.data_category}', temp={self.temperature}°C)>"


class RiverLevelObservation(Base):
    """Stores hydrological river water levels with strict geographic relevance classification."""
    __tablename__ = "river_level_observations"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    station_name = Column(String(150), nullable=False, index=True)
    river_name = Column(String(100), nullable=False)
    station_code = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    observation_time = Column(DateTime(timezone=True), nullable=False, index=True)
    water_level = Column(Float, nullable=False)
    level_unit = Column(String(20), default="m", nullable=False)
    vertical_datum = Column(String(50), default="MSL", nullable=False)
    geographic_relevance = Column(String(50), nullable=False, index=True)
    # Relevance: WITHIN_PILOT_BASIN, UPSTREAM_DOWNSTREAM, REGIONAL_REFERENCE_ONLY, LOCATION_UNVERIFIED, NOT_RELEVANT
    quality_flag = Column(String(30), default="VALID", nullable=False, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("DataSource", back_populates="river_level_observations")

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "station_name",
            "observation_time",
            name="uq_river_level_obs_record",
        ),
        Index("ix_river_station_time", "station_name", "observation_time"),
        Index("ix_river_relevance_time", "geographic_relevance", "observation_time"),
    )

    def __repr__(self) -> str:
        return f"<RiverLevelObs(st='{self.station_name}', river='{self.river_name}', level={self.water_level}{self.level_unit}, rel='{self.geographic_relevance}')>"

