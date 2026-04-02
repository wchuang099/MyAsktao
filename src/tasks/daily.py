# src/tasks/daily.py
"""
问道日常任务模块 - 日常任务状态机

参考梦幻开发的日常任务设计：
1. 多任务并行/串行执行
2. 任务优先级
3. 精力管理
"""
import time
import logging
from .base import BaseTask, TaskState

logger = logging.getLogger(__name__)


class DailyState:
    """日常任务子状态"""
    CHECK_DAILY = "check_daily"                  # 检查日常状态
    EXECUTE_SINGLE = "execute_single"            # 执行单个日常
    CHECK_STAMINA = "check_stamina"              # 检查精力
    RESTORE_STAMINA = "restore_stamina"          # 恢复精力
    SWITCH_ACCOUNT = "switch_account"            # 切换账号


class DailyTask(BaseTask):
    """
    问道日常任务
    
    日常任务包括：
    1. 除暴安良（巡逻）
    2. 助人为乐（任务链）
    3. 修行（刷道）
    4. 副本（各种副本）
    
    参考梦幻设计：
    - 精力系统
    - 任务优先级
    - 自动切换
    """
    
    task_name = "daily"
    
    def __init__(self, unify, config: dict):
        super().__init__(unify, config)
        
        # 日常配置
        self.enable_patrol = config.get("enable_patrol", True)      # 除暴
        self.enable_helper = config.get("enable_helper", True)      # 助人
        self.enable_cultivate = config.get("enable_cultivate", True) # 修行
        self.enable_fuben = config.get("enable_fuben", True)        # 副本
        
        # 精力配置
        self.min_stamina = config.get("min_stamina", 100)  # 最低精力阈值
        self.auto_restore = config.get("auto_restore", True)
        
        # 任务列表
        self.task_list = self._build_task_list()
        self.current_task_index = 0
        
        # 初始化状态
        self.daily_state = DailyState.CHECK_DAILY
    
    def _build_task_list(self) -> list:
        """构建任务列表"""
        tasks = []
        
        if self.enable_patrol:
            tasks.append(("patrol", "除暴安良"))
        if self.enable_helper:
            tasks.append(("helper", "助人为乐"))
        if self.enable_cultivate:
            tasks.append(("cultivate", "修行"))
        if self.enable_fuben:
            tasks.append(("fuben", "副本"))
        
        return tasks
    
    def on_init(self) -> bool:
        """初始化"""
        logger.info(f"[日常] 开始日常任务，共 {len(self.task_list)} 项")
        
        self.timeout_seconds = 7200  # 2小时
        
        self._close_all_panels()
        
        return True
    
    def execute(self) -> bool:
        """执行日常任务"""
        time.sleep(0.2)
        
        # 状态分发
        if self.daily_state == DailyState.CHECK_DAILY:
            return self._check_daily_status()
        
        elif self.daily_state == DailyState.CHECK_STAMINA:
            return self._check_stamina()
        
        elif self.daily_state == DailyState.EXECUTE_SINGLE:
            return self._execute_single_task()
        
        elif self.daily_state == DailyState.RESTORE_STAMINA:
            return self._restore_stamina()
        
        elif self.daily_state == DailyState.SWITCH_ACCOUNT:
            return self._switch_account()
        
        return True
    
    def _check_daily_status(self) -> bool:
        """检查日常状态"""
        # 检查精力
        stamina = self._get_stamina()
        logger.info(f"[日常] 当前精力: {stamina}")
        
        if stamina < self.min_stamina:
            logger.warning(f"[日常] 精力不足 ({stamina} < {self.min_stamina})")
            
            if self.auto_restore:
                self.daily_state = DailyState.RESTORE_STAMINA
            else:
                self.daily_state = DailyState.SWITCH_ACCOUNT
        else:
            self.daily_state = DailyState.EXECUTE_SINGLE
        
        return True
    
    def _get_stamina(self) -> int:
        """获取当前精力"""
        # 识别精力数值
        self.unify.u.UseDict(1)  # 数字字库
        
        result = self.unify.u.Ocr(
            700, 20, 780, 40,
            color="00ffff-101010"
        )
        
        try:
            return int(result)
        except:
            return 0
    
    def _check_stamina(self) -> bool:
        """检查精力是否足够"""
        stamina = self._get_stamina()
        
        if stamina >= self.min_stamina:
            self.daily_state = DailyState.EXECUTE_SINGLE
        else:
            if self.auto_restore:
                self.daily_state = DailyState.RESTORE_STAMINA
            else:
                self.daily_state = DailyState.SWITCH_ACCOUNT
        
        return True
    
    def _execute_single_task(self) -> bool:
        """执行单个日常任务"""
        # 检查是否还有任务
        if self.current_task_index >= len(self.task_list):
            logger.info("[日常] 所有日常任务完成")
            return False
        
        task_type, task_name = self.task_list[self.current_task_index]
        logger.info(f"[日常] 执行 {task_name}")
        
        # 执行对应任务
        success = False
        
        if task_type == "patrol":
            success = self._execute_patrol()
        elif task_type == "helper":
            success = self._execute_helper()
        elif task_type == "cultivate":
            success = self._execute_cultivate()
        elif task_type == "fuben":
            success = self._execute_daily_fuben()
        
        if success:
            self.current_task_index += 1
            logger.info(f"[日常] {task_name} 完成")
        
        # 检查精力
        stamina = self._get_stamina()
        if stamina < 10:  # 精力耗尽
            logger.warning("[日常] 精力耗尽")
            self.daily_state = DailyState.SWITCH_ACCOUNT
        else:
            self.daily_state = DailyState.EXECUTE_SINGLE
        
        self.reset_timeout()
        return True
    
    def _execute_patrol(self) -> bool:
        """执行除暴安良"""
        logger.info("[日常] 执行除暴安良")
        
        # TODO: 实现除暴任务逻辑
        # 1. 打开日常面板
        # 2. 选择除暴
        # 3. 自动执行
        
        time.sleep(5)
        
        # 检查是否完成
        stamina = self._get_stamina()
        return stamina >= 10
    
    def _execute_helper(self) -> bool:
        """执行助人为乐"""
        logger.info("[日常] 执行助人为乐")
        
        # TODO: 实现助人为乐逻辑
        
        time.sleep(5)
        
        return True
    
    def _execute_cultivate(self) -> bool:
        """执行修行"""
        logger.info("[日常] 执行修行")
        
        # TODO: 实现修行逻辑
        
        time.sleep(5)
        
        return True
    
    def _execute_daily_fuben(self) -> bool:
        """执行日常副本"""
        logger.info("[日常] 执行日常副本")
        
        # TODO: 实现日常副本逻辑
        
        time.sleep(5)
        
        return True
    
    def _restore_stamina(self) -> bool:
        """恢复精力"""
        logger.info("[日常] 恢复精力")
        
        # 寻找精力恢复NPC或使用道具
        # TODO: 实现精力恢复
        
        time.sleep(3)
        
        self.daily_state = DailyState.EXECUTE_SINGLE
        return True
    
    def _switch_account(self) -> bool:
        """切换账号"""
        logger.info("[日常] 准备切换账号")
        
        # 通知主控制器切换账号
        # TODO: 实现切换账号逻辑
        
        return False
    
    def _close_dialog(self):
        """关闭对话框"""
        self.unify.按单个键("esc")
        time.sleep(0.3)
    
    def _close_all_panels(self):
        """关闭所有面板"""
        for _ in range(3):
            self._close_dialog()
            time.sleep(0.2)
    
    def on_cleanup(self):
        """清理"""
        self._close_all_panels()
        logger.info(f"[日常] 日常任务结束，完成 {self.current_task_index} 项")
