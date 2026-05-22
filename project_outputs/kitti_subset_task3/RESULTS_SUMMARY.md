# KITTI Subset Task 3 Summary

## Compared Configurations

| Config | `num_rotations` | Crop size | Init error |
|---|---:|---:|---:|
| Baseline default | 256 | default | default |
| Low-cost | 32 | 48 m | 16 m |

## Quantitative Results

| Metric | Baseline default | Low-cost |
|---|---:|---:|
| Evaluation frames | 5 | 5 |
| Mean lateral error | 1.7901 m | 1.7642 m |
| Mean longitudinal error | 3.4362 m | 3.7002 m |
| Mean yaw error | 3.6082 deg | 7.2644 deg |
| `xy_recall_5m` | 80% | 60% |
| `yaw_recall_5deg` | 60% | 40% |
| Evaluation runtime | 37.013 s | 21.319 s |
| Wall-clock runtime | 39.634 s | 29.614 s |
| Peak resident memory | 7.713 GiB | 3.686 GiB |

## Trade-off

- Evaluation runtime improvement: about **42.4%**
- Wall-clock improvement: about **25.3%**
- Peak RSS reduction: about **52.2%**
- Main quality drop: yaw accuracy

## Output Layout

- `smoke_default_1frame/`: cold-start validation run.
- `baseline_default/`: default OrienterNet KITTI subset evaluation.
- `low_cost_rot32_crop48/`: resource-constrained configuration.
- `_logs/`: stdout and stderr logs for each subprocess.
- `resource_metrics.json`: wall-clock and peak RSS measurements.
- `summary_table.csv`: machine-readable comparison table.

## Observation

The low-cost setting preserves coarse localization ability, but heading quality degrades more clearly than position quality.
