from datetime import date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core import Base
from enums import SLAStatus



class Quota(Base):
    __tablename__ = "quotas"

    id: Mapped[int] = mapped_column(primary_key=True)


class BlockStorageQuota(Quota):
    __tablename__ = "block_storage_quotas"

    id: Mapped[int] = mapped_column(ForeignKey("quotas.id"), primary_key=True)
    gigabytes: Mapped[int] = mapped_column(nullable=False)
    per_volume_gigabytes: Mapped[int] = mapped_column(nullable=False)
    volumes: Mapped[int] = mapped_column(nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "block_storage_quotas",
    }


class ComputeQuota(Quota):
    __tablename__ = "compute_quotas"

    id: Mapped[int] = mapped_column(ForeignKey("quotas.id"), primary_key=True)
    cores: Mapped[int] = mapped_column(nullable=False)
    instances: Mapped[int] = mapped_column(nullable=False)
    ram: Mapped[int] = mapped_column(nullable=False)

    __mapper__args__ = {
        "polymorphic_identity": "compute_quotas",
    }


class NetworkQuota(Quota):
    __tablename__ = "network_quotas"

    id: Mapped[int] = mapped_column(ForeignKey("quotas.id"), primary_key=True)
    networks: Mapped[int] = mapped_column(nullable=False)
    ports: Mapped[int] = mapped_column(nullable=False)
    public_ips: Mapped[int] = mapped_column(nullable=False)
    security_groups: Mapped[int] = mapped_column(nullable=False)
    security_groups_rules: Mapped[int] = mapped_column(nullable=False)


class SLA(Base):
    __tablename__ = "slas"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_uuid: Mapped[str] = mapped_column(nullable=False)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[SLAStatus] = mapped_column(
        nullable=False, default=SLAStatus.DISCUSSING
    )
