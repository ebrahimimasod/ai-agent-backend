from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine
from app.db.models import Base
from app.api.routes_ingest import router as ingest_router
from app.api.routes_posts import router as posts_router
from app.api.routes_chat import router as chat_router

app = FastAPI(title=settings.APP_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-create tables for MVP
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(ingest_router)
app.include_router(posts_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"ok": True}
