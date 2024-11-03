import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from .dedupe_it.service import dedupe_records
from .dedupe_it.models import Record
from .dedupe_it.logger import logger
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    port = os.getenv("PORT", "8080")
    logger.info(f"Starting server with PORT={port}")
    yield
    # Shutdown
    logger.info("Shutting down server")


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/dedupe")
async def dedupe(records: List[Record], request: Request):
    try:
        # Check number of records
        if len(records) > 100:
            raise HTTPException(
                status_code=413,
                detail="Too many records. Maximum allowed is 100 records.",
            )

        # Check payload size (100KB = 102400 bytes)
        body = await request.body()
        if len(body) > 102400:
            raise HTTPException(
                status_code=413,
                detail="Request too large. Maximum allowed size is 100KB.",
            )

        result = await dedupe_records(records)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "port": os.getenv("PORT", "8080")}
