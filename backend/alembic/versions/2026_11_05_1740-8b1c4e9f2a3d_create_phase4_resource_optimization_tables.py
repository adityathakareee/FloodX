"""Create Phase 4 Emergency Resource Optimization and Decision Intelligence tables

Revision ID: 8b1c4e9f2a3d
Revises: 59a8c1e2f3d4
Create Date: 2026-11-05 17:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b1c4e9f2a3d'
down_revision = '59a8c1e2f3d4'
branch_labels = None
depends_on = None


def upgrade():
    # 1. emergency_resources table
    op.create_table(
        'emergency_resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('available_quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('allocated_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('operational_status', sa.String(length=32), nullable=False, server_default='AVAILABLE'),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('base_address', sa.String(length=255), nullable=True),
        sa.Column('assigned_location_name', sa.String(length=255), nullable=True),
        sa.Column('responsible_authority', sa.String(length=128), nullable=False, server_default='PMC Disaster Management Cell'),
        sa.Column('capacity_specs', sa.JSON(), nullable=True),
        sa.Column('is_simulated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('data_source', sa.String(length=128), nullable=False, server_default='MUNICIPAL_REGISTER_SIMULATED'),
        sa.Column('verification_status', sa.String(length=64), nullable=False, server_default='SIMULATED_DEMO'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource_id')
    )
    op.create_index(op.f('ix_emergency_resources_id'), 'emergency_resources', ['id'], unique=False)
    op.create_index(op.f('ix_emergency_resources_resource_id'), 'emergency_resources', ['resource_id'], unique=True)
    op.create_index(op.f('ix_emergency_resources_category'), 'emergency_resources', ['category'], unique=False)
    op.create_index(op.f('ix_emergency_resources_resource_type'), 'emergency_resources', ['resource_type'], unique=False)
    op.create_index(op.f('ix_emergency_resources_operational_status'), 'emergency_resources', ['operational_status'], unique=False)

    # 2. resource_inventory_history table
    op.create_table(
        'resource_inventory_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('previous_status', sa.String(length=32), nullable=True),
        sa.Column('new_status', sa.String(length=32), nullable=True),
        sa.Column('previous_available', sa.Integer(), nullable=True),
        sa.Column('new_available', sa.Integer(), nullable=True),
        sa.Column('actor', sa.String(length=128), nullable=False, server_default='Disaster Management Administrator'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['resource_id'], ['emergency_resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resource_inventory_history_id'), 'resource_inventory_history', ['id'], unique=False)
    op.create_index(op.f('ix_resource_inventory_history_resource_id'), 'resource_inventory_history', ['resource_id'], unique=False)

    # 3. emergency_demand_assessments table
    op.create_table(
        'emergency_demand_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assessment_id', sa.String(length=64), nullable=False),
        sa.Column('sector_id', sa.String(length=64), nullable=False),
        sa.Column('sector_name', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('priority_level', sa.String(length=32), nullable=False, server_default='MODERATE_PRIORITY'),
        sa.Column('priority_score', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('demand_score', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('accessibility_score', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('infrastructure_score', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('evidence_type', sa.String(length=64), nullable=False, server_default='TERRAIN_SUSCEPTIBILITY'),
        sa.Column('required_ambulances', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_rescue_teams', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_food_packets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_water_liters', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_medical_kits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_blankets', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('urgency_reason', sa.Text(), nullable=True),
        sa.Column('missing_data_notes', sa.Text(), nullable=True),
        sa.Column('is_simulated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assessment_id')
    )
    op.create_index(op.f('ix_emergency_demand_assessments_id'), 'emergency_demand_assessments', ['id'], unique=False)
    op.create_index(op.f('ix_emergency_demand_assessments_sector_id'), 'emergency_demand_assessments', ['sector_id'], unique=False)
    op.create_index(op.f('ix_emergency_demand_assessments_priority_level'), 'emergency_demand_assessments', ['priority_level'], unique=False)

    # 4. optimization_runs table
    op.create_table(
        'optimization_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('solver_type', sa.String(length=64), nullable=False, server_default='ORTOOLS_MIP_SCIP'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='OPTIMAL'),
        sa.Column('objective_value', sa.Float(), nullable=True),
        sa.Column('total_response_time_minutes', sa.Float(), nullable=True),
        sa.Column('total_assigned_resources', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_unmet_demand', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('demand_coverage_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('execution_duration_ms', sa.Float(), nullable=True),
        sa.Column('parameters_json', sa.JSON(), nullable=True),
        sa.Column('summary_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id')
    )
    op.create_index(op.f('ix_optimization_runs_id'), 'optimization_runs', ['id'], unique=False)
    op.create_index(op.f('ix_optimization_runs_run_id'), 'optimization_runs', ['run_id'], unique=True)
    op.create_index(op.f('ix_optimization_runs_status'), 'optimization_runs', ['status'], unique=False)

    # 5. resource_allocations table
    op.create_table(
        'resource_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('allocation_id', sa.String(length=64), nullable=False),
        sa.Column('optimization_run_id', sa.Integer(), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('demand_sector_id', sa.String(length=64), nullable=False),
        sa.Column('assigned_quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('estimated_travel_time_sec', sa.Float(), nullable=True),
        sa.Column('estimated_distance_m', sa.Float(), nullable=True),
        sa.Column('route_edge_ids', sa.JSON(), nullable=True),
        sa.Column('route_geojson', sa.JSON(), nullable=True),
        sa.Column('route_uncertainty_note', sa.Text(), nullable=True),
        sa.Column('allocated_by', sa.String(length=128), nullable=False, server_default='Disaster Management Administrator'),
        sa.Column('approved_by', sa.String(length=128), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['optimization_run_id'], ['optimization_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resource_id'], ['emergency_resources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('allocation_id')
    )
    op.create_index(op.f('ix_resource_allocations_id'), 'resource_allocations', ['id'], unique=False)
    op.create_index(op.f('ix_resource_allocations_allocation_id'), 'resource_allocations', ['allocation_id'], unique=True)
    op.create_index(op.f('ix_resource_allocations_status'), 'resource_allocations', ['status'], unique=False)
    op.create_index(op.f('ix_resource_allocations_demand_sector_id'), 'resource_allocations', ['demand_sector_id'], unique=False)

    # 6. disaster_scenarios table
    op.create_table(
        'disaster_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rainfall_multiplier', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('dam_discharge_cfs', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('simulated_closed_edge_ids', sa.JSON(), nullable=True),
        sa.Column('resource_availability_factor', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('demand_surge_factor', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_by', sa.String(length=128), nullable=False, server_default='Disaster Management Administrator'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scenario_id')
    )
    op.create_index(op.f('ix_disaster_scenarios_id'), 'disaster_scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_disaster_scenarios_scenario_id'), 'disaster_scenarios', ['scenario_id'], unique=True)


def downgrade():
    op.drop_table('disaster_scenarios')
    op.drop_table('resource_allocations')
    op.drop_table('optimization_runs')
    op.drop_table('emergency_demand_assessments')
    op.drop_table('resource_inventory_history')
    op.drop_table('emergency_resources')

