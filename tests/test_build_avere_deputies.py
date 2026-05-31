"""Tests for build_avere_deputies.build_leg() join logic."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "build_avere_deputies",
        ROOT / "scripts" / "build_avere_deputies.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


@pytest.fixture()
def fixture_root(tmp_path: Path) -> Path:
    leg = 2024

    # 1. avere index
    _write_json(
        tmp_path / f"data/v1/declaratii-avere/legislatura-{leg}.json",
        {
            "meta": {},
            "data": [
                {
                    "cdep_idm": 1,
                    "deputat_nume": "Popescu Ion",
                    "legislatura": leg,
                    "partid_short": "PSD",
                    "n_declaratii": 1,
                    "ultima_conturi_ron": 100000.0,
                    "ultima_venituri_ron": 50000.0,
                    "ultima_imobile_count": 2,
                    # Single declaration: delta present in index but must be nulled in output.
                    "delta_conturi_ron": 0.0,
                    "delta_imobile": 0,
                },
                {
                    "cdep_idm": 2,
                    "deputat_nume": "Ionescu Ana",
                    "legislatura": leg,
                    "partid_short": "PNL",
                    "n_declaratii": 0,
                    "ultima_conturi_ron": None,
                    "ultima_venituri_ron": None,
                    "ultima_imobile_count": None,
                },
                {
                    "cdep_idm": 3,
                    "deputat_nume": "Vasile Dan",
                    "legislatura": leg,
                    "partid_short": "PSD",
                    "n_declaratii": 2,
                    "ultima_conturi_ron": 250000.0,
                    "ultima_venituri_ron": 90000.0,
                    "ultima_imobile_count": 3,
                    # ≥2 declarations: evolution deltas should pass through to output.
                    "delta_conturi_ron": 60294.0,
                    "delta_imobile": 1,
                },
            ],
        },
    )

    # 2. avere detail for deputy 1 only
    _write_json(
        tmp_path / f"data/v1/declaratii-avere/legislatura-{leg}/1.json",
        {
            "data": {
                "cdep_idm": 1,
                "declaratii": [
                    {
                        "suprafata_total_mp": 150.0,
                        "datorii_total_ron": 30000.0,
                        "auto_count": 2,
                    }
                ],
            }
        },
    )

    # 3. deputati index
    _write_json(
        tmp_path / f"data/v1/deputati/legislatura-{leg}.json",
        {
            "meta": {},
            "data": [
                {"cdep_idm": 1, "image": "https://cdep.ro/img/1.jpg"},
                {"cdep_idm": 2, "image": "https://cdep.ro/img/2.jpg"},
            ],
        },
    )

    # 4. party CSV
    csv_path = tmp_path / "data/assets/legenda-partide.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(
        "ID,Denumire,Ordine,Logo,CUI,Adresa,Judet,UAT,tip-partid\n"
        "PSD,Partidul Social Democrat,1,PSD.jpg,,,,,\n"
        "PNL,Partidul National Liberal,2,PNL.jpg,,,,,\n",
        encoding="utf-8",
    )

    return tmp_path


def test_output_file_created(fixture_root: Path) -> None:
    mod = _load_module()
    ret = mod.build_leg(2024, root=fixture_root)
    assert ret == 0
    assert (fixture_root / "data/v1/stats/avere-deputies-2024.json").exists()


def test_deputies_count(fixture_root: Path) -> None:
    mod = _load_module()
    mod.build_leg(2024, root=fixture_root)
    payload = json.loads(
        (fixture_root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    assert len(payload["deputies"]) == 3


def test_deputy_with_declaration(fixture_root: Path) -> None:
    mod = _load_module()
    mod.build_leg(2024, root=fixture_root)
    payload = json.loads(
        (fixture_root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    dep = next(d for d in payload["deputies"] if d["cdep_idm"] == 1)
    assert dep["name"] == "Popescu Ion"
    assert dep["partid"] == "PSD"
    assert dep["image"] == "https://cdep.ro/img/1.jpg"
    assert dep["conturi_ron"] == 100000.0
    assert dep["venituri_ron"] == 50000.0
    assert dep["imobile_count"] == 2
    assert dep["suprafata_mp"] == 150.0
    assert dep["datorii_ron"] == 30000.0
    assert dep["auto_count"] == 2


def test_deputy_without_declaration_has_nulls(fixture_root: Path) -> None:
    mod = _load_module()
    mod.build_leg(2024, root=fixture_root)
    payload = json.loads(
        (fixture_root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    dep = next(d for d in payload["deputies"] if d["cdep_idm"] == 2)
    assert dep["conturi_ron"] is None
    assert dep["suprafata_mp"] is None
    assert dep["image"] == "https://cdep.ro/img/2.jpg"


def test_evolution_deltas(fixture_root: Path) -> None:
    """delta_* are null unless the deputy has ≥2 declarations (evolution)."""
    mod = _load_module()
    mod.build_leg(2024, root=fixture_root)
    payload = json.loads(
        (fixture_root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    by_id = {d["cdep_idm"]: d for d in payload["deputies"]}
    # All records carry the keys.
    assert "delta_conturi_ron" in by_id[1] and "delta_imobile" in by_id[1]
    # Single declaration -> nulled even though the index had a value.
    assert by_id[1]["delta_conturi_ron"] is None
    assert by_id[1]["delta_imobile"] is None
    # No declaration -> null.
    assert by_id[2]["delta_conturi_ron"] is None
    # ≥2 declarations -> passed through.
    assert by_id[3]["delta_conturi_ron"] == 60294.0
    assert by_id[3]["delta_imobile"] == 1


def test_parties_dict_present(fixture_root: Path) -> None:
    mod = _load_module()
    mod.build_leg(2024, root=fixture_root)
    payload = json.loads(
        (fixture_root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    assert "parties" in payload
    assert payload["parties"]["PSD"] == "PSD.jpg"
    assert payload["parties"]["PNL"] == "PNL.jpg"


def test_missing_avere_index_returns_nonzero(tmp_path: Path) -> None:
    mod = _load_module()
    ret = mod.build_leg(2024, root=tmp_path)
    assert ret != 0
