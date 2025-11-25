#!/usr/bin/env python3
"""测试通义千问 API 连接和模型访问权限"""

import os
from openai import OpenAI

# 从环境变量读取配置
API_KEY = os.getenv("LLM_API_KEY", "your-api-key-here")
API_BASE = os.getenv("LLM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 要测试的模型列表
MODELS_TO_TEST = [
    "qwen-turbo",
    "qwen-plus",
    "qwen-max",
    "qwen-long",
]

def test_model(client, model_name):
    """测试单个模型是否可访问"""
    try:
        print(f"\n测试模型: {model_name}")
        print("-" * 50)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "你好，请简单介绍一下你自己。"}
            ],
            max_tokens=100,
            temperature=0.7,
        )

        answer = response.choices[0].message.content
        print(f"✅ 成功! 模型 '{model_name}' 可以访问")
        print(f"回答: {answer[:100]}...")
        return True

    except Exception as e:
        error_msg = str(e)
        print(f"❌ 失败! 模型 '{model_name}' 无法访问")
        print(f"错误: {error_msg}")

        # 解析常见错误
        if "403" in error_msg or "AccessDenied" in error_msg:
            print("💡 提示: 该模型未开通或无访问权限")
        elif "401" in error_msg or "Invalid" in error_msg:
            print("💡 提示: API Key 无效或已过期")
        elif "400" in error_msg:
            print("💡 提示: 请求参数错误")

        return False

def main():
    print("=" * 50)
    print("通义千问 API 测试工具")
    print("=" * 50)

    # 检查 API Key
    if API_KEY == "your-api-key-here" or not API_KEY:
        print("\n❌ 错误: 未配置 LLM_API_KEY")
        print("请在 .env 文件中设置有效的 API Key")
        return

    print(f"\nAPI Base: {API_BASE}")
    print(f"API Key: {API_KEY[:20]}...")

    # 创建客户端
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE,
    )

    # 测试所有模型
    results = {}
    for model in MODELS_TO_TEST:
        results[model] = test_model(client, model)

    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    available_models = [m for m, success in results.items() if success]
    unavailable_models = [m for m, success in results.items() if not success]

    if available_models:
        print(f"\n✅ 可用模型 ({len(available_models)}个):")
        for model in available_models:
            print(f"  - {model}")

    if unavailable_models:
        print(f"\n❌ 不可用模型 ({len(unavailable_models)}个):")
        for model in unavailable_models:
            print(f"  - {model}")

    # 给出建议
    print("\n" + "=" * 50)
    print("建议")
    print("=" * 50)

    if available_models:
        recommended = available_models[0]
        print(f"\n推荐使用: {recommended}")
        print(f"\n在 .env 文件中设置:")
        print(f"LLM_MODEL_NAME={recommended}")
    else:
        print("\n⚠️  所有模型都无法访问!")
        print("\n请检查:")
        print("1. API Key 是否正确配置")
        print("2. 是否在阿里云控制台开通了相应的模型服务")
        print("3. 账户是否有足够的余额或额度")
        print("\n访问控制台: https://dashscope.console.aliyun.com/")

if __name__ == "__main__":
    main()
