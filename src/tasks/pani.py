# src/tasks/pani.py
"""
问道叛逆任务模块 - 完整闭环实现

【流程】
领取任务 → 寻路 → 点击NPC → 对话 → 战斗 → 返回交任务 → 循环

【整合模块】
- Pathfinder: 自动寻路
- 图像识别: NPC检测、战斗检测
- OCR: 对话识别
"""

import time
import logging
from .base import BaseTask, TaskState
from .autopath import Pathfinder

logger = logging.getLogger(__name__)


class PaniState:
    """叛逆任务状态"""
    CHECK_TASK = "check_task"           # 检查任务状态
    GO_TO_NPC = "go_to_npc"             # 前往叛逆NPC
    TALK_TO_NPC = "talk_to_npc"         # 与NPC对话
    RECEIVE_TASK = "receive_task"       # 领取任务
    EXECUTE_TASK = "execute_task"       # 执行任务
    RETURN_TO_NPC = "return_to_npc"     # 返回NPC
    COMPLETE_TASK = "complete_task"     # 完成任务

    # 任务类型
    TASK_KILL = "task_kill"             # 杀怪类
    TASK_DELIVER = "task_deliver"       # 送货类
    TASK_COLLECT = "task_collect"       # 采集类


class PaniTask(BaseTask):
    """
    叛逆任务 - 完整闭环实现
    
    使用 Pathfinder 实现自动寻路
    """
    
    task_name = "pani"
    
    # NPC配置
    NPC_NAME = "叛逆"
    NPC_POS = {"x": 400, "y": 300}       # 默认位置，需根据实际调整
    
    def __init__(self, unify, config: dict):
        super().__init__(unify, config)
        
        # 配置参数
        self.max_rounds = config.get("max_rounds", 10)
        self.current_round = 0
        
        # NPC配置
        self.npc_map = config.get("npc_map", "")
        self.npc_x = config.get("npc_x", self.NPC_POS["x"])
        self.npc_y = config.get("npc_y", self.NPC_POS["y"])
        
        # 初始化寻路系统
        self.pathfinder = Pathfinder(unify)
        
        # 任务数据
        self.task_type = None
        self.task_target = None           # 任务目标坐标/位置
        self.task_map = None              # 任务目标所在地图
        
        # 状态机
        self.pani_state = PaniState.CHECK_TASK
        
        # 战斗相关
        self.in_battle = False
        self.battle_timeout = 120         # 战斗超时（秒）
        
        logger.info(f"[叛逆] 初始化: 目标{self.max_rounds}轮, NPC=({self.npc_x},{self.npc_y})")
    
    def on_init(self) -> bool:
        """初始化"""
        logger.info(f"[叛逆] ============== 开始叛逆任务 ==============")
        logger.info(f"[叛逆] 目标: {self.max_rounds}轮")
        self.timeout_seconds = self.config.get("timeout", 1800)
        self.reset_timeout()
        return True
    
    def execute(self) -> bool:
        """状态机主循环"""
        time.sleep(0.1)
        
        if self.pani_state == PaniState.CHECK_TASK:
            return self._step_check_task()
        elif self.pani_state == PaniState.GO_TO_NPC:
            return self._step_go_to_npc()
        elif self.pani_state == PaniState.TALK_TO_NPC:
            return self._step_talk_to_npc()
        elif self.pani_state == PaniState.RECEIVE_TASK:
            return self._step_receive_task()
        elif self.pani_state == PaniState.EXECUTE_TASK:
            return self._step_execute_task()
        elif self.pani_state == PaniState.RETURN_TO_NPC:
            return self._step_return_to_npc()
        elif self.pani_state == PaniState.COMPLETE_TASK:
            return self._step_complete_task()
        
        return True
    
    # ==================== 步骤实现 ====================
    
    def _step_check_task(self) -> bool:
        """【1】检查任务状态"""
        logger.info("[叛逆] 【状态1】检查叛逆任务")
        
        # 识别当前任务（OCR任务栏）
        task_text = self._check_task_bar()
        
        if "叛逆" in task_text or "叛逆" in task_text:
            logger.info("[叛逆] 检测到叛逆任务！")
            # 解析任务目标
            self._parse_task(task_text)
            self.pani_state = PaniState.EXECUTE_TASK
        else:
            logger.info("[叛逆] 没有叛逆任务，前往领取")
            self.pani_state = PaniState.GO_TO_NPC
        
        self.reset_timeout()
        return True
    
    def _step_go_to_npc(self) -> bool:
        """【2】前往叛逆NPC"""
        logger.info("[叛逆] 【状态2】前往叛逆NPC")
        logger.info(f"[叛逆] 目标: ({self.npc_x}, {self.npc_y})")
        
        # 使用 Pathfinder 寻路
        arrived = self.pathfinder.move_to(self.npc_x, self.npc_y)
        
        if arrived:
            logger.info("[叛逆] 到达NPC处")
            self.pani_state = PaniState.TALK_TO_NPC
        else:
            logger.warning("[叛逆] 寻路失败，重试")
        
        self.reset_timeout()
        return True
    
    def _step_talk_to_npc(self) -> bool:
        """【3】与NPC对话"""
        logger.info("[叛逆] 【状态3】与NPC对话")
        
        # 点击NPC
        self.unify.鼠标移动(self.npc_x, self.npc_y)
        self.unify.左键点击()
        time.sleep(0.5)
        
        # 等待对话框
        if self._wait_for_dialog(5):
            logger.info("[叛逆] 对话框已出现")
            self.pani_state = PaniState.RECEIVE_TASK
        else:
            logger.warning("[叛逆] 未检测到对话框，尝试再次点击")
            self.unify.左键点击()
            time.sleep(0.5)
        
        self.reset_timeout()
        return True
    
    def _step_receive_task(self) -> bool:
        """【4】领取任务"""
        logger.info("[叛逆] 【状态4】领取任务")
        
        # 识别对话框内容
        dialog_text = self._read_dialog()
        logger.info(f"[叛逆] 对话内容: {dialog_text}")
        
        # 查找并点击"领取"选项
        if self._click_option("领") or self._click_option("接受"):
            logger.info("[叛逆] 领取成功")
            
            self.current_round += 1
            logger.info(f"[叛逆] ====== 第 {self.current_round}/{self.max_rounds} 轮 ======")
            
            # 关闭对话框
            self.unify.按键(27)  # ESC
            time.sleep(0.3)
            
            # 切换到执行任务
            self.pani_state = PaniState.EXECUTE_TASK
        else:
            # 检查是否没有任务了
            if "没有" in dialog_text or "完成" in dialog_text:
                logger.info("[叛逆] 今日叛逆任务已完成")
                return False  # 结束任务
        
        self.reset_timeout()
        return True
    
    def _step_execute_task(self) -> bool:
        """【5】执行任务"""
        logger.info("[叛逆] 【状态5】执行任务")
        
        if self.task_type == PaniState.TASK_KILL:
            return self._execute_kill()
        elif self.task_type == PaniState.TASK_DELIVER:
            return self._execute_deliver()
        elif self.task_type == PaniState.TASK_COLLECT:
            return self._execute_collect()
        else:
            # 默认杀怪流程
            return self._execute_kill()
    
    def _execute_kill(self) -> bool:
        """杀怪子流程"""
        logger.info("[叛逆-杀怪] 开始杀怪")
        
        if not self.task_target:
            logger.warning("[叛逆-杀怪] 未获取到目标位置")
            return False
        
        # 寻路到怪物位置
        target_x, target_y = self.task_target
        logger.info(f"[叛逆-杀怪] 寻路到: ({target_x}, {target_y})")
        
        arrived = self.pathfinder.move_to(target_x, target_y)
        if not arrived:
            logger.warning("[叛逆-杀怪] 寻路失败")
        
        # 等待一下确保到位
        time.sleep(0.5)
        
        # 点击怪物触发战斗
        self.unify.左键点击()
        time.sleep(1)
        
        # 等待战斗结束
        if self._wait_for_battle_end(self.battle_timeout):
            logger.info("[叛逆-杀怪] 战斗胜利！")
            self.unify.中延时()
        else:
            logger.warning("[叛逆-杀怪] 战斗超时")
        
        # 切换到返回NPC
        self.pani_state = PaniState.RETURN_TO_NPC
        self.reset_timeout()
        return True
    
    def _execute_deliver(self) -> bool:
        """送货子流程"""
        logger.info("[叛逆-送货] 开始送货")
        
        if not self.task_target:
            logger.warning("[叛逆-送货] 未获取到目标位置")
            return False
        
        target_x, target_y = self.task_target
        logger.info(f"[叛逆-送货] 寻路到: ({target_x}, {target_y})")
        
        # 寻路
        self.pathfinder.move_to(target_x, target_y)
        time.sleep(0.5)
        
        # 与收货NPC对话
        self.unify.左键点击()
        time.sleep(0.5)
        
        if self._wait_for_dialog(5):
            # 选择交货选项
            self._click_option("交") or self._click_option("给")
            time.sleep(0.3)
        
        self.unify.按键(27)  # ESC关闭
        logger.info("[叛逆-送货] 送货完成")
        
        self.pani_state = PaniState.RETURN_TO_NPC
        self.reset_timeout()
        return True
    
    def _execute_collect(self) -> bool:
        """采集子流程"""
        logger.info("[叛逆-采集] 开始采集")
        
        if not self.task_target:
            logger.warning("[叛逆-采集] 未获取到采集点位置")
            return False
        
        target_x, target_y = self.task_target
        logger.info(f"[叛逆-采集] 寻路到: ({target_x}, {target_y})")
        
        # 寻路
        self.pathfinder.move_to(target_x, target_y)
        time.sleep(0.5)
        
        # 执行采集（多次点击）
        for i in range(5):
            self.unify.左键点击()
            time.sleep(0.5)
            
            # 检查是否采集完成（对话框消失）
            if not self._check_dialog_visible():
                logger.info(f"[叛逆-采集] 采集完成！")
                break
        
        self.pani_state = PaniState.RETURN_TO_NPC
        self.reset_timeout()
        return True
    
    def _step_return_to_npc(self) -> bool:
        """【6】返回NPC"""
        logger.info("[叛逆] 【状态6】返回NPC")
        
        # 使用 Pathfinder 返回
        arrived = self.pathfinder.move_to(self.npc_x, self.npc_y)
        
        if arrived:
            logger.info("[叛逆] 到达NPC处")
            self.pani_state = PaniState.COMPLETE_TASK
        else:
            logger.warning("[叛逆] 返回失败")
        
        self.reset_timeout()
        return True
    
    def _step_complete_task(self) -> bool:
        """【7】完成任务"""
        logger.info("[叛逆] 【状态7】完成任务")
        
        # 点击NPC
        self.unify.左键点击()
        time.sleep(0.5)
        
        if self._wait_for_dialog(5):
            # 选择完成任务选项
            if self._click_option("完成") or self._click_option("交"):
                logger.info("[叛逆] 任务完成！")
                self.unify.按键(27)
                time.sleep(0.3)
            else:
                self.unify.按键(27)
        
        # 检查是否全部完成
        if self.current_round >= self.max_rounds:
            logger.info(f"[叛逆] ============== 全部完成！ ==============")
            logger.info(f"[叛逆] 共完成 {self.current_round} 轮")
            return False
        
        # 继续下一轮
        logger.info(f"[叛逆] 剩余 {self.max_rounds - self.current_round} 轮")
        self.pani_state = PaniState.CHECK_TASK
        self.reset_timeout()
        return True
    
    # ==================== 辅助方法 ====================
    
    def _check_task_bar(self) -> str:
        """
        检查任务栏是否有叛逆任务
        
        Returns:
            任务栏文字内容
        """
        try:
            # 问道任务栏通常在屏幕右侧
            # 需要根据实际调整识别区域
            text = self.unify.文字识别(600, 200, 800, 600, "ffffff-050505")
            logger.debug(f"[叛逆] 任务栏识别: {text}")
            return text
        except Exception as e:
            logger.warning(f"[叛逆] 任务栏识别失败: {e}")
            return ""
    
    def _parse_task(self, task_text: str):
        """
        解析任务内容
        
        从任务栏文字中提取：
        - 任务类型（杀怪/送货/采集）
        - 目标位置
        """
        # 简化解析，实际需要更复杂的OCR处理
        
        if "杀" in task_text:
            self.task_type = PaniState.TASK_KILL
        elif "送" in task_text or "货" in task_text:
            self.task_type = PaniState.TASK_DELIVER
        elif "采" in task_text:
            self.task_type = PaniState.TASK_COLLECT
        else:
            self.task_type = PaniState.TASK_KILL  # 默认杀怪
        
        logger.info(f"[叛逆] 任务类型: {self.task_type}")
        
        # 尝试解析坐标
        # 格式可能是 "叛逆 杀怪 30,50" 或 "坐标(30,50)"
        import re
        match = re.search(r'(\d+)[,\s]+(\d+)', task_text)
        if match:
            self.task_target = (int(match.group(1)), int(match.group(2)))
            logger.info(f"[叛逆] 目标坐标: {self.task_target}")
        else:
            # 默认目标位置（需要根据实际调整）
            self.task_target = (self.npc_x + 100, self.npc_y)
    
    def _read_dialog(self) -> str:
        """
        读取对话框内容
        
        Returns:
            对话框文字
        """
        try:
            # 对话框区域（需要根据实际调整）
            text = self.unify.文字识别(200, 400, 600, 550, "ffffff-050505")
            return text
        except Exception as e:
            logger.warning(f"[叛逆] 对话框识别失败: {e}")
            return ""
    
    def _check_dialog_visible(self) -> bool:
        """检查对话框是否可见"""
        try:
            # 检测对话框边框或特定文字
            text = self.unify.文字识别(200, 380, 600, 420, "ffffff-050505")
            return len(text) > 0
        except:
            return False
    
    def _wait_for_dialog(self, timeout: int = 10) -> bool:
        """
        等待对话框出现
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            True if dialog appeared
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._check_dialog_visible():
                return True
            time.sleep(0.2)
        return False
    
    def _click_option(self, keyword: str) -> bool:
        """
        点击包含关键字的选项
        
        Args:
            keyword: 选项关键字
        
        Returns:
            True if clicked
        """
        try:
            # 读取对话框所有选项
            # 实际需要更复杂的图像识别来定位选项
            # 这里简化处理，直接点击固定位置
            
            # 常见选项位置（需要根据实际调整）
            option_y_positions = [470, 490, 510, 530]
            
            for y in option_y_positions:
                # 识别这行的文字
                text = self.unify.文字识别(250, y, 400, y + 20, "ffffff-050505")
                
                if keyword in text:
                    # 点击该选项
                    self.unify.鼠标移动(350, y + 10)
                    self.unify.左键点击()
                    logger.info(f"[叛逆] 点击选项: {text}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"[叛逆] 点击选项失败: {e}")
            return False
    
    def _wait_for_battle_end(self, timeout: int = 120) -> bool:
        """
        等待战斗结束
        
        Args:
            timeout: 超时时间（秒）
        
        Returns:
            True if battle ended successfully
        """
        start_time = time.time()
        last_action = time.time()
        
        while time.time() - start_time < timeout:
            # 检测战斗是否结束
            # 方法1: 检查战斗相关UI
            # 方法2: 检查血条/蓝条变化
            # 方法3: OCR识别战斗结果
            
            current_hp = self.unify.获取血量()
            
            if current_hp > 0:
                # 血量正常，检查是否有"胜利"/"失败"字样
                try:
                    text = self.unify.文字识别(300, 350, 500, 400, "ffff00-050505")
                    if "胜利" in text or "失败" in text:
                        logger.info(f"[叛逆] 战斗结果: {text}")
                        return "胜利" in text
                except:
                    pass
                
                # 检查血量是否长时间不变（可能卡住）
                if time.time() - last_action > 30:
                    logger.info("[叛逆] 战斗进行中...")
                    last_action = time.time()
            else:
                # 血量为0，可能死亡
                logger.warning("[叛逆] 角色死亡！")
                return False
            
            time.sleep(0.5)
        
        logger.warning("[叛逆] 战斗超时")
        return False
    
    def _find_npc(self) -> bool:
        """
        寻找NPC
        
        Returns:
            True if NPC found
        """
        try:
            # 使用图像识别找NPC
            # result = self.unify.找图(0, 0, 800, 600, "叛逆NPC.bmp", sim=0.8)
            # if result[0] == 0:
            #     x, y = result[1], result[2]
            #     self.unify.鼠标移动(x, y)
            #     return True
            
            # 简化：直接移动到预设位置
            self.unify.鼠标移动(self.npc_x, self.npc_y)
            return True
            
        except Exception as e:
            logger.warning(f"[叛逆] 寻找NPC失败: {e}")
            return False
    
    def _find_monster(self) -> bool:
        """
        寻找怪物
        
        Returns:
            True if monster found
        """
        try:
            # 简化：点击屏幕中心
            self.unify.鼠标移动(400, 300)
            self.unify.左键点击()
            return True
        except:
            return False
    
    def on_cleanup(self):
        """清理"""
        logger.info(f"[叛逆] ============== 任务结束 ==============")
        logger.info(f"[叛逆] 完成轮数: {self.current_round}/{self.max_rounds}")
