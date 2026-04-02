# worker.py
"""
问道脚本工作进程 - 任务执行入口

功能：
1. 多窗口独立进程管理
2. 任务链顺序执行
3. 状态机驱动
4. 异常处理和恢复
"""
import sys
import os
import time
import json
import logging
import signal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tasks import (
    TaskChain, TaskInfo,
    LoginTask, ShimenTask, BangpaiTask, FubenTask, PaniTask,
    TaskMonitor
)
from src.utils.unify import UNIFY

# 全局日志标识（VNC端口）
LOG_TAG = ""

def setup_logging(vnc_port):
    """配置日志格式，使用VNC端口标识"""
    global LOG_TAG
    LOG_TAG = str(vnc_port)
    
    # 创建日志格式器
    formatter = logging.Formatter(
        f'[端口{vnc_port}] %(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日志
    logging.basicConfig(
        level=logging.INFO,
        format=f'[端口{vnc_port}] %(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    return formatter

logger = logging.getLogger(__name__)


# ==================== 任务映射 ====================

TASK_MAPPING = {
    "login": LoginTask,
    "shimen": ShimenTask,
    "bangpai": BangpaiTask,
    "fuben": FubenTask,
    "pani": PaniTask,
}

TASK_NAMES = {
    "login": "登录",
    "shimen": "师门任务",
    "bangpai": "帮派任务",
    "fuben": "副本任务",
    "pani": "叛逆任务",
}


# ==================== 配置加载 ====================

def load_window_config(window_id):
    """加载窗口配置"""
    config_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "task_chain.json"
    )
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 根据窗口索引获取对应的端口配置
            port = str(100 + window_id)
            if port in data:
                return data[port]
            
            # 兼容旧格式
            window_key = f"window_{window_id}"
            if window_key in data:
                return data[window_key]
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    # 返回默认配置
    return {
        "vnc_port": 100 + window_id,
        "pid_vid": "",
        "task_flow": ["shimen"],
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


# ==================== 任务执行 ====================

def execute_task_chain(window_id, unify, task_flow):
    """
    执行任务链
    
    流程：
    1. 遍历任务列表
    2. 每个任务独立运行
    3. 完成后剔除并保存断点
    """
    total_tasks = len(task_flow)
    current_index = 0
    vnc_port = unify.vnc_port
    
    print(f"[端口{vnc_port}] 开始执行任务链: {task_flow}")
    logger.info(f"开始执行任务链: {task_flow}")
    
    while current_index < total_tasks:
        task_name = task_flow[current_index]
        task_display = TASK_NAMES.get(task_name, task_name)
        
        print(f"[端口{vnc_port}] 当前任务: {task_display} ({current_index + 1}/{total_tasks})")
        logger.info(f"执行任务: {task_name}")
        
        # 创建任务配置
        config = {
            "account": "",
            "password": "",
            "server": "",
            "role_index": 0,
            "timeout": 600,
        }
        
        # 创建任务实例
        task = create_task(unify, task_name, config)
        
        if task is None:
            logger.error(f"无法创建任务: {task_name}")
            current_index += 1
            continue
        
        try:
            # 执行任务
            success = task.run()
            
            if success:
                logger.info(f"任务完成: {task_name}")
                print(f"[端口{vnc_port}] 任务完成: {task_display}")
            else:
                logger.warning(f"任务中断或失败: {task_name}")
                print(f"[端口{vnc_port}] 任务未完成: {task_display}")
        
        except Exception as e:
            logger.error(f"任务异常: {e}")
            print(f"[端口{vnc_port}] 任务异常: {e}")
        
        current_index += 1
        time.sleep(1)
    
    logger.info(f"所有任务执行完毕")


# ==================== 信号处理 ====================

_running = True

def signal_handler(signum, frame):
    """信号处理器"""
    global _running
    print(f"[端口{LOG_TAG}] 收到停止信号")
    _running = False


# ==================== 主入口 ====================

def main(window_id):
    """主入口"""
    global _running
    
    window_id = int(window_id)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 加载配置
    window_config = load_window_config(window_id)
    
    # 获取VNC端口
    vnc_port = window_config.get("vnc_port", 100 + window_id)
    
    # 配置日志（使用VNC端口）
    setup_logging(vnc_port)
    
    print(f"{'=' * 50}")
    print(f"[端口{vnc_port}] 进程启动")
    print(f"{'=' * 50}")
    logger.info(f"进程启动")
    
    # 获取任务流
    task_flow = window_config.get("task_flow", ["shimen"])
    
    # 转换中文任务名为英文
    name_to_key = {"登录": "login", "登录任务": "login",
                   "师门任务": "shimen", "师门": "shimen",
                   "帮派任务": "bangpai", "帮派": "bangpai",
                   "副本任务": "fuben", "副本": "fuben",
                   "叛逆任务": "pani", "叛逆": "pani"}
    
    normalized_flow = []
    for task in task_flow:
        if task in name_to_key:
            normalized_flow.append(name_to_key[task])
        elif task in TASK_MAPPING:
            normalized_flow.append(task)
    
    if not normalized_flow:
        normalized_flow = ["shimen"]
    
    try:
        # 创建UNIFY实例
        logger.info(f"连接VNC端口: {vnc_port}")
        
        unify = UNIFY(vnc_port)
        
        # 执行任务链
        execute_task_chain(window_id, unify, normalized_flow)
        
    except KeyboardInterrupt:
        logger.info(f"用户中断")
    
    except Exception as e:
        logger.error(f"主进程异常: {e}")
    
    finally:
        logger.info(f"进程结束")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python worker.py <window_id>")
        print("示例: python worker.py 1")
        sys.exit(1)
    
    main(sys.argv[1])
