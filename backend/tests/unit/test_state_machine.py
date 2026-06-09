"""阶段状态机测试。"""
import pytest

from app.core.errors import ErrorCode, ProtocolError
from app.core.state_machine import Phase, assert_legal_transition, is_legal


def test_phase_enum_values() -> None:
    assert Phase.INIT.value == "INIT"
    assert Phase.WORLD.value == "WORLD"
    assert Phase.CHARACTERS.value == "CHARACTERS"
    assert Phase.OUTLINE.value == "OUTLINE"
    assert Phase.WRITING.value == "WRITING"
    assert Phase.DONE.value == "DONE"


@pytest.mark.parametrize(
    "frm,to",
    [
        (Phase.INIT, Phase.WORLD),
        (Phase.WORLD, Phase.CHARACTERS),
        (Phase.CHARACTERS, Phase.OUTLINE),
        (Phase.OUTLINE, Phase.WRITING),
        (Phase.WRITING, Phase.DONE),
    ],
)
def test_legal_forward_transitions(frm: Phase, to: Phase) -> None:
    assert is_legal(frm, to) is True
    assert_legal_transition(frm, to)  # 不抛


@pytest.mark.parametrize(
    "frm,to",
    [
        (Phase.WORLD, Phase.INIT),
        (Phase.CHARACTERS, Phase.WORLD),
        (Phase.OUTLINE, Phase.CHARACTERS),
        (Phase.WRITING, Phase.OUTLINE),
        (Phase.DONE, Phase.WRITING),
    ],
)
def test_legal_backward_transitions(frm: Phase, to: Phase) -> None:
    """任意阶段可回退一格或更多。"""
    assert is_legal(frm, to) is True


def test_self_transition_illegal() -> None:
    """同阶段转移视为非法（必须 explicit 走 API）。"""
    assert is_legal(Phase.WORLD, Phase.WORLD) is False


@pytest.mark.parametrize(
    "frm,to",
    [
        (Phase.INIT, Phase.CHARACTERS),
        (Phase.INIT, Phase.OUTLINE),
        (Phase.WORLD, Phase.OUTLINE),
        (Phase.WORLD, Phase.DONE),
        (Phase.CHARACTERS, Phase.WRITING),
    ],
)
def test_skipping_forward_illegal(frm: Phase, to: Phase) -> None:
    """不能跳阶段向前。"""
    assert is_legal(frm, to) is False
    with pytest.raises(ProtocolError) as ei:
        assert_legal_transition(frm, to)
    assert ei.value.code == ErrorCode.STATE_ILLEGAL_TRANSITION
