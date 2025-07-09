#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI_NovelGenerator Web启动脚本
自动检查依赖并启动Web界面
"""

import sys
import subprocess
import importlib.util

def check_and_install_gradio():
    """检查并安装Gradio"""
    try:
        import gradio
        print(f"✅ Gradio已安装，版本: {gradio.__version__}")
        return True
    except ImportError:
        print("❌ 未找到Gradio，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gradio>=4.0.0"])
            print("✅ Gradio安装成功！")
            return True
        except subprocess.CalledProcessError:
            print("❌ Gradio安装失败，请手动安装：pip install gradio")
            return False

def check_dependencies():
    """检查必要依赖"""
    required_modules = [
        'requests', 'typing_extensions', 'langchain', 'langchain_core',
        'langchain_openai', 'chromadb', 'openai'
    ]

    missing_modules = []
    for module in required_modules:
        if importlib.util.find_spec(module) is None:
            missing_modules.append(module)

    if missing_modules:
        print(f"❌ 缺少以下依赖: {', '.join(missing_modules)}")
        print("请运行以下命令安装：")
        print(f"pip install {' '.join(missing_modules)}")
        return False

    print("✅ 所有必要依赖已安装")
    return True

def main():
    """主函数"""
    print("🚀 AI小说生成器Web版启动检查...")

    # 检查Gradio
    if not check_and_install_gradio():
        sys.exit(1)

    # 检查其他依赖
    if not check_dependencies():
        print("\n💡 提示：你可以运行以下命令安装所有依赖：")
        print("pip install -r web_requirements.txt")
        sys.exit(1)

    # 启动Web应用
    print("\n🌟 正在启动Web界面...")
    try:
        from web_app import create_interface
        demo = create_interface()

        print("✅ Web界面启动成功！")
        print("📝 访问地址: http://localhost:7860")
        print("🔧 配置说明: 请先在'模型配置'标签页中设置API密钥")
        print("📚 使用流程: 配置模型 -> 设置小说参数 -> 按步骤生成")
        print("\n按 Ctrl+C 停止服务")

        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False
        )

    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保所有依赖已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()