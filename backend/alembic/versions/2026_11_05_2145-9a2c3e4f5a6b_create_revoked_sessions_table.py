"""Create persistent authority session revocation table for Phase 5.2

Revision ID: 9a2c3e4f5a6b
Revises: 8b1c4e9f2a3d
Create Date: 2026-11-05 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a2c3e4f5a6b'
down_revision = '8b1c4e9f2a3d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'revoked_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('actor', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(length=128), nullable=False, server_default='LOGOUT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti')
    )
    op.create_index(op.f('ix_revoked_sessions_id'), 'revoked_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_revoked_sessions_jti'), 'revoked_sessions', ['jti'], unique=True)
    op.create_index(op.f('ix_revoked_sessions_expires_at'), 'revoked_sessions', ['expires_at'], unique=False)
    op.create_index('ix_revoked_sessions_jti_expires', 'revoked_sessions', ['jti', 'expires_at'], unique=False)


def downgrade():
    op.drop_index('ix_revoked_sessions_jti_expires', table_name='revoked_sessions')
    op.drop_index(op.f('ix_revoked_sessions_expires_at'), table_name='revoked_sessions')
    op.drop_index(op.f('ix_revoked_sessions_jti'), table_name='revoked_sessions')
    op.drop_index(op.f('ix_revoked_sessions_id'), table_name='revoked_sessions')
    op.drop_table('revoked_sessions')

