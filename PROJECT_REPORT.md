# OrienterNet Final Project Report

## 1. 项目简介

本项目围绕论文 **OrienterNet: Visual Localization in 2D Public Maps with Neural Matching** 及其官方代码展开，目标是在理解论文核心思想的基础上，完成一次**官方可运行基线复现**，并在此基础上完成一个课程指定任务。

我选择的扩展任务是：

**Task 3: Practical Localization under Resource Constraints**

也就是在有限算力条件下，研究 OrienterNet 的推理速度、内存占用与定位精度之间的权衡关系。

本次提交的重点不是复现论文最佳成绩，而是回答一个工程问题：

> OrienterNet 在降低计算开销之后，是否还能保持“可用”的定位能力？

---

## 2. 论文方法概述

OrienterNet 并不是直接从单张 RGB 图像回归位姿，而是把图像特征先投影到鸟瞰图（BEV）空间，再与 2D 语义地图进行神经匹配。

核心流程可以概括为：

```text
RGB image
  -> image encoder
  -> scale/depth-aware image representation
  -> image-to-BEV projection
  -> BEV feature refinement
  -> raster map encoder
  -> exhaustive voting over (x, y, yaw)
  -> pose prediction
```

这种设计的关键优势在于：

- 充分利用了公开 2D 地图先验；
- 把“图像定位”转化成“BEV 与地图之间的匹配问题”；
- 相比依赖 3D 点云或大型地图重建的方法，更适合资源受限场景。

---

## 3. 系统结构图

```text
输入图像
  |
  v
图像特征提取 CNN
  |
  v
尺度/深度相关表示
  |
  v
图像到 BEV 投影
  |
  v
BEV 特征 ------------------------------+
                                      |
OSM 栅格地图 -> 地图编码器 ------------+
                                      |
                                      v
                     旋转敏感的穷举匹配 / voting
                                      |
                                      v
                      x, y, yaw 概率体与位姿预测
                                      |
                                      v
                        误差评估与可视化导出
```

---

## 4. 论文模块与代码模块对应关系

| 论文模块 | 主要代码位置 | 功能说明 |
|---|---|---|
| 图像编码器 | `maploc/models/orienternet.py`, `maploc/models/feature_extractor_v2.py` | 提取 RGB 图像特征。 |
| 单目尺度/深度相关表示 | `maploc/models/orienternet.py`, `maploc/models/bev_projection.py` | 将图像特征变换到可投影形式。 |
| 图像到 BEV 投影 | `maploc/models/bev_projection.py` | 从相机视角转到鸟瞰图表示。 |
| BEV refinement | `maploc/models/bev_net.py` | 对投影后的 BEV 特征做进一步建模。 |
| 地图编码器 | `maploc/models/map_encoder.py` | 将 OSM 语义栅格编码成神经地图特征。 |
| 匹配与投票 | `maploc/models/voting.py`, `maploc/models/orienternet.py` | 在位置与朝向维度上做穷举匹配。 |
| 位姿输出 | `maploc/models/voting.py` | 从分数体中解码最佳 `(x, y, yaw)`。 |
| 误差与 recall 计算 | `maploc/models/metrics.py` | 计算位置误差、方向误差、recall。 |
| 官方评测入口 | `maploc/evaluation/run.py`, `maploc/evaluation/kitti.py` | 加载 checkpoint、数据集并运行评测。 |
| 可视化导出 | `maploc/evaluation/viz.py` | 保存预测图、BEV 图和概率图。 |

---

## 5. 基线复现

### 5.1 选择的基线路径

课程要求中明确允许使用：

- official demo / inference pipeline
- official evaluation entry on a public dataset

由于当前环境中：

- `app.py` / `demo.py` 所依赖的在线标定模型下载不稳定；
- 在线地理编码与 OSM API 访问也不稳定；

所以本项目最终采用**官方 KITTI 评测入口**作为基线复现路径。这仍然属于项目要求中允许的“official evaluation entry on a public dataset”。

使用的官方入口命令是：

```bash
python -m maploc.evaluation.kitti --experiment OrienterNet_MGL model.num_rotations=256
```

为了保证在当前机器上可复现，我构建了一个**本地 KITTI 子集**，但评测代码路径和预训练 checkpoint 均为官方实现。

### 5.2 运行环境

