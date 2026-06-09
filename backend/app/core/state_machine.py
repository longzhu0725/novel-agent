"""项目阶段状态机。"""
from __future__ import annotations

from enum import Enum

from app.core.errors import ErrorCode, ProtocolError


class Phase(str, Enum):
    """项目所处阶段。"""

    INIT = "INIT"
    WORLD = "WORLD"
    CHARACTERS = "CHARACTERS"
    OUTLINE = "OUTLINE"
    WRITING = "WRITING"
    DONE = "DONE"


# 阶段序号，用于"向前一格"的回退
_ORDER: dict[Phase, int] = {
    Phase.INIT: 0,
    Phase.WORLD: 1,
    Phase.CHARACTERS: 2,
    Phase.OUTLINE: 3,
    Phase.WRITING: 4,
    Phase.DONE: 5,
}


def is_legal(frm: Phase, to: Phase) -> bool:
    """判断从 frm 到 to 是否合法。规则：
    - 同阶段：非法
    - 向前一格：合法（如 WORLD -> CHARACTERS）
    - 向后任意格：合法（如 WRITING -> WORLD，二稿）
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
