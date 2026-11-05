"""create_phase3_evacuation_tables

Revision ID: 482a93df1b7c
Revises: 316c69d4d4cf
Create Date: 2026-11-05 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = '482a93df1b7c'
down_revision: Union[str, None] = '316c69d4d4cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Road Closures
    op.create_table(
        'road_closures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('edge_id', sa.String(length=50), nullable=False),
        sa.Column('source_feature_id', sa.Integer(), nullable=True),
        sa.Column('road_name', sa.String(length=255), nullable=False),
        sa.Column('closure_status', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('verification_source', sa.String(length=255), nullable=False),
        sa.Column('reporting_authority', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('audit_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_road_closures_edge_id'), 'road_closures', ['edge_id'], unique=False)
    op.create_index(op.f('ix_road_closures_id'), 'road_closures', ['id'], unique=False)
    op.create_index(op.f('ix_road_closures_is_active'), 'road_closures', ['is_active'], unique=False)
    op.create_index('ix_road_closures_edge_active', 'road_closures', ['edge_id', 'is_active'], unique=False)

    # 2. Shelters
    op.create_table(
        'shelters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('facility_id', sa.Integer(), nullable=True),
        sa.Column('osm_id', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('facility_type', sa.String(length=50), nullable=False),
        sa.Column('verification_status', sa.String(length=50), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('geom', Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=True),
        sa.Column('total_capacity', sa.Integer(), nullable=True),
        sa.Column('current_occupancy', sa.Integer(), nullable=False),
        sa.Column('available_capacity', sa.Integer(), nullable=True),
        sa.Column('has_medical_support', sa.Boolean(), nullable=False),
        sa.Column('is_wheelchair_accessible', sa.Boolean(), nullable=False),
        sa.Column('has_generator_power', sa.Boolean(), nullable=False),
        sa.Column('emergency_contact', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('verified_by', sa.String(length=100), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('properties_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['facility_id'], ['spatial_features.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shelters_id'), 'shelters', ['id'], unique=False)
    op.create_index(op.f('ix_shelters_name'), 'shelters', ['name'], unique=False)
    op.create_index(op.f('ix_shelters_osm_id'), 'shelters', ['osm_id'], unique=False)
    op.create_index(op.f('ix_shelters_facility_id'), 'shelters', ['facility_id'], unique=False)
    op.create_index(op.f('ix_shelters_verification_status'), 'shelters', ['verification_status'], unique=False)

    # 3. Shelter Update History
    op.create_table(
        'shelter_update_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shelter_id', sa.Integer(), nullable=False),
        sa.Column('update_type', sa.String(length=50), nullable=False),
        sa.Column('previous_value', sa.String(length=255), nullable=True),
        sa.Column('new_value', sa.String(length=255), nullable=False),
        sa.Column('updated_by', sa.String(length=100), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['shelter_id'], ['shelters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shelter_update_history_id'), 'shelter_update_history', ['id'], unique=False)
    op.create_index(op.f('ix_shelter_update_history_shelter_id'), 'shelter_update_history', ['shelter_id'], unique=False)

    # 4. Evacuation Audit Logs
    op.create_table(
        'evacuation_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('details_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evacuation_audit_logs_id'), 'evacuation_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_evacuation_audit_logs_event_type'), 'evacuation_audit_logs', ['event_type'], unique=False)


def downgrade() -> None:
    op.drop_table('evacuation_audit_logs')
    op.drop_table('shelter_update_history')
    op.drop_table('shelters')
    op.drop_table('road_closures')

