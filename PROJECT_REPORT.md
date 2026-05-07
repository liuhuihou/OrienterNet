# OrienterNet Final Project Report

## 1. 项目背景与目标

本项目基于 OrienterNet 论文与官方代码，研究如何利用 2D 公共地图进行自动驾驶场景下的视觉定位。OrienterNet 的核心目标是：在给定一张 RGB 图像和一个粗略地理先验的情况下，同时预测车辆在地图上的二维位置与朝向，并输出可解释的匹配概率分布。

本次最终提交围绕两个层次展开。第一层是基线复现，即确认官方 demo 或评测流程可以正常运行，并记录对应的指标、日志和可视化结果。第二层是任务扩展，我选择 Task 3：Practical Localization under Resource Constraints，重点分析如何在有限算力和有限显存下保持可用的定位精度。

## 2. 论文核心方法概述

OrienterNet 不是直接在图像平面上做位姿回归，而是先把图像特征转换到鸟瞰图表示，再与地图特征进行匹配。系统的大致流程可以概括为：图像编码、尺度或深度先验估计、图像到 BEV 的投影、地图栅格编码，以及在位置和旋转维度上的穷举投票。这个设计的关键优势在于，它把“看图定位”转化成“图像 BEV 与语义地图之间的匹配问题”，从而更适合利用地图先验。

从代码实现上看，主干逻辑集中在 [maploc/models/orienternet.py](maploc/models/orienternet.py)。其中图像编码器负责提取图像特征，BEV 投影模块完成视角变换，地图编码器把地图栅格转换成可匹配的神经特征，最后通过 voting 模块得到位置和朝向的分数图。Demo 与评测入口分别位于 [maploc/demo.py](maploc/demo.py)、[app.py](app.py)、[maploc/evaluation/run.py](maploc/evaluation/run.py)、[maploc/evaluation/mapillary.py](maploc/evaluation/mapillary.py) 和 [maploc/evaluation/kitti.py](maploc/evaluation/kitti.py)。

## 3. 论文模块与代码模块对应关系

| 论文模块 | 主要代码位置 | 功能说明 |
|---|---|---|
| 图像编码器 | [maploc/models/orienternet.py](maploc/models/orienternet.py), [maploc/models/feature_extractor_v2.py](maploc/models/feature_extractor_v2.py) | 提取图像特征并生成多尺度特征图。 |
| 单目尺度/深度先验 | [maploc/models/orienternet.py](maploc/models/orienternet.py), [maploc/models/bev_projection.py](maploc/models/bev_projection.py) | 将图像特征映射到极坐标或深度相关表示。 |
| 图像到 BEV 投影 | [maploc/models/bev_projection.py](maploc/models/bev_projection.py) | 完成图像空间到鸟瞰空间的转换。 |
| 地图编码器 | [maploc/models/map_encoder.py](maploc/models/map_encoder.py) | 将 2D 地图栅格编码成神经地图特征。 |
| 神经匹配与投票 | [maploc/models/orienternet.py](maploc/models/orienternet.py), [maploc/models/voting.py](maploc/models/voting.py) | 在空间与朝向上计算匹配分数并输出位姿候选。 |
| 结果输出与度量 | [maploc/models/orienternet.py](maploc/models/orienternet.py), [maploc/models/metrics.py](maploc/models/metrics.py) | 计算 recall、位置误差和朝向误差等指标。 |
| Demo 入口 | [maploc/demo.py](maploc/demo.py), [app.py](app.py) | 对单张图像进行端到端定位。 |
| 官方评测入口 | [maploc/evaluation/run.py](maploc/evaluation/run.py), [maploc/evaluation/mapillary.py](maploc/evaluation/mapillary.py), [maploc/evaluation/kitti.py](maploc/evaluation/kitti.py) | 运行单帧或序列化评测流程。 |
| 序列定位 | [maploc/models/sequential.py](maploc/models/sequential.py), [maploc/evaluation/run.py](maploc/evaluation/run.py) | 融合短序列中的多帧信息，提升稳定性。 |

## 4. 基线复现结果与说明

### 4.1 环境信息

本项目的基线复现需要记录以下信息：

