"""Initial migration for SQLite

Revision ID: 9511a14d000f
Revises: 
Create Date: 2025-01-09 18:46:00.366514

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9511a14d000f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('series_base',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('date_create', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('date_update', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('time_series_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('date_create', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('date_update', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('series_group',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('series_code', sa.String(length=10), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['series_base.id'], ),
    sa.ForeignKeyConstraint(['parent_id'], ['series_group.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('series_code')
    )
    op.create_table('time_series',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('delta_type', sa.String(length=10), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['series_base.id'], ),
    sa.ForeignKeyConstraint(['type_id'], ['time_series_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('data_point',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('date_release', sa.Date(), nullable=True),
    sa.Column('time_series_id', sa.Integer(), nullable=False),
    sa.Column('date_create', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('date_update', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['time_series_id'], ['time_series.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('seriesgroup_seriesbase',
    sa.Column('seriesgroup_id', sa.Integer(), nullable=False),
    sa.Column('seriesbase_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['seriesbase_id'], ['series_base.id'], ),
    sa.ForeignKeyConstraint(['seriesgroup_id'], ['series_group.id'], ),
    sa.PrimaryKeyConstraint('seriesgroup_id', 'seriesbase_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('seriesgroup_seriesbase')
    op.drop_table('data_point')
    op.drop_table('time_series')
    op.drop_table('series_group')
    op.drop_table('time_series_type')
    op.drop_table('series_base')
    # ### end Alembic commands ###