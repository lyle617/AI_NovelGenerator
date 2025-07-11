# 📖 AI 小说生成器 - 智能创作工具

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Gradio](https://img.shields.io/badge/Gradio-Web%20UI-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**🚀 全新 Web 界面 | 🎯 智能创作流程 | 📚 专业级小说生成**

</div>

<div align="center">

✨ **核心功能特性** ✨

| 功能模块             | 关键能力                         | 最新更新   |
| -------------------- | -------------------------------- | ---------- |
| 🌐 **现代 Web 界面** | Gradio 驱动的响应式 Web UI       | ✅ **NEW** |
| 🎨 **小说设定工坊**  | 世界观架构 / 角色设定 / 剧情蓝图 | ✅ 优化    |
| 📖 **智能章节生成**  | 多阶段生成保障剧情连贯性         | ✅ 修复    |
| 🧠 **状态追踪系统**  | 角色发展轨迹 / 伏笔管理系统      | ✅ 增强    |
| 🔍 **语义检索引擎**  | 基于向量的长程上下文一致性维护   | ✅ 优化    |
| 📚 **知识库集成**    | 支持本地文档参考                 | ✅ 稳定    |
| ✅ **自动审校机制**  | 检测剧情矛盾与逻辑冲突           | ✅ 改进    |
| 🎯 **智能进度管理**  | 自动检测文件状态，恢复创作进度   | ✅ **NEW** |

</div>

> 🎉 **2025 年重大更新**：全新 Web 界面，简化操作流程，智能进度管理，让 AI 小说创作更加专业和高效！

## 📅 **最新更新日志**

### 🎯 **2025-01-11 - Web 界面重构**

- ✅ **全新 Gradio Web 界面**：现代化响应式设计
- ✅ **智能进度恢复**：自动检测已有文件，从任意步骤继续创作
- ✅ **简化操作流程**：一键式分步生成，所见即所得
- ✅ **优化用户体验**：滚动条始终可见，界面更直观
- ✅ **修复核心 Bug**：生成目录、章节、定稿功能参数错误修复
- ✅ **自定义小说类型**：支持用户输入任意小说类型
- ✅ **配置管理优化**：保存/加载配置更便捷

### 📚 **历史更新**

- **2025-03-13**：新增闲云修改，优化内容指导功能
- **2025-03-09**：添加字数显示功能
- **2025-03-05**：添加角色库功能

---

## 📑 目录导航

1. [环境准备](#-环境准备)
2. [项目架构](#-项目架构)
3. [配置指南](#⚙️-配置指南)
4. [运行说明](#🚀-运行说明)
5. [使用教程](#📘-使用教程)
6. [疑难解答](#❓-疑难解答)

---

## 🛠 环境准备

确保满足以下运行条件：

- **Python 3.9+** 运行环境（推荐 3.10-3.12 之间）
- **pip** 包管理工具
- 有效 API 密钥：
  - 云端服务：OpenAI / DeepSeek 等
  - 本地服务：Ollama 等兼容 OpenAI 的接口

---

## 📥 安装说明

1. **下载项目**

   - 通过 [GitHub](https://github.com) 下载项目 ZIP 文件，或使用以下命令克隆本项目：
     ```bash
     git clone https://github.com/YILING0013/AI_NovelGenerator
     ```

2. **安装编译工具（可选）**

   - 如果对某些包无法正常安装，访问 [Visual Studio Build Tools](https://visualstudio.microsoft.com/zh-hans/visual-cpp-build-tools/) 下载并安装 C++编译工具，用于构建部分模块包；
   - 安装时，默认只包含 MSBuild 工具，需手动勾选左上角列表栏中的 **C++ 桌面开发** 选项。

3. **安装依赖并运行**
   - 打开终端，进入项目源文件目录：
     ```bash
     cd AI_NovelGenerator
     ```
   - 安装项目依赖：
     ```bash
     pip install -r requirements.txt
     ```
   - 安装完成后，运行主程序：
     ```bash
     python main.py
     ```

> 如果缺失部分依赖，后续**手动执行**
>
> ```bash
> pip install XXX
> ```
>
> 进行安装即可

## 🗂 项目架构

```
novel-generator/
├── main.py                      # 入口文件, 运行 GUI
├── ui.py                        # 图形界面
├── novel_generator.py           # 章节生成核心逻辑
├── consistency_checker.py       # 一致性检查, 防止剧情冲突
|—— chapter_directory_parser.py  # 目录解析
|—— embedding_adapters.py        # Embedding 接口封装
|—— llm_adapters.py              # LLM 接口封装
├── prompt_definitions.py        # 定义 AI 提示词
├── utils.py                     # 常用工具函数, 文件操作
├── config_manager.py            # 管理配置 (API Key, Base URL)
├── config.json                  # 用户配置文件 (可选)
└── vectorstore/                 # (可选) 本地向量数据库存储
```

---

## ⚙️ 配置指南

### 📌 基础配置（config.json）

```json
{
  "api_key": "sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "base_url": "https://api.openai.com/v1",
  "interface_format": "OpenAI",
  "model_name": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 4096,
  "embedding_api_key": "sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "embedding_interface_format": "OpenAI",
  "embedding_url": "https://api.openai.com/v1",
  "embedding_model_name": "text-embedding-ada-002",
  "embedding_retrieval_k": 4,
  "topic": "星穹铁道主角星穿越到原神提瓦特大陆，拯救提瓦特大陆，并与其中的角色展开爱恨情仇的小说",
  "genre": "玄幻",
  "num_chapters": 120,
  "word_number": 4000,
  "filepath": "D:/AI_NovelGenerator/filepath"
}
```

### 🔧 配置说明

1. **生成模型配置**

   - `api_key`: 大模型服务的 API 密钥
   - `base_url`: API 终端地址（本地服务填 Ollama 等地址）
   - `interface_format`: 接口模式
   - `model_name`: 主生成模型名称（如 gpt-4, claude-3 等）
   - `temperature`: 创意度参数（0-1，越高越有创造性）
   - `max_tokens`: 模型最大回复长度

2. **Embedding 模型配置**

   - `embedding_model_name`: 模型名称（如 Ollama 的 nomic-embed-text）
   - `embedding_url`: 服务地址
   - `embedding_retrieval_k`:

3. **小说参数配置**
   - `topic`: 核心故事主题
   - `genre`: 作品类型
   - `num_chapters`: 总章节数
   - `word_number`: 单章目标字数
   - `filepath`: 生成文件存储路径

---

## 🚀 运行说明

### **🌐 Web 界面启动（推荐）**

```bash
python web_app.py
```

执行后，Web 界面将在浏览器中自动打开，提供现代化的创作体验：

- 📱 **响应式设计**：支持桌面和移动设备
- 🎯 **智能进度管理**：自动检测并恢复创作进度
- ✨ **实时预览**：生成内容立即显示
- 🔄 **无缝工作流**：从架构到定稿的完整流程

### **🖥️ 传统 GUI 界面**

```bash
python main.py
```

启动传统的桌面 GUI 界面（基于 Tkinter）。

### **📦 打包为可执行文件**

如果你想在无 Python 环境的机器上使用本工具：

```bash
pip install pyinstaller
pyinstaller main.spec
```

打包完成后，会在 `dist/` 目录下生成可执行文件。

---

## 📘 使用教程

1. **启动后，先完成基本参数设置：**

   - **API Key & Base URL**（如 `https://api.openai.com/v1`）
   - **模型名称**（如 `gpt-3.5-turbo`、`gpt-4o` 等）
   - **Temperature** (0~1，决定文字创意程度)
   - **主题(Topic)**（如 “废土世界的 AI 叛乱”）
   - **类型(Genre)**（如 “科幻”/“魔幻”/“都市幻想”）
   - **章节数**、**每章字数**（如 10 章，每章约 3000 字）
   - **保存路径**（建议创建一个新的输出文件夹）

2. **点击「Step1. 生成设定」**

   - 系统将基于主题、类型、章节数等信息，生成：
     - `Novel_setting.txt`：包含世界观、角色信息、雷点暗线等。
   - 可以在生成后的 `Novel_setting.txt` 中查看或修改设定内容。

3. **点击「Step2. 生成目录」**

   - 系统会根据已完成的 `Novel_setting.txt` 内容，为全部章节生成：
     - `Novel_directory.txt`：包括每章标题和简要提示。
   - 可以在生成后的文件中查看、修改或补充章节标题和描述。

4. **点击「Step3. 生成章节草稿」**

   - 在生成章节之前，你可以：
     - **设置章节号**（如写第 1 章，就填 `1`）
     - **在“本章指导”输入框**中提供对本章剧情的任何期望或提示
   - 点击按钮后，系统将：
     - 自动读取前文设定、`Novel_directory.txt`、以及已定稿章节
     - 调用向量检索回顾剧情，保证上下文连贯
     - 生成本章大纲 (`outline_X.txt`) 及正文 (`chapter_X.txt`)
   - 生成完成后，你可在左侧的文本框查看、编辑本章草稿内容。

5. **点击「Step4. 定稿当前章节」**

   - 系统将：
     - **更新全局摘要**（写入 `global_summary.txt`）
     - **更新角色状态**（写入 `character_state.txt`）
     - **更新向量检索库**（保证后续章节可以调用最新信息）
     - **更新剧情要点**（如 `plot_arcs.txt`）
   - 定稿完成后，你可以在 `chapter_X.txt` 中看到定稿后的文本。

6. **一致性检查（可选）**

   - 点击「[可选] 一致性审校」按钮，对最新章节进行冲突检测，如角色逻辑、剧情前后矛盾等。
   - 若有冲突，会在日志区输出详细提示。

7. **重复第 4-6 步** 直到所有章节生成并定稿！

---

### 🌐 **Web 界面操作流程（推荐）**

#### 1. **🚀 启动 Web 界面**

```bash
python web_app.py
```

浏览器将自动打开 AI 小说生成器的现代化 Web 界面。

#### 2. **⚙️ 配置 AI 模型**

在"🤖 AI 模型配置"区域设置：

- **LLM 接口**：选择 OpenAI、DeepSeek 等
- **API 密钥**：输入你的 API Key
- **模型名称**：如`gpt-4o-mini`、`deepseek-chat`等
- **Embedding 模型**：用于语义检索的模型

#### 3. **📖 设置小说参数**

在"📖 小说设置"区域配置：

- **📝 主题描述**：详细描述你的小说主题
- **📚 小说类型**：选择预设类型或输入自定义类型
- **📊 章节数量**：计划创作的总章节数（支持 1-1000 章）
- **📄 每章字数**：单章目标字数
- **💾 保存/加载配置**：方便重复使用设置

#### 4. **🎯 设置创作参数**

在"🎯 创作设置"区域：

- **📖 当前创作章节**：选择要生成的章节号
- **📝 本章创作指导**：对本章剧情的具体要求
- **📁 保存路径**：小说文件的保存目录

#### 5. **🔄 智能分步生成**

系统提供四步式创作流程，**支持智能进度恢复**：

**📋 第一步：生成架构** → **📑 第二步：生成目录** → **📝 第三步：生成章节** → **✅ 第四步：内容定稿**

每一步完成后，内容自动显示在对应 Tab 中，下一步按钮自动启用。

#### 6. **🎯 智能进度管理**

- **自动检测**：切换项目路径时自动检测已有文件
- **进度恢复**：从任意步骤继续创作，无需重新开始
- **状态提示**：清晰显示当前创作进度和可执行操作

> **向量检索配置提示**
>
> 1. embedding 模型需要显示指定接口和模型名称；
> 2. 使用**本地 Ollama**的**Embedding**时需提前启动 Ollama 服务：
>    ```bash
>    ollama serve  # 启动服务
>    ollama pull nomic-embed-text  # 下载/启用模型
>    ```
> 3. 切换不同 Embedding 模型后建议清空 vectorstore 目录
> 4. 云端 Embedding 需确保对应 API 权限已开通

---

## 🎯 **Web 界面新特性**

### ✨ **用户体验优化**

- **🎨 现代化设计**：基于 Gradio 的响应式 Web 界面
- **📱 跨平台兼容**：支持桌面和移动设备访问
- **🔄 实时更新**：生成内容立即显示，无需手动刷新
- **📋 智能 Tab 管理**：架构、目录、章节、角色、摘要分 Tab 显示

### 🚀 **智能功能**

- **🎯 进度恢复**：自动检测已有文件，从任意步骤继续创作
- **🔄 状态管理**：按钮状态智能更新，引导用户操作
- **📊 滚动优化**：所有内容区域支持流畅滚动
- **💾 配置管理**：一键保存/加载创作配置

### 🛠️ **技术改进**

- **🐛 Bug 修复**：修复生成目录、章节、定稿功能的参数错误
- **📈 性能优化**：更快的页面响应和内容加载
- **🔧 参数验证**：智能参数检查，减少错误发生
- **📚 类型扩展**：支持 30+预设小说类型，可自定义输入

---

## ❓ 疑难解答

### Q1: Expecting value: line 1 column 1 (char 0)

该问题大概率由于 API 未正确响应造成，也许响应了一个 html？其它内容，导致出现该报错；

### Q2: HTTP/1.1 504 Gateway Timeout？

确认接口是否稳定；

### Q3: 如何切换不同的 Embedding 提供商？

在 GUI 界面中对应输入即可。

---

如有更多问题或需求，欢迎在**项目 Issues** 中提出。
