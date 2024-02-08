from typing import TYPE_CHECKING, List

from app.provider.enum import ProviderStatus, ProviderType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import Base

if TYPE_CHECKING:
    from requests import ProviderFederation


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[ProviderType] = mapped_column(nullable=False)
    auth_url: Mapped[str] = mapped_column(nullable=False)
    is_public: Mapped[bool] = mapped_column(default=False)
    status: Mapped[ProviderStatus] = mapped_column(
        nullable=False, default=ProviderStatus.ACTIVE
    )
    # vol_types: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    image_tags: Mapped[str] = mapped_column(nullable=True)
    network_tags: Mapped[str] = mapped_column(nullable=True)

    mentioning_requests: Mapped[List["ProviderFederation"]] = relationship(
        back_populates="provider"
    )


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    site: Mapped[str] = mapped_column(nullable=False)
    country: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    latitude: Mapped[float] = mapped_column(nullable=True)
    longitude: Mapped[float] = mapped_column(nullable=True)


class IdentityProvider(Base):
    __tablename__ = "identity_providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
