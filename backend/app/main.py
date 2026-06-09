"""FastAPI 入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import chat, chapters, characters, outline, projects, world, ws


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 触发依赖注入并初始化 schema
    from app.api.deps import get_file_repo, get_sqlite_repo

    get_sqlite_repo()
    get_file_repo()
    yield


app = FastAPI(title="Novel Agent", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(projects.router)
app.include_router(world.router)
app.include_router(characters.router)
app.include_router(outline.router)
app.include_router(chapters.router)
app.include_router(chat.router)
app.include_router(ws.router)
