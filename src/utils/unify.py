# src/utils/unify.py
"""
问道UNIFY控制封装

提供统一的游戏控制接口，包括：
- 鼠标操作
- 键盘操作  
- 图像识别
- OCR识别
"""
import time
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils import yjs
from src.utils.yjs import code_dict
from collections import deque
import PyUnifyEN
from src.utils.paths import assets_root


class UNIFY:
    """
    一个 UNIFY 实例 = 一个虚拟机的完整能力边界
    
    提供游戏自动化所需的全部控制能力
    """
    
    def __init__(self, vnc_port, enable_resources=True):
        """
        初始化UNIFY实例
        
        Args:
            vnc_port: VNC端口号
            enable_resources: 是否加载资源文件（yolo、bmp等），设为False可用于框架测试
        """
        self.vnc_port = vnc_port
        self.u = PyUnifyEN.Unify()
        self.u.bsLoadDLL("Unify.dll")
        
        # 登录授权
        result = self.u.bsLogin("158496099", "F8H54C9VP951G32R")
        print(f"[UNIFY] 授权登录结果: {result}")
        
        # 连接VNC
        self.u.bsConnect(vnc_port)
        print(f"[UNIFY] 连接VNC端口: {vnc_port}")
        
        # 资源加载（可选，用于框架测试时可跳过）
        self.enable_resources = enable_resources
        
        if enable_resources:
            try:
                self._load_resources()
            except Exception as e:
                print(f"[UNIFY] 资源加载失败: {e}，将使用简化模式")
                self.enable_resources = False
        
        # 初始化 yjs 设备（鼠标键盘控制）
        self.yjs = yjs.get_yjs(vnc_port)
        
        # 绑定窗口
        self._bind_window()
    
    def _load_resources(self):
        """加载资源文件"""
        # 加载 yolo
        onnx_path = assets_root("yolo", "best.onnx", check=False)
        if os.path.exists(onnx_path):
            self.u.yoloInit(onnx_path)
            print(f"[UNIFY] YOLO初始化完成")
        
        # 设置资源路径
        self.u.SetPath(assets_root())
        
        # 加载位图
        self.u.LoadAllBitMap()
        
        # 加载字库
        font_files = [
            (1, "fonts/坐标字库.txt"),
            (2, "fonts/地图字库.txt"),
            (4, "fonts/通用字库.txt"),
            (5, "fonts/NPC字库.txt"),
            (6, "fonts/对话字库.txt"),
            (7, "fonts/回合字库.txt"),
            (8, "fonts/任务字库.txt"),
        ]
        
        for dict_id, font_file in font_files:
            font_path = assets_root(font_file, check=False)
            if os.path.exists(font_path):
                self.u.LoadDict(dict_id, font_file)
        
        print(f"[UNIFY] 资源加载完成")
    
    def _bind_window(self):
        """绑定游戏窗口"""
        try:
            result = self.u.FindPic(0, 0, 1024, 768, "客户端图标.bmp", "151515", 1.0, 0)
            _, x, y = result
            if x >= 0:
                self.u.bsSetClientLocation(x - 10, y + 61)
                print(f"[UNIFY] 窗口绑定成功")
            else:
                print(f"[UNIFY] 未找到客户端图标（正常，如未在游戏中）")
        except Exception as e:
            print(f"[UNIFY] 窗口绑定失败: {e}")
    
    # ==================== 鼠标操作 ====================
    
    def 左键点击(self):
        """左键单击"""
        self.yjs.LeftClick()
    
    def 稳定左键单击(self):
        """稳定左键单击（右键+左键）"""
        self.yjs.RightClick()
        time.sleep(0.3)
        self.yjs.LeftClick()
    
    def 右键点击(self):
        """右键单击"""
        self.yjs.RightClick()
    
    def 相对移动(self, dx, dy):
        """相对移动鼠标"""
        self.yjs.MoveR(dx, dy)
    
    def 鼠标移动(self, x, y):
        """移动鼠标到绝对坐标"""
        self.u.MoveTo(x, y)
        self.u.bsForceDrawing()
    
    # ==================== 键盘操作 ====================
    
    def 组合键(self, *keys, hold=0.2, after=0.2):
        """
        稳定组合键：
        - 先按修饰键
        - 等待 hold 秒
        - 再按主键
        - 最后释放
        """
        codes = [code_dict[k.lower()] for k in keys]
        
        for code in codes:
            self.yjs.KeyDown(code)
            time.sleep(0.05)
        
        time.sleep(hold)
        
        for code in reversed(codes):
            self.yjs.KeyUp(code)
            time.sleep(0.05)
        
        time.sleep(after)
    
    def 按单个键(self, key):
        """按单个键"""
        self.yjs.KeyPressChar(key)
    
    def 按键(self, key_code):
        """按指定键码"""
        self.yjs.KeyDown(key_code)
        time.sleep(0.1)
        self.yjs.KeyUp(key_code)
    
    # ==================== 延时 ====================
    
    def 小延时(self):
        """小延时 80-210ms"""
        self.u.otSleep(80, 210)
    
    def 中延时(self):
        """中延时 400-800ms"""
        self.u.otSleep(400, 800)
    
    def 大延时(self):
        """大延时 1500-2000ms"""
        self.u.otSleep(1500, 2000)
    
    # ==================== 图像识别 ====================
    
    def 找图(self, x1, y1, x2, y2, image_name, color="202020", sim=0.8, index=0):
        """
        查找图片
        
        Returns:
            (状态, x, y) - 状态0表示找到，-1表示未找到
        """
        try:
            return self.u.FindPic(x1, y1, x2, y2, image_name, color, sim, index)
        except Exception as e:
            return (-1, 0, 0)
    
    def 找图Ex(self, x1, y1, x2, y2, image_name, color="202020", sim=0.8, index=0):
        """
        查找所有匹配的图像
        
        Returns:
            字符串，格式如 "0,x,y|0,x,y|..."
        """
        try:
            return self.u.FindPicEx(x1, y1, x2, y2, image_name, color, sim, index)
        except Exception as e:
            return ""
    
    def 找色(self, x1, y1, x2, y2, color, sim=0.9, dir=2):
        """查找颜色"""
        try:
            return self.u.FindColor(x1, y1, x2, y2, color, sim, dir)
        except:
            return None
    
    def yolo检测(self, x1, y1, x2, y2, use_window=True, index=0, cls=-1, 
                 filter=-1, area=-1, min_conf=0.25, min_area=0.45):
        """YOLO目标检测"""
        try:
            return self.u.yoloDetectFromWindow_Parsed(
                x1, y1, x2, y2, use_window, index, cls, filter, area, min_conf, min_area
            )
        except Exception as e:
            return (False, 0, 0, 0, 0)
    
    # ==================== OCR识别 ====================
    
    def 文字识别(self, x1, y1, x2, y2, color="ffffff-050505"):
        """
        OCR文字识别
        
        Args:
            color: 颜色参数，如 "ffffff-050505"
        
        Returns:
            识别的文字
        """
        try:
            return self.u.Ocr(x1, y1, x2, y2, f"color={color}")
        except Exception as e:
            return ""
    
    def 使用字库(self, dict_id):
        """切换OCR字库"""
        self.u.UseDict(dict_id)
    
    # ==================== 窗口操作 ====================
    
    def 获取窗口数量(self):
        """获取多开窗口数量"""
        try:
            res = self.u.FindPicEx(-4, -38, 775, -5, "多窗口特征", "101010", 1.0, 0)
            queue = deque()
            if not res:
                return queue
            for item in res.split("|"):
                parts = item.split(",")
                if len(parts) >= 3:
                    _, x, y = parts
                    queue.append((int(x), int(y)))
            return queue
        except:
            return deque()
    
    def 激活窗口(self, x, y):
        """激活指定窗口"""
        self.u.MoveTo(x - 30, y)
        self.u.LeftClick()
        time.sleep(0.3)
        
        status, rx, ry = self.u.FindPic(-4, -38, 775, -5, "窗口激活特征", "101010", 0.9, 0)
        return status == 0 and abs(rx - x) <= 5
    
    # ==================== 游戏状态 ====================
    
    def 获取血量(self):
        """获取角色血量百分比"""
        try:
            x1, y1, x2, y2 = 699, 27, 785, 38
            血条总长度 = x2 - x1
            
            res = self.u.FindColor(x1, y1, x2, y2,
                "a51810-202020|e6b6b5-202020|ce1c19-202020|7b0800-202020|ef1c10-202020", 
                0.9, 2)
            
            if res is None:
                return 0
            
            _, x, y = res
            return (x - x1) / 血条总长度 * 100
        except:
            return 0
    
    def 获取蓝量(self):
        """获取角色蓝量百分比"""
        try:
            x1, y1, x2, y2 = 697, 40, 785, 53
            蓝条总长度 = x2 - x1
            
            res = self.u.FindColor(x1, y1, x2, y2,
                "2159b5-202020|00356b-202020|4275c5-202020|21599c-202020", 
                0.9, 2)
            
            if res is None:
                return 0
            
            _, x, y = res
            return (x - x1) / 蓝条总长度 * 100
        except:
            return 0
    
    def 坐标识别(self):
        """识别当前坐标"""
        self.u.UseDict(1)
        return self.u.Ocr(0, 0, 122, 23, color="ffffff-050505")
    
    # ==================== 快捷属性 ====================
    
    @property
    def 鼠标(self):
        """鼠标控制对象"""
        return self.yjs
    
    @property
    def 键盘(self):
        """键盘控制对象"""
        return self.yjs


# 兼容性别名
Unify = UNIFY
