# src/tasks/monitor.py
"""
问道任务监控模块 - 超时与断线处理

参考梦幻开发的超时监控系统设计：
1. 双线程协作（主线程 + 监控线程）
2. 动态倒计时机制
3. 强制重启流程
"""
import time
import threading
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class TaskMonitor:
    """
    任务超时监控器
    
    参考梦幻开发的超时监控系统：
    - 独立监控线程
    - 动态倒计时
    - 超时回调触发
    """
    
    def __init__(self, timeout: int = 300, on_timeout: Optional[Callable] = None):
        """
        初始化监控器
        
        Args:
            timeout: 超时时间（秒）
            on_timeout: 超时回调函数
        """
        self.timeout = timeout
        self.on_timeout = on_timeout
        
        # 动态超时时间（可动态调整）
        self._current_timeout = timeout
        
        # 控制标志
        self._running = False
        self._paused = False
        
        # 监控线程
        self._monitor_thread: Optional[threading.Thread] = None
        
        # 锁
        self._lock = threading.Lock()
        
        # 回调计数
        self._timeout_count = 0
    
    def start(self):
        """启动监控"""
        if self._running:
            logger.warning("[监控] 监控器已在运行")
            return
        
        self._running = True
        self._paused = False
        self._timeout_count = 0
        
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info(f"[监控] 监控启动，超时时间: {self.timeout}秒")
    
    def stop(self):
        """停止监控"""
        self._running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
            self._monitor_thread = None
        
        logger.info("[监控] 监控停止")
    
    def pause(self):
        """暂停监控（不触发超时）"""
        self._paused = True
        logger.debug("[监控] 监控暂停")
    
    def resume(self):
        """恢复监控"""
        self._paused = False
        self.reset()
        logger.debug("[监控] 监控恢复")
    
    def reset(self):
        """重置倒计时"""
        with self._lock:
            self._current_timeout = self.timeout
        logger.debug(f"[监控] 倒计时重置: {self.timeout}秒")
    
    def extend(self, seconds: int):
        """延长超时时间"""
        with self._lock:
            self._current_timeout += seconds
        logger.debug(f"[监控] 延长超时: +{seconds}秒")
    
    def _monitor_loop(self):
        """监控循环（在独立线程中运行）"""
        while self._running:
            time.sleep(1)
            
            # 暂停时不计时
            if self._paused:
                continue
            
            with self._lock:
                self._current_timeout -= 1
                
                if self._current_timeout <= 0:
                    # 超时触发
                    self._timeout_count += 1
                    logger.warning(f"[监控] 第 {self._timeout_count} 次超时")
                    
                    # 调用超时回调
                    if self.on_timeout:
                        try:
                            self.on_timeout()
                        except Exception as e:
                            logger.error(f"[监控] 超时回调异常: {e}")
                    
                    # 重置计时器继续监控
                    self._current_timeout = self.timeout
    
    def get_status(self) -> dict:
        """获取监控状态"""
        with self._lock:
            remaining = self._current_timeout
        
        return {
            "running": self._running,
            "paused": self._paused,
            "remaining": remaining,
            "timeout_count": self._timeout_count
        }


