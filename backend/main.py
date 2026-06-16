"""
WooMMO Web — FastAPI Entry Point
"""
import sys
sys.path.insert(0, "/opt/woommo/logic")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, admin, jobs, products, links
from app.models.database import init_db

app = FastAPI(
    title="WooMMO Web API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sau khi deploy đổi thành domain thật
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(jobs.router)
app.include_router(products.router)
app.include_router(links.router)


@app.on_event("startup")
def startup():
    init_db()
    print("✅ WooMMO Web API started")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "woommo-api"}
