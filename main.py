import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from graph import State, graph
from openai_config import openai_embeddings
from supabase_config import supabase

load_dotenv()

ALLOWED_FILE_TYPE = "application/pdf"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = "uploads"

app = FastAPI()


@app.get("/hello")
def hello():
    return {
        "message": "Hello World",
        "time": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
    }


class ChatInput(BaseModel):
    question: str


@app.post("/chat")
def chat(input: ChatInput):
    if not input.question:
        raise HTTPException(status_code=400, detail="No user input.")

    initial_state = State(question=input.question, context=[], answer="")
    result = graph.invoke(initial_state)

    return result["answer"]


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
):
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="127.0.0.1", port=8000)
