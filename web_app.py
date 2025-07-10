# web_app.py
# -*- coding: utf-8 -*-
"""
AI_NovelGenerator Gradio Web Interface
基于原有GUI功能创建的Web界面版本
"""

import gradio as gr
import os
import json
import threading
import traceback
from typing import Optional, Tuple, Dict, Any

# 导入原有的核心功能模块
from config_manager import load_config, save_config, test_llm_config, test_embedding_config
from novel_generator import (
    Novel_architecture_generate,
    Chapter_blueprint_generate,
    generate_chapter_draft,
    finalize_chapter,
    import_knowledge_file,
    clear_vector_store
)
from consistency_checker import check_consistency
from utils import read_file, save_string_to_txt, clear_file_content
from llm_adapters import create_llm_adapter
from embedding_adapters import create_embedding_adapter

class NovelGeneratorWebApp:
    """AI小说生成器Web应用类"""

    def __init__(self):
        self.config_file = "config.json"
        self.loaded_config = load_config(self.config_file)

        # 初始化默认配置
        self.init_default_config()

        # 状态变量
        self.current_chapter_num = 1
        self.generation_in_progress = False

    def init_default_config(self):
        """初始化默认配置"""
        if self.loaded_config:
            self.last_llm = self.loaded_config.get("last_interface_format", "OpenAI")
            self.last_embedding = self.loaded_config.get("last_embedding_interface_format", "OpenAI")
        else:
            self.last_llm = "OpenAI"
            self.last_embedding = "OpenAI"

    def log_message(self, message: str) -> str:
        """添加日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] {message}\n"

    def get_llm_config_from_form(self, interface_format, api_key, base_url, model_name,
                                temperature, max_tokens, timeout):
        """从表单获取LLM配置"""
        return {
            "interface_format": interface_format,
            "api_key": api_key,
            "base_url": base_url,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout
        }

    def get_embedding_config_from_form(self, interface_format, api_key, base_url,
                                     model_name, retrieval_k):
        """从表单获取Embedding配置"""
        return {
            "interface_format": interface_format,
            "api_key": api_key,
            "base_url": base_url,
            "model_name": model_name,
            "retrieval_k": retrieval_k
        }

    def save_config_to_file(self, llm_config, embedding_config, novel_params):
        """保存配置到文件"""
        try:
            config_data = {
                "last_interface_format": llm_config["interface_format"],
                "last_embedding_interface_format": embedding_config["interface_format"],
                "llm_configs": {
                    llm_config["interface_format"]: {
                        "api_key": llm_config["api_key"],
                        "base_url": llm_config["base_url"],
                        "model_name": llm_config["model_name"],
                        "temperature": llm_config["temperature"],
                        "max_tokens": llm_config["max_tokens"],
                        "timeout": llm_config["timeout"]
                    }
                },
                "embedding_configs": {
                    embedding_config["interface_format"]: {
                        "api_key": embedding_config["api_key"],
                        "base_url": embedding_config["base_url"],
                        "model_name": embedding_config["model_name"],
                        "retrieval_k": embedding_config["retrieval_k"]
                    }
                },
                "other_params": novel_params
            }

            success = save_config(config_data, self.config_file)
            if success:
                self.loaded_config = config_data
                return "✅ 配置保存成功！"
            else:
                return "❌ 配置保存失败！"
        except Exception as e:
            return f"❌ 保存配置时出错: {str(e)}"

    def load_config_from_file(self):
        """从文件加载配置"""
        try:
            cfg = load_config(self.config_file)
            if not cfg:
                return None, "未找到配置文件"

            # 提取LLM配置
            last_llm = cfg.get("last_interface_format", "OpenAI")
            llm_configs = cfg.get("llm_configs", {})
            llm_config = llm_configs.get(last_llm, {})

            # 提取Embedding配置
            last_embedding = cfg.get("last_embedding_interface_format", "OpenAI")
            embedding_configs = cfg.get("embedding_configs", {})
            embedding_config = embedding_configs.get(last_embedding, {})

            # 提取其他参数
            other_params = cfg.get("other_params", {})

            return {
                "llm_interface": last_llm,
                "llm_api_key": llm_config.get("api_key", ""),
                "llm_base_url": llm_config.get("base_url", "https://api.openai.com/v1"),
                "llm_model": llm_config.get("model_name", "gpt-4o-mini"),
                "temperature": llm_config.get("temperature", 0.7),
                "max_tokens": llm_config.get("max_tokens", 8192),
                "timeout": llm_config.get("timeout", 600),
                "embedding_interface": last_embedding,
                "embedding_api_key": embedding_config.get("api_key", ""),
                "embedding_base_url": embedding_config.get("base_url", "https://api.openai.com/v1"),
                "embedding_model": embedding_config.get("model_name", "text-embedding-ada-002"),
                "retrieval_k": embedding_config.get("retrieval_k", 4),
                "topic": other_params.get("topic", ""),
                "genre": other_params.get("genre", "玄幻"),
                "num_chapters": other_params.get("num_chapters", 10),
                "word_number": other_params.get("word_number", 3000),
                "filepath": other_params.get("filepath", ""),
                "user_guidance": other_params.get("user_guidance", ""),
                "characters_involved": other_params.get("characters_involved", ""),
                "key_items": other_params.get("key_items", ""),
                "scene_location": other_params.get("scene_location", ""),
                "time_constraint": other_params.get("time_constraint", "")
            }, "✅ 配置加载成功！"
        except Exception as e:
            return None, f"❌ 加载配置时出错: {str(e)}"

# 创建全局应用实例
app = NovelGeneratorWebApp()

def create_interface():
    """创建Gradio界面"""

    # 定义LLM接口选项
    llm_interfaces = ["OpenAI", "DeepSeek", "Azure OpenAI", "Azure AI", "Ollama",
                     "ML Studio", "Gemini", "阿里云百炼", "火山引擎", "硅基流动"]

    # 定义类型选项
    genres = ["玄幻", "仙侠", "都市", "历史", "科幻", "军事", "游戏", "体育", "悬疑", "其他"]

    # 自动加载已保存的配置
    config_data, config_message = app.load_config_from_file()
    if config_data:
        print(f"✅ 自动加载配置成功: {config_message}")
        # 使用加载的配置作为默认值
        default_llm_interface = config_data["llm_interface"]
        default_llm_api_key = config_data["llm_api_key"]
        default_llm_base_url = config_data["llm_base_url"]
        default_llm_model = config_data["llm_model"]
        default_temperature = config_data["temperature"]
        default_max_tokens = config_data["max_tokens"]
        default_timeout = config_data["timeout"]
        default_embedding_interface = config_data["embedding_interface"]
        default_embedding_api_key = config_data["embedding_api_key"]
        default_embedding_base_url = config_data["embedding_base_url"]
        default_embedding_model = config_data["embedding_model"]
        default_retrieval_k = config_data["retrieval_k"]
        default_topic = config_data["topic"]
        default_genre = config_data["genre"]
        default_num_chapters = config_data["num_chapters"]
        default_word_number = config_data["word_number"]
        default_filepath = config_data["filepath"]
        default_user_guidance = config_data["user_guidance"]
        default_characters_involved = config_data["characters_involved"]
        default_key_items = config_data["key_items"]
        default_scene_location = config_data["scene_location"]
        default_time_constraint = config_data["time_constraint"]
    else:
        print(f"⚠️ 未找到配置文件，使用默认值: {config_message}")
        # 使用默认值
        default_llm_interface = "OpenAI"
        default_llm_api_key = ""
        default_llm_base_url = "https://api.openai.com/v1"
        default_llm_model = "gpt-4o-mini"
        default_temperature = 0.7
        default_max_tokens = 8192
        default_timeout = 600
        default_embedding_interface = "OpenAI"
        default_embedding_api_key = ""
        default_embedding_base_url = "https://api.openai.com/v1"
        default_embedding_model = "text-embedding-ada-002"
        default_retrieval_k = 4
        default_topic = ""
        default_genre = "玄幻"
        default_num_chapters = 10
        default_word_number = 3000
        default_filepath = ""
        default_user_guidance = ""
        default_characters_involved = ""
        default_key_items = ""
        default_scene_location = ""
        default_time_constraint = ""

    # 创建自定义CSS样式
    custom_css = """
    /* 全局样式 - 确保所有页面宽度一致 */
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
        padding: 0 1rem !important;
    }

    /* 确保所有标签页内容宽度一致 */
    .tab-content {
        width: 100% !important;
        max-width: 1400px !important;
        margin: 0 auto !important;
        padding: 1rem !important;
    }

    /* 标签页容器 */
    .gradio-tabs {
        width: 100% !important;
    }

    .gradio-tabitem {
        width: 100% !important;
        max-width: 1400px !important;
        margin: 0 auto !important;
        padding: 1rem !important;
    }

    /* 行和列的一致性 */
    .gradio-row {
        width: 100% !important;
        margin: 0 !important;
        gap: 1rem !important;
    }

    .gradio-column {
        width: 100% !important;
    }

    /* 确保所有标签页内容宽度一致 */
    .gradio-tabitem {
        max-width: 1400px !important;
        margin: 0 auto !important;
        width: 100% !important;
    }

    /* 标题样式 */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        width: 100% !important;
        max-width: 1400px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .main-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 1rem;
    }

    /* 卡片样式 */
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border: 1px solid #e1e5e9;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        width: 100% !important;
    }

    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    /* 按钮样式 */
    .primary-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .primary-button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }

    /* 标签页样式 */
    .tab-nav {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.5rem;
        margin-bottom: 1rem;
    }

    /* 日志窗口样式 */
    .log-container {
        background: #1e1e1e;
        color: #00ff00;
        font-family: 'Courier New', monospace;
        border-radius: 8px;
        padding: 1rem;
    }

    /* 配置区域样式 */
    .config-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    /* 文本框和输入组件统一宽度 */
    .gradio-textbox, .gradio-dropdown, .gradio-number, .gradio-slider {
        width: 100% !important;
    }

    /* 确保所有输入组件容器宽度一致 */
    .gradio-form > * {
        width: 100% !important;
        margin-bottom: 1rem !important;
    }

    /* 状态指示器 */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .status-success { background-color: #28a745; }
    .status-warning { background-color: #ffc107; }
    .status-error { background-color: #dc3545; }

    /* 确保按钮容器宽度一致 */
    .gradio-button {
        width: 100% !important;
        margin: 0.5rem 0 !important;
    }

    /* 日志容器样式统一 */
    .log-container {
        width: 100% !important;
        max-width: 100% !important;
    }

    /* 响应式设计 */
    @media (max-width: 768px) {
        .gradio-container {
            max-width: 100% !important;
            padding: 0 0.5rem !important;
        }

        .main-header {
            padding: 1.5rem !important;
            margin-bottom: 1rem !important;
        }

        .main-title {
            font-size: 2rem !important;
        }

        .main-subtitle {
            font-size: 1rem !important;
        }

        .feature-card {
            margin: 0.5rem 0 !important;
            padding: 1rem !important;
        }

        .config-section {
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
        }

        .gradio-tabitem {
            padding: 0.5rem !important;
        }
    }
    """

    with gr.Blocks(
        title="AI小说生成器 - 智能创作平台",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as demo:

        # Landing页面头部
        with gr.Row():
            with gr.Column():
                gr.HTML("""
                <div class="main-header">
                    <div class="main-title">🎯 AI小说生成器</div>
                    <div class="main-subtitle">基于大语言模型的智能小说创作平台</div>
                    <div style="margin-top: 1rem;">
                        <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; margin: 0 0.5rem;">
                            ✨ 智能架构生成
                        </span>
                        <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; margin: 0 0.5rem;">
                            📚 章节蓝图规划
                        </span>
                        <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; margin: 0 0.5rem;">
                            🔍 智能上下文检索
                        </span>
                    </div>
                </div>
                """)

        # 主要状态变量
        log_state = gr.State("")

        with gr.Tabs() as tabs:
            # Tab 0: 欢迎页面
            with gr.Tab("🏠 欢迎", id="welcome"):
                with gr.Column(elem_classes=["tab-content"]):
                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.HTML("""
                            <div class="feature-card">
                                <h2>🚀 快速开始</h2>
                                <p>欢迎使用AI小说生成器！按照以下步骤开始您的创作之旅：</p>
                                <ol style="line-height: 1.8;">
                                    <li><strong>配置模型</strong> - 前往"模型配置"页面设置您的AI模型</li>
                                    <li><strong>设置参数</strong> - 在"小说参数"页面填写小说基本信息</li>
                                    <li><strong>开始创作</strong> - 在"主要功能"页面按步骤生成小说</li>
                                    <li><strong>管理文件</strong> - 使用"文件管理"页面查看和编辑内容</li>
                                </ol>
                            </div>
                            """)

                        with gr.Row():
                            with gr.Column():
                                gr.HTML("""
                                <div class="feature-card">
                                    <h3>✨ 核心功能</h3>
                                    <ul style="line-height: 1.6;">
                                        <li><strong>智能架构生成</strong> - AI自动构建小说世界观和情节框架</li>
                                        <li><strong>章节蓝图规划</strong> - 详细的章节大纲和剧情安排</li>
                                        <li><strong>草稿智能生成</strong> - 基于上下文的章节内容创作</li>
                                        <li><strong>一致性检查</strong> - 自动检测剧情逻辑和角色一致性</li>
                                    </ul>
                                </div>
                                """)

                            with gr.Column():
                                gr.HTML("""
                                <div class="feature-card">
                                    <h3>🎯 支持的模型</h3>
                                    <ul style="line-height: 1.6;">
                                        <li><strong>OpenAI</strong> - GPT-4, GPT-3.5系列</li>
                                        <li><strong>Google Gemini</strong> - Gemini Pro, Flash系列</li>
                                        <li><strong>DeepSeek</strong> - DeepSeek Chat系列</li>
                                        <li><strong>火山引擎</strong> - 豆包系列模型</li>
                                        <li><strong>其他</strong> - Azure OpenAI, Ollama等</li>
                                    </ul>
                                </div>
                                """)

                    with gr.Column(scale=1):
                        gr.HTML("""
                        <div class="feature-card">
                            <h3>📊 系统状态</h3>
                            <div style="margin: 1rem 0;">
                                <div style="margin: 0.5rem 0;">
                                    <span class="status-indicator status-warning"></span>
                                    <span>配置状态: 待设置</span>
                                </div>
                                <div style="margin: 0.5rem 0;">
                                    <span class="status-indicator status-warning"></span>
                                    <span>模型连接: 未测试</span>
                                </div>
                                <div style="margin: 0.5rem 0;">
                                    <span class="status-indicator status-success"></span>
                                    <span>系统状态: 正常</span>
                                </div>
                            </div>
                        </div>
                        """)

                        gr.HTML("""
                        <div class="feature-card">
                            <h3>💡 使用提示</h3>
                            <ul style="line-height: 1.6; font-size: 0.9rem;">
                                <li>首次使用请先配置API密钥</li>
                                <li>建议先测试模型连接</li>
                                <li>设置合适的保存路径</li>
                                <li>可以随时编辑生成的内容</li>
                                <li>支持多种文件格式导出</li>
                            </ul>
                        </div>
                        """)

                        # 快速配置按钮
                        with gr.Row():
                            quick_config_btn = gr.Button("🔧 快速配置", variant="primary", elem_classes=["primary-button"])
                            quick_start_btn = gr.Button("🚀 开始创作", variant="primary", elem_classes=["primary-button"])

            # Tab 1: 主要功能
            with gr.Tab("📝 主要功能", id="main"):
                with gr.Column(elem_classes=["tab-content"]):
                    with gr.Row():
                        with gr.Column(scale=2):
                            # 章节内容区域
                            gr.HTML("""
                            <div class="config-section">
                                <h3>📖 当前章节内容</h3>
                                <p>在这里查看和编辑生成的章节内容</p>
                            </div>
                            """)
                        chapter_content = gr.Textbox(
                            label="章节内容（可编辑）",
                            lines=15,
                            max_lines=20,
                            placeholder="生成的章节内容将显示在这里...\n\n💡 提示：\n1. 内容生成后可以直接编辑\n2. 编辑后的内容会在定稿时保存\n3. 支持Markdown格式",
                            interactive=True
                        )

                        # Step按钮区域
                        gr.HTML("""
                        <div class="config-section">
                            <h3>🚀 智能生成流程</h3>
                            <p>按照以下步骤完成小说创作，每个步骤都会基于前一步的结果</p>
                        </div>
                        """)
                        with gr.Row():
                            btn_step1 = gr.Button("Step1. 生成架构", variant="primary", elem_classes=["primary-button"])
                            btn_step2 = gr.Button("Step2. 生成目录", variant="primary", elem_classes=["primary-button"])
                            btn_step3 = gr.Button("Step3. 生成草稿", variant="primary", elem_classes=["primary-button"])
                            btn_step4 = gr.Button("Step4. 定稿章节", variant="primary", elem_classes=["primary-button"])

                        # 步骤说明
                        gr.HTML("""
                        <div style="margin: 1rem 0; padding: 1rem; background: #f8f9fa; border-radius: 8px; font-size: 0.9rem;">
                            <strong>📋 流程说明：</strong><br>
                            <strong>Step1</strong> - 根据主题生成完整的小说架构和世界观<br>
                            <strong>Step2</strong> - 基于架构生成详细的章节蓝图<br>
                            <strong>Step3</strong> - 生成指定章节的草稿内容<br>
                            <strong>Step4</strong> - 定稿章节并更新全局状态
                        </div>
                        """)

                        # 辅助功能按钮
                        gr.HTML("""
                        <div class="config-section">
                            <h3>🔧 辅助工具</h3>
                            <p>提供额外的创作辅助功能</p>
                        </div>
                        """)
                        with gr.Row():
                            btn_consistency = gr.Button("🔍 一致性检查", elem_classes=["primary-button"])
                            btn_import_knowledge = gr.Button("📚 导入知识库", elem_classes=["primary-button"])
                            btn_clear_vectorstore = gr.Button("🗑️ 清空向量库", variant="stop")
                            btn_plot_arcs = gr.Button("📊 查看剧情要点", elem_classes=["primary-button"])

                        # 日志区域
                        gr.HTML("""
                        <div class="config-section">
                            <h3>📋 系统日志</h3>
                            <p>实时显示生成过程和系统状态</p>
                        </div>
                        """)
                        log_output = gr.Textbox(
                            label="系统日志",
                            lines=8,
                            max_lines=10,
                            interactive=False,
                            value="",
                            elem_classes=["log-container"]
                        )

                    with gr.Column(scale=1):
                        # 右侧：配置和参数
                        gr.HTML("""
                        <div class="config-section">
                            <h3>⚙️ 快速配置</h3>
                            <p>设置当前创作的基本参数</p>
                        </div>
                        """)

                        # 文件路径设置
                        filepath_input = gr.Textbox(
                            label="📁 保存路径",
                            placeholder="例如: /Users/username/novels/my_novel",
                            value=default_filepath,
                            info="小说文件的保存目录"
                        )

                        # 章节号设置
                        chapter_num_input = gr.Number(
                            label="📖 当前章节号",
                            value=1,
                            minimum=1,
                            step=1,
                            info="要生成或编辑的章节编号"
                        )

                        # 本章指导
                        user_guidance_input = gr.Textbox(
                            label="💡 本章指导",
                            lines=4,
                            value=default_user_guidance,
                            placeholder="例如：\n- 主角遇到神秘老人\n- 揭示重要线索\n- 营造紧张氛围\n- 为下章埋下伏笔",
                            info="对本章剧情发展的具体要求和提示"
                        )

                        # 配置管理
                        gr.HTML("""
                        <div class="config-section">
                            <h3>💾 配置管理</h3>
                            <p>保存和加载创作配置</p>
                        </div>
                        """)
                        with gr.Row():
                            btn_load_config = gr.Button("📥 加载配置", elem_classes=["primary-button"])
                            btn_save_config = gr.Button("💾 保存配置", elem_classes=["primary-button"])

                        # 创作进度
                        gr.HTML("""
                        <div class="feature-card">
                            <h4>📊 创作进度</h4>
                            <div style="margin: 0.5rem 0;">
                                <div style="background: #e9ecef; border-radius: 10px; height: 8px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; width: 0%; transition: width 0.3s ease;"></div>
                                </div>
                                <small style="color: #6c757d;">0% 完成 (0/10 章节)</small>
                            </div>
                        </div>
                        """)

                        # 快捷操作
                        gr.HTML("""
                        <div class="feature-card">
                            <h4>⚡ 快捷操作</h4>
                            <div style="font-size: 0.9rem; line-height: 1.6;">
                                <div>🔧 <strong>Ctrl+S</strong> - 保存当前内容</div>
                                <div>📝 <strong>Ctrl+E</strong> - 编辑模式</div>
                                <div>🔄 <strong>Ctrl+R</strong> - 重新生成</div>
                                <div>💾 <strong>Ctrl+Shift+S</strong> - 导出文件</div>
                            </div>
                        </div>
                        """)

            # Tab 2: 详细配置
            with gr.Tab("🔧 模型配置", id="config"):
                with gr.Column(elem_classes=["tab-content"]):
                    with gr.Row():
                        with gr.Column(scale=2):
                            with gr.Row():
                                with gr.Column():
                                    gr.HTML("""
                                    <div class="config-section">
                                        <h3>🤖 LLM模型设置</h3>
                                        <p>配置用于文本生成的大语言模型</p>
                                    </div>
                                    """)
                                llm_interface = gr.Dropdown(
                                    choices=llm_interfaces,
                                    label="🔌 接口类型",
                                    value=default_llm_interface,
                                    info="选择AI服务提供商"
                                )
                                llm_api_key = gr.Textbox(
                                    label="🔑 API Key",
                                    type="password",
                                    value=default_llm_api_key,
                                    placeholder="请输入API密钥",
                                    info="从服务商获取的API密钥"
                                )
                                llm_base_url = gr.Textbox(
                                    label="🌐 Base URL",
                                    value=default_llm_base_url,
                                    placeholder="API基础URL",
                                    info="API服务的基础地址"
                                )
                                llm_model = gr.Textbox(
                                    label="🎯 模型名称",
                                    value=default_llm_model,
                                    placeholder="模型名称",
                                    info="具体的模型标识符"
                                )

                                gr.HTML("""
                                <div style="margin: 1rem 0;">
                                    <h4>⚙️ 生成参数</h4>
                                </div>
                                """)
                                with gr.Row():
                                    temperature = gr.Slider(
                                        label="🌡️ Temperature",
                                        minimum=0.0,
                                        maximum=2.0,
                                        value=default_temperature,
                                        step=0.1,
                                        info="控制输出的随机性 (0.0-2.0)"
                                    )
                                    max_tokens = gr.Number(
                                        label="📏 Max Tokens",
                                        value=default_max_tokens,
                                        minimum=1,
                                        info="单次生成的最大字符数"
                                    )
                                    timeout = gr.Number(
                                        label="⏱️ Timeout (秒)",
                                        value=default_timeout,
                                        minimum=1,
                                        info="请求超时时间"
                                    )

                                btn_test_llm = gr.Button("🧪 测试LLM配置", variant="primary", elem_classes=["primary-button"])

                            with gr.Column():
                                gr.HTML("""
                                <div class="config-section">
                                    <h3>🔍 Embedding模型设置</h3>
                                    <p>配置用于向量检索的嵌入模型</p>
                                </div>
                                """)
                                embedding_interface = gr.Dropdown(
                                    choices=llm_interfaces,
                                    label="🔌 接口类型",
                                    value=default_embedding_interface,
                                    info="选择Embedding服务提供商"
                                )
                                embedding_api_key = gr.Textbox(
                                    label="🔑 API Key",
                                    type="password",
                                    value=default_embedding_api_key,
                                    placeholder="请输入API密钥",
                                    info="可与LLM使用相同密钥"
                                )
                                embedding_base_url = gr.Textbox(
                                    label="🌐 Base URL",
                                    value=default_embedding_base_url,
                                    placeholder="API基础URL",
                                    info="Embedding API的基础地址"
                                )
                                embedding_model = gr.Textbox(
                                    label="🎯 模型名称",
                                    value=default_embedding_model,
                                    placeholder="Embedding模型名称",
                                    info="向量化模型的标识符"
                                )

                                gr.HTML("""
                                <div style="margin: 1rem 0;">
                                    <h4>🔧 检索参数</h4>
                                </div>
                                """)
                                retrieval_k = gr.Number(
                                    label="📊 检索数量 (K)",
                                    value=default_retrieval_k,
                                    minimum=1,
                                    maximum=20,
                                    info="每次检索返回的相关片段数量"
                                )

                                btn_test_embedding = gr.Button("🧪 测试Embedding配置", variant="primary", elem_classes=["primary-button"])

                    with gr.Column(scale=1):
                        # 配置测试日志区域
                        gr.HTML("""
                        <div class="config-section">
                            <h3>📋 配置测试日志</h3>
                            <p>实时显示模型配置测试的详细过程</p>
                        </div>
                        """)
                        config_log_output = gr.Textbox(
                            label="测试日志",
                            lines=20,
                            max_lines=25,
                            interactive=False,
                            value="",
                            placeholder="💡 点击测试按钮查看详细日志...\n\n🔍 这里会显示：\n• 连接状态\n• 请求参数\n• 响应结果\n• 错误诊断\n• 性能指标",
                            elem_classes=["log-container"]
                        )

                        # 清空日志按钮
                        btn_clear_config_log = gr.Button("🗑️ 清空日志", variant="secondary")

                        # 配置状态卡片
                        gr.HTML("""
                        <div class="feature-card">
                            <h4>📊 配置状态</h4>
                            <div style="margin: 0.5rem 0;">
                                <div style="margin: 0.3rem 0;">
                                    <span class="status-indicator status-warning"></span>
                                    <span style="font-size: 0.9rem;">LLM: 待测试</span>
                                </div>
                                <div style="margin: 0.3rem 0;">
                                    <span class="status-indicator status-warning"></span>
                                    <span style="font-size: 0.9rem;">Embedding: 待测试</span>
                                </div>
                            </div>
                        </div>
                        """)

                        # 推荐配置
                        gr.HTML("""
                        <div class="feature-card">
                            <h4>💡 推荐配置</h4>
                            <div style="font-size: 0.85rem; line-height: 1.5;">
                                <strong>🚀 快速开始:</strong><br>
                                • OpenAI: gpt-4o-mini<br>
                                • Gemini: gemini-1.5-flash<br>
                                • DeepSeek: deepseek-chat<br><br>
                                <strong>⚙️ 参数建议:</strong><br>
                                • Temperature: 0.7-0.9<br>
                                • Max Tokens: 4096-8192<br>
                                • Timeout: 60-300秒
                            </div>
                        </div>
                        """)

            # Tab 3: 小说参数
            with gr.Tab("📚 小说参数", id="params"):
                with gr.Column(elem_classes=["tab-content"]):
                    gr.Markdown("### 📖 基本设置")

                    topic_input = gr.Textbox(
                        label="主题 (Topic)",
                        lines=3,
                        placeholder="请描述小说的主题和背景...",
                        value=default_topic
                    )

                    with gr.Row():
                        genre_input = gr.Dropdown(
                            choices=genres,
                            label="类型",
                            value=default_genre
                        )
                        num_chapters_input = gr.Number(
                            label="章节数",
                            value=default_num_chapters,
                            minimum=1
                        )
                        word_number_input = gr.Number(
                            label="每章字数",
                            value=default_word_number,
                            minimum=100
                        )

                    gr.Markdown("### 🎭 可选元素")

                    characters_involved_input = gr.Textbox(
                        label="核心人物",
                        lines=2,
                        value=default_characters_involved,
                        placeholder="描述主要角色..."
                    )

                    with gr.Row():
                        key_items_input = gr.Textbox(
                            label="关键道具",
                            value=default_key_items,
                            placeholder="重要物品或道具..."
                        )
                        scene_location_input = gr.Textbox(
                            label="空间坐标",
                            value=default_scene_location,
                            placeholder="主要场景位置..."
                        )
                        time_constraint_input = gr.Textbox(
                            label="时间压力",
                            value=default_time_constraint,
                            placeholder="时间相关的约束..."
                        )

            # Tab 4: 文件管理
            with gr.Tab("📁 文件管理", id="files"):
                with gr.Column(elem_classes=["tab-content"]):
                    with gr.Tabs():
                        with gr.Tab("小说架构"):
                            with gr.Row():
                                btn_load_architecture = gr.Button("加载 Novel_architecture.txt")
                                btn_save_architecture = gr.Button("保存修改")
                        architecture_content = gr.Textbox(
                            label="小说架构内容",
                            lines=20,
                            placeholder="小说架构内容将显示在这里...",
                            interactive=True
                        )

                    with gr.Tab("章节蓝图"):
                        with gr.Row():
                            btn_load_blueprint = gr.Button("加载 Novel_directory.txt")
                            btn_save_blueprint = gr.Button("保存修改")
                        blueprint_content = gr.Textbox(
                            label="章节蓝图内容",
                            lines=20,
                            placeholder="章节蓝图内容将显示在这里...",
                            interactive=True
                        )

                    with gr.Tab("角色状态"):
                        with gr.Row():
                            btn_load_character = gr.Button("加载 character_state.txt")
                            btn_save_character = gr.Button("保存修改")
                        character_content = gr.Textbox(
                            label="角色状态内容",
                            lines=20,
                            placeholder="角色状态内容将显示在这里...",
                            interactive=True
                        )

                    with gr.Tab("全局摘要"):
                        with gr.Row():
                            btn_load_summary = gr.Button("加载 global_summary.txt")
                            btn_save_summary = gr.Button("保存修改")
                        summary_content = gr.Textbox(
                            label="全局摘要内容",
                            lines=20,
                            placeholder="全局摘要内容将显示在这里...",
                            interactive=True
                        )

        # 在Blocks上下文内直接设置事件处理器
        # 配置相关事件
        btn_load_config.click(
            fn=handle_load_config,
            outputs=[
                llm_interface, llm_api_key, llm_base_url,
                llm_model, temperature, max_tokens, timeout,
                embedding_interface, embedding_api_key, embedding_base_url,
                embedding_model, retrieval_k,
                topic_input, genre_input, num_chapters_input,
                word_number_input, filepath_input, user_guidance_input,
                characters_involved_input, key_items_input,
                scene_location_input, time_constraint_input,
                log_output
            ]
        )

        btn_save_config.click(
            fn=handle_save_config,
            inputs=[
                llm_interface, llm_api_key, llm_base_url,
                llm_model, temperature, max_tokens, timeout,
                embedding_interface, embedding_api_key, embedding_base_url,
                embedding_model, retrieval_k,
                topic_input, genre_input, num_chapters_input,
                word_number_input, filepath_input, user_guidance_input,
                characters_involved_input, key_items_input,
                scene_location_input, time_constraint_input
            ],
            outputs=log_output
        )

        # 测试配置事件
        btn_test_llm.click(
            fn=handle_test_llm_config,
            inputs=[
                llm_interface, llm_api_key, llm_base_url,
                llm_model, temperature, max_tokens, timeout, config_log_output
            ],
            outputs=config_log_output
        )

        btn_test_embedding.click(
            fn=handle_test_embedding_config,
            inputs=[
                embedding_interface, embedding_api_key,
                embedding_base_url, embedding_model, config_log_output
            ],
            outputs=config_log_output
        )

        # 清空配置日志事件
        btn_clear_config_log.click(
            fn=handle_clear_config_log,
            outputs=config_log_output
        )

        # 快速配置和开始按钮事件
        quick_config_btn.click(
            fn=lambda: None,
            js="() => { document.querySelector('[data-testid=\"tab-config\"]').click(); }"
        )

        quick_start_btn.click(
            fn=lambda: None,
            js="() => { document.querySelector('[data-testid=\"tab-main\"]').click(); }"
        )

        # 核心生成功能事件
        btn_step1.click(
            fn=handle_generate_architecture,
            inputs=[
                llm_interface, llm_api_key, llm_base_url,
                llm_model, temperature, max_tokens, timeout,
                topic_input, genre_input, num_chapters_input,
                word_number_input, filepath_input, user_guidance_input,
                log_output
            ],
            outputs=log_output
        )

        btn_step2.click(
            fn=handle_generate_blueprint,
            inputs=[
                llm_interface, llm_api_key, llm_base_url,
                llm_model, temperature, max_tokens, timeout,
                filepath_input, log_output
            ],
            outputs=log_output
        )

        btn_step3.click(
            fn=handle_generate_chapter_draft,
            inputs=[
                llm_interface, llm_api_key, llm_base_url,
                llm_model, temperature, max_tokens, timeout,
                embedding_interface, embedding_api_key, embedding_base_url,
                embedding_model, retrieval_k,
                filepath_input, chapter_num_input, user_guidance_input,
                log_output
            ],
            outputs=[chapter_content, log_output]
        )

        btn_step4.click(
            fn=handle_finalize_chapter,
            inputs=[
                llm_interface, llm_api_key, llm_base_url,
                llm_model, temperature, max_tokens, timeout,
                embedding_interface, embedding_api_key, embedding_base_url,
                embedding_model,
                filepath_input, chapter_num_input, chapter_content,
                log_output
            ],
            outputs=log_output
        )

        # 辅助功能事件
        btn_consistency.click(
            fn=handle_consistency_check,
            inputs=[
                llm_interface, llm_api_key, llm_base_url,
                llm_model, temperature, max_tokens, timeout,
                filepath_input, chapter_num_input, log_output
            ],
            outputs=log_output
        )

        btn_import_knowledge.click(
            fn=handle_import_knowledge,
            inputs=[filepath_input, log_output],
            outputs=log_output
        )

        btn_clear_vectorstore.click(
            fn=handle_clear_vectorstore,
            inputs=[filepath_input, log_output],
            outputs=log_output
        )

        btn_plot_arcs.click(
            fn=handle_show_plot_arcs,
            inputs=[filepath_input, log_output],
            outputs=log_output
        )

        # 文件管理事件
        btn_load_architecture.click(
            fn=lambda filepath: handle_load_file(filepath, "Novel_architecture.txt"),
            inputs=filepath_input,
            outputs=[architecture_content, log_output]
        )

        btn_save_architecture.click(
            fn=lambda filepath, content: handle_save_file(filepath, "Novel_architecture.txt", content),
            inputs=[filepath_input, architecture_content],
            outputs=log_output
        )

        btn_load_blueprint.click(
            fn=lambda filepath: handle_load_file(filepath, "Novel_directory.txt"),
            inputs=filepath_input,
            outputs=[blueprint_content, log_output]
        )

        btn_save_blueprint.click(
            fn=lambda filepath, content: handle_save_file(filepath, "Novel_directory.txt", content),
            inputs=[filepath_input, blueprint_content],
            outputs=log_output
        )

        btn_load_character.click(
            fn=lambda filepath: handle_load_file(filepath, "character_state.txt"),
            inputs=filepath_input,
            outputs=[character_content, log_output]
        )

        btn_save_character.click(
            fn=lambda filepath, content: handle_save_file(filepath, "character_state.txt", content),
            inputs=[filepath_input, character_content],
            outputs=log_output
        )

        btn_load_summary.click(
            fn=lambda filepath: handle_load_file(filepath, "global_summary.txt"),
            inputs=filepath_input,
            outputs=[summary_content, log_output]
        )

        btn_save_summary.click(
            fn=lambda filepath, content: handle_save_file(filepath, "global_summary.txt", content),
            inputs=[filepath_input, summary_content],
            outputs=log_output
        )

        return demo

# 事件处理函数
def handle_load_config():
    """处理加载配置事件"""
    config_data, message = app.load_config_from_file()
    if config_data:
        return (
            config_data["llm_interface"],
            config_data["llm_api_key"],
            config_data["llm_base_url"],
            config_data["llm_model"],
            config_data["temperature"],
            config_data["max_tokens"],
            config_data["timeout"],
            config_data["embedding_interface"],
            config_data["embedding_api_key"],
            config_data["embedding_base_url"],
            config_data["embedding_model"],
            config_data["retrieval_k"],
            config_data["topic"],
            config_data["genre"],
            config_data["num_chapters"],
            config_data["word_number"],
            config_data["filepath"],
            config_data["user_guidance"],
            config_data["characters_involved"],
            config_data["key_items"],
            config_data["scene_location"],
            config_data["time_constraint"],
            message
        )
    else:
        return (
            "OpenAI", "", "https://api.openai.com/v1", "gpt-4o-mini", 0.7, 8192, 600,
            "OpenAI", "", "https://api.openai.com/v1", "text-embedding-ada-002", 4,
            "", "玄幻", 10, 3000, "", "", "", "", "", "",
            message
        )

def handle_save_config(llm_interface, llm_api_key, llm_base_url, llm_model, temperature, max_tokens, timeout,
                      embedding_interface, embedding_api_key, embedding_base_url, embedding_model, retrieval_k,
                      topic, genre, num_chapters, word_number, filepath, user_guidance,
                      characters_involved, key_items, scene_location, time_constraint):
    """处理保存配置事件"""
    llm_config = app.get_llm_config_from_form(
        llm_interface, llm_api_key, llm_base_url, llm_model, temperature, max_tokens, timeout
    )
    embedding_config = app.get_embedding_config_from_form(
        embedding_interface, embedding_api_key, embedding_base_url, embedding_model, retrieval_k
    )
    novel_params = {
        "topic": topic,
        "genre": genre,
        "num_chapters": num_chapters,
        "word_number": word_number,
        "filepath": filepath,
        "user_guidance": user_guidance,
        "characters_involved": characters_involved,
        "key_items": key_items,
        "scene_location": scene_location,
        "time_constraint": time_constraint
    }

    return app.save_config_to_file(llm_config, embedding_config, novel_params)

def handle_test_llm_config(interface_format, api_key, base_url, model_name, temperature, max_tokens, timeout, current_log):
    """处理测试LLM配置事件"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    log_msg = current_log + f"\n[{timestamp}] 🧪 开始测试LLM配置...\n"
    log_msg += f"接口类型: {interface_format}\n"
    log_msg += f"模型名称: {model_name}\n"
    log_msg += f"Base URL: {base_url}\n"
    log_msg += f"Temperature: {temperature}\n"
    log_msg += f"Max Tokens: {max_tokens}\n"
    log_msg += f"Timeout: {timeout}秒\n"
    log_msg += "-" * 50 + "\n"

    try:
        log_msg += "正在创建LLM适配器...\n"
        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        log_msg += "✅ LLM适配器创建成功\n"

        test_prompt = "Please reply 'OK'"
        log_msg += f"发送测试提示: {test_prompt}\n"
        log_msg += "等待模型响应...\n"

        response = llm_adapter.invoke(test_prompt)
        if response and response.strip():
            log_msg += f"✅ LLM配置测试成功！\n"
            log_msg += f"模型回复: {response}\n"
            log_msg += f"回复长度: {len(response)} 字符\n"
        else:
            log_msg += "❌ LLM配置测试失败：未获取到响应\n"
            log_msg += "可能原因：\n"
            log_msg += "1. API密钥无效\n"
            log_msg += "2. 网络连接问题\n"
            log_msg += "3. 模型名称错误\n"
            log_msg += "4. 服务器暂时不可用\n"

    except Exception as e:
        log_msg += f"❌ LLM配置测试出错: {str(e)}\n"
        log_msg += "详细错误信息:\n"
        import traceback
        log_msg += traceback.format_exc() + "\n"

    log_msg += "=" * 50 + "\n"
    return log_msg

def handle_test_embedding_config(interface_format, api_key, base_url, model_name, current_log):
    """处理测试Embedding配置事件"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    log_msg = current_log + f"\n[{timestamp}] 🔍 开始测试Embedding配置...\n"
    log_msg += f"接口类型: {interface_format}\n"
    log_msg += f"模型名称: {model_name}\n"
    log_msg += f"Base URL: {base_url}\n"
    log_msg += "-" * 50 + "\n"

    try:
        log_msg += "正在创建Embedding适配器...\n"
        embedding_adapter = create_embedding_adapter(
            interface_format=interface_format,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
        log_msg += "✅ Embedding适配器创建成功\n"

        test_text = "这是一个测试文本"
        log_msg += f"测试文本: {test_text}\n"
        log_msg += "正在生成向量...\n"

        embeddings = embedding_adapter.embed_query(test_text)
        if embeddings and len(embeddings) > 0:
            log_msg += f"✅ Embedding配置测试成功！\n"
            log_msg += f"生成的向量维度: {len(embeddings)}\n"
            log_msg += f"向量前5个值: {embeddings[:5]}\n"
        else:
            log_msg += "❌ Embedding配置测试失败：未获取到向量\n"
            log_msg += "可能原因：\n"
            log_msg += "1. API密钥无效\n"
            log_msg += "2. 模型名称错误\n"
            log_msg += "3. 网络连接问题\n"
            log_msg += "4. 服务不支持该模型\n"

    except Exception as e:
        log_msg += f"❌ Embedding配置测试出错: {str(e)}\n"
        log_msg += "详细错误信息:\n"
        import traceback
        log_msg += traceback.format_exc() + "\n"

    log_msg += "=" * 50 + "\n"
    return log_msg

def handle_clear_config_log():
    """清空配置日志"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] 📋 配置测试日志已清空\n"

def handle_load_file(filepath, filename):
    """处理文件加载事件"""
    if not filepath:
        return "", "❌ 请先设置保存文件路径"

    full_path = os.path.join(filepath, filename)
    content = read_file(full_path)
    if content:
        return content, f"✅ 已加载 {filename}"
    else:
        return "", f"❌ 无法加载 {filename}"

def handle_save_file(filepath, filename, content):
    """处理文件保存事件"""
    if not filepath:
        return "❌ 请先设置保存文件路径"

    full_path = os.path.join(filepath, filename)
    try:
        clear_file_content(full_path)
        save_string_to_txt(content, full_path)
        return f"✅ 已保存 {filename}"
    except Exception as e:
        return f"❌ 保存 {filename} 时出错: {str(e)}"

# 核心生成功能处理函数
def handle_generate_architecture(llm_interface, llm_api_key, llm_base_url, llm_model, temperature, max_tokens, timeout,
                                topic, genre, num_chapters, word_number, filepath, user_guidance, current_log):
    """处理生成小说架构事件"""
    if not filepath:
        return current_log + app.log_message("❌ 请先设置保存文件路径")

    if not topic.strip():
        return current_log + app.log_message("❌ 请先输入小说主题")

    try:
        log_msg = current_log + app.log_message("🚀 开始生成小说架构...")

        # 在后台线程中执行生成
        def generate_task():
            try:
                Novel_architecture_generate(
                    interface_format=llm_interface,
                    api_key=llm_api_key,
                    base_url=llm_base_url,
                    llm_model=llm_model,
                    topic=topic,
                    genre=genre,
                    number_of_chapters=int(num_chapters),
                    word_number=int(word_number),
                    filepath=filepath,
                    user_guidance=user_guidance,
                    temperature=temperature,
                    max_tokens=int(max_tokens),
                    timeout=int(timeout)
                )
                return "✅ 小说架构生成完成！"
            except Exception as e:
                return f"❌ 生成小说架构时出错: {str(e)}"

        # 这里简化处理，实际应该使用异步或进度条
        result = generate_task()
        return log_msg + app.log_message(result)

    except Exception as e:
        return current_log + app.log_message(f"❌ 生成小说架构时出错: {str(e)}")

def handle_generate_blueprint(llm_interface, llm_api_key, llm_base_url, llm_model, temperature, max_tokens, timeout,
                             filepath, current_log):
    """处理生成章节蓝图事件"""
    if not filepath:
        return current_log + app.log_message("❌ 请先设置保存文件路径")

    try:
        log_msg = current_log + app.log_message("🚀 开始生成章节蓝图...")

        def generate_task():
            try:
                Chapter_blueprint_generate(
                    interface_format=llm_interface,
                    api_key=llm_api_key,
                    base_url=llm_base_url,
                    llm_model=llm_model,
                    filepath=filepath,
                    temperature=temperature,
                    max_tokens=int(max_tokens),
                    timeout=int(timeout)
                )
                return "✅ 章节蓝图生成完成！"
            except Exception as e:
                return f"❌ 生成章节蓝图时出错: {str(e)}"

        result = generate_task()
        return log_msg + app.log_message(result)

    except Exception as e:
        return current_log + app.log_message(f"❌ 生成章节蓝图时出错: {str(e)}")

def handle_generate_chapter_draft(llm_interface, llm_api_key, llm_base_url, llm_model, temperature, max_tokens, timeout,
                                 embedding_interface, embedding_api_key, embedding_base_url, embedding_model, retrieval_k,
                                 filepath, chapter_num, user_guidance, current_log):
    """处理生成章节草稿事件"""
    if not filepath:
        return "", current_log + app.log_message("❌ 请先设置保存文件路径")

    try:
        log_msg = current_log + app.log_message(f"🚀 开始生成第{chapter_num}章草稿...")

        def generate_task():
            try:
                result = generate_chapter_draft(
                    interface_format=llm_interface,
                    api_key=llm_api_key,
                    base_url=llm_base_url,
                    llm_model=llm_model,
                    embedding_interface_format=embedding_interface,
                    embedding_api_key=embedding_api_key,
                    embedding_base_url=embedding_base_url,
                    embedding_model_name=embedding_model,
                    retrieval_k=int(retrieval_k),
                    filepath=filepath,
                    chapter_num=int(chapter_num),
                    user_guidance=user_guidance,
                    temperature=temperature,
                    max_tokens=int(max_tokens),
                    timeout=int(timeout)
                )

                # 读取生成的章节内容
                chapter_file = os.path.join(filepath, f"chapter_{chapter_num}.txt")
                chapter_content = read_file(chapter_file)

                return chapter_content, "✅ 章节草稿生成完成！"
            except Exception as e:
                return "", f"❌ 生成章节草稿时出错: {str(e)}"

        chapter_content, result_msg = generate_task()
        return chapter_content, log_msg + app.log_message(result_msg)

    except Exception as e:
        return "", current_log + app.log_message(f"❌ 生成章节草稿时出错: {str(e)}")

def handle_finalize_chapter(llm_interface, llm_api_key, llm_base_url, llm_model, temperature, max_tokens, timeout,
                           embedding_interface, embedding_api_key, embedding_base_url, embedding_model,
                           filepath, chapter_num, chapter_content, current_log):
    """处理定稿章节事件"""
    if not filepath:
        return current_log + app.log_message("❌ 请先设置保存文件路径")

    if not chapter_content.strip():
        return current_log + app.log_message("❌ 章节内容为空，无法定稿")

    try:
        log_msg = current_log + app.log_message(f"🚀 开始定稿第{chapter_num}章...")

        # 先保存当前章节内容
        chapter_file = os.path.join(filepath, f"chapter_{chapter_num}.txt")
        save_string_to_txt(chapter_content, chapter_file)

        def finalize_task():
            try:
                finalize_chapter(
                    interface_format=llm_interface,
                    api_key=llm_api_key,
                    base_url=llm_base_url,
                    llm_model=llm_model,
                    embedding_interface_format=embedding_interface,
                    embedding_api_key=embedding_api_key,
                    embedding_base_url=embedding_base_url,
                    embedding_model_name=embedding_model,
                    filepath=filepath,
                    chapter_num=int(chapter_num),
                    temperature=temperature,
                    max_tokens=int(max_tokens),
                    timeout=int(timeout)
                )
                return "✅ 章节定稿完成！已更新全局摘要、角色状态和向量库。"
            except Exception as e:
                return f"❌ 定稿章节时出错: {str(e)}"

        result = finalize_task()
        return log_msg + app.log_message(result)

    except Exception as e:
        return current_log + app.log_message(f"❌ 定稿章节时出错: {str(e)}")

# 辅助功能处理函数
def handle_consistency_check(llm_interface, llm_api_key, llm_base_url, llm_model, temperature, max_tokens, timeout,
                            filepath, chapter_num, current_log):
    """处理一致性检查事件"""
    if not filepath:
        return current_log + app.log_message("❌ 请先设置保存文件路径")

    try:
        log_msg = current_log + app.log_message(f"🔍 开始检查第{chapter_num}章的一致性...")

        def check_task():
            try:
                result = check_consistency(
                    interface_format=llm_interface,
                    api_key=llm_api_key,
                    base_url=llm_base_url,
                    llm_model=llm_model,
                    filepath=filepath,
                    chapter_num=int(chapter_num),
                    temperature=temperature,
                    max_tokens=int(max_tokens),
                    timeout=int(timeout)
                )
                return f"✅ 一致性检查完成！\n{result}"
            except Exception as e:
                return f"❌ 一致性检查时出错: {str(e)}"

        result = check_task()
        return log_msg + app.log_message(result)

    except Exception as e:
        return current_log + app.log_message(f"❌ 一致性检查时出错: {str(e)}")

def handle_import_knowledge(filepath, current_log):
    """处理导入知识库事件"""
    if not filepath:
        return current_log + app.log_message("❌ 请先设置保存文件路径")

    try:
        log_msg = current_log + app.log_message("📚 开始导入知识库...")

        # 这里简化处理，实际应该提供文件选择界面
        knowledge_file = os.path.join(filepath, "knowledge.txt")
        if os.path.exists(knowledge_file):
            import_knowledge_file(knowledge_file, filepath)
            return log_msg + app.log_message("✅ 知识库导入完成！")
        else:
            return log_msg + app.log_message(f"❌ 未找到知识库文件: {knowledge_file}")

    except Exception as e:
        return current_log + app.log_message(f"❌ 导入知识库时出错: {str(e)}")

def handle_clear_vectorstore(filepath, current_log):
    """处理清空向量库事件"""
    if not filepath:
        return current_log + app.log_message("❌ 请先设置保存文件路径")

    try:
        log_msg = current_log + app.log_message("🗑️ 开始清空向量库...")
        clear_vector_store(filepath)
        return log_msg + app.log_message("✅ 向量库已清空！")

    except Exception as e:
        return current_log + app.log_message(f"❌ 清空向量库时出错: {str(e)}")

def handle_show_plot_arcs(filepath, current_log):
    """处理查看剧情要点事件"""
    if not filepath:
        return current_log + app.log_message("❌ 请先设置保存文件路径")

    try:
        plot_arcs_file = os.path.join(filepath, "plot_arcs.txt")
        content = read_file(plot_arcs_file)
        if content:
            return current_log + app.log_message(f"📖 剧情要点内容：\n{content}")
        else:
            return current_log + app.log_message("❌ 未找到剧情要点文件")

    except Exception as e:
        return current_log + app.log_message(f"❌ 查看剧情要点时出错: {str(e)}")

# 删除重复的事件处理器函数，已经在create_interface中直接设置

if __name__ == "__main__":
    demo = create_interface()

    print("🚀 启动AI小说生成器Web界面...")
    print("📝 访问地址: http://localhost:7860")

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )