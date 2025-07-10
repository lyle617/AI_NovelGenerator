#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Gemini配置和诊断SSL问题
"""

import sys
import os
import logging
import ssl
import socket
import requests
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_adapters import create_llm_adapter
from embedding_adapters import create_embedding_adapter

# 设置详细的日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_network_connectivity():
    """测试网络连接"""
    print("\n🌐 网络连接测试")
    print("-" * 50)

    # 测试基本网络连接
    try:
        response = requests.get("https://www.google.com", timeout=10)
        print(f"✅ Google连接正常: {response.status_code}")
    except Exception as e:
        print(f"❌ Google连接失败: {e}")

    # 测试Gemini API端点
    try:
        response = requests.get("https://generativelanguage.googleapis.com", timeout=10)
        print(f"✅ Gemini API端点可达: {response.status_code}")
    except Exception as e:
        print(f"❌ Gemini API端点不可达: {e}")

    # 测试SSL连接
    try:
        context = ssl.create_default_context()
        with socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname="generativelanguage.googleapis.com") as ssock:
                print(f"✅ SSL连接正常: {ssock.version()}")
    except Exception as e:
        print(f"❌ SSL连接失败: {e}")

def test_gemini_llm():
    """测试Gemini LLM"""
    print("\n🤖 测试Gemini LLM...")
    print("-" * 50)

    # 配置参数
    api_key = "AIzaSyCp1LrhhP9zAlS_VgCCaw517OFz-4vDCAg"  # 你的API密钥
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    # 测试不同的模型
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro",
        "gemini-pro"
    ]

    for model_name in models_to_test:
        print(f"\n🧪 测试模型: {model_name}")
        print("-" * 30)

        try:
            llm_adapter = create_llm_adapter(
                interface_format="Gemini",
                api_key=api_key,
                base_url=base_url,
                model_name=model_name,
                temperature=0.7,
                max_tokens=100,
                timeout=30
            )

            test_prompt = "请简单回复'测试成功'"
            print(f"发送提示词: {test_prompt}")

            response = llm_adapter.invoke(test_prompt)

            if response and response.strip():
                print(f"✅ 成功！回复: {response}")
                return True  # 找到可用模型就返回
            else:
                print(f"❌ 失败：空响应")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")

    return False

def test_gemini_embedding():
    """测试Gemini Embedding"""
    print("\n🔍 测试Gemini Embedding...")
    print("-" * 50)

    # 配置参数
    api_key = "AIzaSyCp1LrhhP9zAlS_VgCCaw517OFz-4vDCAg"
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    # 测试不同的模型
    models_to_test = [
        "text-embedding-004",
        "embedding-001"
    ]

    for model_name in models_to_test:
        print(f"\n🧪 测试Embedding模型: {model_name}")
        print("-" * 30)

        try:
            embedding_adapter = create_embedding_adapter(
                interface_format="Gemini",
                api_key=api_key,
                base_url=base_url,
                model_name=model_name
            )

            test_text = "测试文本"
            embedding = embedding_adapter.embed_query(test_text)

            if embedding and len(embedding) > 0:
                print(f"✅ 成功！向量维度: {len(embedding)}")
                print(f"前3个值: {embedding[:3]}")
                return True
            else:
                print(f"❌ 失败：未获取到向量")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")

    return False

def test_web_interface_logging():
    """测试Web界面的日志功能"""
    print("\n🌐 测试Web界面日志功能")
    print("-" * 50)

    # 模拟Web界面的测试函数
    from web_app import handle_test_llm_config, handle_test_embedding_config

    # 测试参数
    api_key = "AIzaSyCp1LrhhP9zAlS_VgCCaw517OFz-4vDCAg"
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    model_name = "gemini-1.5-flash"

    print("测试LLM配置日志输出...")
    current_log = ""
    log_result = handle_test_llm_config(
        interface_format="Gemini",
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        temperature=0.7,
        max_tokens=100,
        timeout=30,
        current_log=current_log
    )

    print("LLM测试日志:")
    print(log_result)

    print("\n测试Embedding配置日志输出...")
    embedding_log = handle_test_embedding_config(
        interface_format="Gemini",
        api_key=api_key,
        base_url=base_url,
        model_name="text-embedding-004",
        current_log=""
    )

    print("Embedding测试日志:")
    print(embedding_log)

def main():
    """主测试函数"""
    print("🔍 Gemini配置诊断工具")
    print("="*60)

    # 1. 网络连接测试
    test_network_connectivity()

    # 2. LLM测试
    llm_success = test_gemini_llm()

    # 3. Embedding测试
    embedding_success = test_gemini_embedding()

    # 4. Web界面日志测试
    test_web_interface_logging()

    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结:")
    print(f"LLM测试: {'✅ 成功' if llm_success else '❌ 失败'}")
    print(f"Embedding测试: {'✅ 成功' if embedding_success else '❌ 失败'}")

    if not llm_success or not embedding_success:
        print("\n💡 故障排除建议:")
        print("1. 检查网络连接是否稳定")
        print("2. 尝试使用VPN或更换网络环境")
        print("3. 检查防火墙设置")
        print("4. 验证API密钥是否正确且有效")
        print("5. 确认Gemini API在你的地区可用")
        print("6. 尝试降低请求频率")

    print("\n🌐 Web界面使用说明:")
    print("1. 启动Web界面后，进入'模型配置'标签页")
    print("2. 右侧现在有专用的'配置测试日志'窗口")
    print("3. 点击'测试LLM配置'或'测试Embedding配置'查看详细日志")
    print("4. 可以点击'清空日志'按钮清除历史记录")

if __name__ == "__main__":
    main()