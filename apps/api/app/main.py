from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.extension import _rate_limit_exceeded_handler

from app.api.routes import (
    admin,
    alerts,
    auth,
    avatar,
    children,
    comfort_modes,
    conversation,
    data_rights,
    helper_profiles,
    liveavatar,
    parent,
    voice,
)
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Always Near API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.backend_cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(parent.router)
app.include_router(children.router)
app.include_router(helper_profiles.router)
app.include_router(avatar.router)
app.include_router(voice.router)
app.include_router(conversation.router)
app.include_router(comfort_modes.router)
app.include_router(alerts.router)
app.include_router(admin.router)
app.include_router(data_rights.router)
app.include_router(liveavatar.router)
