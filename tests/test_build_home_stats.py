"""Tests for build_home_stats.build_leg() — precomputed homepage counts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "build_home_stats",
        ROOT / "scripts" / "build_home_stats.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_reads_meta_count_and_falls_back_to_len(tmp_path: Path) -> None:
    mod = _load_module()
    base = tmp_path / "data" / "v1"
    # meta.count present
    _write_json(base / "deputati/legislatura-2024.json", {"meta": {"count": 335}, "data": []})
    # voturi lives under voturi/{leg}/_index.json
    _write_json(base / "voturi/2024/_index.json", {"meta": {"count": 885}, "data": []})
    # no meta.count → fall back to len(data)
    _write_json(
        base / "comisii/legislatura-2024.json",
        {"meta": {}, "data": [{"id": 1}, {"id": 2}, {"id": 3}]},
    )

    assert mod.build_leg(2024, root=tmp_path) == 0

    out = json.loads((base / "stats" / "home-2024.json").read_text(encoding="utf-8"))
    assert out["counts"]["deputati"] == 335
    assert out["counts"]["voturi"] == 885
    assert out["counts"]["comisii"] == 3
    # missing sources are simply absent, not zero
    assert "interpelari" not in out["counts"]
    # headline count is the sum of all collected counts
    assert out["meta"]["count"] == 335 + 885 + 3
    assert out["meta"]["legislatura"] == 2024


def test_no_sources_writes_nothing(tmp_path: Path) -> None:
    mod = _load_module()
    assert mod.build_leg(2024, root=tmp_path) == 0
    assert not (tmp_path / "data" / "v1" / "stats" / "home-2024.json").exists()
