"""Pydantic 数据模型（与 SQLite 表一一对应）。"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.core.state_machine import Phase


class Project(BaseModel):
    id: str
    name: str
    logline: str = ""
    genre: str = ""
    style_notes: str = ""
    current_phase: Phase = Phase.INIT
    storage_dir: str
    created_at: datetime
    updated_at: datetime


class WorldDoc(BaseModel):
    project_id: str
    content_md: str = ""
    version: int = 0


class Character(BaseModel):
    id: str
    project_id: str
    name: str
    role: str = "配角"
    profile_md: str = ""
    updated_at: datetime


class CharacterRelationship(BaseModel):
    id: str
    project_id: str
    source_id: str
    target_id: str
    type: str
    note: str = ""


class OutlineNode(BaseModel):
    id: str
    project_id: str
    parent_id: str | None
    order: int
    title: str
    summary_md: str = ""
    chapter_id: str | None = None


class ChapterStatus(str, Enum):
    DRAFT = "draft"
    DRAFT_PARTIAL = "draft_partial"
    REVIEWING = "reviewing"
    FINAL = "final"


class Chapter(BaseModel):
    id: str
    project_id: str
    outline_node_id: str | None = None
    order: int
    title: str
    content_md: str = ""
    word_count: int = 0
    status: ChapterStatus = ChapterStatus.DRAFT
    created_at: datetime
    updated_at: datetime


class ChatMessage(BaseModel):
    id: str
    session_id: str
    project_id: str
    role: str
    content: str
    tool_calls_json: str = "[]"
    created_at: datetime


class ProjectContext(BaseModel):
    project_id: str
    phase: Phase = Phase.INIT
    rolling_summary: str = ""
    last_active_at: datetime | None = None
