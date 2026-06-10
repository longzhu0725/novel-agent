"""项目阶段状态机。"""
from __future__ import annotations

from enum import Enum

from app.core.errors import ErrorCode, ProtocolError


class Phase(str, Enum):
    """项目所处阶段。"""

    INIT = "INIT"
    FOUNDATION = "FOUNDATION"   # 基础设定（世界观 + 人物志，并行）
    WRITING = "WRITING"         # 撰文（按大纲分组写章节）
    DONE = "DONE"


# 阶段序号
_ORDER: dict[Phase, int] = {
    Phase.INIT: 0,
    Phase.FOUNDATION: 1,
    Phase.WRITING: 2,
    Phase.DONE: 3,
}


def is_legal(frm: Phase, to: Phase) -> bool:
    """判断从 frm 到 to 是否合法。规则：
    - 同阶段：非法
    - 向前一格：合法
    - 向后任意格：合法（用于二稿回看）
    - 向前跳多格：非法
    """
    if frm == to:
        return False
    f, t = _ORDER[frm], _ORDER[to]
    return t == f + 1 or t < f


def assert_legal_transition(frm: Phase, to: Phase) -> None:
    """非法转移抛 ProtocolError。"""
    if not is_legal(frm, to):
        raise ProtocolError(
            code=ErrorCode.STATE_ILLEGAL_TRANSITION,
            message=f"非法阶段转移：{frm.value} -> {to.value}",
        )


# 老 phase → 新 phase 的迁移映射
# 旧版本：INIT → WORLD → CHARACTERS → OUTLINE → WRITING → DONE
# 新版本：INIT → FOUNDATION → WRITING → DONE
LEGACY_PHASE_MAP: dict[str, Phase] = {
    "WORLD": Phase.FOUNDATION,
    "CHARACTERS": Phase.FOUNDATION,
    "OUTLINE": Phase.WRITING,
    # "WRITING" 和 "DONE" 在新版本里仍存在
    "INIT": Phase.INIT,
}


def migrate_legacy_phase(value: str) -> Phase:
    """老 phase 字符串迁移到新 Phase。未知值默认 WRITING（保守）。"""
    if not value:
        return Phase.INIT
    try:
        return Phase(value)
    except ValueError:
        pass
    return LEGACY_PHASE_MAP.get(value, Phase.WRITING)
