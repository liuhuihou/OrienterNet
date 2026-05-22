# OrienterNet Final Project Slides

---

# Slide 1: Title

**Map-Prior-based Localization for Autonomous Driving**  
Final Project based on OrienterNet  
Task 3: Practical Localization under Resource Constraints

---

# Slide 2: Project Goal

- Read and understand OrienterNet
- Reproduce one official runnable baseline
- Complete one controlled extension task
- Chosen task: **Task 3**

Main question:

> Can we reduce inference cost while keeping localization useful?

---

# Slide 3: OrienterNet Core Idea

- Input: RGB image + coarse geographic prior
- Output: 2D position + heading
- Key idea:
  - image features -> BEV
  - map features from rasterized semantic map
  - exhaustive matching over translation and rotation

---

# Slide 4: Pipeline

```text
RGB image
 -> image encoder
 -> image-to-BEV projection
 -> BEV features
 -> map encoder
 -> rotation-aware voting
 -> pose prediction
```

Main code:

- `maploc/models/orienternet.py`
- `maploc/models/bev_projection.py`
- `maploc/models/map_encoder.py`
- `maploc/models/voting.py`

---

# Slide 5: Baseline Route

- Official pipeline used: KITTI evaluation entry
- Checkpoint: `OrienterNet_MGL`
- Local reproducible subset:
  - KITTI `2011_09_26_drive_0005_sync`
  - 10-frame split file
  - 5 deterministic evaluation frames

Why this route:

- demo path depends on unstable online services
- KITTI evaluation gives stable offline ground-truth metrics

---

# Slide 6: Environment

- OS: Windows 10.0.26200
- Python: 3.11.9
- PyTorch: 2.12.0
- CPU-only environment
- CUDA available: `False`

Therefore Task 3 compares:

- runtime
- peak RSS memory
- localization quality

---

# Slide 7: Baseline Result

| Metric | Value |
|---|---:|
| Mean lateral error | 1.7901 m |
| Mean longitudinal error | 3.4362 m |
| Mean yaw error | 3.6082 deg |
| `xy_recall_5m` | 80% |
| `yaw_recall_5deg` | 60% |
| Eval runtime | 37.013 s |
| Peak RSS | 7.713 GiB |

---

# Slide 8: Success / Failure Cases

Success cases:

- `0000000054.png`
- `0000000055.png`
- `0000000049.png`

Failure case:

- `0000000050.png`

Failure type:

- heading still reasonable
- translation drifts beyond 5 m threshold

---

# Slide 9: Task 3 Design

Controlled parameters:

- `model.num_rotations`
- `data.crop_size_meters`
- `data.max_init_error`

Compared settings:

- Baseline default: `num_rotations=256`
- Low-cost: `num_rotations=32`, `crop_size_meters=48`, `max_init_error=16`

---

# Slide 10: Task 3 Results

| Metric | Baseline | Low-cost |
|---|---:|---:|
| Eval runtime | 37.013 s | 21.319 s |
| Peak RSS | 7.713 GiB | 3.686 GiB |
| `xy_recall_5m` | 80% | 60% |
| `yaw_recall_5deg` | 60% | 40% |
| Mean yaw error | 3.6082 deg | 7.2644 deg |

Key trade-off:

- faster
- less memory
- worse orientation quality

---

# Slide 11: Typical Degradation Example

Frame: `0000000054.png`

| Config | Position error | Yaw error |
|---|---:|---:|
| Baseline | 3.3622 m | 5.2893 deg |
| Low-cost | 5.2694 m | 15.1330 deg |

Interpretation:

- coarser rotation search hurts heading first
- heading degradation then hurts translation

---

# Slide 12: Final Conclusion

- Baseline reproduction completed
- Task 3 experiment completed
- Low-cost setting is useful for:
  - lower latency
  - lower memory
  - coarse localization
- Default setting is better when heading quality matters

Final takeaway:

> In OrienterNet, reducing cost mainly sacrifices orientation accuracy before coarse position accuracy.
