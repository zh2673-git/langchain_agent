"""
自定义工具：文本处理
提供各种文本处理和分析功能
"""

import re
import json
from typing import Dict, List
from langchain_core.tools import tool
from backend.tools.adapters.universal_tool_adapter import universal_adapter
import logging

logger = logging.getLogger(__name__)


@tool
def text_statistics(text: str) -> str:
    """
    分析文本统计信息
    
    Args:
        text: 要分析的文本
    
    Returns:
        文本统计结果
    """
    try:
        # 基本统计
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        
        # 字符类型统计
        letters = sum(1 for c in text if c.isalpha())
        digits = sum(1 for c in text if c.isdigit())
        spaces = sum(1 for c in text if c.isspace())
        punctuation = char_count - letters - digits - spaces
        
        # 词频统计（前5个）
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = f"""📊 文本统计分析:
        
📏 基本信息:
- 字符数: {char_count}
- 单词数: {word_count}
- 行数: {line_count}

🔤 字符类型:
- 字母: {letters}
- 数字: {digits}
- 空格: {spaces}
- 标点: {punctuation}

🔥 高频词汇:"""
        
        for word, count in top_words:
            result += f"\n- {word}: {count}次"
        
        return result
        
    except Exception as e:
        return f"❌ 文本分析失败: {str(e)}"


@tool
def text_formatter(text: str, format_type: str = "clean") -> str:
    """
    格式化文本
    
    Args:
        text: 要格式化的文本
        format_type: 格式化类型 (clean, title, sentence, code)
    
    Returns:
        格式化后的文本
    """
    try:
        if format_type == "clean":
            # 清理多余空格和换行
            cleaned = re.sub(r'\s+', ' ', text.strip())
            return f"🧹 清理后的文本:\n{cleaned}"
        
        elif format_type == "title":
            # 标题格式化
            title = text.strip().title()
            return f"📝 标题格式:\n{title}"
        
        elif format_type == "sentence":
            # 句子格式化
            sentences = re.split(r'[.!?]+', text)
            formatted = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:].lower()
                    formatted.append(sentence)
            result = '. '.join(formatted)
            if result and not result.endswith('.'):
                result += '.'
            return f"📖 句子格式:\n{result}"
        
        elif format_type == "code":
            # 代码格式化（简单缩进）
            lines = text.split('\n')
            formatted_lines = []
            indent_level = 0
            
            for line in lines:
                line = line.strip()
                if line:
                    if line.endswith(':'):
                        formatted_lines.append('    ' * indent_level + line)
                        indent_level += 1
                    elif line in ['end', '}', ')', ']']:
                        indent_level = max(0, indent_level - 1)
                        formatted_lines.append('    ' * indent_level + line)
                    else:
                        formatted_lines.append('    ' * indent_level + line)
                else:
                    formatted_lines.append('')
            
            return f"💻 代码格式:\n" + '\n'.join(formatted_lines)
        
        else:
            return f"❌ 未知格式类型: {format_type}，支持: clean, title, sentence, code"
        
    except Exception as e:
        return f"❌ 格式化失败: {str(e)}"


def extract_information(text: str, info_type: str = "emails") -> str:
    """
    从文本中提取信息
    
    Args:
        text: 源文本
        info_type: 信息类型 (emails, urls, phones, numbers)
    
    Returns:
        提取的信息
    """
    try:
        if info_type == "emails":
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            return f"📧 邮箱地址 ({len(emails)}个):\n" + '\n'.join(f"- {email}" for email in emails) if emails else "未找到邮箱地址"
        
        elif info_type == "urls":
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
            return f"🔗 网址 ({len(urls)}个):\n" + '\n'.join(f"- {url}" for url in urls) if urls else "未找到网址"
        
        elif info_type == "phones":
            phones = re.findall(r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', text)
            return f"📞 电话号码 ({len(phones)}个):\n" + '\n'.join(f"- {phone}" for phone in phones) if phones else "未找到电话号码"
        
        elif info_type == "numbers":
            numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
            return f"🔢 数字 ({len(numbers)}个):\n" + '\n'.join(f"- {num}" for num in numbers) if numbers else "未找到数字"
        
        else:
            return f"❌ 未知信息类型: {info_type}，支持: emails, urls, phones, numbers"
        
    except Exception as e:
        return f"❌ 信息提取失败: {str(e)}"


# 注册到统一适配器
def register_text_processing_tools():
    """注册文本处理工具到统一适配器"""
    try:
        # 注册信息提取工具
        universal_adapter.register_tool(
            name="extract_information",
            function=extract_information,
            description="从文本中提取特定信息，如邮箱、网址、电话号码等",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要分析的文本"
                    },
                    "info_type": {
                        "type": "string",
                        "description": "信息类型",
                        "enum": ["emails", "urls", "phones", "numbers"],
                        "default": "emails"
                    }
                },
                "required": ["text"]
            }
        )
        
        logger.info("Text processing tools registered successfully")
    except Exception as e:
        logger.error(f"Failed to register text processing tools: {e}")


# 自动注册
register_text_processing_tools()

# 导出工具
__all__ = ["text_statistics", "text_formatter", "extract_information"]
