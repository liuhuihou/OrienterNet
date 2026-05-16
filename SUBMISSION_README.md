# Submission README

## Deliverables

| Item | Path |
|---|---|
| Technical report | `PROJECT_REPORT.md` |
| Presentation slides | `PRESENTATION_SLIDES.md` |
| Submission guide | `SUBMISSION_README.md` |
| Experiment outputs | `project_outputs/kitti_subset_task3/` |
| Experiment scripts | `project_assets/` |

## Main Result Files

- Baseline summary:
  - `project_outputs/kitti_subset_task3/baseline_default/summary.json`
- Baseline case metrics:
  - `project_outputs/kitti_subset_task3/baseline_default/case_metrics.csv`
- Low-cost summary:
  - `project_outputs/kitti_subset_task3/low_cost_rot32_crop48/summary.json`
- Low-cost case metrics:
  - `project_outputs/kitti_subset_task3/low_cost_rot32_crop48/case_metrics.csv`
- Combined summary:
  - `project_outputs/kitti_subset_task3/RESULTS_SUMMARY.md`
  - `project_outputs/kitti_subset_task3/summary_table.csv`

## Reproduction Commands

Run baseline:

```bash
MPLCONFIGDIR=/tmp/matplotlib ../.venv/bin/python project_assets/run_task3_kitti_subset.py --only baseline
```

Run low-cost setting:

```bash
MPLCONFIGDIR=/tmp/matplotlib ../.venv/bin/python project_assets/run_task3_kitti_subset.py --only low_cost
```

Export case-level metrics:

```bash
MPLCONFIGDIR=/tmp/matplotlib ../.venv/bin/python project_assets/export_case_metrics.py
```

Record resource usage:

```bash
MPLCONFIGDIR=/tmp/matplotlib /usr/bin/time -v \
  ../.venv/bin/python project_assets/run_task3_kitti_subset.py --only baseline
```
