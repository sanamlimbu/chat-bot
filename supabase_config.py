from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

from config import config
from openai_config import openai_embeddings

supabase = create_client(config.supabase_url, config.supabase_service_key)

vector_store = SupabaseVectorStore(
    embedding=openai_embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
)
