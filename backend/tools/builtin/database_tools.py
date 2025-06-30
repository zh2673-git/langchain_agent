"""
数据库工具 - LangChain内置工具
提供SQLite数据库操作能力
"""

from langchain_core.tools import tool
import sqlite3
import os
import tempfile
from typing import List, Dict, Any
import json

# 默认数据库路径
DEFAULT_DB_PATH = os.path.join(tempfile.gettempdir(), "langchain_demo.db")

def _get_db_connection(db_path: str = None) -> sqlite3.Connection:
    """获取数据库连接"""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
    return conn

def _init_demo_database():
    """初始化演示数据库"""
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        
        # 创建示例表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                salary REAL NOT NULL,
                hire_date TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                manager TEXT,
                budget REAL
            )
        ''')
        
        # 插入示例数据（如果表为空）
        cursor.execute("SELECT COUNT(*) FROM employees")
        if cursor.fetchone()[0] == 0:
            employees_data = [
                ("张三", "技术部", 8000, "2023-01-15"),
                ("李四", "销售部", 6000, "2023-02-20"),
                ("王五", "技术部", 9000, "2022-12-10"),
                ("赵六", "人事部", 5500, "2023-03-05"),
                ("钱七", "销售部", 6500, "2023-01-30")
            ]
            cursor.executemany(
                "INSERT INTO employees (name, department, salary, hire_date) VALUES (?, ?, ?, ?)",
                employees_data
            )
        
        cursor.execute("SELECT COUNT(*) FROM departments")
        if cursor.fetchone()[0] == 0:
            departments_data = [
                ("技术部", "张三", 100000),
                ("销售部", "李四", 80000),
                ("人事部", "赵六", 50000)
            ]
            cursor.executemany(
                "INSERT INTO departments (name, manager, budget) VALUES (?, ?, ?)",
                departments_data
            )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"初始化数据库失败: {e}")

# 初始化演示数据库
_init_demo_database()

@tool
def sql_query(query: str, db_path: str = None) -> str:
    """执行SQL查询
    
    Args:
        query: SQL查询语句
        db_path: 数据库文件路径（可选，默认使用演示数据库）
        
    Returns:
        str: 查询结果（JSON格式）
        
    Examples:
        - sql_query("SELECT * FROM employees")
        - sql_query("SELECT department, AVG(salary) FROM employees GROUP BY department")
        - sql_query("SELECT COUNT(*) as total FROM employees")
    """
    try:
        conn = _get_db_connection(db_path)
        cursor = conn.cursor()
        
        # 执行查询
        cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            # 查询操作
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            conn.close()
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            # 修改操作
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return f"操作完成，影响了 {affected_rows} 行"
            
    except Exception as e:
        return f"SQL执行错误: {str(e)}"

@tool
def list_tables(db_path: str = None) -> str:
    """列出数据库中的所有表
    
    Args:
        db_path: 数据库文件路径（可选）
        
    Returns:
        str: 表列表
    """
    try:
        conn = _get_db_connection(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        conn.close()
        
        if tables:
            table_list = [table[0] for table in tables]
            return f"数据库表: {', '.join(table_list)}"
        else:
            return "数据库中没有表"
            
    except Exception as e:
        return f"获取表列表失败: {str(e)}"

@tool
def describe_table(table_name: str, db_path: str = None) -> str:
    """描述表结构
    
    Args:
        table_name: 表名
        db_path: 数据库文件路径（可选）
        
    Returns:
        str: 表结构信息
    """
    try:
        conn = _get_db_connection(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        conn.close()
        
        if columns:
            result = f"表 '{table_name}' 的结构:\n"
            for col in columns:
                result += f"- {col[1]} ({col[2]})"
                if col[3]:  # NOT NULL
                    result += " NOT NULL"
                if col[5]:  # PRIMARY KEY
                    result += " PRIMARY KEY"
                result += "\n"
            return result
        else:
            return f"表 '{table_name}' 不存在"
            
    except Exception as e:
        return f"获取表结构失败: {str(e)}"

def create_database_tools():
    """创建数据库工具列表"""
    return [sql_query, list_tables, describe_table]
