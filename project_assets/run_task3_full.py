import csv
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:  # pragma: no cover - local environment helper
    psutil = None


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "project_outputs" / "kitti_subset_task3"
LOG_DIR = OUTPUT_DIR / "_logs"
DATA_DIR = ROOT / "datasets" / "kitti_subset"

REQUIRED_DATA = [
    DATA_DIR / "tiles.pkl",
    DATA_DIR / "2011_09_26" / "calib_cam_to_cam.txt",
    DATA_DIR
    / "2011_09_26"
    / "2011_09_26_drive_0005_sync"
    / "image_02"
    / "data"
    / "0000000049.png",
    DATA_DIR
    / "2011_09_26"
    / "2011_09_26_drive_0005_sync"
    / "oxts"
    / "data"
    / "0000000049.txt",
]

RUNS = [
    {
        "mode": "smoke",
        "name": "smoke_default_1frame",
        "label": "Smoke",
        "num_rotations": 256,
        "crop_size_meters": "default",
        "max_init_error": "default",
    },
    {
        "mode": "baseline",
        "name": "baseline_default",
        "label": "Baseline default",
        "num_rotations": 256,
        "crop_size_meters": "default",
        "max_init_error": "default",
    },
    {
        "mode": "low_cost",
        "name": "low_cost_rot32_crop48",
        "label": "Low-cost",
        "num_rotations": 32,
        "crop_size_meters": 48,
        "max_init_error": 16,
    },
]


def ensure_required_data() -> None:
    missing = [path for path in REQUIRED_DATA if not path.exists()]
    if missing:
        formatted = "\n".join(f"  - {path}" for path in missing)
        raise FileNotFoundError(
            "KITTI subset is incomplete. Missing required files:\n" + formatted
        )


def archive_existing_outputs() -> Path | None:
    if not OUTPUT_DIR.exists():
        return None
    archive_root = ROOT / "project_outputs" / "_archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    archive_path = archive_root / f"kitti_subset_task3_{stamp}"
    shutil.move(str(OUTPUT_DIR), str(archive_path))
    return archive_path


def process_tree_rss(process: "psutil.Process") -> int | None:
    if psutil is None:
        return None
    total = 0
    try:
        processes = [process, *process.children(recursive=True)]
    except psutil.Error:
        processes = [process]
    for proc in processes:
        try:
            total += proc.memory_info().rss
        except psutil.Error:
            continue
    return total


