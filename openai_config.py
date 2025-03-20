from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import config

openai_llm = ChatOpenAI(
    model_name="gpt-4o",
    api_key=config.openai_api_key,
    temperature=0.7,
    max_retries=2,
)

openai_embeddings = OpenAIEmbeddings(
    api_key=config.openai_api_key, model="text-embedding-3-small"
)
