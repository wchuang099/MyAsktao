# src/tasks/login.py
"""
问道登录模块 - 登录状态机

参考梦幻开发的自动登录设计：
1. 账号信息读取与封装
2. 界面判定流程
3. 多状态流转
4. 超时重试机制
"""
import time
import logging
from .base import BaseTask, TaskState

logger = logging.getLogger(__name__)


class LoginState:
    """登录子状态"""
    CHECK_ACCOUNT = "check_account"           # 检查账号界面
    INPUT_ACCOUNT = "input_account"          # 输入账号
    INPUT_PASSWORD = "input_password"        # 输入密码
    SELECT_SERVER = "select_server"           # 选择服务器
    SELECT_ROLE = "select_role"              # 选择角色
    CONFIRM_LOGIN = "confirm_login"          # 确认登录
    WAIT_ENTER_GAME = "wait_enter_game"      # 等待进入游戏
    CHECK_IN_GAME = "check_in_game"           # 检查是否在游戏中
    LOGIN_SUCCESS = "login_success"           # 登录成功
    LOGIN_FAILED = "login_failed"            # 登录失败


class LoginTask(BaseTask):
    """
    问道登录任务
    
    状态机流程：
    检查账号界面 → 输入账号 → 输入密码 → 选择服务器 → 选择角色 → 确认登录 → 等待进入 → 检查成功
    """
    
    task_name = "login"
    
    def __init__(self, unify, config: dict):
        super().__init__(unify, config)
        
        # 登录信息
        self.account = config.get("account", "")
        self.password = config.get("password", "")
        self.server = config.get("server", "")
        self.role_index = config.get("role_index", 0)
        
        # 界面判定参数
        self.max_retry = config.get("max_retry", 3)
        self.retry_count = 0
        
        # 初始化子状态机
        self.login_state = LoginState.CHECK_ACCOUNT
    
    def on_init(self) -> bool:
        """初始化检查"""
        logger.info(f"[登录] 账号: {self.account}, 服务器: {self.server}")
        
        # 检查是否已在游戏中
        if self._check_in_game():
            logger.info("[登录] 已在游戏中，跳过登录")
            self.set_state(TaskState.COMPLETED)
            return False
        
        return True
    
    def execute(self) -> bool:
        """
        执行登录状态机
        
        Returns:
            True if login completed
        """
        # 延时防止CPU占用
        time.sleep(0.3)
        
        # 状态分发
        if self.login_state == LoginState.CHECK_ACCOUNT:
            return self._check_account_ui()
        
        elif self.login_state == LoginState.INPUT_ACCOUNT:
            return self._input_account()
        
        elif self.login_state == LoginState.INPUT_PASSWORD:
            return self._input_password()
        
        elif self.login_state == LoginState.SELECT_SERVER:
            return self._select_server()
        
        elif self.login_state == LoginState.SELECT_ROLE:
            return self._select_role()
        
        elif self.login_state == LoginState.CONFIRM_LOGIN:
            return self._confirm_login()
        
        elif self.login_state == LoginState.WAIT_ENTER_GAME:
            return self._wait_enter_game()
        
        elif self.login_state == LoginState.CHECK_IN_GAME:
            return self._check_in_game_state()
        
        elif self.login_state == LoginState.LOGIN_SUCCESS:
            self.set_state(TaskState.COMPLETED)
            return False
        
        elif self.login_state == LoginState.LOGIN_FAILED:
            self.set_state(TaskState.FAILED)
            return False
        
        return True
    
    def _check_account_ui(self) -> bool:
        """检查账号界面"""
        # 查找账号输入框特征
        result = self.unify.u.FindPic(
            0, 0, 800, 600, 
            "登录账号框.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            logger.info("[登录] 检测到账号输入界面")
            self.login_state = LoginState.INPUT_ACCOUNT
            return True
        
        # 检查是否在选择服务器界面
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "服务器列表.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            logger.info("[登录] 检测到服务器选择界面")
            self.login_state = LoginState.SELECT_SERVER
            return True
        
        # 检查是否在选择角色界面
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "角色选择.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            logger.info("[登录] 检测到角色选择界面")
            self.login_state = LoginState.SELECT_ROLE
            return True
        
        # 检查是否在游戏中
        if self._check_in_game():
            self.login_state = LoginState.LOGIN_SUCCESS
            return True
        
        logger.debug("[登录] 等待账号界面...")
        self.unify.小延时()
        return True
    
    def _input_account(self) -> bool:
        """输入账号"""
        # 模拟点击账号输入框
        self.unify.鼠标移动(400, 300)
        self.unify.左键点击()
        time.sleep(0.2)
        
        # 清空原有内容
        self.unify.组合键("ctrl", "a")
        time.sleep(0.1)
        
        # 输入账号
        for char in self.account:
            self.unify.按单个键(char)
            time.sleep(0.05)
        
        logger.info(f"[登录] 账号输入完成")
        self.login_state = LoginState.INPUT_PASSWORD
        self.reset_timeout()
        return True
    
    def _input_password(self) -> bool:
        """输入密码"""
        # Tab切换到密码框
        self.unify.按单个键("tab")
        time.sleep(0.2)
        
        # 输入密码
        for char in self.password:
            self.unify.按单个键(char)
            time.sleep(0.05)
        
        logger.info("[登录] 密码输入完成")
        
        # 点击登录按钮
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "登录按钮.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
        
        self.login_state = LoginState.WAIT_ENTER_GAME
        self.reset_timeout()
        return True
    
    def _select_server(self) -> bool:
        """选择服务器"""
        if not self.server:
            # 如果没有指定服务器，选择默认
            logger.info("[登录] 未指定服务器，选择默认")
            self.unify.鼠标移动(400, 200)
            self.unify.左键点击()
        else:
            # TODO: 查找并点击指定服务器
            logger.info(f"[登录] 选择服务器: {self.server}")
        
        time.sleep(1)
        self.login_state = LoginState.SELECT_ROLE
        self.reset_timeout()
        return True
    
    def _select_role(self) -> bool:
        """选择角色"""
        # 根据角色索引选择
        # 角色列表位置计算
        role_y_base = 300
        role_height = 80
        role_x = 400
        role_y = role_y_base + self.role_index * role_height
        
        self.unify.鼠标移动(role_x, role_y)
        self.unify.左键点击()
        
        logger.info(f"[登录] 选择角色索引: {self.role_index}")
        
        time.sleep(0.5)
        self.login_state = LoginState.CONFIRM_LOGIN
        self.reset_timeout()
        return True
    
    def _confirm_login(self) -> bool:
        """确认登录"""
        # 点击进入游戏按钮
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "进入游戏.bmp", "202020", 0.8, 0
        )
        
        if result[0] == 0:
            self.unify.鼠标移动(result[1], result[2])
            self.unify.左键点击()
            logger.info("[登录] 点击进入游戏")
        
        self.login_state = LoginState.WAIT_ENTER_GAME
        self.reset_timeout()
        return True
    
    def _wait_enter_game(self) -> bool:
        """等待进入游戏"""
        # 等待进度条消失
        for _ in range(30):
            time.sleep(1)
            
            # 检查是否在游戏中
            if self._check_in_game():
                self.login_state = LoginState.LOGIN_SUCCESS
                return True
            
            # 检查是否返回了账号界面（登录失败）
            result = self.unify.u.FindPic(
                0, 0, 800, 600,
                "登录账号框.bmp", "202020", 0.8, 0
            )
            
            if result[0] == 0:
                self.retry_count += 1
                if self.retry_count >= self.max_retry:
                    logger.error("[登录] 登录失败次数过多")
                    self.login_state = LoginState.LOGIN_FAILED
                    return True
                
                logger.warning(f"[登录] 登录失败，重试 {self.retry_count}/{self.max_retry}")
                self.login_state = LoginState.INPUT_ACCOUNT
                return True
        
        logger.warning("[登录] 等待进入游戏超时")
        self.login_state = LoginState.CHECK_IN_GAME
        return True
    
    def _check_in_game_state(self) -> bool:
        """检查是否在游戏中状态"""
        if self._check_in_game():
            self.login_state = LoginState.LOGIN_SUCCESS
            return True
        
        # 超时重试
        self.retry_count += 1
        if self.retry_count >= self.max_retry:
            self.login_state = LoginState.LOGIN_FAILED
            return True
        
        self.login_state = LoginState.CHECK_ACCOUNT
        return True
    
    def _check_in_game(self) -> bool:
        """检查是否已进入游戏"""
        # 通过查找游戏特征判断是否在游戏中
        # 例如：左上角地图名、底部任务栏等
        
        result = self.unify.u.FindPic(
            0, 0, 800, 600,
            "游戏主界面特征.bmp", "202020", 0.8, 0
        )
        
        return result[0] == 0
    
    def on_cleanup(self):
        """清理"""
        logger.info("[登录] 登录流程结束")
