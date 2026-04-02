# yjs.py
# -*- coding: utf-8 -*-
import ctypes
from ctypes import wintypes
from src.utils.paths import assets_root
from src.utils.config import Config

# ================== 键码映射 ==================
code_dict = {
    "1": 49, "2": 50, "3": 51, "4": 52, "5": 53, "6": 54, "7": 55, "8": 56, "9": 57, "0": 48,
    "-": 189, "=": 187, "back": 8, "a": 65, "b": 66, "c": 67, "d": 68, "e": 69, "f": 70, "g": 71,
    "h": 72, "i": 73, "j": 74, "k": 75, "l": 76, "m": 77, "n": 78, "o": 79, "p": 80, "q": 81,
    "r": 82, "s": 83, "t": 84, "u": 85, "v": 86, "w": 87, "x": 88, "y": 89, "z": 90, "ctrl": 17,
    "alt": 18, "shift": 16, "win": 91, "space": 32, "cap": 20, "tab": 9, "~": 192, "esc": 27,
    "enter": 13, "up": 38, "down": 40, "left": 37, "right": 39, "option": 93, "print": 44,
    "delete": 46, "home": 36, "end": 35, "pgup": 33, "pgdn": 34, "f1": 112, "f2": 113, "f3": 114,
    "f4": 115, "f5": 116, "f6": 117, "f7": 118, "f8": 119, "f9": 120, "f10": 121, "f11": 122,
    "f12": 123, "[": 219, "]": 221, "\\": 220, ";": 186, "'": 222, ",": 188, ".": 190, "/": 191,
}

# ================== YJS 实例池 ==================
_yjs_pool = {}  # port -> YJS


def get_yjs(port: int):
    """
    按端口获取 YJS（一个端口一个实例）
    """
    if port not in _yjs_pool:
        _yjs_pool[port] = YJS.from_port(port)
    return _yjs_pool[port]


class YJS:
    """底层鼠标键盘 DLL 封装（绑定一个虚拟机）"""

    @classmethod
    def from_port(cls, port: int):
        """
        根据端口 → 查配置 → 创建 YJS
        """
        cfg = Config()

        # 例子：
        # [yjs]
        # 102 = 0xC216,0x0102
        # 103 = 0xC216,0x0103
        raw = cfg.get("yjs", str(port))
        if not raw:
            raise RuntimeError(f"未配置端口 {port} 的 VID/PID")

        vid_hex, pid_hex = raw.split(",")
        VID = int(vid_hex, 16)
        PID = int(pid_hex, 16)

        return cls(1024, 768, VID=VID, PID=PID)

    def __init__(self, w, h, VID, PID, move_flag=0, KeyDelay=None):
        self.w, self.h = w, h
        self.move_flag = move_flag

        dll_path = assets_root("plugins", "msdk.dll")
        self.objdll = ctypes.windll.LoadLibrary(dll_path)

        self.objdll.M_Open_VidPid.restype = wintypes.LPHANDLE
        self.hdl = self.objdll.M_Open_VidPid(VID, PID)
        if self.hdl == -1:
            raise Exception(f"打开设备失败 VID={VID:x} PID={PID:x}")

        self.__ResolutionUsed()
        self.__EnableRealMouse(move_flag)


    def __ResolutionUsed(self):
        if self.move_flag == 1:
            self.objdll.M_ResolutionUsed(self.hdl, self.w, self.h)

    def __EnableRealMouse(self, move_flag):
        if move_flag == 1:
            self.objdll.M_SetParam(self.hdl, 1, 10, 20)


    # ---------- 基础能力 ----------
    def KeyPress(self, code):
        self.objdll.M_KeyPress2(self.hdl, code, 1)

    def KeyPressChar(self, char):
        """按单个字符"""
        self.KeyPress(code_dict[char.lower()])

    def KeyDown(self, code):
        self.objdll.M_KeyDown2(self.hdl, code, 1)

    def KeyUp(self, code):
        self.objdll.M_KeyUp2(self.hdl, code, 1)

    def MoveTo(self, x: int, y: int):
        if self.move_flag == 0:
            self.objdll.M_MoveTo3_D(self.hdl, x, y)
        elif self.move_flag == 1:
            self.objdll.M_MoveTo3(self.hdl, x, y)

    def LeftClick(self):
        self.objdll.M_LeftClick(self.hdl, 1)

    def RightClick(self):
        self.objdll.M_RightClick(self.hdl, 1)

    def LeftDown(self):
        self.objdll.M_LeftDown(self.hdl)

    def LeftUp(self):
        self.objdll.M_LeftUp(self.hdl)

    def RightDown(self):
        self.objdll.M_RightDown(self.hdl)

    def RightUp(self):
        self.objdll.M_RightUp(self.hdl)

    def LeftDoubleClick(self):
        self.objdll.M_LeftDoubleClick(self.hdl, 1)

    def RightDoubleClick(self):
        self.objdll.M_RightDoubleClick(self.hdl, 1)

    def MoveR(self, rx: int, ry: int):
        self.objdll.M_MoveR(self.hdl, rx, ry)

    def KeyPressStr(self, str_: str):
        """按字符串"""
        bt_str = str_.encode("gbk")
        p_str = ctypes.c_char_p(bt_str)
        self.objdll.M_KeyInputStringGBK(self.hdl, p_str, len(bt_str))