- 操作系统：Linux
- Python 版本：[填写]
- PyTorch 版本：[填写]
- GPU 型号与显存：[填写]
- 关键依赖版本：[填写]

### 4.2 基线流程

如果目标是快速证明仓库可运行，建议优先执行官方 demo：

```bash
python app.py
```

如果你具备数据集访问权限，则建议补充官方评测流程。Mapillary 评测命令如下：

```bash
python -m maploc.data.mapillary.prepare --token $YOUR_ACCESS_TOKEN
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL model.num_rotations=256
```

KITTI 评测命令如下：

```bash
python -m maploc.data.kitti.prepare
python -m maploc.evaluation.kitti --experiment OrienterNet_MGL model.num_rotations=256
```

### 4.3 基线应记录的指标

| 指标 | 基线结果 | 说明 |
|---|---:|---|
| 定位成功率 / Recall | [填写] | 按所选评测脚本输出填写。 |
| 位置误差 | [填写] | 若评测集提供真值则填写。 |
| 朝向误差 | [填写] | 若评测集提供真值则填写。 |
| 单样本运行时间 | [填写] | 建议在相同硬件上统计。 |
| 峰值 GPU 显存 | [填写] | Task 3 必填。 |

### 4.4 基线证据清单

基线部分必须提供以下证据：

- 环境信息或截图。
- 运行命令。
- 输入数据或子集说明。
- 真实跑通的日志或终端输出。
- 至少 3 个成功案例。
- 至少 1 个失败案例，并给出原因分析。

## 5. Task 3：资源受限场景下的实用定位

### 5.1 任务目标

Task 3 的核心不是追求最强精度，而是在有限资源下找到一个可实际部署的平衡点。也就是说，需要明确回答三个问题：在什么配置下模型还能保持可用定位质量，哪些参数最影响速度和显存，以及推荐的运行点是什么。

### 5.2 可控变量

结合仓库默认配置和评测实现，最值得控制的参数有以下几个：

- `model.num_rotations`：控制旋转搜索分辨率，直接影响速度和显存。
- `data.resize_image`：控制输入分辨率，影响特征提取和后续匹配成本。
- `data.crop_size_meters`：控制地图裁剪范围，影响搜索空间大小。
- `data.max_init_error`：控制初始先验误差范围，影响候选空间宽度。
- `data.pixel_per_meter`：控制地图分辨率，影响空间精度和计算量。

从仓库配置看，`maploc/conf/orienternet.yaml` 中默认的模型参数包含 `num_rotations=64`、`x_max=32`、`pixel_per_meter=${data.pixel_per_meter}`。数据配置中，Mapillary 常用 `pixel_per_meter=2`、`crop_size_meters=64`、`max_init_error=48`、`resize_image=512`；KITTI 常用 `pixel_per_meter=2`、`crop_size_meters=64`、`max_init_error=32`、`resize_image=[448,160]`。

### 5.3 任务 3 实验方案表

下面这张表可以直接作为实验计划和结果记录模板使用。

| 方案 | 配置内容 | 目的 | 预期记录项 |
|---|---|---|---|
| 默认配置 | 使用官方或仓库默认参数，例如 `model.num_rotations=256` 或当前评测脚本默认值；保持 `resize_image`、`crop_size_meters`、`max_init_error` 不变。 | 作为性能与资源消耗的对照基线。 | Recall、位置误差、朝向误差、单样本时间、峰值显存。 |
| 低成本配置 A | 将 `model.num_rotations` 从较大值降低到 `64`，必要时进一步尝试 `32`。 | 验证减少旋转搜索是否能显著降低推理成本。 | Recall 下降幅度、朝向误差变化、运行时间变化、显存变化。 |
| 低成本配置 B | 在保持旋转数相对稳定的情况下，适度减小 `data.resize_image` 或缩小地图搜索范围。 | 验证输入分辨率和搜索空间缩减对效率的影响。 | Recall 变化、位置误差变化、运行时间变化、峰值显存。 |
| 推荐运行点 | 在精度和效率之间选择最均衡的一组参数，例如 `num_rotations=64` 配合默认地图范围。 | 给出一个实际部署时可接受的方案。 | 最终推荐配置、对应性能指标、与默认配置的差距。 |

