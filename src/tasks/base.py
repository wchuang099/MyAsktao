# src/tasks/base.py
"""
问道任务基类 - 状态机实现

参考梦幻开发状态机设计：
1. 任务状态流转
2. 子状态机支持
3. 超时监控集成
"""
from enum import Enum
from typing import Callable, Optional, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class TaskState(Enum):
    """任务状态枚举"""
    IDLE = "idle"                    # 空闲/未开始
    INIT = "init"                   # 初始化
    RUNNING = "running"             # 运行中
    WAITING = "waiting"             # 等待中
    COMPLETED = "completed"         # 完成
    FAILED = "failed"               # 失败
    STOPPED = "stopped"             # 停止


class BaseTask:
    """
    任务基类 - 状态机模式
    
    参考梦幻开发的打图任务状态机设计：
    - 状态流转：读取任务 → 飞行 → 寻路 → 移动 → 点击 → 战斗
    - 超时监控：防止卡死
    - 断点续传：支持中断恢复
    """
    
    # 任务名称（子类必须定义）
    task_name: str = "base_task"
    
    def __init__(self, unify, config: Dict[str, Any]):
        """
        初始化任务
        
        Args:
            unify: UNIFY实例（包含游戏控制能力）
            config: 任务配置
        """
        self.unify = unify
        self.config = config
        
        # 状态机
        self.state = TaskState.IDLE
        self.sub_state: Optional[str] = None
        
        # 超时控制
        self.timeout_seconds = config.get("timeout", 300)
        self.last_action_time = time.time()
        
        # 任务数据
        self.task_data: Dict[str, Any] = {}
        
        # 控制标志
        self._stopped = False
        self._paused = False
        
        logger.info(f"[{self.task_name}] 任务初始化")
    
    def reset_timeout(self):
        """重置超时计时器"""
        self.last_action_time = time.time()
    
    def check_timeout(self) -> bool:
        """
        检查是否超时
        
        Returns:
            True if timeout
        """
        elapsed = time.time() - self.last_action_time
        if elapsed > self.timeout_seconds:
            logger.warning(f"[{self.task_name}] 任务超时 ({elapsed:.0f}秒)")
            return True
        return False
    
    def set_state(self, state: TaskState, sub_state: Optional[str] = None):
        """设置任务状态"""
        logger.debug(f"[{self.task_name}] 状态变更: {self.state.value} -> {state.value}, 子状态: {sub_state}")
        self.state = state
        self.sub_state = sub_state
        self.reset_timeout()
    
    def stop(self):
        """停止任务"""
        self._stopped = True
        self.set_state(TaskState.STOPPED)
        logger.info(f"[{self.task_name}] 任务停止")
    
    def pause(self):
        """暂停任务"""
        self._paused = True
        logger.info(f"[{self.task_name}] 任务暂停")
    
    def resume(self):
        """恢复任务"""
        self._paused = False
        logger.info(f"[{self.task_name}] 任务恢复")
    
    def is_running(self) -> bool:
        """检查任务是否在运行"""
        return self.state in (TaskState.INIT, TaskState.RUNNING, TaskState.WAITING)
    
    def is_stopped(self) -> bool:
        """检查任务是否已停止"""
        return self._stopped or self.state == TaskState.STOPPED
    
    # ====================
    # 子类必须实现的方法
    # ====================
    
    def on_init(self) -> bool:
        """
        初始化阶段（可选重写）
        
        Returns:
            True if success
        """
        return True
    
    def execute(self) -> bool:
        """
        执行任务主逻辑
        
        必须重写！这是状态机的核心执行方法。
        
        Returns:
            True if task completed successfully
        """
        raise NotImplementedError("子类必须实现execute方法")
    
    def on_cleanup(self):
        """
        清理阶段（可选重写）
        
        用于任务结束后的资源清理、界面恢复等
        """
        pass
    
    # ====================
    # 主执行入口
    # ====================
    
    def run(self) -> bool:
        """
        运行任务（主入口）
        
        包含完整的生命周期管理：
        1. 初始化
        2. 执行
        3. 超时检测
        4. 清理
        """
        try:
            # 初始化阶段
            self.set_state(TaskState.INIT)
            if not self.on_init():
                self.set_state(TaskState.FAILED)
                return False
            
            # 执行阶段
            self.set_state(TaskState.RUNNING)
            while self.is_running() and not self._stopped:
                # 超时检测
                if self.check_timeout():
                    self.set_state(TaskState.FAILED)
                    return False
                
                # 暂停检测
                if self._paused:
                    time.sleep(0.5)
                    continue
                
                # 执行任务逻辑
                if not self.execute():
                    self.set_state(TaskState.COMPLETED)
                    break
                
                # 小延时防止CPU占用过高
                time.sleep(0.1)
            
            # 清理阶段
            self.on_cleanup()
            
            if self._stopped:
                self.set_state(TaskState.STOPPED)
            else:
                self.set_state(TaskState.COMPLETED)
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.task_name}] 任务异常: {e}")
            self.set_state(TaskState.FAILED)
            return False


class SubStateMachine:
    """
    子状态机 - 用于复杂任务的子流程管理
    
    例如：师门任务中的"对话"子状态机
    """
    
    def __init__(self, owner: BaseTask):
        self.owner = owner
        self.current_state: Optional[str] = None
        self.state_handlers: Dict[str, Callable] = {}
    
    def register_state(self, state: str, handler: Callable):
        """注册状态处理函数"""
        self.state_handlers[state] = handler
    
    def set_state(self, state: str):
        """切换状态"""
        logger.debug(f"[子状态机] {self.current_state} -> {state}")
        self.current_state = state
    
    def execute(self) -> bool:
        """执行当前状态"""
        if self.current_state is None:
            return True
        
        handler = self.state_handlers.get(self.current_state)
        if handler is None:
            logger.warning(f"[子状态机] 未找到状态处理器: {self.current_state}")
            return False
        
        return handler()
