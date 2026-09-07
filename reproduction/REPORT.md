# Deterministic gripper reconstruction

This directory reproduces the gripper figures discussed in OpenVLA issue #303 using only the two public CSV files already present at this repository root. It does not contain model weights, private data, or source code from any other project.

## Run

```bash
python reproduction/fetch_inputs.py
python reproduction/reproduce.py --output reproduction/results.json
python -m unittest discover -s reproduction -p "test_*.py"
```

## Frozen transformation

The source URLs and SHA-256 values are pinned in `input_manifest.json`. `fetch_inputs.py` downloads the two public CSVs into the ignored `inputs/` directory and rejects them if either hash differs.

1. Read the ground-truth `gripper` column in CSV row order as delta-like commands.
2. Accumulate it into a state and clamp every accumulated value to `[0, 1]`.
3. Convert that state to binary using `state >= 0.5`.
4. Convert the predicted `gripper` value to binary using `value >= 0.5`.
5. For offset `k`, compare true row `i` with predicted row `i + k`; unmatched endpoint rows are excluded.

The clamping step is material. The published ground-truth column contains motion-like values such as `1.0`, `0.999739`, then decreasing values, and later negative values. Treating that column as an already-binary state does not reproduce the figures below.

## Primary result

| Configuration | Mismatches | Compared rows | Rate |
| --- | ---: | ---: | ---: |
| Extra inversion of predicted state | 109 | 115 | 94.78% |
| No extra prediction inversion | 6 | 115 | 5.22% |
| No inversion, prediction offset `-1` | 4 | 114 | 3.51% |

The final percentage uses 114, not 115, because the `-1` offset removes one endpoint that has no counterpart. Thus `4 / 114 = 3.5088...%`, reported as `3.51%`.

The `-2` offset also has four mismatches, over 113 comparable rows (`3.54%`). This is why the offset result is presented as a bounded alignment observation, not as a unique optimum or a causal conclusion.

## Controlled checks

`reproduce.py` emits a predeclared offset sweep from `-2` through `+2`, and three circular-shift placebo controls. The offset sweep makes the endpoint exclusion explicit; the placebo controls retain the predicted class balance while breaking frame correspondence.

These checks support a narrow conclusion: the public CSVs are consistent with a representation reconstruction in which the extra prediction inversion is incorrect, and a `-1` frame offset reduces the remaining disagreement. They do **not** establish that any OpenVLA component is frozen, that the model is generally correct, or a causal explanation of the model's behavior. Establishing those claims would require a separately specified intervention experiment with the model and its preprocessing path.
