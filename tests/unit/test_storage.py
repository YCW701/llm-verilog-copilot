from __future__ import annotations

import hashlib
import json

import pytest

from verilog_copilot.benchmarks import local_fixtures
from verilog_copilot.models import FailureCategory, StageResult, StageStatus, to_jsonable
from verilog_copilot.storage import (
    OutputExistsError,
    copy_file_exclusive,
    create_run_dir,
    sha256_file,
    write_json_exclusive,
)


def test_create_run_dir_refuses_existing(tmp_path):
    target = tmp_path / "nested" / "run 1"
    create_run_dir(target)
    with pytest.raises(OutputExistsError):
        create_run_dir(target)


def test_create_run_dir_refuses_existing_file(tmp_path):
    f = tmp_path / "taken"
    f.write_text("keep me")
    with pytest.raises(OutputExistsError):
        create_run_dir(f)
    assert f.read_text() == "keep me"


def test_write_json_exclusive_never_overwrites(tmp_path):
    p = tmp_path / "result.json"
    write_json_exclusive(p, {"a": 1})
    with pytest.raises(OutputExistsError):
        write_json_exclusive(p, {"a": 2})
    assert json.loads(p.read_text()) == {"a": 1}
    assert [x.name for x in tmp_path.iterdir()] == ["result.json"], "temp file left behind"


def test_copy_file_exclusive(tmp_path):
    src, dst = tmp_path / "a.v", tmp_path / "b.v"
    src.write_text("module m; endmodule\n")
    copy_file_exclusive(src, dst)
    assert sha256_file(dst) == sha256_file(src)
    with pytest.raises(OutputExistsError):
        copy_file_exclusive(src, dst)


def test_sha256_file(tmp_path):
    p = tmp_path / "x"
    p.write_bytes(b"abc")
    assert sha256_file(p) == hashlib.sha256(b"abc").hexdigest()


def test_to_jsonable_converts_enums():
    data = to_jsonable({"stage": StageResult(status=StageStatus.TIMEOUT), "cat": FailureCategory.NONE})
    assert data["stage"]["status"] == "timeout" and data["cat"] == "none"
    json.dumps(data)


def test_registry_pins_current_trusted_checker_hash():
    bundle = local_fixtures.get_bundle("adder4")
    for tf in bundle.trusted_files:
        assert tf.path.is_file(), f"trusted checker missing: {tf.path}"
        assert sha256_file(tf.path) == tf.sha256, "trusted checker changed; review before re-pinning"


def test_unknown_task_raises():
    with pytest.raises(KeyError):
        local_fixtures.get_bundle("nope")
