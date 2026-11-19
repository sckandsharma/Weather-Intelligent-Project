from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import auth, chat, documents, evaluation, users, weather
from app.core.config import settings
from app.core.security import limiter
from app.database.session import get_db

app = FastAPI(title=settings.APP_NAME)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(weather.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")


@app.get("/")
def home():
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/database")
def database_health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT current_database(), current_user")).one()
    return {
        "status": "healthy",
        "database": result[0],
        "user": result[1],
    }