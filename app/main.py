import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import auth, expenses


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Expense Tracker", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(expenses.router)


@app.get("/health")
def health():
    return {"status": "ok"}


if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
