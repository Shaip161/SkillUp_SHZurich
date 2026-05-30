from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import gap, health, jobs, match, users
from app.config import settings

app = FastAPI(title="Job Matcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(match.router)
app.include_router(gap.router)
app.include_router(users.router)
