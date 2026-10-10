"""Add cards JSON column to messages table

Revision ID: 0002_add_cards_to_messages
Revises: 0001_initial_schema
Create Date: 2026-10-10 17:45:00
"""

from alembic import op
import sqlalchemy as sa


revision = '0002_add_cards_to_messages'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('messages', sa.Column('cards', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('messages', 'cards')
