"""阶段状态机测试（新设计：INIT → FOUNDATION → WRITING → DONE）。"""
import pytest

from app.core.errors import ErrorCode, ProtocolError
from app.core.state_machine import (
    Phase,
    assert_legal_transition,
    is_legal,
    migrate_legacy_phase,
)


def test_phase_enum_values() -> None:
    assert Phase.INIT.value == "INIT"
    assert Phase.FOUNDATION.value == "FOUNDATION"
    assert Phase.WRITING.value == "WRITING"
    assert Phase.DONE.value == "DONE"


@pytest.mark.parametrize(
    "frm,to",
    [
        (Phase.INIT, Phase.FOUNDATION),
        (Phase.FOUNDATION, Phase.WRITING),
        (Phase.WRITING, Phase.DONE),
    ],
)
def test_legal_forward_transitions(frm: Phase, to: Phase) -> None:
    assert is_legal(frm, to) is True
    assert_legal_transition(frm, to)  # 不抛


@pytest.mark.parametrize(
    "frm,to",
    [
        (Phase.FOUNDATION, Phase.INIT),
        (Phase.WRITING, Phase.FOUNDATION),
        (Phase.WRITING, Phase.INIT),
        (Phase.DONE, Phase.WRITING),
        (Phase.DONE, Phase.FOUNDATION),
        (Phase.DONE, Phase.INIT),
    ],
)
def test_legal_backward_transitions(frm: Phase, to: Phase) -> None:
    """任意阶段可回退一格或更多。"""
    assert is_legal(frm, to) is True


def test_self_transition_illegal() -> None:
    """同阶段转移视为非法。"""
    assert is_legal(Phase.WRITING, Phase.WRITING) is False


@pytest.mark.parametrize(
    "frm,to",
    [
        (Phase.INIT, Phase.WRITING),
        (Phase.INIT, Phase.DONE),
        (Phase.FOUNDATION, Phase.DONE),
    ],
)
def test_skipping_forward_illegal(frm: Phase, to: Phase) -> None:
    """不能跳阶段向前。"""
    assert is_legal(frm, to) is False
    with pytest.raises(ProtocolError) as ei:
        assert_legal_transition(frm, to)
    assert ei.value.code == ErrorCode.STATE_ILLEGAL_TRANSITION


def test_legacy_phase_migration() -> None:
    """老 phase 字符串应被迁移到新 phase。"""
    assert migrate_legacy_phase("WORLD") == Phase.FOUNDATION
    assert migrate_legacy_phase("CHARACTERS") == Phase.FOUNDATION
    assert migrate_legacy_phase("OUTLINE") == Phase.WRITING
    assert migrate_legacy_phase("WRITING") == Phase.WRITING
    assert migrate_legacy_phase("DONE") == Phase.DONE
    assert migrate_legacy_phase("INIT") == Phase.INIT
    assert migrate_legacy_phase("") == Phase.INIT
    assert migrate_legacy_phase("garbage") == Phase.WRITING  # 保守回退
