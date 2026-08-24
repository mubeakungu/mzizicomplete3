"""Add strategy performance tracking

Revision ID: ADD_STRATEGY_TRACKING
Revises: [PREVIOUS_MIGRATION_ID]
Create Date: 2026-08-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_strategy_tracking_001'
down_revision = None  # Set to previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Create strategy_performance table
    op.create_table(
        'strategy_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_type', sa.String(50), nullable=False),
        sa.Column('strategy_name', sa.String(50), nullable=False),
        sa.Column('total_bets', sa.Integer(), server_default='0'),
        sa.Column('total_wagered', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total_won', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total_lost', sa.Numeric(10, 2), server_default='0'),
        sa.Column('win_count', sa.Integer(), server_default='0'),
        sa.Column('loss_count', sa.Integer(), server_default='0'),
        sa.Column('best_profit', sa.Numeric(10, 2), server_default='0'),
        sa.Column('worst_loss', sa.Numeric(10, 2), server_default='0'),
        sa.Column('average_multiplier', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for faster queries
    op.create_index(
        'ix_strategy_performance_user_id_game_type',
        'strategy_performance',
        ['user_id', 'game_type'],
        unique=False
    )
    
    op.create_index(
        'ix_strategy_performance_strategy_name',
        'strategy_performance',
        ['strategy_name'],
        unique=False
    )


def downgrade():
    op.drop_index('ix_strategy_performance_strategy_name', table_name='strategy_performance')
    op.drop_index('ix_strategy_performance_user_id_game_type', table_name='strategy_performance')
    op.drop_table('strategy_performance')
