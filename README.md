# 问道脚本中控台

基于梦幻开发实战的多进程自动化脚本框架。

## 快速开始

### 1. 安装依赖

```bash
pip install PySide2
```

> 注意：PyUnifyEN 和 PySide2 需要预先安装，这是硬件控制库的依赖。

### 2. 运行GUI

```bash
cd d:/PyProject/MyAsktao
python main.py
```

### 3. 或直接运行Worker进程

```bash
python main.py --worker 1
python main.py --worker 2
```

## 功能说明

### 窗口管理
- 支持 5 个游戏窗口同时管理
- 每个窗口独立进程运行
- 实时状态监控

### 任务链配置
- 可视化任务链配置界面
- 预设方案一键应用
- 支持拖拽排序

### 可用任务
| 任务 | 说明 |
|------|------|
| 登录 | 自动登录游戏 |
| 师门任务 | 完成师门任务循环 |
| 帮派任务 | 执行帮派任务 |
| 副本任务 | 副本自动通关 |

### 右键菜单
- 执行单个任务
- 启动/停止任务链
- 窗口配置

## 项目结构

```
MyAsktao/
├── main.py              # 入口文件
├── src/
│   ├── gui.py           # GUI界面
│   ├── worker.py        # Worker进程
│   ├── utils/
│   │   └── unify.py     # UNIFY控制封装
│   └── tasks/
│       ├── base.py      # 任务基类
│       ├── task_chain.py # 任务链管理
│       ├── login.py     # 登录任务
│       ├── shimen.py    # 师门任务
│       ├── bangpai.py  # 帮派任务
│       └── fuben.py    # 副本任务
├── assets/              # 资源文件
└── task_chain.json      # 任务配置
```

## 新增任务指南

参考 `src/tasks/base.py` 中的 `BaseTask` 基类：

```python
from src.tasks.base import BaseTask, TaskState

class MyTask(BaseTask):
    task_name = "my_task"
    
    def on_init(self) -> bool:
        """初始化阶段"""
        return True
    
    def execute(self) -> bool:
        """执行主逻辑，返回 False 表示任务完成"""
        # TODO: 实现你的任务逻辑
        
        # 任务完成
        return False
    
    def on_cleanup(self):
        """清理阶段"""
        pass
```

然后在 `worker.py` 的 `TASK_MAPPING` 中注册：

```python
TASK_MAPPING = {
    "login": LoginTask,
    "shimen": ShimenTask,
    # 添加新任务
    "my_task": MyTask,
}
```

## 配置说明

配置文件 `task_chain.json` 示例：

```json
{
    "window_1": {
        "vnc_port": 101,
        "account": "your_account",
        "task_flow": ["login", "shimen"]
    },
    "chain_list": ["登录", "师门任务"]
}
```
