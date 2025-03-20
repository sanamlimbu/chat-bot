from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    openai_api_key: str
    langchain_api_key: str
    langchain_project: str
    langchain_tracing: bool
    supabase_url: str
    supabase_service_key: str


config = Config()
