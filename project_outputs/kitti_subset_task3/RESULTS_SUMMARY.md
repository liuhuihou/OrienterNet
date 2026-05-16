# KITTI Subset Task 3 Summary

## Compared Configurations

| Config | `num_rotations` | Crop size | Init error |
|---|---:|---:|---:|
| Baseline default | 256 | default | default |
| Low-cost | 32 | 48 m | 16 m |

## Quantitative Results

| Metric | Baseline default | Low-cost |
|---|---:|---:|
| Mean lateral error | 1.7901 m | 1.7642 m |
| Mean longitudinal error | 3.4362 m | 3.7002 m |
| Mean yaw error | 3.6082 deg | 7.2644 deg |
| `xy_recall_5m` | 80% | 60% |
| `yaw_recall_5deg` | 60% | 40% |
| Evaluation runtime | 27.876 s | 19.229 s |
| Wall-clock runtime | 31.23 s | 23.29 s |
| Peak resident memory | 6.78 GiB | 3.45 GiB |

## Trade-off

- Runtime improvement: about **31.0%**
- Wall-clock improvement: about **25.4%**
- Memory reduction: about **49.1%**
- Main quality drop: yaw accuracy

## Observation

The low-cost setting still preserves coarse localization ability, but heading quality degrades much more clearly than position quality.