class ReconnectionHandler:
    """
    断线重连处理器
    
    参考梦幻开发的自动重连设计：
    1. 检测断线状态
    2. 重新登录流程
    3. 任务状态恢复
    """
    
    def __init__(self, unify, login_task):
        """
        初始化
        
        Args:
            unify: UNIFY实例
            login_task: 登录任务类
        """
        self.unify = unify
        self.login_task = login_task
        
        # 重连配置
        self.max_retry = 3
        self.retry_count = 0
        
        # 重连状态
        self.is_disconnected = False
    
    def check_connection(self) -> bool:
        """
        检查连接状态
        
        Returns:
            True if connected
        """
        # 检测游戏主界面特征
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "游戏主界面特征.bmp", "202020", 0.8, 0
        )
        
        connected = result[0] == 0
        
        if not connected and not self.is_disconnected:
            logger.warning("[重连] 检测到断线")
            self.is_disconnected = True
        
        return connected
    
    def reconnect(self) -> bool:
        """
        执行重连
        
        Returns:
            True if reconnected successfully
        """
        if self.retry_count >= self.max_retry:
            logger.error(f"[重连] 重连次数超过上限: {self.max_retry}")
            return False
        
        self.retry_count += 1
        logger.info(f"[重连] 第 {self.retry_count} 次重连...")
        
        try:
            # 1. 关闭可能的弹窗
            self._close_popups()
            
            # 2. 检查是否需要完全重新登录
            if self._need_full_relogin():
                logger.info("[重连] 需要完全重新登录")
                return self._full_relogin()
            
            # 3. 尝试自动重连（游戏内有重连机制）
            return self._auto_reconnect()
            
        except Exception as e:
            logger.error(f"[重连] 重连异常: {e}")
            return False
    
    def _close_popups(self):
        """关闭弹窗"""
        for _ in range(5):
            self.unify.按单个键("esc")
            time.sleep(0.3)
            
            # 检查是否还有弹窗
            result = self.unify.u.FindPic(
                0, 0, 800, 600,
                "弹窗特征.bmp", "202020", 0.8, 0
            )
            
            if result[0] != 0:
                break
    
    def _need_full_relogin(self) -> bool:
        """检查是否需要完全重新登录"""
        # 检查是否在登录界面
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "登录界面.bmp", "202020", 0.8, 0
        )
        
        return result[0] == 0
    
    def _auto_reconnect(self) -> bool:
        """自动重连"""
        # 点击重连按钮
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "重连按钮.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[重连] 点击重连按钮")
            
            # 等待重连
            time.sleep(5)
            
            # 检查是否重连成功
            for _ in range(30):
                if self.check_connection():
                    logger.info("[重连] 重连成功")
                    self.is_disconnected = False
                    self.retry_count = 0
                    return True
                time.sleep(1)
        
        return False
    
    def _full_relogin(self) -> bool:
        """完全重新登录"""
        try:
            # 创建登录任务实例
            login = self.login_task(self.unify, {})
            
            # 运行登录流程
            login.run()
            
            # 检查是否登录成功
            if self.check_connection():
                logger.info("[重连] 重新登录成功")
                self.is_disconnected = False
                self.retry_count = 0
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[重连] 重新登录异常: {e}")
            return False


class MultiTaskController:
    """
    多任务控制器
    
    参考梦幻开发的任务链设计：
    1. 任务队列管理
    2. 状态监控
    3. 异常处理
    """
    
    def __init__(self, window_id: int, unify):
        """
        初始化
        
        Args:
            window_id: 窗口ID
            unify: UNIFY实例
        """
        self.window_id = window_id
        self.unify = unify
        
        # 监控器
        self.monitor = TaskMonitor(timeout=300)
        
        # 当前任务
        self.current_task = None
        
        # 运行状态
        self._running = False
    
    def start_monitoring(self):
        """启动监控"""
        self.monitor.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitor.stop()
    
    def execute_with_monitor(self, task) -> bool:
        """
        带监控的任务执行
        
        Args:
            task: 任务实例
        
        Returns:
            True if success
        """
        self.current_task = task
        self._running = True
        
        # 重置监控
        self.monitor.reset()
        
        try:
            # 执行任务
            result = task.run()
            
            # 任务完成后重置重试计数
            self.monitor.reset()
            
            return result
            
        except Exception as e:
            logger.error(f"[控制器] 任务执行异常: {e}")
            return False
        
        finally:
            self._running = False
            self.current_task = None
    
    def emergency_stop(self):
        """紧急停止"""
        logger.warning("[控制器] 紧急停止")
        
        if self.current_task:
            self.current_task.stop()
        
        self._running = False
        self.monitor.stop()
