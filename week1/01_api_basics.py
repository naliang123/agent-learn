"""
Week 1 Day 1 · 大模型 API 输入输出实验

目的：不用任何框架，用原生 openai SDK 打调用，把 request / response 的
每一个字段都打印出来看清楚。这是后面理解 tool calling 消息轨迹的地基。

用法：
    1) 把 API key 填进项目根目录的 .env（见 .env.example）
    2) uv run python week1/01_api_basics.py

五组实验：
    1. 最小调用        —— 看清响应对象的完整结构
    2. system prompt   —— 看 system 消息如何影响输出
    3. temperature     —— 0.0 与 1.0 各跑两次，看确定性差异
    4. max_tokens 截断 —— 看 finish_reason 变成 length 时长什么样
    5. 流式 stream     —— 看 chunk 的结构和拼装方式
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv

load_dotenv()


def build_client():
    """按优先级选一个可用的 key。返回 (client, model_name)。"""
    if os.getenv("DEEPSEEK_API_KEY"):
        return (
            __import__("openai").OpenAI(
                api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            ),
            os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        )
    if os.getenv("AIHUBMIX_API_KEY"):
        return (
            __import__("openai").OpenAI(
                api_key=os.environ["AIHUBMIX_API_KEY"],
                base_url=os.getenv("AIHUBMIX_BASE_URL", "https://aihubmix.com/v1"),
            ),
            os.getenv("AIHUBMIX_MODEL", "gpt-4o-mini"),
        )
    sys.exit(
        "未找到 API key。请在项目根目录 .env 中配置（参考 .env.example）：\n"
        "  DEEPSEEK_API_KEY=sk-xxx\n"
        "  或 AIHUBMIX_API_KEY=sk-xxx"
    )


def dump(obj):
    """把 SDK 的响应对象转成可打印的 JSON，兼容不同版本的 openai SDK。"""
    for attr in ("model_dump", "dict"):
        if hasattr(obj, attr):
            try:
                return getattr(obj, attr)()
            except Exception:
                pass
    return vars(obj)


def show(title, payload, resp):
    print("\n" + "=" * 66)
    print(title)
    print("=" * 66)
    print("--- REQUEST ---")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("--- RESPONSE ---")
    print(json.dumps(dump(resp), ensure_ascii=False, indent=2, default=str))
    usage = getattr(resp, "usage", None)
    if usage:
        print(f"--- USAGE: {dump(usage)} ---")


def main():
    client, model = build_client()
    print(f"model = {model}")

    # ---------- 实验 1：最小调用 ----------
    p1 = {
        "model": model,
        "messages": [{"role": "user", "content": "用一句话解释什么是 RAG"}],
    }
    r1 = client.chat.completions.create(**p1)
    show("实验 1 · 最小调用：看清响应结构", p1, r1)

    # ---------- 实验 2：system prompt ----------
    p2 = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个严格的后端工程师，回答只给结论，不超过 20 字。"},
            {"role": "user", "content": "用一句话解释什么是 RAG"},
        ],
    }
    r2 = client.chat.completions.create(**p2)
    show("实验 2 · 加 system prompt：对比实验 1 的输出变化", p2, r2)

    # ---------- 实验 3：temperature ----------
    for temp in (0.0, 1.0):
        p3 = {
            "model": model,
            "messages": [{"role": "user", "content": "给我一个中国的城市名"}],
            "temperature": temp,
        }
        a = client.chat.completions.create(**p3)
        b = client.chat.completions.create(**p3)
        print("\n" + "=" * 66)
        print(f"实验 3 · temperature={temp}（同一 prompt 跑两次，看是否一致）")
        print("=" * 66)
        print("  第 1 次:", a.choices[0].message.content)
        print("  第 2 次:", b.choices[0].message.content)
        print("  是否一致:", a.choices[0].message.content == b.choices[0].message.content)

    # ---------- 实验 4：max_tokens 截断 ----------
    p4 = {
        "model": model,
        "messages": [{"role": "user", "content": "详细介绍 Transformer 的注意力机制，不少于 500 字"}],
        "max_tokens": 30,
    }
    r4 = client.chat.completions.create(**p4)
    print("\n" + "=" * 66)
    print("实验 4 · max_tokens=30 强制截断")
    print("=" * 66)
    print("  finish_reason =", r4.choices[0].finish_reason)
    print("  实际输出 =", repr(r4.choices[0].message.content))
    print("  usage =", dump(getattr(r4, "usage", {})))

    # ---------- 实验 5：流式 ----------
    p5 = {
        "model": model,
        "messages": [{"role": "user", "content": "用 10 个字介绍 Agent"}],
        "stream": True,
    }
    print("\n" + "=" * 66)
    print("实验 5 · stream=True：看 chunk 结构")
    print("=" * 66)
    chunks = client.chat.completions.create(**p5)
    collected = []
    for i, chunk in enumerate(chunks):
        d = dump(chunk)
        if i < 3:
            print(f"  chunk[{i}] =", json.dumps(d, ensure_ascii=False, default=str))
        delta = d.get("choices", [{}])[0].get("delta", {}) or {}
        if delta.get("content"):
            collected.append(delta["content"])
    print("  拼装结果 =", "".join(collected))
    print("  说明：流式最后一个 chunk 的 choices 为空列表，usage 通常在最后（或需 stream_options 才有）")

    print("\n" + "=" * 66)
    print("Day 1 自检（答不上来就回头看 RESPONSE 的 JSON）")
    print("=" * 66)
    print("  1. 响应里 choices[i].message.role 是什么？为什么是这个值？")
    print("  2. usage 里 prompt_tokens / completion_tokens 分别怎么算出来的？")
    print("  3. finish_reason 有哪几种？各自代表什么情况？")
    print("  4. system / user / assistant 三种 role 在请求里怎么排？模型只看最后一条吗？")
    print("  5. 为什么 temperature=0 时两次调用仍可能不完全一致？")


if __name__ == "__main__":
    main()