### 5.4 推荐实验顺序

建议按下面顺序做实验，避免一次改太多变量：

1. 先跑默认配置并记录完整指标。
2. 只修改 `model.num_rotations`，观察速度和精度变化。
3. 如果需要进一步降本，再修改 `resize_image` 或搜索范围。
4. 选择一个综合表现最稳的配置作为推荐运行点。

## 6. 可执行实验步骤

### 步骤 1：确认环境

建议先记录以下命令输出：

```bash
python --version
python -c "import torch; print(torch.__version__)"
nvidia-smi
```

### 步骤 2：跑通基线

先执行最容易成功的官方 demo：

```bash
python app.py
```

如果 demo 成功，再执行官方评测：

```bash
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL model.num_rotations=256
```

或：

```bash
python -m maploc.evaluation.kitti --experiment OrienterNet_MGL model.num_rotations=256
```

### 步骤 3：保存基线证据

把下列内容保存到报告附件或实验记录中：

- 终端日志。
- 输出指标。
- 成功案例截图。
- 失败案例截图。

### 步骤 4：跑低成本配置

最推荐的 Task 3 低成本改法是减少旋转数：

```bash
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL model.num_rotations=64
```

如果需要更强的降本，可以继续尝试：

```bash
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL model.num_rotations=32
```

如果使用 KITTI，则对应替换为：

```bash
python -m maploc.evaluation.kitti --experiment OrienterNet_MGL model.num_rotations=64
```

### 步骤 5：整理对比结果

将默认配置与低成本配置放入同一张表中比较：

| 配置 | Recall / 准确率 | 位置误差 | 朝向误差 | 运行时间 | 峰值显存 |
|---|---:|---:|---:|---:|---:|
| 默认配置 | [填写] | [填写] | [填写] | [填写] | [填写] |
| 低成本配置 | [填写] | [填写] | [填写] | [填写] | [填写] |

### 步骤 6：写最终结论

最终结论建议围绕以下三点展开：

- 降低成本后性能损失是否可接受。
- 哪个参数对速度和显存影响最大。
- 哪个配置最适合作为实际部署方案。

## 7. 结果分析写法

写结果时建议按照“现象 - 原因 - 结论”的方式组织：

1. 先描述默认配置的性能与资源占用。
2. 再描述低成本配置带来的变化。
3. 最后解释变化背后的原因，例如旋转搜索变少导致匹配空间减少，或者分辨率降低导致特征更粗糙。

## 8. 失败分析

Task 3 的失败通常来自资源压缩过度。常见问题包括：旋转数过少导致朝向估计不稳定，搜索范围过小导致真实位姿落在候选空间之外，输入分辨率过低导致 BEV 特征模糊，以及地图裁剪太小导致上下文信息不足。报告中至少需要选一个代表性失败案例，并解释它属于哪一类失效模式。

## 9. 结论

本项目表明，OrienterNet 的定位流程具有清晰的模块化结构，适合通过控制旋转数、图像分辨率和搜索范围来分析效率与精度之间的关系。Task 3 的重点不在于追求最优数值，而在于给出一个工程上合理、可部署的配置建议。最终报告应明确说明：默认配置的基线效果、低成本配置的性能损失，以及推荐的实际运行点。

## 10. 命令清单

| 目的 | 命令 |
|---|---|
| Demo | `python app.py` |
| Mapillary 基线 | `python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL model.num_rotations=256` |
| Mapillary 低成本 | `python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL model.num_rotations=64` |
| KITTI 基线 | `python -m maploc.evaluation.kitti --experiment OrienterNet_MGL model.num_rotations=256` |
| KITTI 低成本 | `python -m maploc.evaluation.kitti --experiment OrienterNet_MGL model.num_rotations=64` |

## 11. 最终交付物检查表

- 论文总结。
- 系统图。
- 论文模块到代码模块映射。
- 基线结果表。
- 至少 3 个成功案例。
- 至少 1 个失败案例。
- Task 3 低成本配置说明。
- 默认配置与低成本配置对比表。
- 最终结论与推荐运行点。
