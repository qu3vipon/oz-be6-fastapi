"""Add PostComment

Revision ID: bbaee5254aae
Revises: f68c0c8281ae
Create Date: 2024-12-11 13:15:24.341217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbaee5254aae'
down_revision: Union[str, None] = 'f68c0c8281ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('post_comment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['post_comment.id'], ),
    sa.ForeignKeyConstraint(['post_id'], ['feed_post.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['service_user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('post_comment')
    # ### end Alembic commands ###