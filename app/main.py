from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, SessionLocal
from app.data.seed_rebates import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Retrofit & Rebate Finder",
    description="Dashboard for Canadian homeowners to find energy retrofit rebates",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.rebates import router as rebates_router  # noqa: E402

app.include_router(rebates_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
