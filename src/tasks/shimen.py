# src/tasks/shimen.py
"""
问道师门任务模块 - 师门状态机

参考梦幻开发的打图任务状态机设计：
1. 任务读取 → 寻路 → 交互 → 战斗
2. 超时监控
3. 异常处理
"""
import time
import logging
from .base import BaseTask, TaskState

logger = logging.getLogger(__name__)


class ShimenState:
    """师门任务子状态"""
    # 主流程
    CHECK_TASK = "check_task"                    # 检查师门任务状态
    GO_TO_NPC = "go_to_npc"                      # 前往师傅处
    TALK_TO_MASTER = "talk_to_master"            # 与师傅对话
    RECEIVE_TASK = "receive_task"                 # 领取任务
    EXECUTE_TASK = "execute_task"                # 执行任务
    RETURN_TO_MASTER = "return_to_master"        # 回去交任务
    COMPLETE_TASK = "complete_task"              # 完成任务
    
    # 任务类型子状态
    TASK_KILL = "task_kill"                      # 击杀类
    TASK_DELIVER = "task_deliver"                # 送货类
    TASK_FIND = "task_find"                      # 寻找类
    TASK_BATTLE = "task_battle"                  # 战斗类


class ShimenTask(BaseTask):
    """
    问道师门任务
    
    师门任务流程：
    1. 检查是否已有师门任务
    2. 没有则找师傅领任务
    3. 根据任务类型执行（杀怪/送货/寻人/战斗）
    4. 完成后回去交任务
    5. 循环10次师门
    
    参考梦幻打图状态机设计：
    - 任务读取
    - 智能寻路
    - NPC交互
    - 战斗处理
    """
    
    task_name = "shimen"
    
    def __init__(self, unify, config: dict):
        super().__init__(unify, config)
        
        # 师门配置
        self.max_rounds = config.get("max_rounds", 10)  # 师门轮数
        self.current_round = 0
        
        # 师傅位置
        self.master_pos = config.get("master_pos", {"x": 380, "y": 250})
        
        # 当前任务信息
        self.task_type = None  # kill/deliver/find/battle
        self.task_target = None  # 任务目标
        self.task_location = None  # 任务地点
        
        # 师傅位置配置（揽仙镇）
        self.master_map = config.get("master_map", "揽仙镇")
        
        # 初始化状态
        self.shimen_state = ShimenState.CHECK_TASK
        self.task_loop = 0
    
    def on_init(self) -> bool:
        """初始化"""
        logger.info(f"[师门] 开始师门任务，目标 {self.max_rounds} 轮")
        
        # 初始化超时时间
        self.timeout_seconds = 1800  # 30分钟超时
        
        # 关闭可能存在的对话框
        self._close_dialog()
        
        return True
    
    def execute(self) -> bool:
        """
        执行师门任务状态机
        
        Returns:
            True if should continue, False if task completed
        """
        time.sleep(0.2)
        
        # 状态分发
        if self.shimen_state == ShimenState.CHECK_TASK:
            return self._check_task_status()
        
        elif self.shimen_state == ShimenState.GO_TO_NPC:
            return self._go_to_npc()
        
        elif self.shimen_state == ShimenState.TALK_TO_MASTER:
            return self._talk_to_master()
        
        elif self.shimen_state == ShimenState.RECEIVE_TASK:
            return self._receive_task()
        
        elif self.shimen_state == ShimenState.EXECUTE_TASK:
            return self._execute_task()
        
        elif self.shimen_state == ShimenState.RETURN_TO_MASTER:
            return self._return_to_master()
        
        elif self.shimen_state == ShimenState.COMPLETE_TASK:
            return self._complete_task()
        
        return True
    
    def _check_task_status(self) -> bool:
        """检查师门任务状态"""
        # 检查是否有师门任务（通过快捷栏或任务追踪）
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "师门任务图标.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            # 有师门任务，识别任务内容
            logger.info("[师门] 检测到师门任务")
            return self._parse_task_content()
        else:
            # 没有师门任务，去找师傅
            logger.info("[师门] 没有师门任务，前往师傅处")
            self.shimen_state = ShimenState.GO_TO_NPC
            return True
    
    def _parse_task_content(self) -> bool:
        """解析任务内容"""
        # 使用OCR识别任务详情
        self.unify.u.UseDict(8)  # 任务字库
        
        # 识别任务追踪栏
        task_text = self.unify.u.Ocr(
            0, 0, 200, 30,
            color="00ff00-101010"  # 绿色任务文字
        )
        
        logger.info(f"[师门] 任务内容: {task_text}")
        
        # 解析任务类型
        if "击杀" in task_text or "消灭" in task_text:
            self.task_type = ShimenState.TASK_KILL
        elif "送到" in task_text or "交给" in task_text:
            self.task_type = ShimenState.TASK_DELIVER
        elif "寻找" in task_text or "找到" in task_text:
            self.task_type = ShimenState.TASK_FIND
        elif "战斗" in task_text or "教训" in task_text:
            self.task_type = ShimenState.TASK_BATTLE
        else:
            self.task_type = ShimenState.TASK_KILL  # 默认
        
        self.shimen_state = ShimenState.EXECUTE_TASK
        self.reset_timeout()
        return True
    
    def _go_to_npc(self) -> bool:
        """前往NPC处"""
        # 前往师傅处领任务
        # 根据师傅位置寻路
        
        logger.info(f"[师门] 前往 {self.master_map} 找师傅")
        
        # 使用飞行或寻路
        # TODO: 实现具体的寻路逻辑
        
        # 假设已到达
        self.shimen_state = ShimenState.TALK_TO_MASTER
        return True
    
    def _talk_to_master(self) -> bool:
        """与师傅对话"""
        # 找到师傅NPC
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "师傅NPC特征.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            # 点击师傅
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[师门] 点击师傅")
            
            # 等待对话框
            time.sleep(1)
            
            # 检测对话框
            if self._check_dialog():
                self.shimen_state = ShimenState.RECEIVE_TASK
                return True
        else:
            # 未找到师傅，小范围移动搜索
            logger.debug("[师门] 未找到师傅NPC")
            self.unify.相对移动(50, 0)
            time.sleep(0.5)
        
        return True
    
    def _receive_task(self) -> bool:
        """领取任务"""
        # 识别对话框内容
        self.unify.u.UseDict(6)  # 对话字库
        
        dialog_text = self.unify.u.Ocr(
            100, 100, 500, 400,
            color="ffff00-202020"
        )
        
        logger.info(f"[师门] 对话内容: {dialog_text}")
        
        # 查找"领取任务"选项
        result = self.unify.u.FindPic(
            100, 100, 500, 400,
            "领取任务选项.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[师门] 领取任务")
        
        time.sleep(0.5)
        
        # 关闭对话框
        self._close_dialog()
        
        # 切换到执行任务状态
        self.shimen_state = ShimenState.EXECUTE_TASK
        self.current_round += 1
        self.reset_timeout()
        
        logger.info(f"[师门] 第 {self.current_round}/{self.max_rounds} 轮")
        return True
    
    def _execute_task(self) -> bool:
        """执行任务"""
        if self.task_type == ShimenState.TASK_KILL:
            return self._execute_kill_task()
        elif self.task_type == ShimenState.TASK_DELIVER:
            return self._execute_deliver_task()
        elif self.task_type == ShimenState.TASK_FIND:
            return self._execute_find_task()
        elif self.task_type == ShimenState.TASK_BATTLE:
            return self._execute_battle_task()
        
        # 默认回去交任务
        self.shimen_state = ShimenState.RETURN_TO_MASTER
        return True
    
    def _execute_kill_task(self) -> bool:
        """执行击杀任务"""
        logger.info("[师门] 执行击杀任务")
        
        # 读取任务目标
        # TODO: 实现具体的杀怪逻辑
        
        # 模拟杀怪
        time.sleep(2)
        
        # 检测战斗结束
        if self._check_battle_end():
            self.shimen_state = ShimenState.RETURN_TO_MASTER
        
        return True
    
    def _execute_deliver_task(self) -> bool:
        """执行送货任务"""
        logger.info("[师门] 执行送货任务")
        
        # TODO: 寻路到目标NPC
        # TODO: 对话交付物品
        
        time.sleep(2)
        
        self.shimen_state = ShimenState.RETURN_TO_MASTER
        return True
    
    def _execute_find_task(self) -> bool:
        """执行寻人任务"""
        logger.info("[师门] 执行寻人任务")
        
        # TODO: 寻路到目标位置
        # TODO: 点击目标NPC
        
        time.sleep(2)
        
        self.shimen_state = ShimenState.RETURN_TO_MASTER
        return True
    
    def _execute_battle_task(self) -> bool:
        """执行战斗任务"""
        logger.info("[师门] 执行战斗任务")
        
        # TODO: 寻路到战斗地点
        # TODO: 触发战斗
        # TODO: 等待战斗结束
        
        time.sleep(3)
        
        if self._check_battle_end():
            self.shimen_state = ShimenState.RETURN_TO_MASTER
        
        return True
    
    def _return_to_master(self) -> bool:
        """返回师傅处"""
        logger.info("[师门] 返回师傅处交任务")
        
        # 飞行或寻路回师傅处
        # TODO: 实现具体的寻路逻辑
        
        time.sleep(1)
        
        self.shimen_state = ShimenState.TALK_TO_MASTER
        return True
    
    def _complete_task(self) -> bool:
        """完成任务"""
        # 与师傅对话交任务
        if self._check_dialog():
            # 查找"完成任务"选项
            result = self.unify.u.FindPic(
                100, 100, 500, 400,
                "完成选项.bmp", "202020", 0.8, 0
            )
            
            if result[0] == 0:
                self.unify.鼠标移动(result[1], result[2])
                self.unify.左键点击()
                logger.info("[师门] 完成任务")
        
        self._close_dialog()
        
        # 检查是否完成全部师门
        if self.current_round >= self.max_rounds:
            logger.info("[师门] 全部师门完成！")
            return False
        
        # 继续下一轮
        self.shimen_state = ShimenState.CHECK_TASK
        self.reset_timeout()
        return True
    
    def _check_dialog(self) -> bool:
        """检查是否存在对话框"""
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "对话框特征.bmp", "202020", 0.8, 0
        )
        return result[0] == 0
    
    def _close_dialog(self):
        """关闭对话框"""
        # ESC键关闭
        self.unify.按单个键("esc")
        time.sleep(0.3)
    
    def _check_battle_end(self) -> bool:
        """检查战斗是否结束"""
        # 检查是否在战斗中
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "战斗结束特征.bmp", "202020", 0.8, 0
        )
        
        return result[0] == 0
    
    def on_cleanup(self):
        """清理"""
        self._close_dialog()
        logger.info(f"[师门] 师门任务结束，完成 {self.current_round} 轮")
