# src/tasks/fuben.py
"""
问道副本任务模块 - 副本状态机

参考梦幻开发的打图任务和押镖任务设计：
1. 阶段化流程管理
2. BOSS识别与处理
3. 战斗流程封装
"""
import time
import logging
from .base import BaseTask, TaskState

logger = logging.getLogger(__name__)


class FubenState:
    """副本任务子状态"""
    # 副本流程
    CHECK_FUBEN = "check_fuben"                  # 检查副本状态
    ENTER_FUBEN = "enter_fuben"                  # 进入副本
    SELECT_FUBEN = "select_fuben"                # 选择副本类型
    WAIT_FUBEN = "wait_fuben"                    # 等待副本加载
    EXECUTE_STAGE = "execute_stage"              # 执行副本阶段
    BATTLE_BOSS = "battle_boss"                  # BOSS战斗
    COMPLETE_FUBEN = "complete_fuben"           # 完成副本
    
    # 副本类型
    FUBEN_TIANZHU = "tianzhu"                   # 天珠副本
    FUBEN_XUANMEN = "xuanmen"                   # 玄门副本
    FUBEN_XIANYUAN = "xianyuan"                 # 轩辕副本
    FUBEN_YOULONG = "youlong"                   # 幽冥副本


class FubenTask(BaseTask):
    """
    问道副本任务
    
    副本流程：
    1. 检查并进入副本
    2. 按阶段执行副本内容
    3. BOSS战处理
    4. 领取奖励
    
    参考梦幻打图设计：
    - 状态机流程
    - BOSS识别
    - 战斗封装
    """
    
    task_name = "fuben"
    
    def __init__(self, unify, config: dict):
        super().__init__(unify, config)
        
        # 副本配置
        self.fuben_type = config.get("fuben_type", FubenState.FUBEN_TIANZHU)
        self.auto_retry = config.get("auto_retry", 3)
        
        # 阶段管理
        self.current_stage = 0
        self.max_stage = config.get("max_stage", 5)
        
        # BOSS识别配置
        self.boss_positions = config.get("boss_positions", [])
        
        # 初始化状态
        self.fuben_state = FubenState.CHECK_FUBEN
        self.stage_state = None
    
    def on_init(self) -> bool:
        """初始化"""
        logger.info(f"[副本] 开始 {self.fuben_type} 副本")
        
        self.timeout_seconds = 3600  # 1小时超时
        
        self._close_all_panels()
        
        return True
    
    def execute(self) -> bool:
        """执行副本任务"""
        time.sleep(0.2)
        
        # 随机战斗检测（参考梦幻押镖设计）
        if self._check_random_battle():
            return True
        
        # 状态分发
        if self.fuben_state == FubenState.CHECK_FUBEN:
            return self._check_fuben_status()
        
        elif self.fuben_state == FubenState.ENTER_FUBEN:
            return self._enter_fuben()
        
        elif self.fuben_state == FubenState.SELECT_FUBEN:
            return self._select_fuben_type()
        
        elif self.fuben_state == FubenState.WAIT_FUBEN:
            return self._wait_fuben_load()
        
        elif self.fuben_state == FubenState.EXECUTE_STAGE:
            return self._execute_stage()
        
        elif self.fuben_state == FubenState.BATTLE_BOSS:
            return self._battle_boss()
        
        elif self.fuben_state == FubenState.COMPLETE_FUBEN:
            return self._complete_fuben()
        
        return True
    
    def _check_fuben_status(self) -> bool:
        """检查副本状态"""
        # 检查是否在副本中
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "副本地图特征.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            logger.info("[副本] 当前在副本中")
            self.fuben_state = FubenState.EXECUTE_STAGE
            return True
        else:
            # 需要进入副本
            logger.info("[副本] 需要进入副本")
            self.fuben_state = FubenState.ENTER_FUBEN
            return True
    
    def _enter_fuben(self) -> bool:
        """进入副本"""
        # 打开副本面板
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "副本按钮.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[副本] 点击副本按钮")
            time.sleep(1)
        
        self.fuben_state = FubenState.SELECT_FUBEN
        return True
    
    def _select_fuben_type(self) -> bool:
        """选择副本类型"""
        # 根据配置的副本类型选择
        fuben_images = {
            FubenState.FUBEN_TIANZHU: "天珠副本.bmp",
            FubenState.FUBEN_XUANMEN: "玄门副本.bmp",
            FubenState.FUBEN_XIANYUAN: "轩辕副本.bmp",
            FubenState.FUBEN_YOULONG: "幽冥副本.bmp",
        }
        
        fuben_img = fuben_images.get(self.fuben_type, "天珠副本.bmp")
        
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            fuben_img, "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info(f"[副本] 选择 {self.fuben_type}")
            time.sleep(0.5)
        
        # 点击进入副本
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "进入副本.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[副本] 点击进入")
        
        self.fuben_state = FubenState.WAIT_FUBEN
        self.reset_timeout()
        return True
    
    def _wait_fuben_load(self) -> bool:
        """等待副本加载"""
        # 等待副本加载进度条消失
        for _ in range(30):
            time.sleep(1)
            
            # 检查是否进入副本
            result = self.unify.u.FindPic(
                0, 0, 800, 600,
                "副本地图特征.bmp", "202020", 0.8, 0
            )
            
            if result[0] == 0:
                logger.info("[副本] 副本加载完成")
                self.fuben_state = FubenState.EXECUTE_STAGE
                self.current_stage = 1
                return True
            
            # 检查是否还在loading
            result = self.unify.u.FindPic(
                0, 0, 800, 600,
                "加载中.bmp", "202020", 0.8, 0
            )
            
            if result[0] != 0:
                logger.info("[副本] 加载中...")
        
        logger.warning("[副本] 等待加载超时")
        self.fuben_state = FubenState.EXECUTE_STAGE
        return True
    
    def _execute_stage(self) -> bool:
        """执行副本阶段"""
        logger.info(f"[副本] 执行第 {self.current_stage} 阶段")
        
        # 根据副本类型和阶段执行
        if self.fuben_type == FubenState.FUBEN_TIANZHU:
            return self._execute_tianzhu_stage()
        elif self.fuben_type == FubenState.FUBEN_XUANMEN:
            return self._execute_xuanmen_stage()
        else:
            return self._execute_common_stage()
    
    def _execute_tianzhu_stage(self) -> bool:
        """执行天珠副本阶段"""
        # 天珠副本阶段逻辑
        stage_tasks = {
            1: self._tianzhu_stage1,  # 第一波小怪
            2: self._tianzhu_stage2,  # 第二波小怪
            3: self._tianzhu_stage3,  # BOSS战
        }
        
        stage_handler = stage_tasks.get(self.current_stage, self._tianzhu_stage1)
        
        if stage_handler():
            # 阶段完成，检查是否还有下一阶段
            self.current_stage += 1
            
            if self.current_stage > self.max_stage:
                self.fuben_state = FubenState.COMPLETE_FUBEN
            else:
                self.reset_timeout()
        else:
            # 阶段未完成，继续处理
            pass
        
        return True
    
    def _execute_xuanmen_stage(self) -> bool:
        """执行玄门副本阶段"""
        # 玄门副本阶段逻辑
        # TODO: 根据具体副本设计
        
        time.sleep(2)
        
        # 检查BOSS
        if self._find_boss():
            self.fuben_state = FubenState.BATTLE_BOSS
        
        return True
    
    def _execute_common_stage(self) -> bool:
        """执行通用副本阶段"""
        logger.info(f"[副本] 执行通用阶段")
        
        # 识别并移动到下一区域
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "下一区域.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[副本] 前往下一区域")
            time.sleep(1)
        
        # 检查是否遇到BOSS
        if self._find_boss():
            self.fuben_state = FubenState.BATTLE_BOSS
        
        return True
    
    # ===== 天珠副本阶段处理 =====
    
    def _tianzhu_stage1(self) -> bool:
        """天珠第一阶段：清理小怪"""
        logger.info("[副本] 天珠第一阶段：清理小怪")
        
        # 寻找并击杀小怪
        for _ in range(10):
            if self._find_and_attack_enemy():
                time.sleep(2)
            else:
                break
        
        # 检查是否完成
        return self._check_stage_complete()
    
    def _tianzhu_stage2(self) -> bool:
        """天珠第二阶段：继续清理"""
        logger.info("[副本] 天珠第二阶段：继续清理")
        
        # 移动到下一区域
        self._move_to_next_point()
        time.sleep(1)
        
        # 继续清理
        for _ in range(10):
            if self._find_and_attack_enemy():
                time.sleep(2)
            else:
                break
        
        return self._check_stage_complete()
    
    def _tianzhu_stage3(self) -> bool:
        """天珠第三阶段：BOSS战"""
        logger.info("[副本] 天珠第三阶段：BOSS战")
        
        # 寻找BOSS
        if self._find_boss():
            self.fuben_state = FubenState.BATTLE_BOSS
        else:
            # 没找到BOSS，继续清理
            self._find_and_attack_enemy()
        
        return True
    
    # ===== 战斗处理 =====
    
    def _find_and_attack_enemy(self) -> bool:
        """寻找并攻击敌人"""
        # 查找敌人
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "敌人特征.bmp", "202020", 0.7, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[副本] 发现敌人")
            
            # 等待进入战斗
            time.sleep(1)
            
            if self._check_in_battle():
                self._auto_battle()
            
            return True
        
        # 没找到敌人，尝试移动
        self.unify.相对移动(100, 0)
        time.sleep(0.5)
        
        return False
    
    def _find_boss(self) -> bool:
        """寻找BOSS"""
        # 使用更宽松的匹配度寻找BOSS
        for boss_img in ["BOSS特征.bmp", "天珠BOSS.bmp", "玄门BOSS.bmp"]:
            result = self.unify.u.FindPic(
                0, 0, 800, 600,
                boss_img, "202020", 0.7, 0
            )
            
            if result[0] == 0:
                self.unify.鼠标移动(result[1], result[2])
                self.unify.左键点击()
                logger.info(f"[副本] 发现BOSS: {boss_img}")
                return True
        
        return False
    
    def _battle_boss(self) -> bool:
        """BOSS战斗"""
        logger.info("[副本] BOSS战斗中")
        
        # 检测是否在战斗中
        if not self._check_in_battle():
            logger.info("[副本] BOSS战结束")
            self.fuben_state = FubenState.EXECUTE_STAGE
            return True
        
        # 执行自动战斗
        self._auto_battle()
        
        # 检查BOSS血量
        if self._check_boss_hp_low():
            logger.info("[副本] BOSS血量低")
        
        return True
    
    def _auto_battle(self):
        """自动战斗"""
        # 点击自动按钮
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "自动战斗按钮.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[副本] 开启自动战斗")
        
        # 等待战斗结束
        timeout = 300  # 5分钟超时
        start_time = time.time()
        
        while self._check_in_battle():
            if time.time() - start_time > timeout:
                logger.warning("[副本] 战斗超时")
                break
            time.sleep(2)
        
        logger.info("[副本] 战斗结束")
    
    def _check_in_battle(self) -> bool:
        """检查是否在战斗中"""
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "战斗界面.bmp", "202020", 0.8, 0
        )
        return result[0] == 0
    
    def _check_boss_hp_low(self) -> bool:
        """检查BOSS血量是否低"""
        # TODO: 识别BOSS血条
        return False
    
    def _check_stage_complete(self) -> bool:
        """检查阶段是否完成"""
        # 检查是否有完成提示
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "阶段完成.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            logger.info("[副本] 阶段完成")
            self.unify.按单个键("enter")
            time.sleep(1)
            return True
        
        # 或者通过怪物数量判断
        enemy_count = self._count_enemies()
        return enemy_count == 0
    
    def _count_enemies(self) -> int:
        """统计敌人数量"""
        # TODO: 使用OCR或图像识别统计
        return 0
    
    def _move_to_next_point(self):
        """移动到下一个检查点"""
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "检查点.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[副本] 移动到检查点")
    
    def _complete_fuben(self) -> bool:
        """完成副本"""
        logger.info("[副本] 副本完成")
        
        # 领取奖励
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "领取奖励.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[副本] 领取奖励")
            time.sleep(1)
        
        return False
    
    def _check_random_battle(self) -> bool:
        """检查随机战斗"""
        if self._check_in_battle():
            logger.info("[副本] 遭遇随机战斗")
            self._auto_battle()
            return True
        return False
    
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
    
    def on_cleanup(self):
        """清理"""
        self._close_all_panels()
        logger.info(f"[副本] 副本任务结束")
