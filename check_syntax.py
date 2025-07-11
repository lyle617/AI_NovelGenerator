#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语法检查脚本
"""

import sys
import ast

def check_syntax(filename):
    """检查Python文件语法"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 编译检查语法
        ast.parse(source)
        print(f"✅ {filename} 语法检查通过")
        return True
        
    except SyntaxError as e:
        print(f"❌ {filename} 语法错误:")
        print(f"   行 {e.lineno}: {e.text}")
        print(f"   错误: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {filename} 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 检查web_app.py语法...")
    
    if check_syntax("web_app.py"):
        print("\n🎉 语法检查通过！可以尝试启动了。")
        
        # 尝试导入测试
        try:
            print("\n🧪 测试模块导入...")
            import web_app
            print("✅ 模块导入成功")
            
            print("\n🎯 测试界面创建...")
            demo = web_app.create_interface()
            print("✅ 界面创建成功")
            
            print("\n🎉 所有测试通过！现在可以启动Web界面了。")
            
        except Exception as e:
            print(f"\n❌ 模块测试失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n❌ 语法检查失败，请修复错误后重试。")

if __name__ == "__main__":
    main()
