# OrienterNet

OrienterNet 是一个基于 OpenStreetMap 的视觉定位项目：输入一张街景图片，模型预测图片对应的位置和朝向。

这个仓库主要有 4 种用法：

1. 跑本地 Demo
2. 评测 KITTI 数据集
3. 评测 Mapillary Geo-Localization 数据集
4. 训练模型

## 1. 环境准备

建议使用 Python 3.8 及以上版本。

如果你只想跑 Demo：

```bash
python -m pip install -r requirements/demo.txt
```

如果你要做评测或训练：

```bash
python -m pip install -r requirements/full.txt
```

如果你希望当前仓库可以直接被 Python 导入，建议额外执行：

```bash
python -m pip install -e .
```

## 2. 最快跑起来

### 方式一：启动本地 Demo

安装完 `requirements/demo.txt` 后，直接运行：

```bash
python app.py
```

启动后会打开一个本地 Gradio 页面。你可以：

- 直接使用 `assets/` 里的示例图片
- 上传自己的图片
- 如果图片没有 EXIF GPS 信息，需要手动输入地址或地标名称

说明：

- 首次运行会自动下载预训练模型
- 默认优先使用 GPU；没有 GPU 时会退回 CPU，但会慢很多

### 方式二：跑仓库自带的 KITTI 子集脚本

仓库里已经带了一个可直接复现实验结果的脚本：

```bash
python project_assets/run_task3_kitti_subset.py --only baseline
```

可选参数：

```bash
python project_assets/run_task3_kitti_subset.py --only smoke
python project_assets/run_task3_kitti_subset.py --only low_cost
python project_assets/run_task3_kitti_subset.py --only all
```

结果会输出到：

```bash
project_outputs/kitti_subset_task3/
```

## 3. 跑 KITTI 评测

### 3.1 准备数据

先下载并整理 KITTI 数据到默认目录 `datasets/kitti/`：

```bash
python -m maploc.data.kitti.prepare
```

如果你想自己生成 OSM tiles，而不是使用脚本下载好的 tiles，可以加：

```bash
python -m maploc.data.kitti.prepare --generate_tiles
```

### 3.2 开始评测

使用预训练模型评测：

```bash
python -m maploc.evaluation.kitti --experiment OrienterNet_MGL model.num_rotations=256
```

导出可视化结果：

```bash
python -m maploc.evaluation.kitti --experiment OrienterNet_MGL \
  --output_dir ./viz_KITTI --num 100 model.num_rotations=256
```

顺序模式评测：

```bash
python -m maploc.evaluation.kitti --experiment OrienterNet_MGL \
  --sequential model.num_rotations=256
```

## 4. 跑 Mapillary 评测

### 4.1 准备数据

先去 Mapillary 申请开发者 token，然后执行：

```bash
python -m maploc.data.mapillary.prepare --token YOUR_ACCESS_TOKEN
```

默认会把数据放到：

```bash
datasets/MGL/
```

### 4.2 开始评测

```bash
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL model.num_rotations=256
```

导出可视化结果：

```bash
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL \
  --output_dir ./viz_MGL --num 100 model.num_rotations=256
```

顺序模式评测：

```bash
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL \
  --sequential model.num_rotations=256
```

如果显存不够，可以把旋转数调低，例如：

```bash
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL model.num_rotations=128
```

## 5. 训练模型

训练 MGL 模型：

```bash
python -m maploc.train experiment.name=OrienterNet_MGL_reproduce
```

如果只有 1 张 GPU，可以把 batch size 调小：

```bash
python -m maploc.train experiment.name=OrienterNet_MGL_reproduce \
  experiment.gpus=1 data.loading.train.batch_size=4
```

训练输出默认保存在：

```bash
experiments/OrienterNet_MGL_reproduce/
```

训练后评测：

```bash
python -m maploc.evaluation.mapillary --experiment OrienterNet_MGL_reproduce
```

指定某个 checkpoint：

```bash
python -m maploc.evaluation.mapillary \
  --experiment OrienterNet_MGL_reproduce/checkpoint-step=340000.ckpt
```

在 KITTI 上微调：

```bash
python -m maploc.train experiment.name=OrienterNet_MGL_kitti data=kitti \
  training.finetune_from_checkpoint='"experiments/OrienterNet_MGL_reproduce/checkpoint-step=340000.ckpt"'
```

## 6. 常用文件

- `app.py`：本地 Demo 入口
- `project_assets/run_task3_kitti_subset.py`：KITTI 子集实验脚本
- `demo.ipynb`：Notebook Demo
- `notebooks/`：可视化分析 Notebook

## 7. 常见问题

### 没有定位先验，Demo 跑不起来

如果图片里没有 EXIF GPS 信息，Demo 需要你手动输入地址、街道名或建筑名。

### 第一次运行很慢

首次运行通常会自动下载预训练模型或数据文件，属于正常现象。

### 显存不够

优先降低：

- `model.num_rotations`
- batch size

## 8. 参考资料

- 论文：`2304.02009v1.pdf`
- 项目页面：https://psarlin.com/orienternet
- 原始仓库：https://github.com/facebookresearch/OrienterNet
