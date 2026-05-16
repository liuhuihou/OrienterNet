import csv
import json
import os
import sys
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


def base_cfg():
    return OmegaConf.create(
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
                    "train": str(SPLIT_FILE),
                    "val": str(SPLIT_FILE),
                    "test": str(SPLIT_FILE),
                },
                "loading": {
                    "train": {"batch_size": 1, "num_workers": 0},
                    "val": {"batch_size": 1, "num_workers": 0},
                    "test": {"batch_size": 1, "num_workers": 0},
                },
                "max_num_val": None,
                "drop_train_too_close_to_val": None,
            },
        }
    )


def export_case_metrics(name: str, overrides: dict):
    rows = []

    def callback(i, model, pred, batch, results):
        lat_err, lon_err = results["directional_error"]
        row = {
            "index": int(i),
            "scene": batch["scene"],
            "name": batch["name"],
            "xy_max_error_m": round(float(results["xy_max_error"]), 4),
            "yaw_max_error_deg": round(float(results["yaw_max_error"]), 4),
            "lateral_error_m": round(float(lat_err), 4),
            "longitudinal_error_m": round(float(lon_err), 4),
        }
        rows.append(row)

    cfg = OmegaConf.merge(base_cfg(), OmegaConf.create(overrides))
    dataset = KittiDataModule(cfg.data)
    evaluate(
        "OrienterNet_MGL",
        cfg,
        dataset,
        split="test",
        sequential=False,
        callback=callback,
        num=5,
        num_workers=0,
    )

    out_dir = OUTPUT_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "case_metrics.json"
    csv_path = out_dir / "case_metrics.csv"
    json_path.write_text(json.dumps(rows, indent=2))
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(rows, indent=2))


def main():
    export_case_metrics("baseline_default", {})
    export_case_metrics(
        "low_cost_rot32_crop48",
        {
            "model": {"num_rotations": 32},
            "data": {"crop_size_meters": 48, "max_init_error": 16},
        },
    )


if __name__ == "__main__":
    main()
