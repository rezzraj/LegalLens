from fastapi import FastAPI
from pydantic import BaseModel
from main import model_generate
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/ask")
async def ask(query: Query):
    answer = model_generate(query.question)
    return {"answer": answer}

