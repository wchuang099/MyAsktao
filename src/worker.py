# worker.py
"""
问道脚本工作进程 - 任务执行入口

参考梦幻开发的多进程架构：
1. 每个窗口独立进程
2. 任务链顺序执行
3. 状态机驱动
"""
import sys
import os
import time
import json
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tasks import (
    TaskChain, TaskState,
    LoginTask, ShimenTask, BangpaiTask, FubenTask,
    TaskMonitor, MultiTaskController
)
from src.utils.unify import UNIFY

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 任务映射
TASK_MAPPING = {
    "login": LoginTask,
    "shimen": ShimenTask,
    "bangpai": BangpaiTask,
    "fuben": FubenTask,
}


def load_window_config(window_id):
    """加载窗口配置"""
    config_file = "task_chain.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return data.get(f"window_{window_id}", {})
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    return {}


def load_account_config(window_id):
    """加载账号配置"""
    config_file = "config/config.ini"
    # TODO: 使用configparser读取ini
    
    return {
        "account": "",
        "password": "",
        "server": "",
        "role_index": 0,
    }


def create_task(unify, task_name, config):
    """创建任务实例"""
    task_class = TASK_MAPPING.get(task_name)
    
    if task_class is None:
        logger.error(f"未知的任务类型: {task_name}")
        return None
    
    try:
        return task_class(unify, config)
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return None


def execute_task_chain(window_id, unify, task_flow):
    """
    执行任务链
    
    参考梦幻开发的任务链执行逻辑：
    1. 遍历任务列表
    2. 每个任务独立运行
    3. 完成后剔除并保存
    """
    logger.info(f"[窗口{window_id}] 开始执行任务链: {task_flow}")
    
    # 创建任务链管理器
    chain = TaskChain(window_id)
    
    # 更新任务流
    if task_flow:
        chain.update_task_flow(task_flow)
    
    # 创建监控器
    monitor = TaskMonitor(timeout=600)
    monitor.start()
    
    # 主循环
    while not chain.is_completed():
        # 获取当前任务
        task_info = chain.get_current_task()
        
        if task_info is None:
            break
        
        task_name = task_info.name
        task_config = task_info.config
        
        logger.info(f"[窗口{window_id}] 执行任务: {task_name}")
        print(f"当前任务: {task_name}")
        
        # 创建任务实例
        task = create_task(unify, task_name, task_config)
        
        if task is None:
            logger.error(f"[窗口{window_id}] 无法创建任务: {task_name}")
            chain.complete_current_task()
            continue
        
        try:
            # 执行任务（带监控）
            success = task.run()
            
            if success:
                logger.info(f"[窗口{window_id}] 任务完成: {task_name}")
                chain.complete_current_task()
            else:
                logger.warning(f"[窗口{window_id}] 任务失败或中断: {task_name}")
                # 可以选择重试或跳过
                # chain.complete_current_task()
        
        except Exception as e:
            logger.error(f"[窗口{window_id}] 任务异常: {e}")
        
        # 重置监控计时
        monitor.reset()
        
        # 小延时
        time.sleep(1)
    
    # 停止监控
    monitor.stop()
    
    logger.info(f"[窗口{window_id}] 所有任务执行完毕")
    print("任务全部完成")


def main(window_id):
    """主入口"""
    window_id = int(window_id)
    
    print(f"[窗口{window_id}] 进程启动")
    logger.info(f"[窗口{window_id}] 进程启动")
    
    # 加载配置
    window_config = load_window_config(window_id)
    account_config = load_account_config(window_id)
    
    # 获取VNC端口
    vnc_port = window_config.get("vnc_port", 102 + window_id)
    
    try:
        # 创建UNIFY实例
        print(f"[窗口{window_id}] 连接VNC端口: {vnc_port}")
        unify = UNIFY(vnc_port)
        
        # 获取任务流
        task_flow = window_config.get("task_flow", [])
        
        # 执行任务链
        execute_task_chain(window_id, unify, task_flow)
        
    except Exception as e:
        logger.error(f"[窗口{window_id}] 主进程异常: {e}")
        print(f"错误: {e}")
    
    print(f"[窗口{window_id}] 进程结束")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python worker.py <window_id>")
        sys.exit(1)
    
    main(sys.argv[1])
