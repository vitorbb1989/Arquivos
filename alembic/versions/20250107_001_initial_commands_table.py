"""Initial commands table

Revision ID: 001_initial
Revises:
Create Date: 2025-01-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria tabela commands"""
    op.create_table(
        'commands',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('command_template', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('category', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('variables', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Índices para melhor performance
    op.create_index(op.f('ix_commands_name'), 'commands', ['name'], unique=False)
    op.create_index(op.f('ix_commands_category'), 'commands', ['category'], unique=False)


def downgrade() -> None:
    """Remove tabela commands"""
    op.drop_index(op.f('ix_commands_category'), table_name='commands')
    op.drop_index(op.f('ix_commands_name'), table_name='commands')
    op.drop_table('commands')
