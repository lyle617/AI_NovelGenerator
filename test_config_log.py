#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置页面日志功能的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_functions():
    """测试配置相关函数"""
    try:
        print("🔍 测试配置功能...")
        
        # 导入必要模块
        from web_app import NovelGeneratorWebApp, handle_test_llm_config, handle_test_embedding_config
        from web_app import handle_save_config_only, handle_load_config_only
        
        # 创建应用实例
        app = NovelGeneratorWebApp()
        print("✅ 应用实例创建成功")
        
        # 测试日志消息功能
        test_msg = app.log_message("这是一条测试消息")
        print(f"✅ 日志消息功能: {test_msg.strip()}")
        
        # 测试配置保存功能（使用测试参数）
        print("\n🧪 测试配置保存功能...")
        test_log = ""
        result_log = handle_save_config_only(
            "OpenAI",  # llm_interface
            "test-key",  # llm_api_key
            "https://api.openai.com/v1",  # llm_base_url
            "gpt-4o-mini",  # llm_model
            0.7,  # temperature
            8192,  # max_tokens
            600,  # timeout
            "OpenAI",  # embedding_interface
            "test-embedding-key",  # embedding_api_key
            "https://api.openai.com/v1",  # embedding_base_url
            "text-embedding-ada-002",  # embedding_model
            4,  # retrieval_k
            test_log  # current_log
        )
        print("✅ 配置保存功能测试完成")
        print(f"📋 日志输出:\n{result_log}")
        
        # 测试配置加载功能
        print("\n🧪 测试配置加载功能...")
        load_result = handle_load_config_only("")
        print("✅ 配置加载功能测试完成")
        print(f"📋 加载结果: {len(load_result)} 个返回值")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_log_formatting():
    """测试日志格式化"""
    try:
        print("\n🎨 测试日志格式化...")
        
        from web_app import NovelGeneratorWebApp
        app = NovelGeneratorWebApp()
        
        # 测试不同类型的日志消息
        test_messages = [
            "✅ 成功消息",
            "❌ 错误消息", 
            "⚠️ 警告消息",
            "🔍 信息消息",
            "💡 提示消息"
        ]
        
        formatted_log = ""
        for msg in test_messages:
            formatted_log += app.log_message(msg)
        
        print("✅ 日志格式化测试完成")
        print(f"📋 格式化结果:\n{formatted_log}")
        
        return True
        
    except Exception as e:
        print(f"❌ 日志格式化测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 配置页面日志功能测试")
    print("=" * 60)
    
    # 测试配置功能
    if not test_config_functions():
        print("\n❌ 配置功能测试失败")
        sys.exit(1)
    
    # 测试日志格式化
    if not test_log_formatting():
        print("\n❌ 日志格式化测试失败")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("🎉 配置页面日志功能正常")
    print("=" * 60)
    
    print("\n💡 使用提示:")
    print("1. 启动Web应用: python start_web.py")
    print("2. 访问配置页面: http://localhost:7860")
    print("3. 点击'模型配置'标签页")
    print("4. 设置API密钥后点击'测试LLM配置'")
    print("5. 在右侧日志区域查看详细测试结果")
    print("6. 使用'清空日志'按钮清理日志")
    print("7. 使用'仅保存配置'/'仅加载配置'管理配置")

if __name__ == "__main__":
    main()
