#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
现代化UI演示脚本
展示新的Web界面设计和功能
"""

import gradio as gr
import webbrowser
import time
import threading

def create_demo_interface():
    """创建演示界面"""

    # 自定义CSS - 现代化设计
    demo_css = """
    /* 演示页面专用样式 */
    .demo-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }

    .demo-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }

    .demo-title {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .demo-subtitle {
        font-size: 1.3rem;
        opacity: 0.9;
        margin-bottom: 2rem;
    }

    .feature-showcase {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin: 2rem 0;
    }

    .feature-item {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border: 1px solid #e1e5e9;
        transition: all 0.3s ease;
        text-align: center;
    }

    .feature-item:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }

    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }

    .feature-title {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #333;
    }

    .feature-desc {
        color: #666;
        line-height: 1.6;
    }

    .demo-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 15px 30px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: white !important;
        transition: all 0.3s ease !important;
        margin: 1rem !important;
    }

    .demo-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4) !important;
    }
    """

    with gr.Blocks(title="AI小说生成器 - 现代化UI演示", css=demo_css) as demo:

        # 演示页面头部
        gr.HTML("""
        <div class="demo-header">
            <div class="demo-title">🎨 现代化UI设计</div>
            <div class="demo-subtitle">AI小说生成器全新Web界面体验</div>
        </div>
        """)

        # 功能展示
        gr.HTML("""
        <div class="feature-showcase">
            <div class="feature-item">
                <span class="feature-icon">🏠</span>
                <div class="feature-title">欢迎页面</div>
                <div class="feature-desc">全新的Landing页面，提供清晰的导航和快速开始指南</div>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🎨</span>
                <div class="feature-title">现代化设计</div>
                <div class="feature-desc">采用渐变色彩、卡片布局和现代化的视觉元素</div>
            </div>
            <div class="feature-item">
                <span class="feature-icon">📋</span>
                <div class="feature-title">详细日志</div>
                <div class="feature-desc">配置测试页面新增专用日志窗口，实时显示详细信息</div>
            </div>
        </div>
        """)

        # 启动按钮
        start_demo_btn = gr.Button("🚀 启动完整版本", elem_classes=["demo-button"], size="lg")

    return demo

def main():
    """主函数"""
    print("🎨 启动现代化UI演示...")
    demo = create_demo_interface()
    demo.launch(server_port=7861)

if __name__ == "__main__":
    main()