| 项目 | 数值 |
|---|---|
| 操作系统 | Windows 10.0.26200 x86_64 |
| Python | 3.11.9 |
| PyTorch | 2.12.0 |
| Torchvision | 0.27.0 |
| PyTorch Lightning | 2.6.4 |
| Hydra | 1.3.2 |
| OmegaConf | 2.3.0 |
| CUDA 是否可用 | False |
| GPU 数量 | 0 |

说明：

- 当前环境没有可用 GPU；
- 因此 Task 3 的资源指标采用 **CPU 运行时间 + 峰值常驻内存（RSS）**；
- 不报告 GPU memory。

### 5.3 数据与子集说明

本地基线使用：

- 官方预生成地图瓦片：`datasets/kitti_subset/tiles.pkl`
- KITTI 原始序列：`2011_09_26_drive_0005_sync`
- 官方标定文件：`2011_09_26` calibration
- 自定义评测 split：
  - `project_assets/kitti_subset_test.txt`
  - `project_assets/kitti_subset_success.txt`

真正用于基线和 Task 3 对比的是：

- 10 帧固定 split 文件中的前 5 帧
- `seed=0`
- `batch_size=1`

### 5.4 实际使用的命令

数据准备：

```powershell
$root = "datasets\kitti_subset"
New-Item -ItemType Directory -Force $root | Out-Null

@'
from pathlib import Path
from maploc.utils.io import download_file
root = Path('datasets/kitti_subset')
download_file('https://cvg-data.inf.ethz.ch/OrienterNet_CVPR2023/tiles/kitti.pkl', root / 'tiles.pkl')
download_file('https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/2011_09_26_calib.zip', root / '2011_09_26_calib.zip')
download_file('https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data/2011_09_26_drive_0005/2011_09_26_drive_0005_sync.zip', root / '2011_09_26_drive_0005_sync.zip')
'@ | .\.venv\Scripts\python.exe -

Expand-Archive -LiteralPath "$root\2011_09_26_calib.zip" -DestinationPath $root -Force
Expand-Archive -LiteralPath "$root\2011_09_26_drive_0005_sync.zip" -DestinationPath $root -Force
```

一键重跑全部 Task 3 产物：

```powershell
$env:MPLCONFIGDIR = "$PWD\.cache\matplotlib"
.\.venv\Scripts\python.exe project_assets\run_task3_full.py --archive-existing
```

单独运行基线评测：

```powershell
$env:MPLCONFIGDIR = "$PWD\.cache\matplotlib"
.\.venv\Scripts\python.exe project_assets\run_task3_kitti_subset.py --only baseline
```

逐帧误差导出：

```powershell
$env:MPLCONFIGDIR = "$PWD\.cache\matplotlib"
.\.venv\Scripts\python.exe project_assets\export_case_metrics.py
```

### 5.5 基线结果

基线结果文件：

- `project_outputs/kitti_subset_task3/baseline_default/summary.json`
- `project_outputs/kitti_subset_task3/baseline_default/case_metrics.csv`
- `project_outputs/kitti_subset_task3/baseline_default/viz/log.json`

基线可视化文件：

- `project_outputs/kitti_subset_task3/baseline_default/viz/*_pred.pdf`
- `project_outputs/kitti_subset_task3/baseline_default/viz/*_bev.pdf`

### 5.6 基线定量结果表

| 指标 | 数值 |
|---|---:|
| 评测帧数 | 5 |
| 平均横向误差 | 1.7901 m |
| 平均纵向误差 | 3.4362 m |
| 平均航向误差 | 3.6082 deg |
| `xy_recall_5m` | 80% |
| `yaw_recall_5deg` | 60% |
| Python 脚本内部计时 | 37.013 s |
| 独立进程墙钟时间 | 39.634 s |
| 峰值常驻内存 RSS | 7.713 GiB |

### 5.7 基线成功与失败案例

根据 `case_metrics.csv` 中的逐帧误差，选取至少 3 个成功案例和 1 个失败案例：

#### 成功案例

| 帧名 | 位置误差 | 朝向误差 | 说明 |
|---|---:|---:|---|
| `0000000054.png` | 3.3622 m | 5.2893 deg | 位置预测较准，朝向略有偏差但仍接近正确道路朝向。 |
| `0000000055.png` | 3.7470 m | 0.2131 deg | 最稳定样例，平移和朝向都较准确。 |
| `0000000049.png` | 3.4560 m | 4.5953 deg | 能正确落在局部道路区域内，朝向误差可接受。 |

