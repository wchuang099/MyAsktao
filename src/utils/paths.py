from pathlib import Path
import sys

_PROJECT_NAME = "MyAsktao"


def project_root(*parts, check: bool = False) -> str:
    """
    返回项目根目录路径，支持拼接子路径

    Args:
        *parts: 相对于项目根目录的子路径部分
        check: 是否检查路径是否存在
    """
    # 获取根目录路径
    if getattr(sys, "frozen", False):
        root_path = Path(sys._MEIPASS)
    else:
        p = Path(__file__).resolve()
        for parent in p.parents:
            if parent.name == _PROJECT_NAME:
                root_path = parent
                break
        else:
            raise RuntimeError("无法定位项目根目录（未找到 MyScript）")

    # 如果有额外的路径部分，继续拼接
    if parts:
        path = root_path.joinpath(*parts)
    else:
        path = root_path

    if check and not path.exists():
        raise FileNotFoundError(f"路径不存在: {path}")

    return str(path)


def assets_root(*parts, check: bool = True) -> str:
    """
    返回 assets 目录下指定子路径的完整路径

    Args:
        *parts: 相对于 assets 目录的子路径部分
        check: 是否检查路径是否存在

    Returns:
        完整路径字符串
    """
    root = Path(project_root())
    path = root / "assets"

    if parts:
        path = path.joinpath(*parts)

    if check and not path.exists():
        raise FileNotFoundError(f"资源不存在: {path}")

    return str(path)


def src_root(*parts, check: bool = True) -> str:
    """
    返回 src 目录下指定子路径的完整路径

    Args:
        *parts: 相对于 src 目录的子路径部分
        check: 是否检查路径是否存在
    """
    root = Path(project_root())
    path = root / "src"

    if parts:
        path = path.joinpath(*parts)

    if check and not path.exists():
        raise FileNotFoundError(f"源码路径不存在: {path}")

    return str(path)


def config_root(*parts, check: bool = True) -> str:
    """
    返回 config 目录下指定子路径的完整路径

    Args:
        *parts: 相对于 config 目录的子路径部分
        check: 是否检查路径是否存在
    """
    root = Path(project_root())
    path = root / "config"

    if parts:
        path = path.joinpath(*parts)

    if check and not path.exists():
        raise FileNotFoundError(f"配置路径不存在: {path}")

    return str(path)


def logs_root(*parts, check: bool = False) -> str:
    """
    返回 logs 目录下指定子路径的完整路径

    Args:
        *parts: 相对于 logs 目录的子路径部分
        check: 是否检查路径是否存在
    """
    root = Path(project_root())
    path = root / "logs"

    if parts:
        path = path.joinpath(*parts)

    if check and not path.exists():
        # 日志目录通常可以不存在，默认不检查
        raise FileNotFoundError(f"日志路径不存在: {path}")

    return str(path)


# # 获取 src 目录
# src_dir = src_root()
#
# # 获取 src/utils 目录
# utils_dir = src_root("utils")
#
# # 获取 src/models/user.py 文件
# user_model = src_root("models", "user.py")
#
# # 获取 config/settings.yaml 文件
# settings = config_root("settings.yaml")
#
# # 获取 logs/2023/app.log 文件（不检查是否存在）
# log_file = logs_root("2023", "app.log", check=False)
#
# # 获取项目根目录下的 README.md 文件（需要修改 project_root 支持拼接）
# readme = project_root("README.md", check=True)