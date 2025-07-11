#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI小说生成器现代化Web版启动脚本
Modern Web Interface with Landing Page
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """打印现代化启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎯 AI小说生成器 - 现代化Web版                              ║
║                                                              ║
║    ✨ 全新现代化界面设计                                      ║
║    🏠 Landing页面展示                                        ║
║    🎨 响应式UI设计                                           ║
║    🚀 完整功能复刻                                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_dependencies():
    """检查依赖"""
    print("🔍 检查系统依赖...")
    
    required_modules = [
        ('gradio', 'Gradio Web框架'),
        ('requests', 'HTTP请求库'),
        ('openai', 'OpenAI客户端'),
        ('langchain', 'LangChain框架'),
        ('chromadb', '向量数据库')
    ]
    
    missing_modules = []
    
    for module, description in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {description}")
        except ImportError:
            missing_modules.append((module, description))
            print(f"  ❌ {description} - 未安装")
    
    if missing_modules:
        print("\n⚠️  发现缺失依赖，请安装：")
        print("pip install gradio>=4.0.0 requests openai langchain chromadb")
        return False
    
    print("✅ 所有依赖检查通过！")
    return True

def test_web_app():
    """测试Web应用"""
    print("\n🧪 测试Web应用...")
    
    try:
        from web_app import create_interface, NovelGeneratorWebApp
        
        # 测试应用创建
        app = NovelGeneratorWebApp()
        print("  ✅ 应用实例创建成功")
        
        # 测试界面创建
        demo = create_interface()
        print("  ✅ 现代化界面创建成功")
        
        return demo
        
    except Exception as e:
        print(f"  ❌ Web应用测试失败: {e}")
        return None

def show_features():
    """显示功能特性"""
    print("\n🎨 现代化界面特性:")
    print("  🏠 Landing页面 - 功能展示和快速开始")
    print("  ⚡ 创作工坊 - 现代化的创作界面")
    print("  🤖 模型配置 - 可视化配置管理")
    print("  📚 小说参数 - 详细的参数设置")
    print("  📖 章节管理 - 直观的章节编辑")
    print("  👥 角色库 - 完整的角色管理")
    print("  📁 文件管理 - 核心文件编辑")
    
    print("\n🎯 设计亮点:")
    print("  ✨ 现代化渐变色彩")
    print("  🎨 响应式卡片设计")
    print("  🔄 实时状态反馈")
    print("  📱 移动端适配")
    print("  🌙 深色模式支持")
    print("  🎭 动画过渡效果")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺失的依赖包")
        sys.exit(1)
    
    # 测试应用
    demo = test_web_app()
    if not demo:
        print("\n❌ Web应用测试失败")
        sys.exit(1)
    
    # 显示功能特性
    show_features()
    
    print("\n" + "="*60)
    print("🚀 启动现代化Web服务...")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 访问地址: http://localhost:7860")
    print("📱 支持移动端访问")
    print("🔧 支持实时配置")
    print("💾 数据本地存储")
    print("\n💡 使用提示:")
    print("  1. 首次使用请访问Landing页面了解功能")
    print("  2. 在模型配置页面设置API密钥")
    print("  3. 在创作工坊开始您的小说创作")
    print("  4. 使用章节管理和角色库完善作品")
    print("\n⌨️  按 Ctrl+C 停止服务")
    print("="*60)
    
    try:
        # 启动服务
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False,
            favicon_path=None,
            show_tips=True,
            enable_queue=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
        print("感谢使用AI小说生成器现代化Web版！")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