def run_and_measure(label: str, command: list[str]) -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    safe_label = label.lower().replace(" ", "_")
    stdout_path = LOG_DIR / f"{safe_label}.stdout.log"
    stderr_path = LOG_DIR / f"{safe_label}.stderr.log"

    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
    env.setdefault("TORCH_HOME", str(ROOT / ".cache" / "torch"))
    Path(env["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(env["TORCH_HOME"]).mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    peak_rss = None
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        proc = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=stdout,
            stderr=stderr,
        )
        ps_proc = psutil.Process(proc.pid) if psutil is not None else None
        while proc.poll() is None:
            if ps_proc is not None:
                rss = process_tree_rss(ps_proc)
                if rss is not None:
                    peak_rss = max(peak_rss or 0, rss)
            time.sleep(0.2)
        if ps_proc is not None:
            rss = process_tree_rss(ps_proc)
            if rss is not None:
                peak_rss = max(peak_rss or 0, rss)
    wall_clock = time.perf_counter() - start

    if proc.returncode != 0:
        raise RuntimeError(
            f"{label} failed with exit code {proc.returncode}. "
            f"See {stderr_path} and {stdout_path}."
        )

    return {
        "label": label,
        "command": command,
        "wall_clock_sec": round(wall_clock, 3),
        "peak_rss_bytes": peak_rss,
        "peak_rss_gib": None
        if peak_rss is None
        else round(peak_rss / (1024**3), 3),
        "stdout_log": str(stdout_path.relative_to(ROOT)),
        "stderr_log": str(stderr_path.relative_to(ROOT)),
    }


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recall_percent(value) -> float:
    return round(float(value) * 100.0, 2)


def build_row(run: dict, resources: dict) -> dict:
    summary = read_json(OUTPUT_DIR / run["name"] / "summary.json")
    log = read_json(OUTPUT_DIR / run["name"] / "viz" / "log.json")
    directional = summary["metrics"]["directional_error_mean_m"]
    results = log["results"]
    return {
        "config": run["name"],
        "num_rotations": run["num_rotations"],
        "crop_size_meters": run["crop_size_meters"],
        "max_init_error": run["max_init_error"],
        "num_samples": summary["num_samples"],
        "eval_runtime_sec": summary["elapsed_sec"],
        "wall_clock_sec": resources["wall_clock_sec"],
        "peak_rss_gib": resources["peak_rss_gib"],
        "mean_lateral_error_m": directional[0],
        "mean_longitudinal_error_m": directional[1],
        "mean_yaw_error_deg": summary["metrics"]["yaw_max_error_mean_deg"],
        "xy_recall_5m": recall_percent(results["xy_recall_5m"]),
        "yaw_recall_5deg": recall_percent(results["yaw_recall_5\u00b0"]),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def percent_change(old: float, new: float) -> float:
    return round((old - new) / old * 100.0, 1)


def write_results_summary(rows: list[dict]) -> None:
    baseline = next(row for row in rows if row["config"] == "baseline_default")
    low_cost = next(row for row in rows if row["config"] == "low_cost_rot32_crop48")
    runtime_gain = percent_change(
        float(baseline["eval_runtime_sec"]), float(low_cost["eval_runtime_sec"])
    )
    wall_gain = percent_change(
        float(baseline["wall_clock_sec"]), float(low_cost["wall_clock_sec"])
    )
    memory_gain = None
    if baseline["peak_rss_gib"] is not None and low_cost["peak_rss_gib"] is not None:
        memory_gain = percent_change(
            float(baseline["peak_rss_gib"]), float(low_cost["peak_rss_gib"])
        )

    memory_line = (
        f"- Peak RSS reduction: about **{memory_gain}%**"
        if memory_gain is not None
        else "- Peak RSS reduction: not available"
    )

    content = f"""# KITTI Subset Task 3 Summary

## Compared Configurations

| Config | `num_rotations` | Crop size | Init error |
|---|---:|---:|---:|
| Baseline default | 256 | default | default |
| Low-cost | 32 | 48 m | 16 m |

## Quantitative Results

| Metric | Baseline default | Low-cost |
|---|---:|---:|
| Evaluation frames | {baseline["num_samples"]} | {low_cost["num_samples"]} |
| Mean lateral error | {baseline["mean_lateral_error_m"]:.4f} m | {low_cost["mean_lateral_error_m"]:.4f} m |
| Mean longitudinal error | {baseline["mean_longitudinal_error_m"]:.4f} m | {low_cost["mean_longitudinal_error_m"]:.4f} m |
| Mean yaw error | {baseline["mean_yaw_error_deg"]:.4f} deg | {low_cost["mean_yaw_error_deg"]:.4f} deg |
| `xy_recall_5m` | {baseline["xy_recall_5m"]:.0f}% | {low_cost["xy_recall_5m"]:.0f}% |
| `yaw_recall_5deg` | {baseline["yaw_recall_5deg"]:.0f}% | {low_cost["yaw_recall_5deg"]:.0f}% |
| Evaluation runtime | {baseline["eval_runtime_sec"]:.3f} s | {low_cost["eval_runtime_sec"]:.3f} s |
| Wall-clock runtime | {baseline["wall_clock_sec"]:.3f} s | {low_cost["wall_clock_sec"]:.3f} s |
| Peak resident memory | {baseline["peak_rss_gib"]:.3f} GiB | {low_cost["peak_rss_gib"]:.3f} GiB |

## Trade-off

- Evaluation runtime improvement: about **{runtime_gain}%**
- Wall-clock improvement: about **{wall_gain}%**
{memory_line}
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
"""
    (OUTPUT_DIR / "RESULTS_SUMMARY.md").write_text(content, encoding="utf-8")


def main() -> None:
    archive_requested = "--archive-existing" in sys.argv[1:]
    ensure_required_data()
    archived = archive_existing_outputs() if archive_requested else None
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    resources = {}
    for run in RUNS:
        print(f"Running {run['label']}...")
        result = run_and_measure(
            run["name"],
            [
                sys.executable,
                str(ROOT / "project_assets" / "run_task3_kitti_subset.py"),
                "--only",
                run["mode"],
            ],
        )
        resources[run["name"]] = {**run, **result}

    print("Exporting case metrics...")
    export_metrics = run_and_measure(
        "export_case_metrics",
        [sys.executable, str(ROOT / "project_assets" / "export_case_metrics.py")],
    )

    rows = [build_row(run, resources[run["name"]]) for run in RUNS]
    comparison_rows = [row for row in rows if row["config"] != "smoke_default_1frame"]
    write_csv(OUTPUT_DIR / "summary_table.csv", comparison_rows)
    write_csv(OUTPUT_DIR / "resource_metrics.csv", list(resources.values()))
    (OUTPUT_DIR / "resource_metrics.json").write_text(
        json.dumps(resources, indent=2), encoding="utf-8"
    )

    report = {
        "archived_previous_output": None if archived is None else str(archived),
        "runs": {run["name"]: read_json(OUTPUT_DIR / run["name"] / "summary.json") for run in RUNS},
        "resources": resources,
        "export_case_metrics": export_metrics,
    }
    (OUTPUT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_results_summary(comparison_rows)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
