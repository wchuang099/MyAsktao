"""
问道脚本中控台 - 启动入口

用法:
    python main.py              # 启动GUI
    python main.py --worker 1   # 直接运行窗口1的任务
    python main.py --worker 2   # 直接运行窗口2的任务
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        # 直接运行worker进程
        if len(sys.argv) < 3:
            print("用法: python main.py --worker <window_id>")
            sys.exit(1)
        
        from src.worker import main as worker_main
        worker_main(sys.argv[2])
    
    else:
        # 启动GUI
        try:
            from PySide2.QtWidgets import QApplication
        except ImportError:
            print("错误: 需要安装 PySide2")
            print("运行: pip install PySide2")
            sys.exit(1)
        
        from src.gui import MainWindow
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        win = MainWindow()
        win.show()
        
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
