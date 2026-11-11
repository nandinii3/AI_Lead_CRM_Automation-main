import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.routers import leads
from app.database import create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="AI Lead CRM Automation", version="0.2.0", lifespan=lifespan)
app.include_router(leads.router)


@app.get("/health")
def health():
    return {"status": "ok"}
