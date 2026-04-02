# src/tasks/bangpai.py
"""
问道帮派任务模块 - 帮派状态机

参考梦幻开发的押镖任务设计：
1. 节点式寻路（地标识别）
2. 长距离移动处理
3. 随机战斗拦截
"""
import time
import logging
from .base import BaseTask, TaskState

logger = logging.getLogger(__name__)


class BangpaiState:
    """帮派任务子状态"""
    # 主流程
    CHECK_BANGPAI = "check_bangpai"              # 检查帮派状态
    ENTER_BANGPAI = "enter_bangpai"              # 进入帮派
    FIND_NPC = "find_npc"                        # 寻找帮派NPC
    TALK_TO_NPC = "talk_to_npc"                  # 与NPC对话
    SELECT_TASK = "select_task"                  # 选择任务类型
    EXECUTE_TASK = "execute_task"                # 执行任务
    
    # 帮派任务类型
    TASK_CONSTRUCTION = "construction"           # 建设类
    TASK_SABOTAGE = "sabotage"                   # 破坏类
    TASK_DELIVER = "deliver"                     # 送货类
    TASK_FIGHT = "fight"                         # 战斗类
    TASK_SCOUT = "scout"                         # 侦察类


class BangpaiTask(BaseTask):
    """
    问道帮派任务
    
    帮派任务类型：
    1. 建设：帮派设施建设
    2. 破坏：破坏其他帮派设施
    3. 送货：帮派货运
    4. 战斗：帮派PK
    5. 侦察：探查敌情
    
    参考梦幻押镖任务设计：
    - 节点式寻路
    - 地标识别
    - 随机战斗处理
    """
    
    task_name = "bangpai"
    
    def __init__(self, unify, config: dict):
        super().__init__(unify, config)
        
        # 帮派配置
        self.max_tasks = config.get("max_tasks", 20)  # 最大任务数
        self.current_task = 0
        
        # 帮派位置
        self.bangpai_location = config.get("bangpai_location", "帮派总管")
        
        # 地标配置（用于节点式寻路）
        self.landmarks = config.get("landmarks", [
            {"name": "帮派管理员", "map": "帮派地图"},
        ])
        
        # 当前任务信息
        self.task_type = None
        self.task_target = None
        
        # 初始化状态
        self.bangpai_state = BangpaiState.CHECK_BANGPAI
    
    def on_init(self) -> bool:
        """初始化"""
        logger.info(f"[帮派] 开始帮派任务，目标 {self.max_tasks} 个")
        
        self.timeout_seconds = 1800
        
        self._close_all_panels()
        
        return True
    
    def execute(self) -> bool:
        """执行帮派任务"""
        time.sleep(0.2)
        
        # 状态分发
        if self.bangpai_state == BangpaiState.CHECK_BANGPAI:
            return self._check_bangpai_status()
        
        elif self.bangpai_state == BangpaiState.ENTER_BANGPAI:
            return self._enter_bangpai()
        
        elif self.bangpai_state == BangpaiState.FIND_NPC:
            return self._find_npc()
        
        elif self.bangpai_state == BangpaiState.TALK_TO_NPC:
            return self._talk_to_npc()
        
        elif self.bangpai_state == BangpaiState.SELECT_TASK:
            return self._select_task_type()
        
        elif self.bangpai_state == BangpaiState.EXECUTE_TASK:
            return self._execute_task()
        
        return True
    
    def _check_bangpai_status(self) -> bool:
        """检查帮派状态"""
        # 检查是否在帮派地图
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "帮派地图特征.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            logger.info("[帮派] 当前在帮派地图")
            self.bangpai_state = BangpaiState.FIND_NPC
            return True
        else:
            # 需要进入帮派
            logger.info("[帮派] 需要进入帮派")
            self.bangpai_state = BangpaiState.ENTER_BANGPAI
            return True
    
    def _enter_bangpai(self) -> bool:
        """进入帮派"""
        # 打开地图
        self.unify.按单个键("tab")
        time.sleep(0.5)
        
        # 查找帮派入口
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "帮派入口.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[帮派] 点击帮派入口")
        
        time.sleep(2)
        
        self.bangpai_state = BangpaiState.FIND_NPC
        return True
    
    def _find_npc(self) -> bool:
        """寻找帮派NPC"""
        # 帮派管理员位置
        # TODO: 根据帮派设施位置调整
        
        logger.info("[帮派] 寻找帮派NPC")
        
        # 节点式寻路 - 使用地标识别
        target_found = False
        for landmark in self.landmarks:
            result = self.unify.u.FindPic(
                0, 0, 800, 600,
                f"{landmark['name']}.bmp", "202020", 0.8, 0
            )
            
            if result[0] == 0:
                self.unify.鼠标移动(result[1], result[2])
                self.unify.左键点击()
                target_found = True
                logger.info(f"[帮派] 找到 {landmark['name']}")
                break
        
        if not target_found:
            logger.debug("[帮派] 未找到目标地标，移动搜索")
            self.unify.相对移动(100, 0)
            time.sleep(1)
            return True
        
        time.sleep(1)
        self.bangpai_state = BangpaiState.TALK_TO_NPC
        return True
    
    def _talk_to_npc(self) -> bool:
        """与NPC对话"""
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "帮派NPC特征.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[帮派] 与NPC对话")
            
            time.sleep(1)
            
            if self._check_dialog():
                self.bangpai_state = BangpaiState.SELECT_TASK
                return True
        else:
            self.unify.相对移动(50, 50)
            time.sleep(0.5)
        
        return True
    
    def _select_task_type(self) -> bool:
        """选择任务类型"""
        # 识别帮派任务面板
        self.unify.u.UseDict(8)  # 任务字库
        
        dialog_text = self.unify.u.Ocr(
            100, 100, 500, 400,
            color="ffff00-202020"
        )
        
        logger.info(f"[帮派] 任务面板内容: {dialog_text}")
        
        # 根据任务内容识别类型
        if "建设" in dialog_text:
            self.task_type = BangpaiState.TASK_CONSTRUCTION
        elif "破坏" in dialog_text:
            self.task_type = BangpaiState.TASK_SABOTAGE
        elif "送货" in dialog_text or "货运" in dialog_text:
            self.task_type = BangpaiState.TASK_DELIVER
        elif "战斗" in dialog_text or "挑战" in dialog_text:
            self.task_type = BangpaiState.TASK_FIGHT
        elif "侦察" in dialog_text or "探查" in dialog_text:
            self.task_type = BangpaiState.TASK_SCOUT
        else:
            # 默认选择建设任务
            result = self.unify.u.FindPic(
                100, 100, 500, 400,
                "建设任务.bmp", "202020", 0.8, 0
            )
            
            if result[0] == 0:
                self.unify.鼠标移动(result[1], result[2])
                self.unify.左键点击()
                self.task_type = BangpaiState.TASK_CONSTRUCTION
        
        logger.info(f"[帮派] 选择任务类型: {self.task_type}")
        
        time.sleep(0.5)
        self._close_dialog()
        
        self.bangpai_state = BangpaiState.EXECUTE_TASK
        self.current_task += 1
        self.reset_timeout()
        
        return True
    
    def _execute_task(self) -> bool:
        """执行任务"""
        logger.info(f"[帮派] 执行 {self.task_type} 任务，第 {self.current_task}/{self.max_tasks} 个")
        
        # 根据任务类型执行
        if self.task_type == BangpaiState.TASK_CONSTRUCTION:
            self._execute_construction()
        elif self.task_type == BangpaiState.TASK_SABOTAGE:
            self._execute_sabotage()
        elif self.task_type == BangpaiState.TASK_DELIVER:
            self._execute_deliver()
        elif self.task_type == BangpaiState.TASK_FIGHT:
            self._execute_fight()
        elif self.task_type == BangpaiState.TASK_SCOUT:
            self._execute_scout()
        
        # 完成任务后检查是否继续
        if self.current_task >= self.max_tasks:
            logger.info("[帮派] 帮派任务全部完成")
            return False
        
        # 继续下一个任务
        self.bangpai_state = BangpaiState.FIND_NPC
        self.reset_timeout()
        return True
    
    def _execute_construction(self):
        """执行建设任务"""
        logger.info("[帮派] 执行建设任务")
        # TODO: 寻路到建设地点，使用设施图标识别
        # TODO: 进行建设操作
        time.sleep(3)
    
    def _execute_sabotage(self):
        """执行破坏任务"""
        logger.info("[帮派] 执行破坏任务")
        # TODO: 前往敌对帮派
        # TODO: 找到目标设施
        # TODO: 进行破坏
        time.sleep(3)
    
    def _execute_deliver(self):
        """执行送货任务"""
        logger.info("[帮派] 执行送货任务")
        # TODO: 读取送货目标
        # TODO: 寻路到目标位置
        # TODO: 交付货物
        time.sleep(3)
    
    def _execute_fight(self):
        """执行战斗任务"""
        logger.info("[帮派] 执行战斗任务")
        # TODO: 寻路到战斗地点
        # TODO: 触发战斗
        # TODO: 等待战斗结束
        time.sleep(5)
    
    def _execute_scout(self):
        """执行侦察任务"""
        logger.info("[帮派] 执行侦察任务")
        # TODO: 前往侦察地点
        # TODO: 使用侦察技能
        # TODO: 报告侦察结果
        time.sleep(3)
    
    def _check_dialog(self) -> bool:
        """检查是否存在对话框"""
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "对话框特征.bmp", "202020", 0.8, 0
        )
        return result[0] == 0
    
    def _close_dialog(self):
        """关闭对话框"""
        self.unify.按单个键("esc")
        time.sleep(0.3)
    
    def _close_all_panels(self):
        """关闭所有面板"""
        for _ in range(3):
            self._close_dialog()
            time.sleep(0.2)
    
    def _check_battle(self) -> bool:
        """检查是否在战斗中"""
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "战斗特征.bmp", "202020", 0.8, 0
        )
        return result[0] == 0
    
    def _check_random_battle(self) -> bool:
        """检查是否遭遇随机战斗"""
        # 参考梦幻押镖的随机战斗拦截
        if self._check_battle():
            logger.info("[帮派] 遭遇随机战斗")
            # 执行自动战斗
            self._auto_battle()
            return True
        return False
    
    def _auto_battle(self):
        """自动战斗处理"""
        # 等待战斗开始
        time.sleep(1)
        
        # 点击自动按钮
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "自动战斗.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[帮派] 点击自动战斗")
        
        # 等待战斗结束
        while self._check_battle():
            time.sleep(2)
        
        logger.info("[帮派] 战斗结束")
    
    def on_cleanup(self):
        """清理"""
        self._close_all_panels()
        logger.info(f"[帮派] 帮派任务结束，完成 {self.current_task} 个任务")
