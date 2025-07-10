#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件检查和管理工具
"""

import os
import json
from config_manager import load_config, save_config

def check_config_file():
    """检查配置文件状态"""
    config_file = "config.json"

    print("🔍 配置文件检查")
    print("="*50)

    # 检查当前工作目录
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")

    # 检查配置文件是否存在
    config_path = os.path.join(current_dir, config_file)
    print(f"配置文件路径: {config_path}")

    if os.path.exists(config_path):
        print("✅ 配置文件存在")

        # 尝试加载配置
        try:
            config = load_config(config_file)
            if config:
                print("✅ 配置文件格式正确")
                print("\n📋 当前配置内容:")
                print("-"*30)

                # 显示LLM配置
                if "last_interface_format" in config:
                    print(f"LLM接口: {config['last_interface_format']}")

                if "llm_configs" in config:
                    for interface, cfg in config["llm_configs"].items():
                        print(f"  {interface}:")
                        print(f"    模型: {cfg.get('model_name', 'N/A')}")
                        print(f"    Base URL: {cfg.get('base_url', 'N/A')}")
                        print(f"    API Key: {'***' if cfg.get('api_key') else 'N/A'}")

                # 显示Embedding配置
                if "last_embedding_interface_format" in config:
                    print(f"Embedding接口: {config['last_embedding_interface_format']}")

                if "embedding_configs" in config:
                    for interface, cfg in config["embedding_configs"].items():
                        print(f"  {interface}:")
                        print(f"    模型: {cfg.get('model_name', 'N/A')}")
                        print(f"    API Key: {'***' if cfg.get('api_key') else 'N/A'}")

                # 显示其他参数
                if "other_params" in config:
                    params = config["other_params"]
                    print(f"小说主题: {params.get('topic', 'N/A')}")
                    print(f"小说类型: {params.get('genre', 'N/A')}")
                    print(f"章节数: {params.get('num_chapters', 'N/A')}")
                    print(f"保存路径: {params.get('filepath', 'N/A')}")

            else:
                print("❌ 配置文件格式错误或为空")

        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
    else:
        print("❌ 配置文件不存在")
        create_default_config()

def create_default_config():
    """创建默认配置文件"""
    print("\n🔧 创建默认配置文件...")

    default_config = {
        "last_interface_format": "OpenAI",
        "last_embedding_interface_format": "OpenAI",
        "llm_configs": {
            "OpenAI": {
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model_name": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 8192,
                "timeout": 600
            },
            "Gemini": {
                "api_key": "",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "model_name": "gemini-1.5-flash",
                "temperature": 0.7,
                "max_tokens": 4096,
                "timeout": 600
            }
        },
        "embedding_configs": {
            "OpenAI": {
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model_name": "text-embedding-ada-002",
                "retrieval_k": 4
            },
            "Gemini": {
                "api_key": "",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "model_name": "text-embedding-004",
                "retrieval_k": 4
            }
        },
        "other_params": {
            "topic": "",
            "genre": "玄幻",
            "num_chapters": 10,
            "word_number": 3000,
            "filepath": "",
            "user_guidance": "",
            "characters_involved": "",
            "key_items": "",
            "scene_location": "",
            "time_constraint": ""
        }
    }

    try:
        success = save_config(default_config, "config.json")
        if success:
            print("✅ 默认配置文件创建成功")
        else:
            print("❌ 默认配置文件创建失败")
    except Exception as e:
        print(f"❌ 创建配置文件时出错: {e}")

def main():
    """主函数"""
    check_config_file()

    print("\n" + "="*50)
    print("💡 使用说明:")
    print("1. 如果配置文件不存在，已自动创建默认配置")
    print("2. 请在Web界面中设置你的API密钥")
    print("3. 配置会自动保存到config.json文件")
    print("4. Web界面启动时会自动加载已保存的配置")

if __name__ == "__main__":
    main()