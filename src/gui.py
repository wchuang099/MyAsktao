# gui.py
"""
问道脚本中控台 - GUI界面

参考梦幻开发的UI设计：
1. 多窗口任务管理
2. 任务链配置
3. 实时状态显示
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import json


class MainWindow(QMainWindow):
    """问道脚本主窗口"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("问道脚本中控台 v1.0")
        self.resize(1000, 600)

        self.processes = {}
        self.task_configs = {}

        self.init_ui()
        self.load_configs()

    def init_ui(self):
        """初始化UI"""
        # 创建中心部件
        central = QWidget()
        self.setCentralWidget(central)

        # 主布局
        main_layout = QVBoxLayout(central)

        # ===== 顶部：窗口表格 =====
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "索引", "窗口名称", "VNC端口", "账号", "等级",
            "当前任务", "进度", "状态"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_menu)
        self.table.verticalHeader().setVisible(False)  # 隐藏行号

        main_layout.addWidget(self.table)

        # 初始化5个窗口行
        for i in range(5):
            self.add_row(i)

        # ===== 中部：任务链配置 =====
        config_group = QGroupBox("任务链配置")
        config_layout = QHBoxLayout()

        # 任务列表（左侧全部任务）
        self.all_tasks_list = QListWidget()
        self.all_tasks_list.setMaximumWidth(150)
        self.all_tasks_list.addItems([
            "登录",
            "师门任务",
            "帮派任务",
            "日常任务",
            "副本任务",
        ])
        config_layout.addWidget(QLabel("可选任务:"))
        config_layout.addWidget(self.all_tasks_list)

        # 中间：添加/移除按钮
        btn_layout = QVBoxLayout()
        self.btn_add = QPushButton("→ 添加")
        self.btn_remove = QPushButton("← 移除")
        self.btn_add.clicked.connect(self.add_task_to_chain)
        self.btn_remove.clicked.connect(self.remove_task_from_chain)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        config_layout.addLayout(btn_layout)

        # 已选任务列表（右侧执行顺序）
        self.chain_list = QListWidget()
        self.chain_list.setMaximumWidth(150)
        self.chain_list.addItems([
            "登录", "师门任务", "帮派任务", "副本任务"
        ])
        config_layout.addWidget(QLabel("执行顺序:"))
        config_layout.addWidget(self.chain_list)

        # 保存按钮
        self.btn_save = QPushButton("保存配置")
        self.btn_save.clicked.connect(self.save_task_chain)
        config_layout.addWidget(self.btn_save)

        config_layout.addStretch()
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # ===== 底部：控制按钮 =====
        btn_group = QHBoxLayout()

        self.btn_start_all = QPushButton("启动全部")
        self.btn_stop_all = QPushButton("停止全部")
        self.btn_start_all.clicked.connect(self.start_all_tasks)
        self.btn_stop_all.clicked.connect(self.stop_all_tasks)

        btn_group.addWidget(self.btn_start_all)
        btn_group.addWidget(self.btn_stop_all)
        btn_group.addStretch()

        main_layout.addLayout(btn_group)

    def add_row(self, i):
        """添加窗口行"""
        self.table.insertRow(i)

        self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
        self.table.setItem(i, 1, QTableWidgetItem(f"窗口_{i + 1}"))
        self.table.setItem(i, 2, QTableWidgetItem(f"10{i + 2}"))  # VNC端口
        self.table.setItem(i, 3, QTableWidgetItem(""))
        self.table.setItem(i, 4, QTableWidgetItem("0"))
        self.table.setItem(i, 5, QTableWidgetItem("无"))
        self.table.setItem(i, 6, QTableWidgetItem(""))
        self.table.setItem(i, 7, QTableWidgetItem("未运行"))

        # 设置对齐
        for col in range(8):
            item = self.table.item(i, col)
            if item:
                item.setTextAlignment(Qt.AlignCenter)

    def load_configs(self):
        """加载配置"""
        config_file = "task_chain.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 更新窗口配置
                for key, config in data.items():
                    row = int(key.split("_")[1]) - 1
                    if 0 <= row < self.table.rowCount():
                        self.table.setItem(row, 2, QTableWidgetItem(config.get("vnc_port", "")))
                        self.table.setItem(row, 3, QTableWidgetItem(config.get("account", "")))
            except Exception as e:
                print(f"加载配置失败: {e}")

    # =========================
    # 任务链配置
    # =========================

    def add_task_to_chain(self):
        """添加任务到执行链"""
        current_row = self.all_tasks_list.currentRow()
        if current_row >= 0:
            task_name = self.all_tasks_list.item(current_row).text()
            self.chain_list.addItem(task_name)

    def remove_task_from_chain(self):
        """从执行链移除任务"""
        current_row = self.chain_list.currentRow()
        if current_row >= 0:
            self.chain_list.takeItem(current_row)

    def save_task_chain(self):
        """保存任务链配置"""
        chain_items = []
        for i in range(self.chain_list.count()):
            chain_items.append(self.chain_list.item(i).text())

        print(f"保存任务链: {chain_items}")
        # TODO: 保存到配置文件

    # =========================
    # 右键菜单
    # =========================

    def show_menu(self, pos):
        """显示右键菜单"""
        row = self.table.currentRow()
        if row == -1:
            return

        menu = QMenu()

        # 执行任务链子菜单
        chain_menu = menu.addMenu("执行任务链")

        # 预设任务链
        chain_menu.addAction("师门 → 帮派 → 副本",
                             lambda: self.run_chain(row, ["login", "shimen", "bangpai", "fuben"]))
        chain_menu.addAction("师门 → 帮派",
                             lambda: self.run_chain(row, ["login", "shimen", "bangpai"]))
        chain_menu.addAction("仅师门",
                             lambda: self.run_chain(row, ["login", "shimen"]))
        chain_menu.addAction("仅帮派",
                             lambda: self.run_chain(row, ["login", "bangpai"]))
        chain_menu.addAction("仅副本",
                             lambda: self.run_chain(row, ["login", "fuben"]))

        menu.addSeparator()

        # 单任务执行
        single_menu = menu.addMenu("执行单个任务")
        single_menu.addAction("登录", lambda: self.run_chain(row, ["login"]))
        single_menu.addAction("师门任务", lambda: self.run_chain(row, ["shimen"]))
        single_menu.addAction("帮派任务", lambda: self.run_chain(row, ["bangpai"]))
        single_menu.addAction("副本任务", lambda: self.run_chain(row, ["fuben"]))

        menu.addSeparator()

        # 全部窗口
        all_menu = menu.addMenu("全部窗口")
        all_menu.addAction("全部启动师门", lambda: self.run_all(["login", "shimen"]))
        all_menu.addAction("全部启动帮派", lambda: self.run_all(["login", "bangpai"]))
        all_menu.addAction("全部停止", self.stop_all_tasks)

        menu.addSeparator()

        menu.addAction("停止当前窗口", lambda: self.stop_task(row))
        menu.addAction("配置窗口...", lambda: self.show_config_dialog(row))

        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def show_config_dialog(self, row):
        """显示配置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"配置窗口_{row + 1}")
        dialog.resize(400, 300)

        layout = QFormLayout()

        # VNC端口
        vnc_port = QSpinBox()
        vnc_port.setRange(100, 999)
        vnc_port.setValue(102 + row)
        layout.addRow("VNC端口:", vnc_port)

        # 账号
        account = QLineEdit()
        layout.addRow("账号:", account)

        # 密码
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        layout.addRow("密码:", password)

        # 服务器
        server = QLineEdit()
        layout.addRow("服务器:", server)

        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            # 保存配置
            self.table.setItem(row, 2, QTableWidgetItem(str(vnc_port.value())))
            self.table.setItem(row, 3, QTableWidgetItem(account.text()))
            self.save_configs()

    def save_configs(self):
        """保存配置"""
        config_file = "task_chain.json"
        data = {}

        for row in range(self.table.rowCount()):
            window_key = f"window_{row + 1}"
            data[window_key] = {
                "vnc_port": self.table.item(row, 2).text(),
                "account": self.table.item(row, 3).text(),
            }

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    # =========================
    # 启动/停止任务
    # =========================

    def run_chain(self, row, tasks):
        """启动任务链"""
        window_id = row + 1

        # 保存任务配置
        self.save_task_config(window_id, tasks)

        # 启动进程
        self.start_process(row)

    def run_all(self, tasks):
        """启动全部窗口"""
        for row in range(self.table.rowCount()):
            self.run_chain(row, tasks)

    def start_all_tasks(self):
        """启动全部任务"""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 7).text() == "未运行":
                # 获取当前配置的任务链
                # TODO: 从配置读取
                self.run_chain(row, ["login", "shimen"])

    def stop_all_tasks(self):
        for row in list(self.processes.keys()):
            self.stop_task(row)

    def save_task_config(self, window_id, tasks):
        """保存任务配置"""
        config_file = "task_chain.json"

        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = {}
        else:
            data = {}

        data[f"window_{window_id}"] = {
            "task_flow": tasks
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def start_process(self, row):
        """启动进程"""
        window_id = row + 1

        # 先停止已有进程
        self.stop_task(row)

        # 启动新进程
        process = QProcess(self)
        process.readyReadStandardOutput.connect(
            lambda: self.read_output(row, process)
        )
        process.finished.connect(lambda: self.on_finished(row))

        # 使用绝对路径
        script_path = os.path.join(os.path.dirname(__file__), "worker.py")
        process.start("python", [script_path, str(window_id)])

        self.processes[row] = process

        self.update_status(row, "准备中", "运行中")

    def stop_task(self, row):
        """停止任务"""
        if row in self.processes:
            self.processes[row].kill()
            del self.processes[row]
            self.update_status(row, "无", "已停止")

    def update_status(self, row, task, status):
        """更新状态"""
        self.table.setItem(row, 5, QTableWidgetItem(task))
        self.table.setItem(row, 7, QTableWidgetItem(status))

    def update_progress(self, row, progress):
        """更新进度"""
        self.table.setItem(row, 6, QTableWidgetItem(progress))

    # =========================
    # 进程输出处理
    # =========================

    def read_output(self, row, process):
        """读取进程输出"""
        data = process.readAllStandardOutput().data().decode().strip()

        if not data:
            return

        print(f"[窗口{row + 1}] {data}")

        # 解析任务状态
        if "当前任务" in data:
            task = data.split(":")[-1].strip()
            self.update_status(row, task, "运行中")

        if "完成" in data or "结束" in data:
            self.update_status(row, "无", "完成")

        if "进度" in data:
            # 提取进度信息
            progress = data.split("进度")[-1].strip()
            self.update_progress(row, progress)

        if "错误" in data or "失败" in data:
            self.update_status(row, "错误", "异常")

    def on_finished(self, row):
        """进程结束"""
        if row in self.processes:
            del self.processes[row]

        if self.table.item(row, 7).text() == "运行中":
            self.update_status(row, "无", "完成")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())
