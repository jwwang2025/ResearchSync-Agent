"""
DeepSeek API 连接测试脚本

用于验证 DeepSeek API Key 配置是否正确
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


def test_deepseek_connection(model=None):
    """测试 DeepSeek API 连接"""
    print("=" * 60)
    print("DeepSeek API 连接测试")
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
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
    
    # 显示环境变量读取情况
    print("配置信息:")
    print("-" * 60)
    
    # 检查 API Key
    if not api_key:
        print("❌ 错误: 未找到 DEEPSEEK_API_KEY 环境变量")
        print("   请在 .env 文件中设置 DEEPSEEK_API_KEY")
        return False
    
    print(f"✓ API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # 检查 Base URL
    base_url = base_url.strip().strip('"').strip("'")  # 去除可能的引号
    if base_url:
        print(f"✓ API 地址: {base_url}")
    else:
        print("✓ 使用默认 DeepSeek API 地址: https://api.deepseek.com")
        base_url = "https://api.deepseek.com"
    
    print()
    print("正在测试连接...")
    print("-" * 60)
    
    try:
        # 创建客户端
        client_kwargs = {
            "api_key": api_key,
            "base_url": base_url,
            "timeout": httpx.Timeout(30.0, read=120.0)
        }
        
        client = OpenAI(**client_kwargs)
        
        # 测试调用 - 尝试多个模型
        if model:
            # 如果指定了模型，只测试该模型
            models_to_try = [model]
        else:
            # 否则尝试多个 DeepSeek 模型
            models_to_try = ["deepseek-chat", "deepseek-coder"]
        
        print("发送测试请求...")
        response = None
        last_error = None
        tested_model = None
        
        for test_model in models_to_try:
            try:
                print(f"  尝试模型: {test_model}...")
                # 测试问题：让模型回答一个有意义的问题
                test_question = "你是谁，你能干什么"
                print(f"  测试问题: {test_question}")
                response = client.chat.completions.create(
                    model=test_model,
                    messages=[
                        {"role": "user", "content": test_question}
                    ],
                    max_tokens=200
                )
                tested_model = test_model
                print(f"  ✓ 模型 {test_model} 可用")
                break
            except Exception as e:
                last_error = e
                error_msg = str(e)
                # 如果是模型不存在错误，继续尝试下一个模型
                if "not found" in error_msg.lower() or "404" in error_msg:
                    print(f"  ✗ 模型 {test_model} 不可用，尝试下一个...")
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
        print(f"✅ DeepSeek API 连接正常: {base_url}")
        
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
        if "timeout" in error_str or "timed out" in error_str:
            print("💡 诊断建议:")
            print("   - 检查网络连接")
            print(f"   - 检查 API 地址是否正确: {base_url}")
            print("   - 尝试访问 API 地址是否可访问")
            print("   - 如果在中国大陆，可能需要配置代理")
        elif "unauthorized" in error_str or "401" in str(e):
            print("💡 诊断建议:")
            print("   - 检查 API Key 是否正确")
            print("   - 确认 API Key 是否有效且有余额")
            print("   - 访问 https://platform.deepseek.com 检查账户状态")
        elif "not found" in error_str or "404" in str(e):
            print("💡 诊断建议:")
            print(f"   - 检查 API 地址是否正确: {base_url}")
            print("   - 检查模型名称是否正确（deepseek-chat 或 deepseek-coder）")
            print("   - 确认 DeepSeek API 服务是否正常运行")
        elif "rate limit" in error_str or "429" in str(e):
            print("💡 诊断建议:")
            print("   - API 调用频率过高，请稍后再试")
            print("   - 检查账户的速率限制")
        elif "insufficient" in error_str or "balance" in error_str:
            print("💡 诊断建议:")
            print("   - 账户余额不足，请充值")
            print("   - 访问 https://platform.deepseek.com 检查账户余额")
        
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试 DeepSeek API 连接")
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="指定要测试的模型名称（如 deepseek-chat, deepseek-coder）。如果不指定，将自动尝试多个模型。"
    )
    args = parser.parse_args()
    
    success = test_deepseek_connection(model=args.model)
    sys.exit(0 if success else 1)

