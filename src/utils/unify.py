#utils/unify.py
import time
from utils import yjs
from utils.yjs import code_dict
from collections import deque
import PyUnifyEN
from utils.paths import assets_root

class UNIFY:
    """
    一个 UNIFY 实例 = 一个虚拟机的完整能力边界
    """
    def __init__(self,vnc_port):
        self.u = PyUnifyEN.Unify()
        self.u.bsLoadDLL("Unify.dll")
        print(f"剩余点数: ",self.u.bsLogin("158496099", "F8H54C9VP951G32R"))
        self.u.bsConnect(vnc_port)
        # 加载 yolo
        onnx_path = assets_root("yolo", "best.onnx")
        self.u.yoloInit(onnx_path)

        # 统一资源根路径
        self.u.SetPath(assets_root())

        # 位图 & 字库
        self.u.LoadAllBitMap()

        self.u.LoadDict(1, "fonts/坐标字库.txt")
        self.u.LoadDict(2, "fonts/地图字库.txt")
        self.u.LoadDict(4, "fonts/通用字库.txt")
        self.u.LoadDict(5, "fonts/NPC字库.txt")
        self.u.LoadDict(6, "fonts/对话字库.txt")
        self.u.LoadDict(7, "fonts/回合字库.txt")
        self.u.LoadDict(8, "fonts/任务字库.txt")

        # ===== 绑定窗口（锚点，必须存在）=====
        result = self.u.FindPic(0, 0, 1024, 768, "客户端图标.bmp", "151515", 1.0, 0)
        _, x, y = result
        if x >= 0:
            self.u.bsSetClientLocation(x - 10, y + 61)
            print(f"✅ 窗口绑定成功")
        else:
            print(f"❌ 未找到客户端")

        # 初始化 yjs 设备
        self.yjs = yjs.get_yjs(vnc_port)
    ## ===== 双头盒子 =====
    def 左键点击(self):
        self.yjs.LeftClick()

    def 稳定左键单击(self):
        self.yjs.RightClick()
        time.sleep(0.3)
        self.yjs.LeftClick()

    def 右键点击(self):
        self.yjs.RightClick()

    def 相对移动(self, dx, dy):
        self.yjs.MoveR(dx, dy)

    def 组合键(self,*keys, hold=0.2, after=0.2):
        """
        稳定组合键：
        - 先按修饰键
        - 等待 hold 秒
        - 再按主键
        - 最后释放
        """
        codes = [code_dict[k.lower()] for k in keys]
        # 1. 按下所有键
        for code in codes:
            self.yjs.KeyDown(code)
            time.sleep(0.05)

        # 2. 关键：给系统时间识别修饰键
        time.sleep(hold)

        # 3. 释放（反序）
        for code in reversed(codes):
            self.yjs.KeyUp(code)
            time.sleep(0.05)

        time.sleep(after)

    def 按单个键(self, key):
        self.yjs.KeyPressChar(key)


    def 小延时(self):
        #休眠minTime - maxTime之间的时间.单位ms.
        self.u.otSleep(80,210)
    def 中延时(self):
        self.u.otSleep(400,800)
    def 大延时(self):
        self.u.otSleep(1500,2000)

    def 获取窗口数量(self):
        """
        return: # 例：0,136,-26|0,290,-26|0,444,-26
        """
        res = self.u.FindPicEx(-4, -38, 775, -5,"多窗口特征","101010",1.0,0)
        queue = deque()
        if not res:
            print("未找到任何窗口")
            return queue
        for item in res.split("|"):
            _, x, y = item.split(",")
            queue.append((int(x), int(y)))
        return queue

    def 逐个激活窗口(self,queue_x, queue_y):
        i = 1
        while i<5:
            self.u.MoveTo(queue_x - 30, queue_y)
            self.u.LeftClick()
            time.sleep(0.3)
            # 获取激活特征
            status, x, y = self.u.FindPic(-4, -38, 775, -5, "窗口激活特征", "101010", 0.9, 0)
            if status == 0 and abs(x - queue_x) <= 5:
                #print(f"窗口激活成功：x={queue_x} y={queue_y}")
                return True
            i = i + 1
        print(f"窗口激活失败：x={queue_x} y={queue_y}")
        return False

    def 鼠标移动(self,目标x, 目标y, 最大修正次数=2, 最大轮次=10):
        for 全局轮次 in range(最大轮次):
            self.u.MoveTo(目标x, 目标y)
            self.u.otSleep(80, 100)
            self.u.bsForceDrawing()

            for 修正次数 in range(1, 最大修正次数 + 1):
                result, x, y, w, h = self.u.yoloDetectFromWindow_Parsed(
                    目标x - 80, 目标y - 80, 目标x + 80, 目标y + 80,
                    True, 0, 0, 0, -1, 0.25, 0.45
                )

                if not result:
                    #print(f"❌ 未检测到鼠标，第{修正次数}次失败")
                    time.sleep(0.15)
                    break

                误差x, 误差y = 目标x - x, 目标y - y
                #print(f"[第{修正次数}次] 偏差 ({误差x},{误差y})")

                if abs(误差x) < 5 and abs(误差y) < 5:
                    #print("✅ 修正完成")
                    return True

                self.相对移动(int(误差x), int(误差y))
                time.sleep(0.25)
                self.u.bsForceDrawing()

            #print("⚙️ 全局修正失败，尝试下一轮")
            self.u.MoveTo(350, -50) # 窗口做了绑定，“绝对移动只能用 unify，双头盒子不知道窗口坐标系”
            time.sleep(0.3)

        print("❌ 鼠标校准失败，放弃本次操作")
        return False

    def 角色移动检测(self):
        """
        return: True
        """
        self.u.GetNowDict()
        self.u.UseDict(1)

        last_coord = self.u.Ocr(0, 0, 122, 23, color="ffffff-050505")
        print(last_coord)
        while True:
            time.sleep(1)
            coord = self.u.Ocr(0, 0, 122, 23, color="ffffff-050505")

            if coord != last_coord:
                print(f"移动中: {last_coord} -> {coord}")
                last_coord = coord
            else:
                print(f"停止移动: {coord}")
                moving = True
                # 如果只想检测一次停止可以 break
                return moving
    def 获取血量(self):
        """
        当前血量/血条总长度 *100 = 百分比
        :return:
        """
        # 方案一：获取颜色数量: 不合适透明血条，有背景干扰极其不准确
        # res = u.GetColorNum(697,24,788,41,"a50808-101010",0.1)
        # #总数量177
        # 当前血量 = (res/177) *100
        # print(当前血量)
        # 方案二: 通过查找血条最右边颜色
        # 血条区域
        x1, y1, x2, y2 = 699, 27, 785, 38
        # 血条总长度
        血条总长度 = x2 - x1

        # 查找血条最右边红色像素

        res = self.u.FindColor(x1, y1, x2, y2,
                          "a51810-202020|e6b6b5-202020|ce1c19-202020|7b0800-202020|ef1c10-202020|7b0800-202020", 0.9, 2)

        if res is None:
            print("未找到血条颜色，血量可能为0")
            return 0

        _, x, y = res
        当前血量 = (x - x1) / 血条总长度 * 100
        print(f"当前血量：{当前血量:.0f}%")
        return 当前血量


    def 获取蓝量(self):
        """
        当前蓝量/蓝条总长度 *100 = 百分比
        :return:
        """
        # 方案一：获取颜色数量: 不合适透明蓝条，有背景干扰极其不准确
        # res = u.GetColorNum(697,24,788,41,"a50808-101010",0.1)
        # #总数量177
        # 当前蓝量 = (res/177) *100
        # print(当前蓝量)
        # 方案二: 通过查找蓝条最右边颜色
        # 蓝条区域
        x1, y1, x2, y2 = 697, 40, 785, 53
        # 蓝条总长度
        蓝条总长度 = x2 - x1

        # 查找蓝条最右边红色像素
        res = self.u.FindColor(x1, y1, x2, y2, "2159b5-202020|00356b-202020|4275c5-202020|21599c-202020", 0.9, 2)
        if res is None:
            print("未找到蓝条颜色，蓝量可能为0")
            return 0

        _, x, y = res
        当前蓝量 = (x - x1) / 蓝条总长度 * 100
        print(f"当前蓝量：{当前蓝量:.0f}%")
        return 当前蓝量


