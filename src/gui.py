# gui.py
"""
问道脚本中控台 - GUI界面

功能：
1. 多窗口任务管理（5窗口）
2. 任务链可视化配置
3. 实时状态显示
4. 单任务/任务链执行
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
    
    # 任务名称映射（中文显示名 -> 任务key）
    TASK_DISPLAY_NAMES = {
        "师门任务": "shimen",
        "帮派任务": "bangpai",
        "副本任务": "fuben",
        "叛逆任务": "pani",
    }
    
    # 任务key -> 中文显示名
    TASK_KEY_NAMES = {
        "shimen": "师门任务",
        "bangpai": "帮派任务",
        "fuben": "副本任务",
        "pani": "叛逆任务",
    }
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("问道脚本中控台 v1.0")
        self.resize(1000, 650)
        
        self.processes = {}
        self.window_configs = {}
        
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
        table_group = QGroupBox("窗口列表")
        table_layout = QVBoxLayout()
        
        self.table = QTableWidget(5, 5)
        self.table.setHorizontalHeaderLabels([
            "索引", "VNC端口", "PID/VID", "当前任务", "状态"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_menu)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 只读
        
        # 设置列宽
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 80)
        
        table_layout.addWidget(self.table)
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group)
        
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
            "师门任务",
            "帮派任务",
            "副本任务",
            "叛逆任务",
        ])
        self.all_tasks_list.setMinimumHeight(80)
        config_layout.addWidget(QLabel("可选任务:"))
        config_layout.addWidget(self.all_tasks_list)
        
        # 中间：添加/移除按钮
        btn_layout = QVBoxLayout()
        btn_layout.addStretch()
        self.btn_add = QPushButton("→ 添加")
        self.btn_remove = QPushButton("← 移除")
        self.btn_clear = QPushButton("清空")
        self.btn_save = QPushButton("保存配置")
        self.btn_add.setMinimumWidth(80)
        self.btn_remove.setMinimumWidth(80)
        self.btn_clear.setMinimumWidth(80)
        self.btn_save.setMinimumWidth(80)
        self.btn_add.clicked.connect(self.add_task_to_chain)
        self.btn_remove.clicked.connect(self.remove_task_from_chain)
        self.btn_clear.clicked.connect(self.clear_chain)
        self.btn_save.clicked.connect(self.save_configs)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch()
        config_layout.addLayout(btn_layout)
        
        # 已选任务列表（右侧执行顺序）
        self.chain_list = QListWidget()
        self.chain_list.setMaximumWidth(180)
        self.chain_list.setMinimumHeight(80)
        self.chain_list.setDragDropMode(QAbstractItemView.InternalMove)
        config_layout.addWidget(QLabel("执行顺序:"))
        config_layout.addWidget(self.chain_list)
        
        # 预设方案
        preset_layout = QVBoxLayout()
        preset_layout.addWidget(QLabel("预设方案:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("自定义")
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        config_layout.addLayout(preset_layout)
        
        # 预设配置（从配置文件加载）
        self.presets = {}
        
        config_layout.addStretch()
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # ===== 底部：控制按钮 =====
        btn_group = QHBoxLayout()
        
        self.btn_start_all = QPushButton("启动全部")
        self.btn_stop_all = QPushButton("停止全部")
        self.btn_pause_all = QPushButton("暂停全部")
        self.btn_start_all.setMinimumWidth(100)
        self.btn_stop_all.setMinimumWidth(100)
        self.btn_pause_all.setMinimumWidth(100)
        
        self.btn_start_all.clicked.connect(self.start_all_tasks)
        self.btn_stop_all.clicked.connect(self.stop_all_tasks)
        self.btn_pause_all.clicked.connect(self.pause_all_tasks)
        
        btn_group.addWidget(self.btn_start_all)
        btn_group.addWidget(self.btn_pause_all)
        btn_group.addWidget(self.btn_stop_all)
        btn_group.addStretch()
        
        # 状态栏
        self.status_label = QLabel("就绪")
        btn_group.addWidget(self.status_label)
        
        main_layout.addLayout(btn_group)
    
    def add_row(self, i):
        """添加窗口行"""
        self.table.insertRow(i)
        
        self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
        self.table.setItem(i, 1, QTableWidgetItem(str(100 + i + 1)))  # VNC端口
        self.table.setItem(i, 2, QTableWidgetItem(""))  # PID/VID
        self.table.setItem(i, 3, QTableWidgetItem("无"))
        self.table.setItem(i, 4, QTableWidgetItem("未运行"))
        
        # 设置对齐
        for col in range(5):
            item = self.table.item(i, col)
            if item:
                item.setTextAlignment(Qt.AlignCenter)
    
    def load_configs(self):
        """加载配置"""
        import configparser
        
        # 加载任务链配置
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "task_chain.json"
        )
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 加载预设方案
                if "presets" in data:
                    self.presets = data["presets"]
                    # 更新下拉框
                    self.preset_combo.blockSignals(True)
                    for preset_name in self.presets.keys():
                        self.preset_combo.addItem(preset_name)
                    self.preset_combo.blockSignals(False)
                
                # 更新任务链列表显示
                if "chain_list" in data:
                    self.chain_list.clear()
                    for task_key in data["chain_list"]:
                        display_name = self.TASK_KEY_NAMES.get(task_key, task_key)
                        self.chain_list.addItem(display_name)
                
            except Exception as e:
                print(f"加载任务链配置失败: {e}")
        
        # 从 config.ini 加载 VNC/PID/VID 配置
        ini_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "config.ini"
        )
        if os.path.exists(ini_file):
            try:
                cfg = configparser.ConfigParser()
                cfg.read(ini_file, encoding="utf-8")
                
                # 更新表格中的 PID/VID
                for row in range(self.table.rowCount()):
                    port = str(100 + row + 1)
                    if cfg.has_option("yjs", port):
                        pid_vid = cfg.get("yjs", port)
                        if pid_vid:
                            self.table.setItem(row, 2, QTableWidgetItem(pid_vid))
                
            except Exception as e:
                print(f"加载YJS配置失败: {e}")
    
    def save_configs(self):
        """保存配置"""
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "task_chain.json"
        )
        
        # 读取现有配置
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = {}
        else:
            data = {}
        
        # 更新任务链配置
        chain_items = []
        for i in range(self.chain_list.count()):
            display_name = self.chain_list.item(i).text()
            task_key = self.TASK_DISPLAY_NAMES.get(display_name, display_name)
            chain_items.append(task_key)
        
        data["chain_list"] = chain_items
        
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"配置已保存: {chain_items}")
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    # =========================
    # 任务链配置
    # =========================
    
    def add_task_to_chain(self):
        """添加任务到执行链"""
        current_row = self.all_tasks_list.currentRow()
        if current_row >= 0:
            task_name = self.all_tasks_list.item(current_row).text()
            self.chain_list.addItem(task_name)
            self.preset_combo.setCurrentIndex(0)  # 切换到自定义
    
    def remove_task_from_chain(self):
        """从执行链移除任务"""
        current_row = self.chain_list.currentRow()
        if current_row >= 0:
            self.chain_list.takeItem(current_row)
            self.preset_combo.setCurrentIndex(0)
    
    def clear_chain(self):
        """清空任务链"""
        self.chain_list.clear()
        self.preset_combo.setCurrentIndex(0)
    
    def on_preset_changed(self, index):
        """预设方案选择"""
        if index == 0:
            return  # 自定义，不做处理
        
        preset_name = self.preset_combo.currentText()
        if preset_name in self.presets:
            self.chain_list.clear()
            for task_key in self.presets[preset_name]:
                display_name = self.TASK_KEY_NAMES.get(task_key, task_key)
                self.chain_list.addItem(display_name)
    
    def get_current_chain(self):
        """获取当前任务链"""
        chain = []
        for i in range(self.chain_list.count()):
            display_name = self.chain_list.item(i).text()
            task_key = self.TASK_DISPLAY_NAMES.get(display_name, display_name)
            chain.append(task_key)
        return chain
    
    # =========================
    # 右键菜单
    # =========================
    
    def show_menu(self, pos):
        """显示右键菜单"""
        row = self.table.currentRow()
        if row == -1:
            return
        
        menu = QMenu()
        
        # 单任务执行
        single_menu = menu.addMenu("执行单个任务")
        single_menu.addAction("师门任务", lambda: self.run_single_task(row, "shimen"))
        single_menu.addAction("帮派任务", lambda: self.run_single_task(row, "bangpai"))
        single_menu.addAction("副本任务", lambda: self.run_single_task(row, "fuben"))
        single_menu.addAction("叛逆任务", lambda: self.run_single_task(row, "pani"))
        
        menu.addSeparator()
        
        menu.addAction("启动任务链", lambda: self.run_chain(row))
        menu.addAction("停止", lambda: self.stop_task(row))
        
        menu.addSeparator()
        
        menu.addAction("配置窗口...", lambda: self.show_config_dialog(row))
        menu.addAction("刷新状态", lambda: self.refresh_status(row))
        
        menu.exec_(self.table.viewport().mapToGlobal(pos))
    
    def show_config_dialog(self, row):
        """显示配置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"配置窗口_{row + 1}")
        dialog.resize(350, 200)
        
        layout = QFormLayout()
        
        # VNC端口
        vnc_port = QSpinBox()
        vnc_port.setRange(100, 999)
        current_port = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        vnc_port.setValue(int(current_port) if current_port.isdigit() else 100 + row)
        layout.addRow("VNC端口:", vnc_port)
        
        # PID/VID（双头盒子）
        pid_vid = QLineEdit()
        pid_vid.setPlaceholderText("如: 0xC216,0x0102")
        pid_vid.setText(self.table.item(row, 2).text() if self.table.item(row, 2) else "")
        layout.addRow("PID/VID:", pid_vid)
        
        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # 保存配置
            self.table.setItem(row, 1, QTableWidgetItem(str(vnc_port.value())))
            self.table.setItem(row, 2, QTableWidgetItem(pid_vid.text()))
            self.save_configs()
    
    def refresh_status(self, row):
        """刷新状态"""
        if row in self.processes and self.processes[row].state() == QProcess.Running:
            self.table.setItem(row, 4, QTableWidgetItem("运行中"))
        else:
            self.table.setItem(row, 4, QTableWidgetItem("未运行"))
            self.table.setItem(row, 3, QTableWidgetItem("无"))
    
    # =========================
    # 启动/停止任务
    # =========================
    
    def run_single_task(self, row, task_key):
        """执行单个任务"""
        window_id = row + 1
        task_display = self.TASK_KEY_NAMES.get(task_key, task_key)
        
        # 保存任务配置
        self.save_task_config(window_id, [task_key])
        
        # 启动进程
        self.start_process(row)
        
        self.update_status(row, task_display, "运行中")
        self.status_label.setText(f"窗口{window_id}执行{task_display}")
    
    def run_chain(self, row):
        """启动任务链"""
        window_id = row + 1
        
        # 获取当前任务链
        task_chain = self.get_current_chain()
        
        if not task_chain:
            QMessageBox.warning(self, "提示", "请先配置任务链")
            return
        
        # 保存任务配置
        self.save_task_config(window_id, task_chain)
        
        # 启动进程
        self.start_process(row)
        
        self.update_status(row, "→".join(self.get_current_chain()[:2]) + "...", "运行中")
        self.status_label.setText(f"窗口{window_id}执行任务链")
    
    def start_all_tasks(self):
        """启动全部任务"""
        task_chain = self.get_current_chain()
        
        if not task_chain:
            QMessageBox.warning(self, "提示", "请先配置任务链")
            return
        
        running_count = 0
        for row in range(self.table.rowCount()):
            if self.table.item(row, 4).text() == "未运行":
                window_id = row + 1
                self.save_task_config(window_id, task_chain)
                self.start_process(row)
                self.update_status(row, task_chain[0], "运行中")
                running_count += 1
        
        self.status_label.setText(f"已启动 {running_count} 个窗口")
    
    def stop_all_tasks(self):
        """停止全部任务"""
        for row in list(self.processes.keys()):
            self.stop_task(row)
        self.status_label.setText("已停止全部")
    
    def pause_all_tasks(self):
        """暂停全部任务"""
        for row, proc in self.processes.items():
            if proc.state() == QProcess.Running:
                proc.suspend()
                self.update_status(row, self.table.item(row, 3).text(), "已暂停")
        self.status_label.setText("已暂停全部")
    
    def save_task_config(self, window_id, tasks):
        """保存任务配置"""
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "task_chain.json"
        )
        
        # 读取现有配置（保留 presets 和 chain_list）
        data = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass
        
        # 确保 data 是字典
        if not isinstance(data, dict):
            data = {}
        
        # 获取VNC端口配置
        row = window_id - 1
        vnc_port = self.table.item(row, 1).text() if self.table.item(row, 1) else str(100 + window_id)
        pid_vid = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        
        # 只更新指定端口的配置，保留其他字段
        data[vnc_port] = {
            "pid_vid": pid_vid,
            "task_flow": tasks,
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
        process.readyReadStandardError.connect(
            lambda: self.read_error(row, process)
        )
        process.finished.connect(lambda code, status: self.on_finished(row, code, status))
        
        # 使用绝对路径
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "src", "worker.py"
        )
        
        process.start("python", [script_path, str(window_id)])
        
        self.processes[row] = process
        self.update_status(row, self.table.item(row, 3).text() or "准备中", "运行中")
    
    def stop_task(self, row):
        """停止任务"""
        if row in self.processes:
            proc = self.processes[row]
            if proc.state() != QProcess.NotRunning:
                proc.kill()
                proc.waitForFinished(1000)
            del self.processes[row]
        
        self.update_status(row, "无", "已停止")
    
    def update_status(self, row, task, status):
        """更新状态"""
        self.table.setItem(row, 3, QTableWidgetItem(task))
        self.table.setItem(row, 4, QTableWidgetItem(status))
    
    # =========================
    # 进程输出处理
    # =========================
    
    def read_output(self, row, process):
        """读取进程输出"""
        data = process.readAllStandardOutput().data().decode('utf-8', errors='ignore').strip()
        
        if not data:
            return
        
        # 日志已在worker中添加端口标识，直接打印
        print(data)
        
        # 解析任务状态
        if "当前任务" in data:
            task = data.split("当前任务:")[-1].strip()
            if "登录" in task:
                self.update_status(row, "登录", "运行中")
            elif "师门" in task:
                self.update_status(row, "师门", "运行中")
            elif "帮派" in task:
                self.update_status(row, "帮派", "运行中")
            elif "副本" in task:
                self.update_status(row, "副本", "运行中")
            elif "叛逆" in task:
                self.update_status(row, "叛逆", "运行中")
        
        if "任务完成" in data:
            self.update_status(row, "完成", "完成")
        
        if "任务执行完毕" in data or "进程结束" in data:
            self.update_status(row, "无", "完成")
        
        if "错误" in data or "失败" in data:
            self.update_status(row, "错误", "异常")
    
    def read_error(self, row, process):
        """读取进程错误"""
        data = process.readAllStandardError().data().decode('utf-8', errors='ignore').strip()
        if data:
            # 日志已在worker中添加端口标识，直接打印
            print(data)
    
    def on_finished(self, row, code, status):
        """进程结束"""
        if row in self.processes:
            del self.processes[row]
        
        current_status = self.table.item(row, 4).text() if self.table.item(row, 4) else ""
        if current_status == "运行中":
            self.update_status(row, "无", "完成")
        
        # 检查是否还有运行中的进程
        running = sum(1 for p in self.processes.values() if p.state() == QProcess.Running)
        self.status_label.setText(f"运行中: {running} 个窗口")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止所有进程
        for row in list(self.processes.keys()):
            self.stop_task(row)
        
        # 保存配置
        self.save_configs()
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    win = MainWindow()
    win.show()
    
    sys.exit(app.exec_())
