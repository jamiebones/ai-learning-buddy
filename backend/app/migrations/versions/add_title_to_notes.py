"""add title column to notes table

Revision ID: add_title_to_notes
Revises: create_document_chunks_and_embeddings
Create Date: 2024-04-02 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_title_to_notes'
down_revision = 'create_document_chunks_and_embeddings'
branch_labels = None
depends_on = None

def upgrade():
    # Add title column to notes table
    op.add_column('notes', sa.Column('title', sa.String(), nullable=False, server_default='Untitled'))

def downgrade():
    # Remove title column from notes table
    op.drop_column('notes', 'title') 