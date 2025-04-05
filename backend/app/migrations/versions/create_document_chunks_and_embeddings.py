"""create document chunks and embeddings tables

Revision ID: create_document_chunks_and_embeddings
Revises: previous_migration
Create Date: 2024-04-02 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = 'create_document_chunks_and_embeddings'
down_revision = 'previous_migration'  # Replace with your previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('notes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_type', sa.String(), nullable=False),
        sa.Column('chunk_metadata', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )
    
    # Create document_embeddings table with vector type
    op.create_table(
        'document_embeddings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('chunk_id', UUID(as_uuid=True), sa.ForeignKey('document_chunks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('embedding', sa.String(), nullable=False),  # Will be altered to vector type
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'))
    )
    
    # Alter embedding column to vector type
    op.execute('ALTER TABLE document_embeddings ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)')
    
    # Create indexes
    op.create_index('idx_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_document_embeddings_chunk_id', 'document_embeddings', ['chunk_id'])
    op.create_index('idx_document_embeddings_vector', 'document_embeddings', ['embedding'], postgresql_using='ivfflat')

def downgrade():
    op.drop_table('document_embeddings')
    op.drop_table('document_chunks')
    op.execute('DROP EXTENSION IF EXISTS vector') 