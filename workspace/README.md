# Workspace 目录

这是一个安全的工作目录，用于文件操作工具。

## 可用的文件操作

1. **list_files** - 列出目录中的文件
   - 使用相对路径，如 "." 或 "data"
   - 不能使用绝对路径

2. **read_file** - 读取文件内容
   - 只能读取workspace目录内的文件

3. **write_file** - 写入文件内容
   - 只能在workspace目录内创建文件

## 示例文件

- README.md (本文件)
- sample_data.txt (示例数据文件)

## 安全限制

所有文件操作都限制在此workspace目录内，确保系统安全。
