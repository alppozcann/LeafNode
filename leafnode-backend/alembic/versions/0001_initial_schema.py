"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("wake_count", sa.Integer(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("humidity", sa.Float(), nullable=False),
        sa.Column("pressure", sa.Float(), nullable=False),
        sa.Column("light", sa.Float(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensor_readings_id", "sensor_readings", ["id"])
    op.create_index("ix_sensor_readings_device_id", "sensor_readings", ["device_id"])

    op.create_table(
        "plant_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plant_name", sa.String(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("temperature_min", sa.Float(), nullable=False),
        sa.Column("temperature_max", sa.Float(), nullable=False),
        sa.Column("humidity_min", sa.Float(), nullable=False),
        sa.Column("humidity_max", sa.Float(), nullable=False),
        sa.Column("pressure_min", sa.Float(), nullable=False),
        sa.Column("pressure_max", sa.Float(), nullable=False),
        sa.Column("light_min", sa.Float(), nullable=False),
        sa.Column("light_max", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )
    op.create_index("ix_plant_profiles_id", "plant_profiles", ["id"])
    op.create_index("ix_plant_profiles_device_id", "plant_profiles", ["device_id"])

    op.create_table(
        "anomaly_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("sensor_reading_id", sa.Integer(), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("expected_min", sa.Float(), nullable=True),
        sa.Column("expected_max", sa.Float(), nullable=True),
        sa.Column("rule_type", sa.String(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["sensor_reading_id"], ["sensor_readings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_anomaly_records_id", "anomaly_records", ["id"])
    op.create_index("ix_anomaly_records_device_id", "anomaly_records", ["device_id"])


def downgrade() -> None:
    op.drop_table("anomaly_records")
    op.drop_table("plant_profiles")
    op.drop_table("sensor_readings")
