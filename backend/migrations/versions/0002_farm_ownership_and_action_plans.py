"""farm_ownership_and_action_plans

Revision ID: 0002_farm_ownership_and_action_plans
Revises: 0001_initial_10_models
Create Date: 2026-10-18 08:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_ownership_action_plans'
down_revision = '0001_initial_10_models'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add owner_token_hash to farm_profiles
    with op.batch_alter_table('farm_profiles') as batch_op:
        batch_op.add_column(sa.Column('owner_token_hash', sa.String(length=64), nullable=True))

    # Create farm_action_plans table
    op.create_table(
        'farm_action_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), sa.ForeignKey('farm_profiles.id'), nullable=True),
        sa.Column('crop_recommendation_id', sa.Integer(), sa.ForeignKey('crop_recommendations.id'), nullable=True),
        sa.Column('crop_name', sa.String(length=128), nullable=False),
        sa.Column('season', sa.String(length=32), nullable=True),
        sa.Column('location_str', sa.String(length=256), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('immediate_actions_json', sa.Text(), nullable=True),
        sa.Column('this_week_plan_json', sa.Text(), nullable=True),
        sa.Column('disclaimer', sa.Text(), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='live', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('farm_action_plans')
    with op.batch_alter_table('farm_profiles') as batch_op:
        batch_op.drop_column('owner_token_hash')
