"""empty message

Revision ID: ca3a68826dbb
Revises: c85b7622c4e5
Create Date: 2020-02-12 20:58:37.928563

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ca3a68826dbb"
down_revision = "c85b7622c4e5"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("user", sa.Column("authenticated", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "authenticated")
    # ### end Alembic commands ###
