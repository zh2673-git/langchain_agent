"""
自定义工具：实用工具集
提供各种实用的小工具功能
"""

import random
import string
import hashlib
import base64
import uuid
from datetime import datetime, timedelta
from langchain_core.tools import tool
from backend.tools.adapters.universal_tool_adapter import universal_adapter
import logging

logger = logging.getLogger(__name__)


@tool
def generate_password(length: int = 12, include_symbols: bool = True) -> str:
    """
    生成随机密码
    
    Args:
        length: 密码长度，默认12位
        include_symbols: 是否包含特殊符号
    
    Returns:
        生成的密码
    """
    try:
        if length < 4:
            return "❌ 密码长度至少为4位"
        if length > 128:
            return "❌ 密码长度不能超过128位"
        
        # 字符集
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?" if include_symbols else ""
        
        # 确保至少包含每种类型的字符
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits)
        ]
        
        if include_symbols:
            password.append(random.choice(symbols))
        
        # 填充剩余长度
        all_chars = lowercase + uppercase + digits + symbols
        for _ in range(length - len(password)):
            password.append(random.choice(all_chars))
        
        # 随机打乱
        random.shuffle(password)
        
        result_password = ''.join(password)
        
        return f"🔐 生成的密码: {result_password}\n\n密码强度信息:\n- 长度: {length}位\n- 包含大写字母: ✅\n- 包含小写字母: ✅\n- 包含数字: ✅\n- 包含特殊符号: {'✅' if include_symbols else '❌'}"
        
    except Exception as e:
        return f"❌ 密码生成失败: {str(e)}"


@tool
def hash_text(text: str, algorithm: str = "md5") -> str:
    """
    计算文本的哈希值
    
    Args:
        text: 要计算哈希的文本
        algorithm: 哈希算法 (md5, sha1, sha256, sha512)
    
    Returns:
        哈希值
    """
    try:
        text_bytes = text.encode('utf-8')
        
        if algorithm == "md5":
            hash_obj = hashlib.md5(text_bytes)
        elif algorithm == "sha1":
            hash_obj = hashlib.sha1(text_bytes)
        elif algorithm == "sha256":
            hash_obj = hashlib.sha256(text_bytes)
        elif algorithm == "sha512":
            hash_obj = hashlib.sha512(text_bytes)
        else:
            return f"❌ 不支持的算法: {algorithm}，支持: md5, sha1, sha256, sha512"
        
        hash_value = hash_obj.hexdigest()
        
        return f"🔒 {algorithm.upper()}哈希值:\n{hash_value}\n\n原文: {text[:50]}{'...' if len(text) > 50 else ''}"
        
    except Exception as e:
        return f"❌ 哈希计算失败: {str(e)}"


@tool
def encode_decode_text(text: str, operation: str = "base64_encode") -> str:
    """
    编码/解码文本
    
    Args:
        text: 要处理的文本
        operation: 操作类型 (base64_encode, base64_decode, url_encode, url_decode)
    
    Returns:
        处理结果
    """
    try:
        if operation == "base64_encode":
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return f"📝 Base64编码结果:\n{encoded}"
        
        elif operation == "base64_decode":
            try:
                decoded = base64.b64decode(text).decode('utf-8')
                return f"📖 Base64解码结果:\n{decoded}"
            except Exception:
                return "❌ Base64解码失败，请检查输入格式"
        
        elif operation == "url_encode":
            import urllib.parse
            encoded = urllib.parse.quote(text)
            return f"🔗 URL编码结果:\n{encoded}"
        
        elif operation == "url_decode":
            import urllib.parse
            decoded = urllib.parse.unquote(text)
            return f"🔓 URL解码结果:\n{decoded}"
        
        else:
            return f"❌ 未知操作: {operation}，支持: base64_encode, base64_decode, url_encode, url_decode"
        
    except Exception as e:
        return f"❌ 编码/解码失败: {str(e)}"


def generate_uuid(version: int = 4) -> str:
    """
    生成UUID
    
    Args:
        version: UUID版本 (1, 4)
    
    Returns:
        生成的UUID
    """
    try:
        if version == 1:
            generated_uuid = str(uuid.uuid1())
            return f"🆔 UUID v1 (基于时间): {generated_uuid}"
        elif version == 4:
            generated_uuid = str(uuid.uuid4())
            return f"🆔 UUID v4 (随机): {generated_uuid}"
        else:
            return f"❌ 不支持的UUID版本: {version}，支持: 1, 4"
        
    except Exception as e:
        return f"❌ UUID生成失败: {str(e)}"


def date_calculator(start_date: str, operation: str = "add", days: int = 1) -> str:
    """
    日期计算器
    
    Args:
        start_date: 起始日期，格式: YYYY-MM-DD
        operation: 操作类型 (add, subtract, diff)
        days: 天数
    
    Returns:
        计算结果
    """
    try:
        # 解析日期
        start = datetime.strptime(start_date, "%Y-%m-%d")
        
        if operation == "add":
            result_date = start + timedelta(days=days)
            return f"📅 日期计算结果:\n{start_date} + {days}天 = {result_date.strftime('%Y-%m-%d')}"
        
        elif operation == "subtract":
            result_date = start - timedelta(days=days)
            return f"📅 日期计算结果:\n{start_date} - {days}天 = {result_date.strftime('%Y-%m-%d')}"
        
        elif operation == "diff":
            today = datetime.now()
            diff = (today - start).days
            return f"📅 日期差计算:\n{start_date} 到今天相差 {abs(diff)} 天"
        
        else:
            return f"❌ 未知操作: {operation}，支持: add, subtract, diff"
        
    except ValueError:
        return f"❌ 日期格式错误，请使用 YYYY-MM-DD 格式，如: 2024-01-01"
    except Exception as e:
        return f"❌ 日期计算失败: {str(e)}"


# 注册到统一适配器
def register_utility_tools():
    """注册实用工具到统一适配器"""
    try:
        # 注册UUID生成工具
        universal_adapter.register_tool(
            name="generate_uuid",
            function=generate_uuid,
            description="生成UUID（通用唯一标识符）",
            parameters={
                "type": "object",
                "properties": {
                    "version": {
                        "type": "integer",
                        "description": "UUID版本",
                        "enum": [1, 4],
                        "default": 4
                    }
                },
                "required": []
            }
        )
        
        # 注册日期计算工具
        universal_adapter.register_tool(
            name="date_calculator",
            function=date_calculator,
            description="日期计算器，支持日期加减和差值计算",
            parameters={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "起始日期，格式: YYYY-MM-DD"
                    },
                    "operation": {
                        "type": "string",
                        "description": "操作类型",
                        "enum": ["add", "subtract", "diff"],
                        "default": "add"
                    },
                    "days": {
                        "type": "integer",
                        "description": "天数",
                        "default": 1
                    }
                },
                "required": ["start_date"]
            }
        )
        
        logger.info("Utility tools registered successfully")
    except Exception as e:
        logger.error(f"Failed to register utility tools: {e}")


# 自动注册
register_utility_tools()

# 导出工具
__all__ = ["generate_password", "hash_text", "encode_decode_text", "generate_uuid", "date_calculator"]