# def 鼠标移动(u,目标x, 目标y, 最大修正次数=5):
#     while True:
#         u.MoveTo(目标x, 目标y)
#         u.otSleep(80, 100)
#         u.bsForceDrawing()
#
#         for 修正次数 in range(1, 最大修正次数 + 1):
#             result, x, y, w, h = u.yoloDetectFromWindow_Parsed(
#                 目标x - 80, 目标y - 80, 目标x + 80, 目标y + 80,
#                 True, 0, 0, 0, -1, 0.25, 0.45
#             )
#
#             if not result:
#                 print(f"❌ 未检测到鼠标，第{修正次数}次失败")
#                 u.bsForceDrawing()
#                 time.sleep(0.1)
#                 u.MoveTo(-1, -1)
#                 break
#
#             误差x, 误差y = 目标x - x, 目标y - y
#             print(f"[第{修正次数}次] 偏差 ({误差x},{误差y})")
#
#             if abs(误差x) < 5 and abs(误差y) < 5:
#                 print("✅ 修正完成")
#                 return True
#             yjs.MoveR(int(误差x), int(误差y))
#             time.sleep(0.3)
#             u.bsForceDrawing()
#
#         print("⚙️ 重新尝试全局修正 ...")
#         u.MoveTo(-1, -1)
