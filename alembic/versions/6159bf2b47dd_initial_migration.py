"""Initial migration.

Revision ID: 6159bf2b47dd
Revises:
Create Date: 2025-11-14 16:30:30.247135

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
import sqlmodel

import fed_mgr
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6159bf2b47dd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_ID = "user.id"
PROVIDER_ID = "provider.id"


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    common_create_update_cols = [
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], [USER_ID]),
        sa.ForeignKeyConstraint(["updated_by_id"], [USER_ID]),
    ]
    common_id_cols = [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    ]

    op.create_table(
        "user",
        sa.Column("sub", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "issuer", fed_mgr.v1.adapters.HttpUrlType(length=255), nullable=False
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
        *common_id_cols,
        if_not_exists=True,
    )
    op.create_table(
        "identityprovider",
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "endpoint", fed_mgr.v1.adapters.HttpUrlType(length=255), nullable=False
        ),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("groups_claim", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("protocol", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("audience", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.UniqueConstraint("endpoint"),
        *common_id_cols,
        *common_create_update_cols,
        if_not_exists=True,
    )
    op.create_table(
        "provider",
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "ready",
                "submitted",
                "evaluation",
                "pre_production",
                "active",
                "deprecated",
                "removed",
                "degraded",
                "maintenance",
                "re_evaluation",
                name="providerstatus",
            ),
            nullable=False,
        ),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("openstack", "kubernetes", name="providertype"),
            nullable=False,
        ),
        sa.Column(
            "auth_endpoint", fed_mgr.v1.adapters.HttpUrlType(length=255), nullable=False
        ),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("support_emails", sa.JSON(), nullable=True),
        sa.Column("image_tags", sa.JSON(), nullable=True),
        sa.Column("network_tags", sa.JSON(), nullable=True),
        sa.Column("rally_username", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("rally_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("floating_ips_enable", sa.Boolean(), nullable=False),
        sa.Column(
            "test_flavor_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("test_network_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.UniqueConstraint("auth_endpoint"),
        sa.UniqueConstraint("name"),
        *common_id_cols,
        *common_create_update_cols,
        if_not_exists=True,
    )
    op.create_table(
        "administrates",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], [PROVIDER_ID], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], [USER_ID]),
        sa.PrimaryKeyConstraint("user_id", "provider_id"),
        if_not_exists=True,
    )
    op.create_table(
        "evaluates",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], [PROVIDER_ID], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], [USER_ID]),
        sa.PrimaryKeyConstraint("user_id", "provider_id"),
        if_not_exists=True,
    )
    op.create_table(
        "idpoverrides",
        sa.Column("groups_claim", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("protocol", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("audience", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("idp_id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["idp_id"], ["identityprovider.id"]),
        sa.ForeignKeyConstraint(["provider_id"], [PROVIDER_ID], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("idp_id", "provider_id"),
        *common_create_update_cols,
        if_not_exists=True,
    )
    op.create_table(
        "region",
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("overbooking_cpu", sa.Float(), nullable=False),
        sa.Column("overbooking_ram", sa.Float(), nullable=False),
        sa.Column("bandwidth_in", sa.Float(), nullable=False),
        sa.Column("bandwidth_out", sa.Float(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], [PROVIDER_ID], ondelete="RESTRICT"),
        sa.UniqueConstraint("name", "provider_id", name="unique_name_provider_couple"),
        *common_id_cols,
        *common_create_update_cols,
        if_not_exists=True,
    )
    op.create_table(
        "usergroup",
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("idp_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["idp_id"], ["identityprovider.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("name", "idp_id", name="unique_name_idp_couple"),
        *common_id_cols,
        *common_create_update_cols,
        if_not_exists=True,
    )
    op.create_table(
        "sla",
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("url", fed_mgr.v1.adapters.HttpUrlType(length=255), nullable=False),
        sa.Column("start_date", sa.DATE(), nullable=False),
        sa.Column("end_date", sa.DATE(), nullable=False),
        sa.Column("user_group_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_group_id"], ["usergroup.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("url"),
        *common_id_cols,
        *common_create_update_cols,
        if_not_exists=True,
    )
    add_project_cols = []
    if conn.dialect.name == "mysql":
        add_project_cols = (
            sa.Column(
                "provider_root_id",
                sa.String(length=32),
                sa.Computed("IF(is_root = TRUE, provider_id, NULL)", persisted=True),
                nullable=True,
            ),
        )
    op.create_table(
        "project",
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "iaas_project_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("is_root", sa.Boolean(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("sla_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["provider_id"], [PROVIDER_ID], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sla_id"], ["sla.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "iaas_project_id", "provider_id", name="unique_projid_provider_couple"
        ),
        *add_project_cols,
        *common_id_cols,
        *common_create_update_cols,
        if_not_exists=True,
    )
    if conn.dialect.name == "sqlite":
        op.create_index(
            "ix_unique_provider_root",
            "project",
            ["provider_id"],
            unique=True,
            sqlite_where=sa.text("is_root = 1"),
            if_not_exists=True,
        )
    elif conn.dialect.name == "mysql":
        op.create_index(
            "ix_unique_provider_root", "project", ["provider_root_id"], unique=True
        )
    op.create_table(
        "regionoverrides",
        sa.Column(
            "default_public_net", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column(
            "default_private_net", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column(
            "private_net_proxy_host", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column(
            "private_net_proxy_user", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("region_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["region_id"], ["region.id"]),
        sa.PrimaryKeyConstraint("region_id", "project_id"),
        *common_create_update_cols,
        if_not_exists=True,
    )


def downgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    op.drop_table("user")
    op.drop_table("sla")
    op.drop_table("idpoverrides")
    op.drop_table("region")
    op.drop_table("regionoverrides")
    op.drop_table("identityprovider")
    op.drop_table("administrates")
    op.drop_table("evaluates")
    op.drop_table("project")
    op.drop_table("usergroup")
    op.drop_table("provider")
    if conn.dialect.name == "sqlite":
        op.drop_index(
            op.f("ix_unique_provider_root"),
            table_name="project",
            sqlite_where=sa.text("is_root = 1"),
        )
    elif conn.dialect.name == "mysql":
        op.drop_index(op.f("ix_unique_provider_root"), table_name="project")
