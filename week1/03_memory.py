"""
Week 1 Day 3 · Memory 四种策略对比

场景：第 1 轮告诉模型"我叫企鹅亮，在准备 Agent 开发实习"，中间闲聊几轮，
      最后问"我叫什么？我在准备什么？"——看每种记忆策略能否答对、花了多少 token。

四种策略：
    A. 全量塞入     —— 能答对，但 token 线性增长
    B. 滑动窗口     —— 只留最近 N 轮，token 少，早期信息丢失（答不出名字）
    C. 摘要压缩     —— 早期对话压成一段摘要，token 中等
    D. 长期记忆落盘 —— 关键事实抽出来存 JSON，跨会话也能答对，token 最少

用法：uv run python week1/03_memory.py
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

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory_store.json")
SYSTEM = "你是一个简短回答的助手，只回答事实，不超过 30 字。"

# 固定的对话脚本：第 1 条是关键信息，中间是无关闲聊，最后一条是检验问题
SCRIPT = [
    "记住：我叫企鹅亮，我正在准备 AI Agent 开发方向的日常实习。",
    "今天天气不错。",
    "帮我算算 12 加 8 是多少。",
    "好的谢谢。",
    "我叫什么名字？我在准备什么？",
]


def build_client():
    if os.getenv("DEEPSEEK_API_KEY"):
        from openai import OpenAI
        return (
            OpenAI(
                api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            ),
            os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        )
    if os.getenv("AIHUBMIX_API_KEY"):
        from openai import OpenAI
        return (
            OpenAI(
                api_key=os.environ["AIHUBMIX_API_KEY"],
                base_url=os.getenv("AIHUBMIX_BASE_URL", "https://aihubmix.com/v1"),
            ),
            os.getenv("AIHUBMIX_MODEL", "gpt-4o-mini"),
        )
    sys.exit("未找到 API key，请先配置 .env")


def chat(client, model, messages):
    resp = client.chat.completions.create(model=model, messages=messages)
    return resp.choices[0].message.content, resp.usage.prompt_tokens


def summarize(client, model, turns):
    """把若干轮对话压成一段摘要（策略 C 用）。"""
    text = "\n".join(f"{r}: {c}" for r, c in turns)
    prompt = (
        "把下面的对话压缩成一段 50 字以内的摘要，"
        "必须保留用户的姓名、目标等所有事实性信息：\n\n" + text
    )
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content


def extract_facts(client, model, turns):
    """从对话里抽取长期事实，返回 dict（策略 D 用）。"""
    text = "\n".join(f"{r}: {c}" for r, c in turns)
    prompt = (
        "从下面的对话里抽取需要长期记住的事实，"
        "只输出 JSON 对象，键用英文短名，不要输出其他内容：\n\n" + text
    )
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.choices[0].message.content.strip()
    # 模型可能包一层 ```json 代码块，剥掉
    if raw.startswith("```"):
        raw = raw.strip("`").split("\n", 1)[-1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def run_strategy(client, model, name, build_messages):
    print("\n" + "=" * 66)
    print(f"策略 {name}")
    print("=" * 66)
    messages = build_messages()
    print(f"发给模型的 messages 条数：{len(messages)}")
    answer, tokens = chat(client, model, messages)
    print(f"prompt_tokens：{tokens}")
    print(f"回答：{answer}")
    return {"name": name, "messages": len(messages), "tokens": tokens, "answer": answer}


def main():
    client, model = build_client()
    print(f"model = {model}")

    # 先按脚本跑完前 4 轮，攒出一段真实的对话历史
    history = [{"role": "system", "content": SYSTEM}]
    for i, text in enumerate(SCRIPT[:-1]):
        history.append({"role": "user", "content": text})
        reply, _ = chat(client, model, history)
        history.append({"role": "assistant", "content": reply})
    question = SCRIPT[-1]
    turns = [(m["role"], m["content"]) for m in history if m["role"] != "system"]
    print(f"\n历史对话已攒好：{len(history)} 条，最后的问题是「{question}」")

    results = []

    # A. 全量塞入
    results.append(
        run_strategy(
            client,
            model,
            "A 全量塞入",
            lambda: history + [{"role": "user", "content": question}],
        )
    )

    # B. 滑动窗口：只保留 system + 最近 2 条
    def window():
        return [history[0]] + history[-2:] + [{"role": "user", "content": question}]

    results.append(run_strategy(client, model, "B 滑动窗口(保留最近2条)", window))

    # C. 摘要压缩：早期对话压成一条 system 摘要
    summary = summarize(client, model, turns[:-2])

    def compressed():
        return [
            {"role": "system", "content": SYSTEM},
            {"role": "system", "content": f"以下是更早对话的摘要：{summary}"},
        ] + history[-2:] + [{"role": "user", "content": question}]

    results.append(run_strategy(client, model, "C 摘要压缩", compressed))
    print(f"（摘要内容：{summary}）")

    # D. 长期记忆：抽取事实存 JSON，之后每轮只注入这份事实
    facts = extract_facts(client, model, turns)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(facts, f, ensure_ascii=False, indent=2)
    print(f"\n已把长期事实写入 {os.path.basename(MEMORY_FILE)}：{facts}")

    def with_memory():
        return [
            {"role": "system", "content": SYSTEM},
            {"role": "system", "content": f"关于用户的长期记忆：{json.dumps(facts, ensure_ascii=False)}"},
            {"role": "user", "content": question},
        ]

    results.append(run_strategy(client, model, "D 长期记忆(JSON)", with_memory))

    # D2. 模拟"新会话"：进程重启、history 清空，只靠长期记忆
    print("\n" + "=" * 66)
    print("策略 D 的杀手锏 · 模拟新会话（history 全部丢弃，只读 memory_store.json）")
    print("=" * 66)
    with open(MEMORY_FILE, encoding="utf-8") as f:
        reloaded = json.load(f)
    fresh = [
        {"role": "system", "content": SYSTEM},
        {"role": "system", "content": f"关于用户的长期记忆：{json.dumps(reloaded, ensure_ascii=False)}"},
        {"role": "user", "content": question},
    ]
    answer, tokens = chat(client, model, fresh)
    print(f"新会话（无任何历史）回答：{answer}")
    print(f"prompt_tokens：{tokens}")

    # ---------- 对比表 ----------
    print("\n" + "=" * 66)
    print("四种策略对比")
    print("=" * 66)
    print(f"{'策略':<22}{'消息条数':<10}{'prompt_tokens':<14}回答")
    for r in results:
        print(f"{r['name']:<22}{r['messages']:<10}{r['tokens']:<14}{r['answer'][:24]}")

    print("\n" + "=" * 66)
    print("Day 3 自检")
    print("=" * 66)
    print("  1. 滑动窗口为什么答不出名字？它丢了什么？")
    print("  2. 摘要压缩和长期记忆的区别是什么？各自适合什么信息？")
    print("  3. 长期记忆存在 JSON 里，如果事实冲突了（用户改了名字）怎么办？")
    print("  4. 为什么长期记忆要放在 system 消息里而不是 user 消息里？")
    print("  5. 上下文里重复注入同样的长期记忆，对 prompt cache 是好事还是坏事？")


if __name__ == "__main__":
    main()
