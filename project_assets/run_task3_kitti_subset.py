import json
import os
import shutil
import sys
import time
import argparse
from pathlib import Path

from omegaconf import OmegaConf

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("TORCH_HOME", "/tmp/torch-cache")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maploc.data import KittiDataModule
from maploc.evaluation.run import evaluate

DATA_DIR = ROOT / "datasets" / "kitti_subset"
OUTPUT_DIR = ROOT / "project_outputs" / "kitti_subset_task3"
SPLIT_FILE = ROOT / "project_assets" / "kitti_subset_test.txt"
SUCCESS_SPLIT_FILE = ROOT / "project_assets" / "kitti_subset_success.txt"


def ensure_subset_marker() -> None:
    (DATA_DIR / ".downloaded").touch(exist_ok=True)


def clean_output_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def run_eval(name: str, dot_cfg: dict, split_file: Path, num_viz: int):
    out_dir = OUTPUT_DIR / name
    clean_output_dir(out_dir)
    cfg = OmegaConf.create(
        {
            "model": {
                "image_encoder": {
                    "backbone": {
                        "pretrained": False,
                    }
                }
            },
            "data": {
                "data_dir": str(DATA_DIR),
                "tiles_filename": "tiles.pkl",
                "splits": {
                    "train": str(split_file),
                    "val": str(split_file),
                    "test": str(split_file),
                },
                "loading": {
                    "train": {"batch_size": 1, "num_workers": 0},
                    "val": {"batch_size": 1, "num_workers": 0},
                    "test": {"batch_size": 1, "num_workers": 0},
                },
                "max_num_val": None,
                "drop_train_too_close_to_val": None,
            }
        }
    )
    cfg = OmegaConf.merge(cfg, OmegaConf.create(dot_cfg))

    dataset = KittiDataModule(cfg.data)
    start = time.perf_counter()
    metrics = evaluate(
        "OrienterNet_MGL",
        cfg,
        dataset,
        split="test",
        sequential=False,
        output_dir=out_dir / "viz",
        num=num_viz,
        num_workers=0,
        viz_kwargs=dict(show_dir_error=True, show_masked_prob=False),
    )
    elapsed = time.perf_counter() - start

    directional = metrics["directional_error"].recall((1, 3, 5)).double().numpy().round(2).tolist()
    yaw = metrics["yaw_max_error"].recall((1, 3, 5)).double().numpy().round(2).tolist()
    result = {
        "name": name,
        "elapsed_sec": round(elapsed, 3),
        "num_samples": num_viz,
        "config": OmegaConf.to_container(cfg, resolve=True),
        "metrics": {
            "directional_error_mean_m": metrics["directional_error"].compute().double().numpy().round(4).tolist(),
            "yaw_max_error_mean_deg": round(float(metrics["yaw_max_error"].compute().item()), 4),
            "directional_recall_at_1_3_5m": directional,
            "yaw_recall_at_1_3_5deg": yaw,
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        choices=["smoke", "baseline", "low_cost", "all"],
        default="all",
    )
    args = parser.parse_args()

    ensure_subset_marker()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = {}
    if args.only in {"smoke", "all"}:
        report["smoke_default_1frame"] = run_eval(
            "smoke_default_1frame",
            {},
            SUCCESS_SPLIT_FILE,
            num_viz=1,
        )
    if args.only in {"baseline", "all"}:
        report["baseline_default"] = run_eval(
            "baseline_default",
            {},
            SPLIT_FILE,
            num_viz=5,
        )
    if args.only in {"low_cost", "all"}:
        report["low_cost_rot32_crop48"] = run_eval(
            "low_cost_rot32_crop48",
            {
                "model": {"num_rotations": 32},
                "data": {"crop_size_meters": 48, "max_init_error": 16},
            },
            SPLIT_FILE,
            num_viz=5,
        )

    (OUTPUT_DIR / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
