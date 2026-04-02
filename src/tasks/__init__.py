# src/tasks/__init__.py
"""
问道自动化任务模块
"""
from .base import BaseTask, TaskState
from .task_chain import TaskChain, TaskInfo
from .login import LoginTask
from .shimen import ShimenTask
from .bangpai import BangpaiTask
from .fuben import FubenTask
from .monitor import TaskMonitor, ReconnectionHandler, MultiTaskController

__all__ = [
    "BaseTask", "TaskState", 
    "TaskChain", "TaskInfo",
    "LoginTask",
    "ShimenTask", 
    "BangpaiTask", 
    "FubenTask",
    "TaskMonitor", "ReconnectionHandler", "MultiTaskController"
]
