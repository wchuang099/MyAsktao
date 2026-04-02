# src/tasks/autopath.py
"""
问道自动寻路系统 - 模板实现

参考梦幻西游跨地图寻路设计：
1. 自省：识别当前地图和坐标
2. 判断：是否跨图，选择节点或直飞
3. 执行：小地图点击 + 坐标变化检测

使用方式：
    pathfinder = Pathfinder(unify)
    # 地图内寻路
    pathfinder.move_to(100, 50)
    # 跨地图寻路
    pathfinder.go_to_map("天墉城", 150, 80)
"""
import re
import time
import logging
from typing import Optional, Tuple, Dict, List

logger = logging.getLogger(__name__)


class Pathfinder:
    """
    问道自动寻路系统
    
    核心功能：
    1. 地图识别：读取左上角地图名
    2. 坐标识别：读取当前坐标
    3. 小地图点击：游戏坐标 -> 屏幕像素 -> 点击
    4. 跨地图寻路：节点式路径规划
    """
    
    # 问道小地图配置（需根据实际调整）
    MAP_RADIUS_X = 320      # 小地图宽度的一半（像素）
    MAP_RADIUS_Y = 320      # 小地图高度的一半（像素）
    MAP_COORD_MAX = 800     # 游戏坐标系最大值（每个地图不同，需动态获取）
    
    # 小地图在屏幕上的位置（相对于窗口左上角，需根据实际情况调整）
    MINI_MAP_X = 760        # 小地图中心X
    MINI_MAP_Y = 120        # 小地图中心Y
    MINI_MAP_OFFSET_X = 0   # X方向偏移修正
    MINI_MAP_OFFSET_Y = 0   # Y方向偏移修正
    
    # 寻路等待配置
    MOVE_TIMEOUT = 15       # 移动超时（秒）
    MOVE_CHECK_INTERVAL = 0.3  # 坐标检测间隔（秒）
    ARRIVE_THRESHOLD = 15   # 到达判定阈值（像素）
    
    # 坐标识别区域（相对于游戏窗口）
    COORD_REGION = (0, 0, 122, 23)  # 左上角坐标区域
    
    def __init__(self, unify):
        """
        初始化寻路系统
        
        Args:
            unify: UNIFY实例
        """
        self.unify = unify
        self.current_map = ""       # 当前地图名
        self.current_coord = (0, 0) # 当前坐标 (x, y)
        
        # 节点式跨图寻路配置
        # 格式：{"目标地图": [(当前地图, 入口X, 入口Y, 出口X, 出口Y), ...]}
        self.path_nodes: Dict[str, List[Tuple]] = {}
        
        # 初始化
        self._refresh_location()
    
    # ==================== 位置识别 ====================
    
    def _refresh_location(self):
        """刷新当前位置（地图名 + 坐标）"""
        self.current_map = self._get_map_name()
        self.current_coord = self._get_coord()
        logger.debug(f"当前位置: {self.current_map} ({self.current_coord[0]}, {self.current_coord[1]})")
    
    def _get_map_name(self) -> str:
        """
        识别当前地图名
        
        Returns:
            地图名称字符串
        """
        try:
            # 使用字库1识别坐标区域的文字
            self.unify.使用字库(1)
            text = self.unify.文字识别(0, 0, 200, 25, "ffffff-050505")
            
            # 解析地图名（格式通常是 "地图名 X,Y" 或 "地图名坐标"）
            # 清理文字
            text = text.strip()
            
            # 提取地图名（去除坐标部分）
            # 常见的地图名关键词
            map_keywords = [
                "揽仙镇", "天墉城", "官道北", "官道南", "无间门", "地府",
                "东海渔村", "凤凰山", "五龙山", "琵琶山", "玉柱洞",
                "乾元山", "终南山", "百花谷", "风月谷", "大雪原"
            ]
            
            for keyword in map_keywords:
                if keyword in text:
                    return keyword
            
            return text.split()[0] if text else ""
            
        except Exception as e:
            logger.warning(f"地图名识别失败: {e}")
            return ""
    
    def _get_coord(self) -> Tuple[int, int]:
        """
        识别当前坐标
        
        Returns:
            (x, y) 元组
        """
        try:
            self.unify.使用字库(1)
            text = self.unify.文字识别(0, 0, 122, 23, "ffffff-050505")
            
            # 解析坐标（格式如 "100, 58" 或 "100 58"）
            # 过滤干扰字符
            text = re.sub(r'[\[\]（）()（）]', '', text)
            
            # 尝试匹配坐标模式
            match = re.search(r'(\d+)[,\s]+(\d+)', text)
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                return (x, y)
            
            # 尝试匹配 "X:" 格式
            match = re.search(r'X[:：]?\s*(\d+)', text)
            if match:
                x = int(match.group(1))
                # 尝试从文字中提取Y
                match_y = re.search(r'Y[:：]?\s*(\d+)', text)
                if match_y:
                    y = int(match_y.group(1))
                    return (x, y)
            
            return (0, 0)
            
        except Exception as e:
            logger.warning(f"坐标识别失败: {e}")
            return (0, 0)
    
    def get_location(self) -> Tuple[str, int, int]:
        """
        获取当前位置（地图名 + 坐标）
        
        Returns:
            (地图名, X坐标, Y坐标)
        """
        self._refresh_location()
        return (self.current_map, self.current_coord[0], self.current_coord[1])
    
    # ==================== 小地图操作 ====================
    
    def _coord_to_pixel(self, target_x: int, target_y: int) -> Tuple[int, int]:
        """
        游戏坐标转换为小地图像素坐标
        
        Args:
            target_x: 游戏坐标X
            target_y: 游戏坐标Y
        
        Returns:
            (像素X, 像素Y)
        """
        # 计算比例（根据实际地图大小调整）
        ratio_x = (self.MAP_RADIUS_X * 2) / self.MAP_COORD_MAX
        ratio_y = (self.MAP_RADIUS_Y * 2) / self.MAP_COORD_MAX
        
        # 转换为相对于小地图中心的偏移
        offset_x = int(target_x * ratio_x) + self.MINI_MAP_OFFSET_X
        offset_y = int(target_y * ratio_y) + self.MINI_MAP_OFFSET_Y
        
        # 加上小地图中心位置
        pixel_x = self.MINI_MAP_X + offset_x
        pixel_y = self.MINI_MAP_Y + offset_y
        
        # 添加随机偏移，防止总是点击同一点
        import random
        offset = random.randint(-3, 3)
        pixel_x += offset
        pixel_y += offset
        
        return (pixel_x, pixel_y)
    
    def _open_mini_map(self) -> bool:
        """
        打开小地图
        
        Returns:
            True if opened
        """
        # 尝试按Tab打开小地图
        self.unify.按单个键("Tab")
        time.sleep(0.3)
        
        # 检查是否打开（可以检测小地图特征）
        # 这里简化处理，直接返回True
        return True
    
    def _close_mini_map(self):
        """关闭小地图"""
        self.unify.按单个键("Tab")
        time.sleep(0.1)
    
    # ==================== 移动检测 ====================
    
    def _is_moving(self, old_coord: Tuple[int, int], timeout: float = 0.5) -> bool:
        """
        检测是否正在移动
        
        Args:
            old_coord: 之前的坐标
            timeout: 检测持续时间
        
        Returns:
            True if still moving
        """
        start_time = time.time()
        stable_count = 0
        required_stable = 3  # 连续3次坐标不变才认为停止
        
        while time.time() - start_time < timeout:
            time.sleep(0.2)
            current = self._get_coord()
            
            # 计算位移
            dx = abs(current[0] - old_coord[0])
            dy = abs(current[1] - old_coord[1])
            
            if dx <= 2 and dy <= 2:
                stable_count += 1
                if stable_count >= required_stable:
                    return False  # 停止移动
            else:
                stable_count = 0
            
            old_coord = current
        
        return True  # 超时前未停止
    
    def _wait_for_arrive(self, target_x: int, target_y: int) -> bool:
        """
        等待到达目标点
        
        Args:
            target_x: 目标X
            target_y: 目标Y
        
        Returns:
            True if arrived
        """
        start_time = time.time()
        last_moving_time = time.time()
        
        while time.time() - start_time < self.MOVE_TIMEOUT:
            time.sleep(self.MOVE_CHECK_INTERVAL)
            
            current = self._get_coord()
            
            # 如果坐标无法识别(0,0)，直接返回成功（假设点击生效）
            if current[0] == 0 and current[1] == 0:
                logger.debug("[寻路] 无法识别坐标，假设到达")
                return True
            
            # 检查是否到达
            distance = ((current[0] - target_x) ** 2 + (current[1] - target_y) ** 2) ** 0.5
            if distance <= self.ARRIVE_THRESHOLD:
                logger.debug(f"到达目标点: ({target_x}, {target_y})")
                return True
            
            # 检查是否卡死（坐标长时间不变且距离目标还远）
            if distance > self.ARRIVE_THRESHOLD:
                if abs(current[0] - self.current_coord[0]) <= 2 and \
                   abs(current[1] - self.current_coord[1]) <= 2:
                    if time.time() - last_moving_time > 3:
                        logger.warning("寻路疑似卡死")
                        return False
                else:
                    last_moving_time = time.time()
            
            self.current_coord = current
        
        logger.warning(f"寻路超时: 目标 ({target_x}, {target_y})")
        return False
    
    # ==================== 核心寻路方法 ====================
    
    def move_to(self, target_x: int, target_y: int, auto_map: bool = True) -> bool:
        """
        地图内移动到指定坐标
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            auto_map: 是否自动开关小地图
        
        Returns:
            True if arrived
        """
        self._refresh_location()
        
        start_x, start_y = self.current_coord
        
        # 检查是否已经在目标点
        distance = ((start_x - target_x) ** 2 + (start_y - target_y) ** 2) ** 0.5
        if distance <= self.ARRIVE_THRESHOLD:
            logger.debug(f"已在目标点附近: ({target_x}, {target_y})")
            return True
        
        logger.info(f"开始寻路: ({start_x}, {start_y}) -> ({target_x}, {target_y})")
        
        # 如果无法识别坐标(0,0)，直接点击目标位置
        if start_x == 0 and start_y == 0:
            logger.info("[寻路] 无法识别坐标，直接点击目标位置")
            # 直接右键双击寻路（问道常用方式）
            pixel_x, pixel_y = self._coord_to_pixel(target_x, target_y)
            self.unify.鼠标移动(pixel_x, pixel_y)
            self.unify.右键点击()
            time.sleep(0.2)
            self.unify.左键点击()
            time.sleep(0.5)
            return True
        
        if auto_map:
            self._open_mini_map()
        
        try:
            # 转换坐标为像素
            pixel_x, pixel_y = self._coord_to_pixel(target_x, target_y)
            
            # 点击小地图
            self.unify.鼠标移动(pixel_x, pixel_y)
            self.unify.左键点击()
            
            # 等待到达
            return self._wait_for_arrive(target_x, target_y)
            
        finally:
            if auto_map:
                self._close_mini_map()
    
    def click_portal(self, portal_x: int, portal_y: int, timeout: int = 10) -> bool:
        """
        点击传送点/传送门
        
        Args:
            portal_x: 传送点X坐标
            portal_y: 传送点Y坐标
            timeout: 超时时间（秒）
        
        Returns:
            True if transported successfully
        """
        old_map = self.current_map
        
        # 先移动到传送点附近
        self.move_to(portal_x, portal_y)
        
        # 等待一下确保到位
        time.sleep(0.5)
        
        # 点击传送（通常需要在传送点再点击一次）
        # 这里需要根据实际游戏机制调整
        self.unify.左键点击()
        time.sleep(0.3)
        self.unify.左键点击()
        
        # 等待地图切换
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            self._refresh_location()
            
            if self.current_map and self.current_map != old_map:
                logger.info(f"传送成功: {old_map} -> {self.current_map}")
                return True
        
        logger.warning(f"传送超时: 从 {old_map} 未能切换地图")
        return False
    
    # ==================== 节点式跨图寻路 ====================
    
    def register_path_node(self, from_map: str, to_map: str, 
                          entry_x: int, entry_y: int,
                          exit_x: int = 0, exit_y: int = 0):
        """
        注册路径节点
        
        Args:
            from_map: 起始地图
            to_map: 目标地图
            entry_x: 入口X坐标（传送阵位置）
            entry_y: 入口Y坐标
            exit_x: 出口X坐标（到达目标地图后的位置）
            exit_y: 出口Y坐标
        """
        if to_map not in self.path_nodes:
            self.path_nodes[to_map] = []
        
        self.path_nodes[to_map].append((from_map, entry_x, entry_y, exit_x, exit_y))
    
    def go_to_map(self, target_map: str, target_x: int = 0, target_y: int = 0,
                  max_retry: int = 3) -> bool:
        """
        跨地图寻路到指定地点
        
        Args:
            target_map: 目标地图名
            target_x: 目标X坐标（可选，默认0）
            target_y: 目标Y坐标（可选，默认0）
            max_retry: 最大重试次数
        
        Returns:
            True if arrived
        """
        self._refresh_location()
        
        # 如果已经在目标地图，直接移动到目标坐标
        if self.current_map == target_map:
            if target_x and target_y:
                return self.move_to(target_x, target_y)
            return True
        
        logger.info(f"跨图寻路: {self.current_map} -> {target_map}")
        
        # 查找到目标地图的路径
        for retry in range(max_retry):
            if self._find_path_to(target_map):
                # 到达目标地图后，移动到指定坐标
                if target_x and target_y:
                    time.sleep(0.5)  # 等待地图切换完成
                    return self.move_to(target_x, target_y)
                return True
            
            logger.warning(f"寻路失败，重试 {retry + 1}/{max_retry}")
            time.sleep(1)
        
        return False
    
    def _find_path_to(self, target_map: str) -> bool:
        """
        查找并执行到目标地图的路径
        
        Args:
            target_map: 目标地图
        
        Returns:
            True if reached target map
        """
        # 检查是否有到目标地图的节点配置
        if target_map not in self.path_nodes:
            logger.error(f"未配置到 {target_map} 的路径节点")
            return False
        
        # 查找从当前位置到目标地图的路径
        nodes = self.path_nodes[target_map]
        
        for from_map, entry_x, entry_y, exit_x, exit_y in nodes:
            if from_map == self.current_map:
                # 找到匹配的节点，执行传送
                logger.info(f"执行传送: {from_map} -> {target_map}")
                return self.click_portal(entry_x, entry_y)
        
        # 没有找到直接路径，尝试递归查找
        # 简化处理：遍历所有节点找中转
        visited = set()
        return self._recursive_path_find(self.current_map, target_map, visited)
    
    def _recursive_path_find(self, current: str, target: str, 
                            visited: set, depth: int = 0) -> bool:
        """
        递归查找路径（支持中转站）
        
        Args:
            current: 当前位置
            target: 目标地图
            visited: 已访问节点
            depth: 递归深度
        
        Returns:
            True if reached
        """
        if depth > 10:  # 防止无限递归
            return False
        
        if current == target:
            return True
        
        if current in visited:
            return False
        
        visited.add(current)
        
        # 查找以 current 为起点的所有路径
        for dest_map, nodes in self.path_nodes.items():
            for from_map, entry_x, entry_y, exit_x, exit_y in nodes:
                if from_map == current:
                    # 执行传送
                    if self.click_portal(entry_x, entry_y):
                        time.sleep(0.5)
                        self._refresh_location()
                        
                        if self.current_map == target:
                            return True
                        
                        # 继续递归
                        if self._recursive_path_find(self.current_map, target, visited, depth + 1):
                            return True
        
        return False
    
    # ==================== 便捷方法 ====================
    
    def go_to_npc(self, npc_name: str, npc_x: int, npc_y: int, 
                 npc_map: str = None) -> bool:
        """
        寻路到NPC位置
        
        Args:
            npc_name: NPC名称
            npc_x: NPC X坐标
            npc_y: NPC Y坐标
            npc_map: NPC所在地图（可选，自动判断）
        
        Returns:
            True if arrived
        """
        if npc_map:
            return self.go_to_map(npc_map, npc_x, npc_y)
        else:
            return self.move_to(npc_x, npc_y)
    
    def wait_for_map(self, map_name: str, timeout: int = 30) -> bool:
        """
        等待到达指定地图
        
        Args:
            map_name: 目标地图名
            timeout: 超时时间（秒）
        
        Returns:
            True if arrived
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self._refresh_location()
            
            if self.current_map == map_name:
                logger.info(f"到达地图: {map_name}")
                return True
            
            time.sleep(0.5)
        
        logger.warning(f"等待地图超时: 目标 {map_name}, 当前 {self.current_map}")
        return False


# ==================== 预设路径节点配置 ====================

def register_common_paths(pathfinder: Pathfinder):
    """
    注册常用路径节点
    
    可以根据实际游戏内容添加更多节点
    """
    # 揽仙镇相关
    # pathfinder.register_path_node("揽仙镇", "天墉城", 入口坐标, 出口坐标)
    
    # 天墉城相关
    # pathfinder.register_path_node("天墉城", "揽仙镇", 入口坐标, 出口坐标)
    
    # 添加更多路径...
    pass
