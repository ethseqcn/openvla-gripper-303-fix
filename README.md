# OpenVLA gripper issue #303: reproducible reconstruction

This repository makes the gripper comparison discussed in [openvla/openvla#303](https://github.com/openvla/openvla/issues/303) independently reproducible from the two public CSV files attached to the original report.

It addresses one narrow question: how do the reported `94.78%`, `5.22%`, and `3.51%` gripper mismatch figures arise from the published data?

## Result

| Comparison | Mismatches | Compared rows | Mismatch rate |
| --- | ---: | ---: | ---: |
| Extra inversion of the predicted state | 109 | 115 | 94.78% |
| No extra prediction inversion | 6 | 115 | 5.22% |
| No inversion, predicted frame offset `-1` | 4 | 114 | 3.51% |

The final result is `4 / 114`, not `4 / 115`, because the one-frame offset removes an endpoint without a matching prediction.

## Why reconstruction is needed

The published ground-truth and predicted gripper columns are not directly in the same representation:

- Ground truth contains delta-like commands, including positive and negative continuous values.
- Predictions are effectively binary values near `0` and `1`.

The comparison therefore reconstructs a bounded ground-truth state before comparing it to the predicted state:

1. Read the published ground-truth `gripper` values in row order.
2. Accumulate them and clamp each state to `[0, 1]`.
3. Convert the reconstructed state using `state >= 0.5`.
4. Convert predictions using `prediction >= 0.5`.
5. For offset `k`, compare ground-truth row `i` with prediction row `i + k`; exclude rows without a counterpart.

The full transformation, exact input hashes, offset sweep, and negative-control checks are documented in [reproduction/REPORT.md](reproduction/REPORT.md).

## Run it

Requirements: Python 3 standard library only.

```bash
python reproduction/fetch_inputs.py
python reproduction/reproduce.py --output reproduction/results.json
python -m unittest discover -s reproduction -p "test_*.py"
```

`fetch_inputs.py` downloads the two source CSVs from the original public repository and verifies their SHA-256 hashes before use. The downloaded data is intentionally not committed here.

## Repository contents

| Path | Purpose |
| --- | --- |
| [reproduction/input_manifest.json](reproduction/input_manifest.json) | Public input URLs and pinned SHA-256 hashes. |
| [reproduction/fetch_inputs.py](reproduction/fetch_inputs.py) | Downloads and verifies the public CSV inputs. |
| [reproduction/reproduce.py](reproduction/reproduce.py) | Deterministic reconstruction and comparison. |
| [reproduction/test_reproduce.py](reproduction/test_reproduce.py) | Assertions for the published counts and input hashes. |
| [reproduction/results.json](reproduction/results.json) | Generated primary result, offset sweep, and placebo controls. |
| [reproduction/REPORT.md](reproduction/REPORT.md) | Detailed method, controls, and interpretation limits. |

## Scope and limits

The code supports a representation reconstruction from the published CSVs. It does **not** show that any OpenVLA component is frozen, that the model is generally correct, or that this mapping establishes a causal explanation of model behavior. Those claims require separately specified interventions using the model and its preprocessing path.

The `-2` offset also has four mismatches over 113 comparable rows (`3.54%`). For that reason, the `-1` result is reported as a bounded alignment observation, not as a unique optimum.

## Public source inputs

The two source CSVs are from [lovecode1/OpenVLA-Gripper-Accuracy-Issue](https://github.com/lovecode1/OpenVLA-Gripper-Accuracy-Issue):

- `fractal20220817_data_original_actions.csv`
- `fractal20220817_data_predicted_actions.csv`
