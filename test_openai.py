"""
OpenAI API 连接测试脚本

用于验证 OpenAI API Key 和代理配置是否正确
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from openai import OpenAI
import httpx

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


def test_openai_connection(model=None):
    """测试 OpenAI API 连接"""
    print("=" * 60)
    print("OpenAI API 连接测试")
    print("=" * 60)
    print()
    
    # 检查 .env 文件是否存在
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✓ 找到配置文件: {env_file}")
    else:
        print(f"⚠ 未找到配置文件: {env_file}")
        print("   将从环境变量读取配置")
    print()
    
    # 加载 .env 文件
    load_dotenv()
    
    # 读取配置
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    
    # 检查是否有错误的变量名（兼容性检查）
    if not base_url:
        model_api_base = os.getenv("MODEL_API_BASE")
        if model_api_base:
            print("⚠ 警告: 检测到 MODEL_API_BASE 环境变量")
            print("   应该使用 OPENAI_API_BASE 而不是 MODEL_API_BASE")
            print(f"   当前值: {model_api_base}")
            print("   请将 .env 文件中的 MODEL_API_BASE 改为 OPENAI_API_BASE")
            print()
            # 尝试使用这个值（去除可能的引号）
            base_url = model_api_base.strip().strip('"').strip("'")
    
    # 显示环境变量读取情况
    print("配置信息:")
    print("-" * 60)
    
    # 检查 API Key
    if not api_key:
        print("❌ 错误: 未找到 OPENAI_API_KEY 环境变量")
        print("   请在 .env 文件中设置 OPENAI_API_KEY")
        return False
    
    print(f"✓ API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # 检查 Base URL
    if base_url:
        base_url = base_url.strip().strip('"').strip("'")  # 去除可能的引号
        if base_url:
            print(f"✓ 代理地址: {base_url}")
            # 检查是否是云雾API或其他常见代理
            if "yunwu" in base_url.lower() or "cloud" in base_url.lower():
                print("  → 检测到云雾API代理")
            elif "wlai" in base_url.lower():
                print("  → 检测到云雾API代理 (wlai.vip)")
            elif "api.openai.com" not in base_url.lower():
                print("  → 使用自定义代理")
        else:
            print("⚠ OPENAI_API_BASE 环境变量存在但为空")
            print("✓ 使用默认 OpenAI API (无代理)")
    else:
        print("⚠ 未找到 OPENAI_API_BASE 环境变量")
        print("✓ 使用默认 OpenAI API (无代理)")
        print()
        print("💡 提示: 如需使用代理（如云雾API），请在 .env 文件中设置:")
        print("   OPENAI_API_BASE=https://your-proxy-url.com/v1")
        print("   注意: 不要使用引号，不要有空格")
    
    print()
    print("正在测试连接...")
    print("-" * 60)
    
    try:
        # 创建客户端
        client_kwargs = {
            "api_key": api_key,
            "timeout": httpx.Timeout(30.0, read=120.0)
        }
        if base_url:
            client_kwargs["base_url"] = base_url
        
        client = OpenAI(**client_kwargs)
        
        # 测试调用 - 尝试多个模型
        if model:
            # 如果指定了模型，只测试该模型
            models_to_try = [model]
        else:
            # 否则尝试多个模型
            models_to_try = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
            if base_url:
                # 如果是代理，也尝试一些常见的代理模型名称
                models_to_try.extend(["gpt-3.5-turbo-0613", "gpt-4-0613"])
        
        print("发送测试请求...")
        response = None
        last_error = None
        tested_model = None
        
        for test_model in models_to_try:
            try:
                print(f"  尝试模型: {test_model}...")
                response = client.chat.completions.create(
                    model=test_model,
                    messages=[
                        {"role": "user", "content": "请回复'测试成功'"}
                    ],
                    max_tokens=50
                )
                tested_model = test_model
                print(f"  ✓ 模型 {test_model} 可用")
                break
            except Exception as e:
                last_error = e
                error_msg = str(e)
                # 如果是503错误且提示无可用渠道，继续尝试下一个模型
                if "503" in error_msg and ("无可用渠道" in error_msg or "No available channels" in error_msg):
                    print(f"  ✗ 模型 {test_model} 在当前代理分组下无可用渠道，尝试下一个...")
                    continue
                else:
                    # 其他错误直接抛出
                    raise
        
        if response is None:
            raise last_error if last_error else Exception("所有模型都不可用")
        
        # 显示结果
        result = response.choices[0].message.content
        print()
        print("=" * 60)
        print("✅ 测试成功！")
        print("=" * 60)
        print(f"模型响应: {result}")
        print()
        print(f"使用的模型: {tested_model or response.model}")
        print(f"Token 使用: {response.usage.total_tokens} (提示: {response.usage.prompt_tokens}, 完成: {response.usage.completion_tokens})")
        
        if base_url:
            print(f"✅ 代理连接正常: {base_url}")
        else:
            print("✅ 直接连接 OpenAI API 正常")
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 测试失败！")
        print("=" * 60)
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print()
        
        # 提供诊断建议
        error_str = str(e).lower()
        if "503" in str(e) and ("无可用渠道" in str(e) or "no available channels" in error_str):
            print("💡 诊断建议:")
            print("   这是代理服务的问题，不是配置问题。可能的原因：")
            print("   1. 代理账户未配置该模型（gpt-3.5-turbo）")
            print("   2. 代理服务当前分组下没有可用的模型渠道")
            print("   3. 代理服务暂时不可用")
            print()
            print("   解决方案：")
            print("   - 登录代理服务管理面板，检查模型配置")
            print("   - 确认代理账户是否有该模型的权限")
            print("   - 尝试使用其他模型（如 gpt-4）")
            print("   - 联系代理服务提供商检查服务状态")
        elif "timeout" in error_str or "timed out" in error_str:
            print("💡 诊断建议:")
            print("   - 检查网络连接")
            if base_url:
                print(f"   - 检查代理地址是否正确: {base_url}")
                print("   - 尝试访问代理地址是否可访问")
            else:
                print("   - 如果在中国大陆，可能需要配置代理")
                print("   - 设置 OPENAI_API_BASE 环境变量使用代理")
        elif "unauthorized" in error_str or "401" in str(e):
            print("💡 诊断建议:")
            print("   - 检查 API Key 是否正确")
            print("   - 确认 API Key 是否有效且有余额")
        elif "not found" in error_str or "404" in str(e):
            print("💡 诊断建议:")
            if base_url:
                print(f"   - 检查代理地址是否正确: {base_url}")
                print("   - 确认代理服务是否正常运行")
            else:
                print("   - 检查模型名称是否正确")
        
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试 OpenAI API 连接")
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="指定要测试的模型名称（如 gpt-4, gpt-3.5-turbo）。如果不指定，将自动尝试多个模型。"
    )
    args = parser.parse_args()
    
    success = test_openai_connection(model=args.model)
    sys.exit(0 if success else 1)

