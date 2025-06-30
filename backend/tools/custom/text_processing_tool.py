"""
文本处理自定义工具
展示更复杂的自定义工具实现
"""

from langchain_core.tools import tool
import re
import json
from typing import Dict, Any

@tool
def text_analyzer_tool(text: str, analysis_type: str = "all") -> str:
    """文本分析工具
    
    Args:
        text: 要分析的文本
        analysis_type: 分析类型，可选值：all（全部）, basic（基础）, advanced（高级）
        
    Returns:
        str: 分析结果（JSON格式）
        
    Examples:
        - text_analyzer_tool("Hello World! This is a test.")
        - text_analyzer_tool("你好世界！这是一个测试。", "basic")
    """
    try:
        # 基础统计
        char_count = len(text)
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        
        # 字符类型统计
        letter_count = sum(1 for c in text if c.isalpha())
        digit_count = sum(1 for c in text if c.isdigit())
        space_count = sum(1 for c in text if c.isspace())
        punct_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
        
        analysis = {
            "basic_stats": {
                "total_characters": char_count,
                "total_words": word_count,
                "total_lines": line_count,
                "letters": letter_count,
                "digits": digit_count,
                "spaces": space_count,
                "punctuation": punct_count
            }
        }
        
        if analysis_type in ["all", "advanced"]:
            # 高级分析
            sentences = re.split(r'[.!?]+', text)
            sentence_count = len([s for s in sentences if s.strip()])
            
            # 词频统计（简单版）
            words = re.findall(r'\b\w+\b', text.lower())
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 获取最常见的5个词
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            
            analysis["advanced_stats"] = {
                "sentence_count": sentence_count,
                "avg_words_per_sentence": round(word_count / max(sentence_count, 1), 2),
                "avg_chars_per_word": round(char_count / max(word_count, 1), 2),
                "top_words": top_words,
                "unique_words": len(word_freq)
            }
            
            # 文本特征
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
            has_english = bool(re.search(r'[a-zA-Z]', text))
            has_numbers = bool(re.search(r'\d', text))
            has_urls = bool(re.search(r'https?://\S+', text))
            has_emails = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
            
            analysis["text_features"] = {
                "contains_chinese": has_chinese,
                "contains_english": has_english,
                "contains_numbers": has_numbers,
                "contains_urls": has_urls,
                "contains_emails": has_emails
            }
        
        return json.dumps(analysis, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"❌ 文本分析失败: {str(e)}"

@tool
def text_formatter_tool(text: str, format_type: str, options: str = "{}") -> str:
    """文本格式化工具
    
    Args:
        text: 要格式化的文本
        format_type: 格式化类型，可选值：uppercase, lowercase, title, reverse, clean, markdown
        options: 格式化选项（JSON字符串），默认为空对象
        
    Returns:
        str: 格式化后的文本
        
    Examples:
        - text_formatter_tool("hello world", "title")
        - text_formatter_tool("  messy text  ", "clean")
        - text_formatter_tool("标题文本", "markdown", '{{"level": 2}}')
    """
    try:
        # 解析选项
        try:
            opts = json.loads(options)
        except:
            opts = {}
        
        if format_type == "uppercase":
            return text.upper()
            
        elif format_type == "lowercase":
            return text.lower()
            
        elif format_type == "title":
            return text.title()
            
        elif format_type == "reverse":
            return text[::-1]
            
        elif format_type == "clean":
            # 清理多余空白
            cleaned = re.sub(r'\s+', ' ', text.strip())
            return cleaned
            
        elif format_type == "markdown":
            level = opts.get("level", 1)
            if level < 1 or level > 6:
                level = 1
            return f"{'#' * level} {text}"
            
        elif format_type == "bullet":
            lines = text.split('\n')
            bullet_char = opts.get("bullet", "•")
            return '\n'.join(f"{bullet_char} {line.strip()}" for line in lines if line.strip())
            
        elif format_type == "numbered":
            lines = text.split('\n')
            start_num = opts.get("start", 1)
            return '\n'.join(f"{i + start_num}. {line.strip()}" for i, line in enumerate(lines) if line.strip())
            
        elif format_type == "quote":
            quote_char = opts.get("quote", ">")
            lines = text.split('\n')
            return '\n'.join(f"{quote_char} {line}" for line in lines)
            
        else:
            return f"❌ 不支持的格式化类型: {format_type}\n支持的类型: uppercase, lowercase, title, reverse, clean, markdown, bullet, numbered, quote"
    
    except Exception as e:
        return f"❌ 文本格式化失败: {str(e)}"

@tool
def text_search_replace_tool(text: str, search_pattern: str, replacement: str, use_regex: bool = False) -> str:
    """文本搜索替换工具
    
    Args:
        text: 原始文本
        search_pattern: 搜索模式
        replacement: 替换文本
        use_regex: 是否使用正则表达式，默认False
        
    Returns:
        str: 替换后的文本
        
    Examples:
        - text_search_replace_tool("Hello World", "World", "Universe")
        - text_search_replace_tool("abc123def", r"\\d+", "XXX", True)
    """
    try:
        if use_regex:
            result = re.sub(search_pattern, replacement, text)
        else:
            result = text.replace(search_pattern, replacement)
        
        return result
        
    except Exception as e:
        return f"❌ 搜索替换失败: {str(e)}"