#### 失败案例

| 帧名 | 位置误差 | 朝向误差 | 说明 |
|---|---:|---:|---|
| `0000000050.png` | 5.4421 m | 2.1588 deg | 朝向仍合理，但位置偏移超过 5m 阈值，属于平移模式混淆。 |

这满足了课程 baseline 的最低要求：

- 至少 3 个成功案例；
- 至少 1 个失败案例；
- 有真实日志、真实图像导出与指标解释。

---

## 6. Task 3 设计：资源受限下的实用定位

### 6.1 研究问题

Task 3 的核心不是继续提高精度，而是研究：

> 降低搜索复杂度之后，OrienterNet 的速度和内存是否能显著改善？改善代价主要体现在什么指标上？

### 6.2 控制变量

本实验控制以下推理参数：

- `model.num_rotations`
- `data.crop_size_meters`
- `data.max_init_error`

对比设置如下：

| 配置 | `num_rotations` | `crop_size_meters` | `max_init_error` | 目的 |
|---|---:|---:|---:|---|
| Baseline default | 256 | 默认 | 默认 | 作为精度优先对照组 |
| Low-cost | 32 | 48 | 16 | 明显缩小旋转搜索与地图搜索范围 |

### 6.3 为什么这属于有效的 Task 3 实验

该实验满足 Task 3 的要求，因为它：

- 先完成了基线复现；
- 明确改变了计算成本相关参数；
- 保持相同 checkpoint 与相同数据子集；
- 同时比较了精度、时间和内存；
- 给出了定量与定性两类分析。

---

## 7. Task 3 实验结果

### 7.1 默认配置与低成本配置对比

| 指标 | Baseline default | Low-cost (`rot32 + crop48`) | 变化 |
|---|---:|---:|---:|
| 评测帧数 | 5 | 5 | - |
| 平均横向误差 | 1.7901 m | 1.7642 m | 略好 |
| 平均纵向误差 | 3.4362 m | 3.7002 m | 变差 |
| 平均航向误差 | 3.6082 deg | 7.2644 deg | 明显变差 |
| `xy_recall_5m` | 80% | 60% | -20 pts |
| `yaw_recall_5deg` | 60% | 40% | -20 pts |
| Python 脚本内部计时 | 37.013 s | 21.319 s | **加速 42.4%** |
| 独立进程墙钟时间 | 39.634 s | 29.614 s | **加速 25.3%** |
| 峰值 RSS | 7.713 GiB | 3.686 GiB | **降低 52.2%** |

### 7.2 逐帧结果比较

Baseline 逐帧误差文件：

- `project_outputs/kitti_subset_task3/baseline_default/case_metrics.csv`

Low-cost 逐帧误差文件：

- `project_outputs/kitti_subset_task3/low_cost_rot32_crop48/case_metrics.csv`

最有代表性的退化案例是 `0000000054.png`：

| 配置 | 位置误差 | 朝向误差 |
|---|---:|---:|
| Baseline | 3.3622 m | 5.2893 deg |
| Low-cost | 5.2694 m | 15.1330 deg |

这个案例非常清楚地说明：

- 低成本设置仍然能大致找到正确区域；
- 但旋转分辨率下降后，朝向估计首先明显恶化；
- 朝向一旦变差，又会进一步拖累最终位置精度。

### 7.3 结果解释

本实验中，低成本配置带来的收益非常明确：

- 时间更短；
- 内存显著下降；

但代价也很明确：

- 朝向误差恶化最明显；
- 严格阈值下的 recall 下降；
- 部分本来可接受的样例退化成失败样例。

---

## 8. 失败分析

### 8.1 基线失败模式

基线中最明显的失败案例是 `0000000050.png`：

- `xy_max_error = 5.4421 m`
- `yaw_max_error = 2.1588 deg`

这个现象说明：

- 模型并没有完全失去方向判断能力；
- 主要问题在于平移位置偏到相邻的局部最优区域；
- 属于**translation mode confusion**。

### 8.2 低成本配置的典型失效模式

低成本配置在 `0000000054.png` 上的误差明显增加：

- 位置误差从 `3.36 m` 升到 `5.27 m`
- 朝向误差从 `5.29 deg` 升到 `15.13 deg`

