"""全局 pytest fixture。"""
from pathlib import Path

import pytest


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """临时数据目录，每个测试独立。"""
    d = tmp_path / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d
