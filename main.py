import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from langchain import hub
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from mangum import Mangum
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from supabase import create_client
from typing_extensions import List, TypedDict

load_dotenv()


class Config(BaseSettings):
    openai_api_key: str
    langchain_api_key: str
    langchain_project: str
    langchain_tracing: bool
    supabase_url: str
    supabase_service_key: str
    telegram_bot_token: str


config = Config()

ALLOWED_FILE_TYPE = "application/pdf"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = "/tmp/uploads"
TELEGRAM_URL = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"

supabase = create_client(config.supabase_url, config.supabase_service_key)


openai_llm = ChatOpenAI(
    model_name="gpt-4o",
    api_key=config.openai_api_key,
    temperature=0.7,
    max_retries=2,
)

openai_embeddings = OpenAIEmbeddings(
    api_key=config.openai_api_key, model="text-embedding-3-small"
)

vector_store = SupabaseVectorStore(
    embedding=openai_embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
)

prompt = hub.pull("rlm/rag-prompt")


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = openai_llm.invoke(messages)
    return {"answer": response.content}


graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()


app = FastAPI(title="Telegram RAG Chat Bot", version="1.0.0")


@app.middleware("http")
async def debug_request_log(request: Request, call_next):
    print(f"REQUEST: {request.method} {request.url}")
    response = await call_next(request)
    print(f"RESPONSE: {response.status_code}")
    return response


@app.get("/health")
def health():
    return {
        "message": "Hello World",
        "time": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
    }


class ChatInput(BaseModel):
    question: str


@app.post("/chat")
def chat(input: ChatInput):
    initial_state = State(question=input.question, context=[], answer="")
    result = graph.invoke(initial_state)

    return result["answer"]


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    if file.content_type != ALLOWED_FILE_TYPE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only PDF is allowed.",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )
        docs = text_splitter.split_documents(documents)

        SupabaseVectorStore.from_documents(
            docs,
            embeddings=openai_embeddings,
            client=supabase,
            table_name="documents",
            query_name="match_documents",
            chunk_size=500,
        )

        return {"message": "PDF processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()

    message = payload.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")

    if not chat_id or not text:
        return {"status": "ignored"}

    try:
        state = State(question=text, context=[], answer="")
        result = graph.invoke(state)
        answer = result["answer"]
    except Exception as e:
        answer = "Sorry, an error occurred while processing your request."

    requests.post(TELEGRAM_URL, json={"chat_id": chat_id, "text": answer})

    return {"status": "ok"}


handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="127.0.0.1", port=8000)
