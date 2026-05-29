from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import agents, analytics, messages, tasks, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Autonomous Enterprise AI Workforce",
        description="Multi-agent orchestration platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(websocket.router, tags=["websocket"])

    @app.get("/")
    async def root():
        return {
            "service": "Autonomous Enterprise AI Workforce",
            "status": "online",
            "version": "0.1.0",
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy", "environment": settings.environment}

    return app


app = create_app()


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("ENVIRONMENT", "development") == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
