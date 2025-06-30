"""
日志管理模块
提供统一的日志配置和管理功能
"""
import sys
from pathlib import Path
from loguru import logger
from ..config import config


def setup_logger():
    """设置日志配置"""
    # 移除默认的日志处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    log_file = Path(config.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        level=config.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8"
    )
    
    return logger


def get_logger(name: str = None):
    """获取日志记录器"""
    if name:
        return logger.bind(name=name)
    return logger


# 初始化日志配置
setup_logger()

# 导出默认日志记录器
__all__ = ["get_logger", "logger"]
