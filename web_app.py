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

    def update_params_overview(self, topic, genre, num_chapters, word_number):
        """更新参数概览显示"""
        topic_display = topic if topic.strip() else "未设置"
        if len(topic_display) > 50:
            topic_display = topic_display[:50] + "..."

        # 使用字符串拼接避免f-string中的复杂JavaScript
        html_content = """
        <div style="background: #f8f9fa; border-radius: 12px; padding: 1.5rem; border-left: 4px solid #667eea;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <div>
                    <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">📖 小说主题</div>
                    <div style="font-size: 0.95rem; color: #333; font-weight: 500;">""" + topic_display + """</div>
                </div>
                <div>
                    <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">📚 类型</div>
                    <div style="font-size: 0.95rem; color: #333; font-weight: 500;">""" + str(genre) + """</div>
                </div>
                <div>
                    <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">📑 章节数</div>
                    <div style="font-size: 0.95rem; color: #333; font-weight: 500;">""" + str(num_chapters) + """章</div>
                </div>
                <div>
                    <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.25rem;">📝 每章字数</div>
                    <div style="font-size: 0.95rem; color: #333; font-weight: 500;">""" + str(word_number) + """字</div>
                </div>
            </div>
        </div>
        """
        return html_content

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
    /* 全局样式 - 强制统一宽度 */
    .gradio-container {
        max-width: 1400px !important;
        width: 100% !important;
        margin: 0 auto !important;
        padding: 1rem !important;
        box-sizing: border-box !important;
    }

    /* 统一的页面容器 - 所有内容的父容器 */
    .page-container {
        max-width: 1400px !important;
        width: 100% !important;
        margin: 0 auto !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }

    /* 强制所有标签页内容宽度一致 */
    .gradio-tabitem {
        max-width: 1400px !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 auto !important;
        box-sizing: border-box !important;
    }

    /* 强制所有行和列的宽度一致 */
    .gradio-row {
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
    }

    .gradio-column {
        width: 100% !important;
    }

    /* 强制所有内容元素宽度一致 */
    .gradio-tabs {
        max-width: 1400px !important;
        width: 100% !important;
        margin: 0 auto !important;
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
        box-sizing: border-box !important;
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
        box-sizing: border-box !important;
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

    /* 响应式设计 */
    @media (max-width: 768px) {
        .main-title { font-size: 2rem; }
        .main-subtitle { font-size: 1rem; }
        .feature-card { margin: 0.5rem 0; padding: 1rem; }
    }
    """

    with gr.Blocks(
        title="AI小说生成器 - 智能创作平台",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as demo:

        # 统一的页面容器 - 包含所有内容
        with gr.Column(elem_classes=["page-container"]):
            # Landing页面头部
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
                with gr.Tab("🤖 AI自动创作", id="main"):
                    # AI创作控制台
                    # with gr.Row():
                    #     ai_control_panel = gr.HTML("""
                    #     <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    #                 color: white; padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem;
                    #                 box-shadow: 0 4px 20px rgba(102,126,234,0.3);">
                    #         <div style="display: flex; justify-content: space-between; align-items: center;">
                    #             <div>
                    #                 <p style="margin: 0; opacity: 0.9; font-size: 0.95rem;">
                    #                     基于大语言模型的全自动小说创作系统，从构思到成稿一键完成
                    #                 </p>
                    #             </div>
                    #             <div style="text-align: center;">
                    #                 <div style="font-size: 2.5rem; margin-bottom: 0.3rem;">🎯</div>
                    #                 <div style="font-size: 0.85rem; opacity: 0.9;">AI驱动</div>
                    #             </div>
                    #         </div>
                    #     </div>
                    #     """)

                    # 小说基础参数设置区
                    gr.HTML("""
                    <div style="margin: 1.5rem 0 1rem 0;">
                        <h3 style="margin: 0 0 0.5rem 0; color: #333; display: flex; align-items: center; gap: 0.5rem;">
                            📖 小说基础参数设置
                            <span style="background: #e3f2fd; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; color: #1976d2;">
                                可直接编辑
                            </span>
                        </h3>
                        <p style="margin: 0; color: #666; font-size: 0.9rem;">设置小说的基本信息，这些参数将影响AI生成的内容风格和结构</p>
                    </div>
                    """)

                    # 基本设置 - 可折叠
                    with gr.Accordion("📖 基本设置", open=True):
                        topic_input = gr.Textbox(
                            label="📝 主题描述",
                            lines=4,
                            max_lines=8,
                            placeholder="请详细描述小说的主题、背景和核心故事...\n\n例如：\n• 故事背景：现代都市/古代仙侠/未来科幻等\n• 主要冲突：角色面临的核心挑战\n• 情感主线：爱情/友情/成长/复仇等\n• 独特元素：让故事与众不同的特色",
                            value=default_topic,
                            info="详细的主题描述有助于AI生成更符合预期的内容",
                            interactive=True,
                            show_label=True,
                            container=True,
                            scale=1
                        )

                        with gr.Row():
                            genre_input = gr.Dropdown(
                                choices=genres,
                                label="📚 小说类型",
                                value=default_genre,
                                info="选择小说的主要类型"
                            )
                            num_chapters_input = gr.Number(
                                label="📊 章节数量",
                                value=default_num_chapters,
                                minimum=1,
                                maximum=100,
                                info="计划创作的总章节数"
                            )
                            word_number_input = gr.Number(
                                label="📄 每章字数",
                                value=default_word_number,
                                minimum=100,
                                maximum=10000,
                                info="每章的目标字数"
                            )

                    # 可选元素 - 可折叠
                    with gr.Accordion("🎭 可选创作元素", open=False):
                        characters_involved_input = gr.Textbox(
                            label="👥 核心人物",
                            lines=3,
                            max_lines=6,
                            value=default_characters_involved,
                            placeholder="描述主要角色的性格、背景和关系...\n\n例如：\n• 主角：姓名、年龄、性格特点、能力特长\n• 配角：与主角的关系、作用和特色\n• 反派：动机、能力、与主角的冲突",
                            info="详细的人物设定有助于保持角色一致性",
                            interactive=True,
                            show_label=True,
                            container=True
                        )

                        with gr.Row():
                            key_items_input = gr.Textbox(
                                label="🔑 关键道具",
                                value=default_key_items,
                                placeholder="重要的物品、武器或道具...",
                                info="影响剧情的重要物品"
                            )
                            scene_location_input = gr.Textbox(
                                label="🌍 空间坐标",
                                value=default_scene_location,
                                placeholder="主要场景和地点...",
                                info="故事发生的主要场所"
                            )
                            time_constraint_input = gr.Textbox(
                                label="⏰ 时间压力",
                                value=default_time_constraint,
                                placeholder="时间相关的约束或紧迫感...",
                                info="推动剧情发展的时间因素"
                            )

                        # 参数操作按钮
                        with gr.Row():
                            btn_load_config = gr.Button("📥 加载配置", elem_classes=["primary-button"], scale=1)
                            btn_save_config = gr.Button("💾 保存配置", elem_classes=["primary-button"], scale=1)
                            btn_reset_params = gr.Button("🔄 重置参数", variant="secondary", scale=1)









                    # AI自动化生成控制台
                    gr.HTML("""
                    <div style="margin: 1.5rem 0 1rem 0;">
                        <h3 style="margin: 0 0 0.5rem 0; color: #333; display: flex; align-items: center; gap: 0.5rem;">
                            🚀 AI自动化生成流程
                            <span style="background: #e8f5e8; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; color: #2e7d32;">
                                一键生成
                            </span>
                        </h3>
                        <p style="margin: 0; color: #666; font-size: 0.9rem;">AI将根据您的设置自动生成完整小说，您也可以分步骤控制生成过程</p>
                    </div>
                    """)



                    # 创作参数设置区
                    gr.HTML("""
                    <div style="margin: 1.5rem 0 1rem 0;">
                        <h3 style="margin: 0 0 0.5rem 0; color: #333; display: flex; align-items: center; gap: 0.5rem;">
                            🎯 创作参数设置
                            <span style="background: #fff3e0; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; color: #f57c00;">
                                必填设置
                            </span>
                        </h3>
                        <p style="margin: 0; color: #666; font-size: 0.9rem;">请先设置以下参数，然后开始分步骤生成</p>
                    </div>
                    """)

                    with gr.Row():
                        with gr.Column(scale=1):
                            current_chapter = gr.Number(
                                label="📖 当前创作章节",
                                value=1,
                                minimum=1,
                                step=1,
                                info="选择要生成或编辑的章节"
                            )

                        with gr.Column(scale=2):
                            user_guidance_input = gr.Textbox(
                                label="📝 本章创作指导",
                                lines=3,
                                max_lines=5,
                                value=default_user_guidance,
                                placeholder="例如：主角遇到神秘老人，揭示重要线索...\n\n可以包括：\n• 本章的主要情节发展\n• 角色的行为和对话要求\n• 场景描述的重点\n• 情感基调和氛围",
                                info="对本章剧情发展的具体要求（可选）",
                                interactive=True,
                                show_label=True,
                                container=True
                            )

                        with gr.Column(scale=2):
                            filepath_input = gr.Textbox(
                                label="📁 保存路径",
                                placeholder="例如: /Users/username/novels/my_novel",
                                value=default_filepath,
                                info="小说文件的保存目录"
                            )
                    # 分步生成按钮组
                    with gr.Row():
                        btn_step1 = gr.Button(
                            "📋 第一步：生成小说架构",
                            variant="primary",
                            elem_classes=["primary-button"],
                            scale=1,
                            size="lg"
                        )
                        btn_step2 = gr.Button(
                            "📑 第二步：生成章节目录",
                            variant="secondary",
                            interactive=False,
                            scale=1,
                            size="lg"
                        )

                    with gr.Row():
                        btn_step3 = gr.Button(
                            "📝 第三步：生成指定章节",
                            variant="secondary",
                            interactive=False,
                            scale=1,
                            size="lg"
                        )
                        btn_step4 = gr.Button(
                            "✅ 第四步：内容定稿优化",
                            variant="secondary",
                            interactive=False,
                            scale=1,
                            size="lg"
                        )
                    # AI生成结果展示区 - 左右分栏布局
                    with gr.Row():
                        # 左侧：生成控制和日志区域 (40%)
                        with gr.Column(scale=2):
                            # AI运行日志和步骤状态
                            with gr.Accordion("📋 AI运行日志 & 步骤状态", open=True):
                                # 步骤状态指示器
                                gr.HTML("""
                                <div style="margin-bottom: 1rem; padding: 0.75rem; background: #f8f9fa; border-radius: 8px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                        <strong style="font-size: 0.9rem; color: #333;">🎯 当前进度</strong>
                                        <span style="font-size: 0.8rem; color: #666;">请按顺序完成</span>
                                    </div>
                                    <div style="display: flex; gap: 0.5rem;">
                                        <div style="flex: 1; padding: 0.4rem; background: #e9ecef; border-radius: 6px; text-align: center; font-size: 0.8rem; color: #495057;">
                                            📋 架构
                                        </div>
                                        <div style="flex: 1; padding: 0.4rem; background: #e9ecef; border-radius: 6px; text-align: center; font-size: 0.8rem; color: #495057;">
                                            📑 目录
                                        </div>
                                        <div style="flex: 1; padding: 0.4rem; background: #e9ecef; border-radius: 6px; text-align: center; font-size: 0.8rem; color: #495057;">
                                            📝 章节
                                        </div>
                                        <div style="flex: 1; padding: 0.4rem; background: #e9ecef; border-radius: 6px; text-align: center; font-size: 0.8rem; color: #495057;">
                                            ✅ 定稿
                                        </div>
                                    </div>
                                </div>
                                """)

                                log_output = gr.Textbox(
                                    label="",
                                    lines=8,
                                    max_lines=15,
                                    interactive=False,
                                    value="🤖 AI小说生成器已启动 - 分步生成模式\n💡 请先在\"模型配置\"页面配置AI模型\n🎯 然后按步骤进行创作：架构 → 目录 → 章节 → 定稿\n📋 每步完成后请确认内容质量再进行下一步\n",
                                    elem_classes=["log-container"],
                                    show_label=False
                                )

                                with gr.Row():
                                    btn_clear_log = gr.Button("🗑️ 清空日志", variant="secondary", scale=1)
                                    btn_export_log = gr.Button("📤 导出日志", variant="secondary", scale=1)

                        # 右侧：文件预览编辑区域 (60%) - 所见即所得
                        with gr.Column(scale=3):
                            gr.HTML("""
                            <div style="margin-bottom: 1rem;">
                                <h4 style="margin: 0; color: #333; display: flex; align-items: center; gap: 0.5rem;">
                                    📁 小说文件管理 & 预览
                                    <span style="background: #e3f2fd; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; color: #1976d2;">
                                        所见即所得
                                    </span>
                                </h4>
                                <p style="margin: 0; color: #666; font-size: 0.85rem;">AI生成的内容将实时显示在下方，您可以直接查看和编辑</p>
                            </div>
                            """)

                            # 文件管理面板 - 使用Tab组织
                            with gr.Tabs():
                                # 小说架构
                                with gr.Tab("📋 小说架构"):
                                    with gr.Row():
                                        btn_load_architecture = gr.Button("📥 加载架构文件", scale=1)
                                        btn_save_architecture = gr.Button("💾 保存修改", scale=1)
                                        btn_refresh_architecture = gr.Button("🔄 刷新显示", scale=1)
                                    architecture_content = gr.Textbox(
                                        label="",
                                        lines=15,
                                        placeholder="📋 小说架构将在这里显示...\n\n点击上方按钮加载现有架构文件，或点击左侧\"第一步：生成小说架构\"开始AI生成。\n\n生成后的架构内容将自动显示在此处，您可以直接编辑和修改。",
                                        interactive=True,
                                        show_label=False
                                    )

                                # 章节蓝图
                                with gr.Tab("📑 章节蓝图"):
                                    with gr.Row():
                                        btn_load_blueprint = gr.Button("📥 加载蓝图文件", scale=1)
                                        btn_save_blueprint = gr.Button("💾 保存修改", scale=1)
                                        btn_refresh_blueprint = gr.Button("🔄 刷新显示", scale=1)
                                    blueprint_content = gr.Textbox(
                                        label="",
                                        lines=15,
                                        placeholder="📑 章节蓝图将在这里显示...\n\n完成架构生成后，点击左侧\"第二步：生成章节目录\"来生成详细的章节蓝图。\n\n生成后的蓝图内容将自动显示在此处，您可以直接编辑章节安排。",
                                        interactive=True,
                                        show_label=False
                                    )

                                # 当前章节内容
                                with gr.Tab("📝 当前章节"):
                                    with gr.Row():
                                        btn_load_current_chapter = gr.Button("📥 加载章节文件", scale=1)
                                        btn_save_current_chapter = gr.Button("💾 保存修改", scale=1)
                                        btn_refresh_current_chapter = gr.Button("🔄 刷新显示", scale=1)
                                    chapter_content = gr.Textbox(
                                        label="",
                                        lines=15,
                                        placeholder="📝 当前章节内容将在这里显示...\n\n完成前两步后，点击左侧\"第三步：生成指定章节\"来生成具体章节内容。\n\n生成后的章节内容将自动显示在此处，您可以直接编辑和完善。",
                                        interactive=True,
                                        show_label=False
                                    )

                                # 角色状态
                                with gr.Tab("👥 角色状态"):
                                    with gr.Row():
                                        btn_load_character = gr.Button("📥 加载角色文件", scale=1)
                                        btn_save_character = gr.Button("💾 保存修改", scale=1)
                                        btn_refresh_character = gr.Button("🔄 刷新显示", scale=1)
                                    character_content = gr.Textbox(
                                        label="",
                                        lines=15,
                                        placeholder="👥 角色状态信息将在这里显示...\n\n在创作过程中，AI会自动维护角色状态信息。\n\n您可以在此查看和编辑角色的发展状态。",
                                        interactive=True,
                                        show_label=False
                                    )

                                # 全局摘要
                                with gr.Tab("📊 全局摘要"):
                                    with gr.Row():
                                        btn_load_summary = gr.Button("📥 加载摘要文件", scale=1)
                                        btn_save_summary = gr.Button("💾 保存修改", scale=1)
                                        btn_refresh_summary = gr.Button("🔄 刷新显示", scale=1)
                                    summary_content = gr.Textbox(
                                        label="",
                                        lines=15,
                                        placeholder="📊 全局摘要将在这里显示...\n\n在创作过程中，AI会自动生成和更新全局摘要。\n\n您可以在此查看整体创作进度和内容概览。",
                                        interactive=True,
                                        show_label=False
                                    )

                        # with gr.Column(scale=1):
                        #     # AI生成进度和控制
                        #     ai_generation_status = gr.HTML("""
                        #     <div style="background: #fff; border-radius: 12px; padding: 1rem; border: 2px solid #e0e0e0;">
                        #         <h4 style="margin: 0 0 1rem 0; color: #333; display: flex; align-items: center; gap: 0.5rem;">
                        #             ⚡ 生成进度
                        #         </h4>
                        #         <div style="margin-bottom: 1rem;">
                        #             <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        #                 <span style="font-size: 0.9rem; color: #666;">当前状态:</span>
                        #                 <span style="font-size: 0.9rem; color: #666;">等待开始</span>
                        #             </div>
                        #             <div style="background: #f5f5f5; border-radius: 10px; height: 8px; overflow: hidden;">
                        #                 <div style="background: #4caf50; height: 100%; width: 0%; transition: width 0.3s ease;"></div>
                        #             </div>
                        #         </div>

                        #         <div style="space-y: 0.5rem;">
                        #             <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        #                 <span style="width: 16px; height: 16px; background: #e0e0e0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem;">1</span>
                        #                 <span style="font-size: 0.85rem; color: #666;">架构设计</span>
                        #             </div>
                        #             <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        #                 <span style="width: 16px; height: 16px; background: #e0e0e0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem;">2</span>
                        #                 <span style="font-size: 0.85rem; color: #666;">目录规划</span>
                        #             </div>
                        #             <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        #                 <span style="width: 16px; height: 16px; background: #e0e0e0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem;">3</span>
                        #                 <span style="font-size: 0.85rem; color: #666;">章节生成</span>
                        #             </div>
                        #             <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                        #                 <span style="width: 16px; height: 16px; background: #e0e0e0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem;">4</span>
                        #                 <span style="font-size: 0.85rem; color: #666;">内容定稿</span>
                        #             </div>
                        #         </div>

                        #         <div style="margin-top: 1rem;">
                        #             <button style="width: 100%; padding: 0.5rem; background: #f44336; color: white; border: none; border-radius: 8px; font-size: 0.85rem; cursor: pointer;" disabled>
                        #                 ⏸️ 暂停生成
                        #             </button>
                        #         </div>
                        #     </div>
                        #     """)



                    # 快速操作区域
                    with gr.Row():

                        # 简化的配置和状态区域
                        with gr.Column():
                            # 快速操作面板（折叠）
                            with gr.Accordion("⚡ 快速操作", open=False):
                                gr.HTML("""
                                <div style="margin-bottom: 1rem; padding: 0.75rem; background: #f0f9ff; border-radius: 8px; border-left: 3px solid #0ea5e9;">
                                    <strong>🚀 一键操作</strong><br>
                                    <small style="color: #0369a1;">
                                        快速执行常用的创作和管理操作
                                    </small>
                                </div>
                                """)



                                with gr.Row():
                                    btn_consistency = gr.Button("🔍 一致性检查", elem_classes=["primary-button"], scale=1)
                                    btn_import_knowledge = gr.Button("📚 导入知识库", elem_classes=["primary-button"], scale=1)

                                with gr.Row():
                                    btn_clear_vectorstore = gr.Button("🗑️ 清空向量库", variant="stop", scale=1)
                                    btn_plot_arcs = gr.Button("📊 查看剧情要点", elem_classes=["primary-button"], scale=1)

                # Tab 2: AI模型配置
                with gr.Tab("🤖 AI模型配置", id="config"):
                    # AI模型配置引导
                    # with gr.Row():
                    #     ai_config_header = gr.HTML("""
                    #     <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    #                 color: white; padding: 2rem; border-radius: 15px; margin-bottom: 1.5rem;
                    #                 box-shadow: 0 4px 20px rgba(102,126,234,0.3);">
                    #         <div style="text-align: center;">
                    #             <h2 style="margin: 0 0 1rem 0; font-size: 1.6rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    #                 🧠 AI大脑配置中心
                    #             </h2>
                    #             <p style="margin: 0 0 1rem 0; opacity: 0.9; font-size: 1rem; max-width: 600px; margin-left: auto; margin-right: auto;">
                    #                 配置AI模型是开始创作的第一步。选择合适的AI大脑，让它为您创作出精彩的小说内容。
                    #             </p>
                    #             <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1.5rem; flex-wrap: wrap;">
                    #                 <div style="text-align: center;">
                    #                     <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
                    #                     <div style="font-size: 0.9rem; opacity: 0.9;">智能创作</div>
                    #                 </div>
                    #                 <div style="text-align: center;">
                    #                     <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
                    #                     <div style="font-size: 0.9rem; opacity: 0.9;">快速配置</div>
                    #                 </div>
                    #                 <div style="text-align: center;">
                    #                     <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                    #                     <div style="font-size: 0.9rem; opacity: 0.9;">精准生成</div>
                    #                 </div>
                    #             </div>
                    #         </div>
                    #     </div>
                    #     """)
                    # AI模型状态概览
                    with gr.Row():
                        config_status_display = gr.HTML("""
                        <div style="background: #f8f9fa; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;
                                    border-left: 4px solid #ffc107;">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <div>
                                    <h3 style="margin: 0 0 1rem 0; color: #333; font-size: 1.1rem;">🔍 AI模型状态检查</h3>
                                    <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                                            <span style="width: 12px; height: 12px; background: #ffc107; border-radius: 50%;"></span>
                                            <span style="font-weight: 500; color: #856404;">创作大脑: 待配置</span>
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                                            <span style="width: 12px; height: 12px; background: #ffc107; border-radius: 50%;"></span>
                                            <span style="font-weight: 500; color: #856404;">理解引擎: 待配置</span>
                                        </div>
                                    </div>
                                </div>
                                <div style="text-align: center; padding: 1rem; background: #fff3cd; border-radius: 8px;">
                                    <div style="font-size: 1.5rem; font-weight: bold; color: #856404;">⚠️</div>
                                    <div style="font-size: 0.85rem; color: #856404; margin-top: 0.25rem;">需要配置</div>
                                </div>
                            </div>
                        </div>
                        """)

                    # 一键智能配置
                    with gr.Row():
                        gr.HTML("""
                        <div style="text-align: center; margin-bottom: 1.5rem;">
                            <h3 style="margin: 0 0 0.5rem 0; color: #333;">⚡ 一键智能配置</h3>
                            <p style="margin: 0; color: #666; font-size: 0.9rem;">选择AI服务商，系统将自动配置最佳参数，立即开始创作</p>
                        </div>
                        """)

                    with gr.Row():
                        with gr.Column():
                            template_openai = gr.Button(
                                "🚀 OpenAI GPT\n业界标杆，质量最高",
                                variant="primary",
                                size="lg",
                                elem_classes=["primary-button"]
                            )
                        with gr.Column():
                            template_gemini = gr.Button(
                                "💎 Google Gemini\n免费额度大，性能优秀",
                                variant="secondary",
                                size="lg"
                            )
                        with gr.Column():
                            template_deepseek = gr.Button(
                                "🔥 DeepSeek\n国产之光，性价比王",
                                variant="secondary",
                                size="lg"
                            )

                    # 配置完成后的引导
                    with gr.Row():
                        config_success_guide = gr.HTML("""
                        <div style="background: #d4edda; border-radius: 12px; padding: 1.5rem; margin-top: 1rem;
                                    border-left: 4px solid #28a745; display: none;" id="config-success-guide">
                            <div style="text-align: center;">
                                <h4 style="margin: 0 0 1rem 0; color: #155724; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                                    ✅ AI大脑配置完成！
                                </h4>
                                <p style="margin: 0 0 1rem 0; color: #155724;">
                                    您的AI创作助手已准备就绪，现在可以开始创作您的小说了！
                                </p>
                                <button onclick="switchToMainTab()" style="background: #28a745; color: white; border: none;
                                        padding: 0.75rem 2rem; border-radius: 8px; font-size: 1rem; cursor: pointer;
                                        box-shadow: 0 2px 4px rgba(40,167,69,0.3);">
                                    🚀 立即开始AI创作
                                </button>
                            </div>
                        </div>
                        """, visible=False)

                    # 详细配置（高级用户）
                    with gr.Accordion("🔧 详细配置 (高级用户)", open=False):
                        gr.HTML("""
                        <div style="margin-bottom: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; border-left: 3px solid #6c757d;">
                            <h4 style="margin: 0 0 0.5rem 0; color: #495057;">💡 高级配置说明</h4>
                            <p style="margin: 0; color: #6c757d; font-size: 0.9rem;">
                                如果您需要自定义AI模型参数，可以在这里进行详细配置。
                                大多数用户使用上方的一键配置即可满足需求。
                            </p>
                        </div>
                        """)

                        with gr.Row():
                            with gr.Column(scale=3):
                                # LLM配置组
                                with gr.Group():
                                    gr.HTML("""
                                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                                color: white; padding: 1rem; border-radius: 10px 10px 0 0; margin: -1rem -1rem 1rem -1rem;">
                                        <h3 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                                            🧠 AI创作大脑设置
                                            <span style="background: rgba(255,255,255,0.2); padding: 0.2rem 0.5rem;
                                                         border-radius: 12px; font-size: 0.8rem;">智能生成</span>
                                        </h3>
                                        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                                            配置AI的核心创作能力，负责生成小说内容
                                        </p>
                                    </div>
                                    """)
                                    # AI创作大脑配置
                                    with gr.Row():
                                        llm_interface = gr.Dropdown(
                                            choices=llm_interfaces,
                                            label="🤖 AI服务商",
                                            value=default_llm_interface,
                                            info="选择提供AI创作能力的服务商",
                                            scale=2
                                        )
                                        llm_model = gr.Textbox(
                                            label="🧠 AI大脑型号",
                                            value=default_llm_model,
                                            placeholder="例如: gpt-4o-mini, gemini-1.5-flash",
                                            info="选择具体的AI创作模型",
                                            scale=2
                                        )

                                    llm_api_key = gr.Textbox(
                                        label="🔑 AI访问密钥",
                                        type="password",
                                        value=default_llm_api_key,
                                        placeholder="sk-... 或其他格式的API密钥",
                                        info="连接AI服务的访问密钥，支持环境变量 $OPENAI_API_KEY"
                                    )

                                    # AI创作参数调优
                                    with gr.Accordion("🎛️ AI创作参数调优", open=False):
                                        llm_base_url = gr.Textbox(
                                            label="🌐 AI服务地址",
                                            value=default_llm_base_url,
                                            placeholder="https://api.openai.com/v1",
                                            info="AI服务的连接地址，通常使用默认值"
                                        )

                                        gr.HTML("""
                                        <div style="margin: 1rem 0 0.5rem 0; padding: 0.75rem; background: #e3f2fd;
                                                    border-radius: 8px; border-left: 3px solid #2196f3;">
                                            <strong>🎨 AI创作风格调节</strong><br>
                                            <small style="color: #1565c0;">
                                                • 创意度: 控制AI的想象力，0.1严谨，0.7平衡，1.5天马行空<br>
                                                • 输出长度: AI单次创作的字数限制，建议4096-8192字<br>
                                                • 响应时间: AI思考时间限制，网络慢时可适当增加
                                            </small>
                                        </div>
                                        """)

                                        with gr.Row():
                                            temperature = gr.Slider(
                                                label="🎨 AI创意度",
                                                minimum=0.0,
                                                maximum=2.0,
                                                value=default_temperature,
                                                step=0.1,
                                                info="AI想象力: 0.1(严谨写实) → 0.7(平衡创作) → 1.5(天马行空)"
                                            )
                                            max_tokens = gr.Number(
                                                label="📝 AI输出长度",
                                                value=default_max_tokens,
                                                minimum=100,
                                                maximum=32000,
                                                info="AI单次创作的字数上限"
                                            )

                                        with gr.Row():
                                            timeout = gr.Number(
                                                label="⏱️ AI响应时间",
                                                value=default_timeout,
                                                minimum=10,
                                                maximum=600,
                                                info="AI思考时间限制(秒)"
                                            )
                                            llm_test_quick = gr.Button(
                                                "⚡ 快速测试AI",
                                                variant="secondary",
                                                scale=1
                                            )

                                    # AI能力测试和保存
                                    with gr.Row():
                                        btn_test_llm = gr.Button(
                                            "🧪 测试AI创作能力",
                                            variant="primary",
                                            elem_classes=["primary-button"],
                                            scale=2
                                        )
                                        btn_save_llm = gr.Button(
                                            "💾 保存AI配置",
                                            variant="secondary",
                                            scale=1
                                        )

                                # 模型状态指示
                                llm_status = gr.HTML("""
                                <div style="margin: 1rem 0; padding: 0.75rem; background: #fff3cd;
                                            border-radius: 8px; border-left: 3px solid #ffc107; display: flex; align-items: center;">
                                    <div style="margin-right: 0.5rem; font-size: 1.2rem;">⚠️</div>
                                    <div>
                                        <div style="font-weight: 500; color: #856404;">未测试</div>
                                        <div style="font-size: 0.85rem; color: #856404;">请先测试配置确保连接正常</div>
                                    </div>
                                </div>
                                """)

                            with gr.Column(scale=2):
                                # AI理解引擎配置组
                                with gr.Group():
                                    gr.HTML("""
                                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                                                color: white; padding: 1rem; border-radius: 10px 10px 0 0; margin: -1rem -1rem 1rem -1rem;">
                                        <h3 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                                            🔍 AI理解引擎设置
                                            <span style="background: rgba(255,255,255,0.2); padding: 0.2rem 0.5rem;
                                                         border-radius: 12px; font-size: 0.8rem;">智能理解</span>
                                        </h3>
                                        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                                            配置AI的理解能力，帮助AI更好地理解上下文和保持故事连贯性
                                        </p>
                                    </div>
                                    """)
                                    # AI理解引擎配置
                                    with gr.Row():
                                        embedding_interface = gr.Dropdown(
                                            choices=llm_interfaces,
                                            label="🤖 AI理解服务商",
                                            value=default_embedding_interface,
                                            info="选择提供AI理解能力的服务商",
                                            scale=2
                                        )
                                        embedding_model = gr.Textbox(
                                            label="🧠 AI理解引擎型号",
                                            value=default_embedding_model,
                                            placeholder="例如: text-embedding-ada-002",
                                            info="AI理解和记忆模型的标识符",
                                            scale=2
                                        )

                                    # AI服务统一配置
                                    gr.HTML("""
                                    <div style="margin: 1rem 0 0.5rem 0; padding: 0.75rem; background: #e8f5e8;
                                                border-radius: 8px; border-left: 3px solid #28a745;">
                                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                            <span style="font-size: 1.1rem;">🔗</span>
                                            <strong style="color: #155724;">AI服务统一配置</strong>
                                        </div>
                                        <small style="color: #155724;">
                                            智能推荐：创作大脑和理解引擎使用相同的AI服务，确保最佳协作效果
                                        </small>
                                    </div>
                                    """)

                                    with gr.Row():
                                        use_same_key = gr.Checkbox(
                                            label="🔗 与创作大脑使用相同的AI服务配置",
                                            value=True,
                                            info="推荐选项：统一AI服务配置，确保创作大脑和理解引擎协同工作"
                                        )

                                # API密钥设置
                                with gr.Group(visible=False) as embedding_api_group:
                                    embedding_api_key = gr.Textbox(
                                        label="🔑 API Key",
                                        type="password",
                                        value=default_embedding_api_key,
                                        placeholder="请输入Embedding专用API密钥",
                                        info="如果与LLM不同，请输入专用密钥"
                                    )
                                    embedding_base_url = gr.Textbox(
                                        label="🌐 Base URL",
                                        value=default_embedding_base_url,
                                        placeholder="https://api.openai.com/v1",
                                        info="Embedding API的基础地址"
                                    )

                                    # AI理解能力测试和保存
                                    with gr.Row():
                                        btn_test_embedding = gr.Button(
                                            "🧪 测试AI理解能力",
                                            variant="primary",
                                            elem_classes=["primary-button"],
                                            scale=2
                                        )
                                        btn_save_embedding = gr.Button(
                                            "💾 保存AI配置",
                                            variant="secondary",
                                            scale=1
                                        )

                                    # AI理解参数调优
                                    with gr.Accordion("🎛️ AI理解参数调优", open=False):
                                        gr.HTML("""
                                        <div style="margin: 0.5rem 0; padding: 0.75rem; background: #e8f5e8;
                                                    border-radius: 8px; border-left: 3px solid #28a745;">
                                            <strong>🧠 AI理解能力调节</strong><br>
                                            <small style="color: #155724;">
                                                • 检索数量: AI每次查找的相关内容片段数量<br>
                                                • 建议值: 3-5片段(精准理解) 或 8-10片段(全面理解)
                                            </small>
                                        </div>
                                        """)

                                        retrieval_k = gr.Number(
                                            label="🔍 AI检索数量",
                                            value=default_retrieval_k,
                                            minimum=1,
                                            maximum=20,
                                            info="AI每次查找的相关内容片段数量"
                                        )

                                # 模型状态指示
                                embedding_status = gr.HTML("""
                                <div style="margin: 1rem 0; padding: 0.75rem; background: #fff3cd;
                                            border-radius: 8px; border-left: 3px solid #ffc107; display: flex; align-items: center;">
                                    <div style="margin-right: 0.5rem; font-size: 1.2rem;">⚠️</div>
                                    <div>
                                        <div style="font-weight: 500; color: #856404;">未测试</div>
                                        <div style="font-size: 0.85rem; color: #856404;">请先测试配置确保连接正常</div>
                                    </div>
                                </div>
                                """)

                    with gr.Column(scale=2):
                        # 配置测试日志区域
                        with gr.Group():
                            gr.HTML("""
                            <div style="background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
                                        color: white; padding: 1rem; border-radius: 10px 10px 0 0; margin: -1rem -1rem 1rem -1rem;">
                                <h3 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                                    📋 配置测试日志
                                    <span style="background: rgba(255,255,255,0.2); padding: 0.2rem 0.5rem;
                                                 border-radius: 12px; font-size: 0.8rem;">实时监控</span>
                                </h3>
                                <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                                    实时显示模型配置测试的详细过程和结果
                                </p>
                            </div>
                            """)

                            config_log_output = gr.Textbox(
                                label="测试日志",
                                lines=15,
                                max_lines=20,
                                interactive=False,
                                value="",
                                placeholder="💡 点击测试按钮查看详细日志...\n\n🔍 这里会显示：\n• 连接状态和响应时间\n• 请求参数和配置验证\n• 模型响应结果\n• 错误诊断和解决建议\n• 性能指标和优化建议",
                                elem_classes=["log-container"]
                            )

                            with gr.Row():
                                btn_clear_config_log = gr.Button("🗑️ 清空日志", variant="secondary", scale=1)
                                btn_export_log = gr.Button("📤 导出日志", variant="secondary", scale=1)

                            # AI配置智能推荐
                            with gr.Group():
                                gr.HTML("""
                                <div style="background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                                            color: white; padding: 1rem; border-radius: 10px 10px 0 0; margin: -1rem -1rem 1rem -1rem;">
                                    <h3 style="margin: 0;">🎯 AI配置智能推荐</h3>
                                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">
                                        根据不同创作需求，为您推荐最适合的AI大脑配置
                                    </p>
                                </div>
                                """)

                                config_suggestions = gr.HTML("""
                                <div style="padding: 1rem 0;">
                                    <div style="margin-bottom: 1rem; padding: 0.75rem; background: #e7f3ff; border-radius: 8px; border-left: 3px solid #007bff;">
                                        <h4 style="margin: 0 0 0.5rem 0; color: #0056b3;">🚀 新手作家</h4>
                                        <ul style="margin: 0; padding-left: 1.2rem; color: #0056b3;">
                                            <li>AI大脑: OpenAI GPT-4o-mini (平衡性能与成本)</li>
                                            <li>创意度: 0.7 (平衡创作)</li>
                                            <li>输出长度: 4096字 (适中篇幅)</li>
                                        </ul>
                                    </div>

                                    <div style="margin-bottom: 1rem; padding: 0.75rem; background: #f0f9ff; border-radius: 8px; border-left: 3px solid #0ea5e9;">
                                        <h4 style="margin: 0 0 0.5rem 0; color: #0369a1;">💎 免费体验</h4>
                                        <ul style="margin: 0; padding-left: 1.2rem; color: #0369a1;">
                                            <li>AI大脑: Google Gemini Flash (免费额度充足)</li>
                                            <li>创意度: 0.8 (稍高创意)</li>
                                            <li>输出长度: 8192字 (长篇创作)</li>
                                        </ul>
                                    </div>

                                    <div style="margin-bottom: 1rem; padding: 0.75rem; background: #fef3e2; border-radius: 8px; border-left: 3px solid #f59e0b;">
                                        <h4 style="margin: 0 0 0.5rem 0; color: #92400e;">🔥 经济实惠</h4>
                                        <ul style="margin: 0; padding-left: 1.2rem; color: #92400e;">
                                            <li>AI大脑: DeepSeek Chat (国产优质，价格亲民)</li>
                                            <li>创意度: 0.9 (高度创新)</li>
                                            <li>输出长度: 6144字 (中长篇)</li>
                                        </ul>
                                    </div>

                                    <div style="padding: 0.75rem; background: #f0fdf4; border-radius: 8px; border-left: 3px solid #22c55e;">
                                        <h4 style="margin: 0 0 0.5rem 0; color: #166534;">⚡ 专业作家</h4>
                                        <ul style="margin: 0; padding-left: 1.2rem; color: #166534;">
                                            <li>AI大脑: OpenAI GPT-4 (顶级创作质量)</li>
                                            <li>创意度: 0.6 (精准控制)</li>
                                            <li>输出长度: 8192字 (专业长度)</li>
                                        </ul>
                                    </div>
                                </div>
                                """)

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
            outputs=[config_log_output, llm_status, config_status_display]
        )

        btn_test_embedding.click(
            fn=handle_test_embedding_config,
            inputs=[
                embedding_interface, embedding_api_key,
                embedding_base_url, embedding_model, config_log_output,
                use_same_key, llm_api_key, llm_base_url
            ],
            outputs=[config_log_output, embedding_status, config_status_display]
        )

        # 清空配置日志事件
        btn_clear_config_log.click(
            fn=handle_clear_config_log,
            outputs=[config_log_output, llm_status, embedding_status, config_status_display]
        )

        # Embedding API密钥同步选项事件
        def toggle_embedding_api_group(use_same):
            """切换Embedding API设置组的显示状态"""
            return gr.Group(visible=not use_same)

        use_same_key.change(
            fn=toggle_embedding_api_group,
            inputs=[use_same_key],
            outputs=[embedding_api_group]
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
                filepath_input, current_chapter, user_guidance_input,
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
                filepath_input, current_chapter, chapter_content,
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
                filepath_input, current_chapter, log_output
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

# 全局配置状态跟踪
config_status = {
    "llm_status": "未配置",
    "embedding_status": "未配置",
    "llm_timestamp": "",
    "embedding_timestamp": "",
    "llm_model": "",
    "embedding_model": ""
}

def generate_ai_status_monitor_html():
    """生成AI状态监控HTML"""
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 确定创作大脑状态
    if config_status["llm_status"] == "成功":
        llm_status_color = "#28a745"
        llm_status_text = "✅ 已就绪"
        llm_model_info = config_status.get('llm_model', '未知模型')
    elif config_status["llm_status"] == "失败":
        llm_status_color = "#dc3545"
        llm_status_text = "❌ 配置失败"
        llm_model_info = "需要重新配置"
    else:
        llm_status_color = "#ffc107"
        llm_status_text = "⚠️ 待配置"
        llm_model_info = "请先配置AI模型"

    # 确定理解引擎状态
    if config_status["embedding_status"] == "成功":
        embedding_status_color = "#28a745"
        embedding_status_text = "✅ 已就绪"
        embedding_model_info = config_status.get('embedding_model', '未知模型')
    elif config_status["embedding_status"] == "失败":
        embedding_status_color = "#dc3545"
        embedding_status_text = "❌ 配置失败"
        embedding_model_info = "需要重新配置"
    else:
        embedding_status_color = "#ffc107"
        embedding_status_text = "⚠️ 待配置"
        embedding_model_info = "请先配置AI模型"

    # 确定整体状态
    if config_status["llm_status"] == "成功" and config_status["embedding_status"] == "成功":
        overall_status = "🚀 AI系统已就绪，可以开始创作"
        overall_color = "#28a745"
    elif config_status["llm_status"] == "成功" or config_status["embedding_status"] == "成功":
        overall_status = "⚡ 部分AI功能可用"
        overall_color = "#ffc107"
    else:
        overall_status = "⚠️ 需要配置AI模型"
        overall_color = "#ffc107"

    return f"""
    <div style="background: #f8f9fa; border-radius: 12px; padding: 1rem; border-left: 4px solid {overall_color};">
        <h4 style="margin: 0 0 1rem 0; color: #333; display: flex; align-items: center; gap: 0.5rem;">
            🤖 AI状态监控
        </h4>
        <div style="space-y: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 0.9rem; color: #666;">创作大脑</span>
                <span style="font-size: 0.85rem; color: {llm_status_color}; font-weight: 500;">{llm_status_text}</span>
            </div>
            <div style="font-size: 0.8rem; color: #666; margin-bottom: 1rem;">{llm_model_info}</div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 0.9rem; color: #666;">理解引擎</span>
                <span style="font-size: 0.85rem; color: {embedding_status_color}; font-weight: 500;">{embedding_status_text}</span>
            </div>
            <div style="font-size: 0.8rem; color: #666; margin-bottom: 1rem;">{embedding_model_info}</div>

            <div style="text-align: center; padding: 0.75rem; background: rgba(255,255,255,0.7); border-radius: 8px; border: 1px solid {overall_color};">
                <div style="font-size: 0.9rem; color: {overall_color}; font-weight: 500;">{overall_status}</div>
            </div>
        </div>
    </div>
    """

def generate_config_status_html():
    """生成配置状态HTML"""
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 确定LLM状态
    if config_status["llm_status"] == "成功":
        llm_indicator = "status-success"
        llm_text = f"LLM: 已配置 ({config_status['llm_model']})"
    elif config_status["llm_status"] == "失败":
        llm_indicator = "status-error"
        llm_text = "LLM: 配置失败"
    else:
        llm_indicator = "status-warning"
        llm_text = "LLM: 待配置"

    # 确定Embedding状态
    if config_status["embedding_status"] == "成功":
        embedding_indicator = "status-success"
        embedding_text = f"Embedding: 已配置 ({config_status['embedding_model']})"
    elif config_status["embedding_status"] == "失败":
        embedding_indicator = "status-error"
        embedding_text = "Embedding: 配置失败"
    else:
        embedding_indicator = "status-warning"
        embedding_text = "Embedding: 待配置"

    # 确定最后更新时间
    if config_status["llm_timestamp"] or config_status["embedding_timestamp"]:
        last_update = max(config_status["llm_timestamp"], config_status["embedding_timestamp"])
    else:
        last_update = "从未配置"

    return f"""
    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 15px; padding: 1.5rem; margin-bottom: 1.5rem;
                border-left: 5px solid #ffc107; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h3 style="margin: 0 0 0.5rem 0; color: #333; font-size: 1.2rem;">📊 配置状态</h3>
                <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span class="status-indicator {llm_indicator}"></span>
                        <span style="font-weight: 500;">{llm_text}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span class="status-indicator {embedding_indicator}"></span>
                        <span style="font-weight: 500;">{embedding_text}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span class="status-indicator status-success"></span>
                        <span style="font-weight: 500;">系统: 正常</span>
                    </div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">最后更新</div>
                <div style="font-weight: 500; color: #333;">{last_update}</div>
            </div>
        </div>
    </div>
    """

def handle_test_llm_config(interface_format, api_key, base_url, model_name, temperature, max_tokens, timeout, current_log):
    """处理测试LLM配置事件"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_msg = current_log + f"\n[{timestamp}] 🧪 开始测试LLM配置...\n"
    log_msg += f"接口类型: {interface_format}\n"
    log_msg += f"模型名称: {model_name}\n"
    log_msg += f"Base URL: {base_url}\n"
    log_msg += f"Temperature: {temperature}\n"
    log_msg += f"Max Tokens: {max_tokens}\n"
    log_msg += f"Timeout: {timeout}秒\n"
    log_msg += "-" * 50 + "\n"

    success = False
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
            success = True

            # 更新全局状态
            config_status["llm_status"] = "成功"
            config_status["llm_timestamp"] = full_timestamp
            config_status["llm_model"] = f"{interface_format} {model_name}"
        else:
            log_msg += "❌ LLM配置测试失败：未获取到响应\n"
            log_msg += "可能原因：\n"
            log_msg += "1. API密钥无效\n"
            log_msg += "2. 网络连接问题\n"
            log_msg += "3. 模型名称错误\n"
            log_msg += "4. 服务器暂时不可用\n"

            # 更新全局状态
            config_status["llm_status"] = "失败"
            config_status["llm_timestamp"] = full_timestamp
            config_status["llm_model"] = f"{interface_format} {model_name}"

    except Exception as e:
        log_msg += f"❌ LLM配置测试出错: {str(e)}\n"
        log_msg += "详细错误信息:\n"
        import traceback
        log_msg += traceback.format_exc() + "\n"

        # 更新全局状态
        config_status["llm_status"] = "失败"
        config_status["llm_timestamp"] = full_timestamp
        config_status["llm_model"] = f"{interface_format} {model_name}"

    log_msg += "=" * 50 + "\n"

    # 生成状态HTML
    if success:
        status_html = f"""
        <div style="margin: 1rem 0; padding: 0.75rem; background: #d4edda;
                    border-radius: 8px; border-left: 3px solid #28a745; display: flex; align-items: center;">
            <div style="margin-right: 0.5rem; font-size: 1.2rem;">✅</div>
            <div>
                <div style="font-weight: 500; color: #155724;">测试成功</div>
                <div style="font-size: 0.85rem; color: #155724;">
                    {interface_format} {model_name} 连接正常 | {timestamp}
                </div>
            </div>
        </div>
        """
    else:
        status_html = """
        <div style="margin: 1rem 0; padding: 0.75rem; background: #f8d7da;
                    border-radius: 8px; border-left: 3px solid #dc3545; display: flex; align-items: center;">
            <div style="margin-right: 0.5rem; font-size: 1.2rem;">❌</div>
            <div>
                <div style="font-weight: 500; color: #721c24;">测试失败</div>
                <div style="font-size: 0.85rem; color: #721c24;">请检查配置参数和网络连接</div>
            </div>
        </div>
        """

    # 生成更新的配置状态HTML
    config_status_html = generate_config_status_html()



    return log_msg, status_html, config_status_html

def handle_test_embedding_config(interface_format, api_key, base_url, model_name, current_log, use_same_key, llm_api_key, llm_base_url):
    """处理测试Embedding配置事件"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 如果选择使用相同密钥，则使用LLM的配置
    if use_same_key:
        actual_api_key = llm_api_key
        actual_base_url = llm_base_url
        log_msg = current_log + f"\n[{timestamp}] 🔍 开始测试Embedding配置...\n"
        log_msg += f"🔗 使用LLM相同配置\n"
        log_msg += f"接口类型: {interface_format}\n"
        log_msg += f"模型名称: {model_name}\n"
        log_msg += f"Base URL: {actual_base_url} (来自LLM配置)\n"
        log_msg += f"API Key: {'***' if actual_api_key else '未设置'} (来自LLM配置)\n"
    else:
        actual_api_key = api_key
        actual_base_url = base_url
        log_msg = current_log + f"\n[{timestamp}] 🔍 开始测试Embedding配置...\n"
        log_msg += f"🔧 使用独立配置\n"
        log_msg += f"接口类型: {interface_format}\n"
        log_msg += f"模型名称: {model_name}\n"
        log_msg += f"Base URL: {actual_base_url}\n"
        log_msg += f"API Key: {'***' if actual_api_key else '未设置'}\n"

    log_msg += "-" * 50 + "\n"

    success = False
    try:
        log_msg += "正在创建Embedding适配器...\n"
        embedding_adapter = create_embedding_adapter(
            interface_format=interface_format,
            api_key=actual_api_key,
            base_url=actual_base_url,
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
            success = True

            # 更新全局状态
            config_status["embedding_status"] = "成功"
            config_status["embedding_timestamp"] = full_timestamp
            config_status["embedding_model"] = f"{interface_format} {model_name}"
        else:
            log_msg += "❌ Embedding配置测试失败：未获取到向量\n"
            log_msg += "可能原因：\n"
            log_msg += "1. API密钥无效\n"
            log_msg += "2. 模型名称错误\n"
            log_msg += "3. 网络连接问题\n"
            log_msg += "4. 服务不支持该模型\n"

            # 更新全局状态
            config_status["embedding_status"] = "失败"
            config_status["embedding_timestamp"] = full_timestamp
            config_status["embedding_model"] = f"{interface_format} {model_name}"

    except Exception as e:
        log_msg += f"❌ Embedding配置测试出错: {str(e)}\n"
        log_msg += "详细错误信息:\n"
        import traceback
        log_msg += traceback.format_exc() + "\n"

        # 更新全局状态
        config_status["embedding_status"] = "失败"
        config_status["embedding_timestamp"] = full_timestamp
        config_status["embedding_model"] = f"{interface_format} {model_name}"

    log_msg += "=" * 50 + "\n"

    # 生成状态HTML
    if success:
        status_html = f"""
        <div style="margin: 1rem 0; padding: 0.75rem; background: #d4edda;
                    border-radius: 8px; border-left: 3px solid #28a745; display: flex; align-items: center;">
            <div style="margin-right: 0.5rem; font-size: 1.2rem;">✅</div>
            <div>
                <div style="font-weight: 500; color: #155724;">测试成功</div>
                <div style="font-size: 0.85rem; color: #155724;">
                    {interface_format} {model_name} 连接正常 | {timestamp}
                </div>
            </div>
        </div>
        """
    else:
        status_html = """
        <div style="margin: 1rem 0; padding: 0.75rem; background: #f8d7da;
                    border-radius: 8px; border-left: 3px solid #dc3545; display: flex; align-items: center;">
            <div style="margin-right: 0.5rem; font-size: 1.2rem;">❌</div>
            <div>
                <div style="font-weight: 500; color: #721c24;">测试失败</div>
                <div style="font-size: 0.85rem; color: #721c24;">请检查配置参数和网络连接</div>
            </div>
        </div>
        """

    # 生成更新的配置状态HTML
    config_status_html = generate_config_status_html()

    return log_msg, status_html, config_status_html

def handle_clear_config_log():
    """清空配置日志"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    # 重置全局配置状态
    config_status["llm_status"] = "未配置"
    config_status["embedding_status"] = "未配置"
    config_status["llm_timestamp"] = ""
    config_status["embedding_timestamp"] = ""
    config_status["llm_model"] = ""
    config_status["embedding_model"] = ""

    # 重置状态HTML
    reset_status_html = """
    <div style="margin: 1rem 0; padding: 0.75rem; background: #fff3cd;
                border-radius: 8px; border-left: 3px solid #ffc107; display: flex; align-items: center;">
        <div style="margin-right: 0.5rem; font-size: 1.2rem;">⚠️</div>
        <div>
            <div style="font-weight: 500; color: #856404;">未测试</div>
            <div style="font-size: 0.85rem; color: #856404;">请先测试配置确保连接正常</div>
        </div>
    </div>
    """

    # 生成重置的配置状态HTML
    config_status_html = generate_config_status_html()

    return f"[{timestamp}] 📋 配置测试日志已清空\n", reset_status_html, reset_status_html, config_status_html

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
        server_port=7863,
        share=False,
        show_error=True
    )