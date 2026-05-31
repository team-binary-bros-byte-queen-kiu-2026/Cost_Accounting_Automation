"""
ConstructAI — FastAPI backend entry point.
Run: uvicorn backend.main:app --reload --port 8000
"""
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .routers import health, analyze, chat, speak, transcribe, admin
from .database.seed_prices import seed as seed_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed database on startup if empty
    try:
        seed_db()
    except Exception as e:
        print(f"[startup] DB seed skipped: {e}")
    yield


app = FastAPI(
    title="ConstructAI",
    description="AI-powered construction cost estimator for the Georgian market.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.environ.get("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(analyze.router, tags=["analysis"])
app.include_router(chat.router, tags=["chat"])
app.include_router(speak.router, tags=["audio"])
app.include_router(transcribe.router, tags=["audio"])
app.include_router(admin.router, tags=["admin"])


@app.get("/")
def root():
    return {"service": "ConstructAI Backend", "docs": "/docs"}
