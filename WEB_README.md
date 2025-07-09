# AI 小说生成器 Web 版本

## 🚀 快速启动

### 方法 1：直接启动（推荐）

```bash
python web_app.py
```

### 方法 2：使用启动脚本（自动检查依赖）

```bash
python start_web.py
```

## 📋 依赖要求

确保已安装以下依赖：

```bash
pip install gradio>=4.0.0
```

其他依赖（通常已安装）：

- requests
- typing-extensions
- langchain
- langchain-core
- langchain-openai
- chromadb
- openai

## 🌐 访问界面

启动成功后，在浏览器中访问：

```
http://localhost:7860
```

## 📖 使用说明

### 1. 配置模型

- 点击"模型配置"标签页
- 设置 LLM 模型（如 OpenAI、DeepSeek 等）
- 设置 Embedding 模型
- 点击"测试配置"确保连接正常

### 2. 设置小说参数

- 点击"小说参数"标签页
- 填写主题、类型、章节数等基本信息
- 设置可选元素（角色、道具等）

### 3. 生成小说

- 返回"主要功能"标签页
- 设置保存路径
- 按顺序点击：
  1. Step1. 生成架构
  2. Step2. 生成目录
  3. Step3. 生成草稿
  4. Step4. 定稿章节

### 4. 文件管理

- 点击"文件管理"标签页
- 可以查看和编辑所有生成的文件
- 支持加载/保存操作

## 🔧 故障排除

### 启动错误

如果遇到 `AttributeError: Cannot call click outside of a gradio.Blocks context` 错误：

- 确保使用的是修复后的 `web_app.py` 版本
- 重新下载最新代码

### 依赖问题

```bash
# 安装Gradio
pip install gradio

# 如果缺少其他依赖
pip install -r web_requirements.txt
```

### 端口占用

如果 7860 端口被占用，修改 `web_app.py` 中的端口号：

```python
demo.launch(server_port=8080)  # 改为其他端口
```

## 📝 功能特性

- ✅ 完整的小说生成流程
- ✅ 多种 AI 模型支持
- ✅ 配置管理和测试
- ✅ 文件管理和编辑
- ✅ 实时日志显示
- ✅ 响应式 Web 界面

## 🆘 获取帮助

如果遇到问题：

1. 检查依赖是否完整安装
2. 确认 API 密钥配置正确
3. 查看控制台错误信息
4. 参考原 GUI 版本的使用说明
