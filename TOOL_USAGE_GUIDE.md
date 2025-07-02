# 🛠️ 工具使用指南

## 📁 文件操作工具

### ⚠️ 重要限制

文件操作工具（`list_files`, `read_file`, `write_file`）有以下安全限制：

1. **只能访问相对路径** - 不能使用绝对路径
2. **工作目录限制** - 只能在 `./workspace` 目录内操作
3. **路径安全检查** - 防止目录遍历攻击

### ✅ 正确使用方式

#### 列出文件 (`list_files`)

```
✅ 正确：
- list_files(".")           # 列出workspace根目录
- list_files("data")        # 列出workspace/data目录
- list_files("data/files")  # 列出workspace/data/files目录

❌ 错误：
- list_files("C:\\Users\\Desktop")     # 绝对路径
- list_files("/home/user")             # 绝对路径
- list_files("../../../etc")           # 目录遍历
```

#### 读取文件 (`read_file`)

```
✅ 正确：
- read_file("README.md")               # 读取workspace/README.md
- read_file("data/config.json")        # 读取workspace/data/config.json

❌ 错误：
- read_file("C:\\Windows\\system.ini") # 绝对路径
- read_file("/etc/passwd")             # 绝对路径
```

#### 写入文件 (`write_file`)

```
✅ 正确：
- write_file("output.txt", "内容")     # 写入workspace/output.txt
- write_file("logs/app.log", "日志")   # 写入workspace/logs/app.log

❌ 错误：
- write_file("C:\\temp\\file.txt", "内容") # 绝对路径
```

### 📂 当前workspace结构

```
workspace/
├── README.md              # 工作目录说明
├── sample_data.txt         # 示例数据文件
└── data/
    └── config.json         # 配置文件示例
```

### 💡 使用建议

1. **先列出目录内容**
   ```
   使用 list_files(".") 查看workspace根目录有什么文件
   ```

2. **逐步导航**
   ```
   使用 list_files("data") 查看子目录内容
   ```

3. **读取示例文件**
   ```
   使用 read_file("README.md") 读取说明文件
   使用 read_file("data/config.json") 读取配置文件
   ```

4. **创建新文件**
   ```
   使用 write_file("my_notes.txt", "我的笔记内容") 创建新文件
   ```

### 🔧 故障排除

#### 问题：目录不存在
```
错误：目录不存在 - some_path
解决：使用 list_files(".") 查看可用目录
```

#### 问题：绝对路径错误
```
错误：不能访问绝对路径 'C:\Users\...'
解决：使用相对路径，如 "data" 而不是 "C:\data"
```

#### 问题：路径超出安全范围
```
错误：目录路径超出安全范围
解决：确保路径在workspace目录内，不要使用 "../" 等
```

### 🎯 实际使用示例

#### 示例1：探索workspace
```
用户：请列出当前工作目录的文件
Agent：使用 list_files(".") 
结果：显示workspace根目录内容
```

#### 示例2：读取配置文件
```
用户：请读取配置文件
Agent：使用 list_files(".") 找到文件，然后 read_file("data/config.json")
结果：显示配置文件内容
```

#### 示例3：创建新文件
```
用户：请创建一个包含当前时间的日志文件
Agent：使用 get_current_time() 获取时间，然后 write_file("log.txt", "时间内容")
结果：创建新的日志文件
```

### 🚀 最佳实践

1. **总是从根目录开始** - 使用 `list_files(".")` 了解结构
2. **使用相对路径** - 避免绝对路径和目录遍历
3. **检查文件存在** - 先列出目录，再操作文件
4. **组合使用工具** - 结合其他工具（如时间、计算）创建有用的文件

这样，Agent就能正确理解和使用文件操作工具了！🎉
