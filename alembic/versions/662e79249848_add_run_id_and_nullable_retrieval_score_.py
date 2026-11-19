"""add_run_id_and_nullable_retrieval_score_to_evaluation_results

Revision ID: 662e79249848
Revises: 39fe8ebd5e3a
Create Date: 2026-11-19 03:08:22.549099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '662e79249848'
down_revision: Union[str, Sequence[str], None] = '39fe8ebd5e3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('evaluation_results', sa.Column('run_id', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_evaluation_results_run_id'), 'evaluation_results', ['run_id'], unique=False)
    op.alter_column('evaluation_results', 'retrieval_score', existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    op.alter_column('evaluation_results', 'retrieval_score', existing_type=sa.Float(), nullable=False)
    op.drop_index(op.f('ix_evaluation_results_run_id'), table_name='evaluation_results')
    op.drop_column('evaluation_results', 'run_id')
