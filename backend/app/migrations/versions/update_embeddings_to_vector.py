"""update embeddings to use pgvector

Revision ID: update_embeddings_to_vector
Revises: create_document_chunks_and_embeddings
Create Date: 2025-04-04 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = 'update_embeddings_to_vector'
down_revision = 'create_document_chunks_and_embeddings'
branch_labels = None
depends_on = None

def upgrade():
    # Create pgvector extension if it doesn't exist
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Drop existing embeddings for clean update
    op.execute('TRUNCATE TABLE document_embeddings')
    
    # Alter the column type to vector
    op.execute('ALTER TABLE document_embeddings ALTER COLUMN embedding TYPE vector(384) USING NULL')
    
    # Create vector index for similarity search
    op.execute('CREATE INDEX IF NOT EXISTS document_embeddings_vector_idx ON document_embeddings USING ivfflat (embedding vector_cosine_ops)')

def downgrade():
    # Drop the index
    op.execute('DROP INDEX IF EXISTS document_embeddings_vector_idx')
    
    # Change back to VARCHAR
    op.execute('ALTER TABLE document_embeddings ALTER COLUMN embedding TYPE VARCHAR') 