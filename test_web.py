#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web应用的简化脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入"""
    try:
        print("🔍 测试导入...")
        
        # 测试基础模块
        import gradio as gr
        print(f"✅ Gradio: {gr.__version__}")
        
        # 测试项目模块
        from config_manager import load_config
        print("✅ config_manager")
        
        from utils import read_file
        print("✅ utils")
        
        from llm_adapters import create_llm_adapter
        print("✅ llm_adapters")
        
        # 测试web应用
        from web_app import NovelGeneratorWebApp, create_interface
        print("✅ web_app")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_app_creation():
    """测试应用创建"""
    try:
        print("\n🏗️ 测试应用创建...")
        
        from web_app import NovelGeneratorWebApp
        app = NovelGeneratorWebApp()
        print("✅ NovelGeneratorWebApp 创建成功")
        
        # 测试基础方法
        msg = app.log_message("测试消息")
        print(f"✅ log_message: {msg.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interface_creation():
    """测试界面创建"""
    try:
        print("\n🎨 测试界面创建...")
        
        from web_app import create_interface
        demo = create_interface()
        print("✅ Gradio界面创建成功")
        
        return True, demo
        
    except Exception as e:
        print(f"❌ 界面创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """主函数"""
    print("=" * 50)
    print("🧪 AI小说生成器Web版测试")
    print("=" * 50)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 导入测试失败，请检查依赖安装")
        sys.exit(1)
    
    # 测试应用创建
    if not test_app_creation():
        print("\n❌ 应用创建测试失败")
        sys.exit(1)
    
    # 测试界面创建
    success, demo = test_interface_creation()
    if not success:
        print("\n❌ 界面创建测试失败")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ 所有测试通过！")
    print("🚀 准备启动Web服务...")
    print("📍 访问地址: http://localhost:7860")
    print("=" * 50)
    
    # 启动服务
    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