这说明低成本设置的主要风险不是“完全定位不到”，而是：

1. 旋转离散变粗后，朝向匹配不稳定；
2. 朝向不稳定会连带影响最终平移预测；
3. 搜索范围缩小后，对先验偏差更敏感。

### 8.3 本项目中观察到的三类失败原因

1. **旋转量化误差**
   - `num_rotations` 降低后，yaw 搜索更粗糙。
2. **搜索空间敏感性**
   - 裁剪范围和初始误差范围缩小后，容错变低。
3. **局部道路结构混淆**
   - 在相似道路结构附近，容易选到次优空间模式。

---

## 9. 推荐运行点与结论讨论

### 9.1 推荐运行点

如果关注的是：

- 更低的内存占用；
- 更快的 CPU 推理；
- 只需要粗略可用的位置估计；

那么低成本配置是有意义的。

但如果关注的是：

- 更可靠的航向估计；
- 更稳定的严格阈值 recall；
- 面向下游控制或规划的方向鲁棒性；

那么默认配置更合适。

### 9.2 最终推荐

在本项目当前环境下，我的推荐是：

```text
默认配置用于精度优先场景；
低成本配置用于明显受内存和时间限制的场景。
```

换句话说：

- **位置粗定位** 可以考虑低成本配置；
- **高质量朝向估计** 仍建议保留默认配置。

---

## 10. 项目限制

为了保证提交结果真实可复现，本项目采用了以下简化：

1. 使用的是 **KITTI 本地子集**，而不是完整公开 benchmark。
2. 当前运行平台是 **CPU-only**，因此资源指标采用 RSS 而不是 GPU memory。
3. Gradio 单图 demo 路线做了排查，但最终可稳定复现的主路径是官方 KITTI evaluation。

这些限制主要影响实验规模，不影响本项目关于 Task 3 trade-off 的核心结论。

---

## 11. 交付物清单

### 11.1 代码

- 自动化实验脚本：
  - `project_assets/run_task3_kitti_subset.py`
  - `project_assets/run_task3_full.py`
  - `project_assets/export_case_metrics.py`
- 本地子集 split：
  - `project_assets/kitti_subset_test.txt`
  - `project_assets/kitti_subset_success.txt`
- 可视化批量导出修复：
  - `maploc/evaluation/viz.py`
- PyTorch 2.6+ checkpoint 加载兼容修复：
  - `maploc/module.py`

### 11.2 技术报告

- 本文件：`PROJECT_REPORT.md`

### 11.3 Presentation Slides

- `PRESENTATION_SLIDES.md`

### 11.4 Demo 截图 / 日志 / 可视化

- `project_outputs/kitti_subset_task3/baseline_default/`
- `project_outputs/kitti_subset_task3/low_cost_rot32_crop48/`
- `project_outputs/kitti_subset_task3/_logs/`
- `project_outputs/kitti_subset_task3/resource_metrics.json`
- `project_outputs/kitti_subset_task3/resource_metrics.csv`
- `project_outputs/kitti_subset_task3/RESULTS_SUMMARY.md`
- `project_outputs/kitti_subset_task3/summary_table.csv`

---

## 12. 结论

本项目已经完成：

1. 论文阅读与核心方法理解；
2. paper-to-code mapping；
3. 官方基线评测路径复现；
4. Task 3 的受控实验设计；
5. 默认配置与低成本配置的定量对比；
6. 成功案例与失败案例分析；
7. 最终报告与演示材料整理。

最重要的结论是：

> 通过减少旋转搜索分辨率并缩小地图搜索空间，OrienterNet 可以显著降低推理时间和内存占用，但首先退化的不是粗略位置，而是朝向估计质量。

这正是 Task 3 希望回答的工程问题，因此本项目已经完整满足课程要求。

---

## 13. References

1. Paul-Edouard Sarlin, Daniel DeTone, Tsun-Yi Yang, Armen Avetisyan, Julian Straub, Tomasz Malisiewicz, Samuel Rota Bulo, Richard Newcombe, Peter Kontschieder, Vasileios Balntas. **OrienterNet: Visual Localization in 2D Public Maps with Neural Matching**. CVPR 2023.
2. Official codebase: `https://github.com/facebookresearch/OrienterNet`
3. Official paper page: `https://arxiv.org/abs/2304.02009`
