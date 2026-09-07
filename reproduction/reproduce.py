#!/usr/bin/env python3
"""Reproduce the OpenVLA issue #303 gripper comparison from public CSVs only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "inputs"
GT_PATH = INPUT_DIR / "fractal20220817_data_original_actions.csv"
PRED_PATH = INPUT_DIR / "fractal20220817_data_predicted_actions.csv"


@dataclass(frozen=True)
class Comparison:
    name: str
    offset: int
    invert_prediction: bool
    compared_rows: int
    mismatches: int

    @property
    def mismatch_rate_percent(self) -> float:
        return 100.0 * self.mismatches / self.compared_rows

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["mismatch_rate_percent"] = round(self.mismatch_rate_percent, 6)
        return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_gripper(path: Path) -> list[float]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "gripper" not in reader.fieldnames:
            raise ValueError(f"{path.name} must have a gripper column")
        return [float(row["gripper"]) for row in reader]


def reconstruct_gt_state(deltas: Iterable[float]) -> list[bool]:
    """Convert published delta-like gripper values to a bounded binary state."""
    state = 0.0
    result: list[bool] = []
    for delta in deltas:
        state = min(1.0, max(0.0, state + delta))
        result.append(state >= 0.5)
    return result


def binary_prediction(values: Iterable[float]) -> list[bool]:
    return [value >= 0.5 for value in values]


def compare(
    name: str,
    gt_state: list[bool],
    prediction: list[bool],
    *,
    offset: int = 0,
    invert_prediction: bool = False,
) -> Comparison:
    mismatches = 0
    compared = 0
    for gt_index, expected in enumerate(gt_state):
        prediction_index = gt_index + offset
        if not 0 <= prediction_index < len(prediction):
            continue
        actual = prediction[prediction_index]
        if invert_prediction:
            actual = not actual
        mismatches += expected != actual
        compared += 1
    return Comparison(name, offset, invert_prediction, compared, mismatches)


def build_report() -> dict[str, object]:
    deltas = read_gripper(GT_PATH)
    predictions = read_gripper(PRED_PATH)
    gt_state = reconstruct_gt_state(deltas)
    pred_state = binary_prediction(predictions)
    if len(gt_state) != len(pred_state):
        raise ValueError("Published CSV row counts differ")

    primary = [
        compare("extra_prediction_inversion", gt_state, pred_state, invert_prediction=True),
        compare("no_extra_prediction_inversion", gt_state, pred_state),
        compare("no_inversion_offset_minus_1", gt_state, pred_state, offset=-1),
    ]
    alignment_sweep = [
        compare(f"no_inversion_offset_{offset:+d}", gt_state, pred_state, offset=offset)
        for offset in range(-2, 3)
    ]

    # These predeclared circular shifts are negative controls: they deliberately
    # break frame correspondence while preserving the prediction marginal counts.
    placebo = []
    for shift in (17, 43, 71):
        shifted = pred_state[shift:] + pred_state[:shift]
        placebo.append(compare(f"circular_shift_placebo_{shift}", gt_state, shifted))

    return {
        "input_hashes": {GT_PATH.name: sha256(GT_PATH), PRED_PATH.name: sha256(PRED_PATH)},
        "rows": {"ground_truth": len(gt_state), "prediction": len(pred_state)},
        "primary": [item.to_dict() for item in primary],
        "alignment_sweep": [item.to_dict() for item in alignment_sweep],
        "placebo_controls": [item.to_dict() for item in placebo],
    }


def manifest_hashes() -> dict[str, str]:
    manifest_path = Path(__file__).with_name("input_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {entry["path"]: entry["sha256"] for entry in manifest["inputs"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Write JSON report to this path instead of stdout.")
    args = parser.parse_args()
    rendered = json.dumps(build_report(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
