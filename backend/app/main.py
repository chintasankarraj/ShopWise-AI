import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analyze import router as analyze_router

load_dotenv()

app = FastAPI(title="ShopWise AI API")

# FRONTEND_URL supports a single origin or a comma-separated list
# (e.g. "https://shopwise.example.com,http://localhost:3000") so
# the deployed frontend origin can be added without touching code.
_frontend_origins = os.getenv("FRONTEND_URL", "http://localhost:3000")

allow_origins = [
    origin.strip()
    for origin in _frontend_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/")
def home():
    return {
        "message": "ShopWise AI Backend Running 🚀"
    }