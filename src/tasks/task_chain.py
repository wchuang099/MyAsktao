# src/tasks/task_chain.py
"""
任务链管理 - 多任务顺序执行

参考梦幻开发的任务链设计：
1. 动态任务链配置
2. 断点续传逻辑
3. 跨账号配置复原
"""
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskInfo:
    """任务信息"""
    name: str           # 任务名称
    enabled: bool = True  # 是否启用
    config: Dict[str, Any] = None  # 任务配置
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class TaskChain:
    """
    任务链管理器
    
    功能：
    1. 管理多任务执行顺序
    2. 断点续传（任务完成后自动剔除并保存）
    3. 任务镜像（支持换号重置）
    4. 实时状态反馈
    """
    
    TASK_FILE = "task_chain.json"
    
    # 任务名称常量
    TASK_LOGIN = "login"
    TASK_DAILY = "daily"
    TASK_SHIMEN = "shimen"
    TASK_BANGPAI = "bangpai"
    TASK_FUBEN = "fuben"
    
    def __init__(self, window_id: int, config_file: Optional[str] = None):
        """
        初始化任务链管理器
        
        Args:
            window_id: 窗口ID（用于配置文件隔离）
            config_file: 配置文件路径
        """
        self.window_id = window_id
        self.config_file = config_file or self.TASK_FILE
        
        # 原始任务链（镜像）
        self.task_mirror: List[TaskInfo] = []
        
        # 当前任务链（实时流）
        self.task_flow: List[TaskInfo] = []
        
        # 当前执行索引
        self.current_index = 0
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载任务链配置"""
        if not os.path.exists(self.config_file):
            logger.info(f"任务链配置文件不存在，创建默认配置")
            self._create_default_config()
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            window_key = f"window_{self.window_id}"
            if window_key in data:
                config = data[window_key]
                
                # 加载任务流
                self.task_flow = [TaskInfo(**t) for t in config.get("task_flow", [])]
                
                # 加载任务镜像
                self.task_mirror = [TaskInfo(**t) for t in config.get("task_mirror", [])]
                
                # 当前索引
                self.current_index = config.get("current_index", 0)
                
                logger.info(f"加载任务链配置: {len(self.task_flow)} 个任务")
        except Exception as e:
            logger.error(f"加载任务链配置失败: {e}")
            self._create_default_config()
    
    def _save_config(self):
        """保存任务链配置"""
        try:
            # 读取现有配置
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
            
            window_key = f"window_{self.window_id}"
            data[window_key] = {
                "task_flow": [asdict(t) for t in self.task_flow],
                "task_mirror": [asdict(t) for t in self.task_mirror],
                "current_index": self.current_index
            }
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"保存任务链配置成功")
        except Exception as e:
            logger.error(f"保存任务链配置失败: {e}")
    
    def _create_default_config(self):
        """创建默认任务链配置"""
        # 默认任务顺序：登录 -> 日常 -> 师门 -> 帮派 -> 副本
        self.task_mirror = [
            TaskInfo(name=self.TASK_LOGIN, enabled=True),
            TaskInfo(name=self.TASK_SHIMEN, enabled=True),
            TaskInfo(name=self.TASK_BANGPAI, enabled=True),
            TaskInfo(name=self.TASK_FUBEN, enabled=True),
        ]
        self.task_flow = [TaskInfo(**asdict(t)) for t in self.task_mirror]
        self.current_index = 0
        self._save_config()
    
    def get_current_task(self) -> Optional[TaskInfo]:
        """获取当前任务"""
        if 0 <= self.current_index < len(self.task_flow):
            return self.task_flow[self.current_index]
        return None
    
    def get_remaining_tasks(self) -> List[TaskInfo]:
        """获取剩余任务列表"""
        return self.task_flow[self.current_index:]
    
    def complete_current_task(self):
        """标记当前任务完成"""
        if self.current_index < len(self.task_flow):
            completed_task = self.task_flow[self.current_index]
            logger.info(f"任务完成: {completed_task.name}")
            
            # 移除已完成任务
            self.task_flow.pop(self.current_index)
            
            # 保存断点
            self._save_config()
    
    def reset_to_mirror(self):
        """重置任务链到镜像状态（换号时调用）"""
        self.task_flow = [TaskInfo(**asdict(t)) for t in self.task_mirror]
        self.current_index = 0
        self._save_config()
        logger.info("任务链已重置到初始状态")
    
    def set_task_config(self, task_name: str, config: Dict[str, Any]):
        """设置任务配置"""
        for task in self.task_mirror:
            if task.name == task_name:
                task.config = config
                break
        
        for task in self.task_flow:
            if task.name == task_name:
                task.config = config
                break
        
        self._save_config()
    
    def is_completed(self) -> bool:
        """检查任务链是否全部完成"""
        return self.current_index >= len(self.task_flow)
    
    def get_status(self) -> Dict[str, Any]:
        """获取任务链状态"""
        return {
            "current_task": self.get_current_task().name if self.get_current_task() else None,
            "remaining_count": len(self.task_flow) - self.current_index,
            "total_count": len(self.task_mirror),
            "progress": f"{self.current_index}/{len(self.task_mirror)}"
        }
    
    def update_task_flow(self, task_flow: List[str]):
        """
        更新任务流顺序
        
        Args:
            task_flow: 任务名称列表，如 ["login", "shimen", "bangpai"]
        """
        self.task_mirror = [TaskInfo(name=name) for name in task_flow]
        self.task_flow = [TaskInfo(name=name) for name in task_flow]
        self.current_index = 0
        self._save_config()
        logger.info(f"更新任务流: {task_flow}")
