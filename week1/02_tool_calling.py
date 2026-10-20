"""
Week 1 Day 2 · Tool Calling 完整机制（本周最重要的一天）

核心目标：看清一条完整的 tool calling 消息轨迹，理解 Agent 循环的本质
         —— messages 数组不断变长 + while 循环反复调 API。

四组实验：
    1. 单工具调用      —— 打印每一轮完整的 messages 快照
    2. 多工具 + 并行调用 —— 一次返回两个 tool_calls 时怎么处理
    3. 工具执行报错     —— 把错误回传给模型，看它如何自我修正
    4. tool_choice     —— auto / required / none 的行为差异

用法：uv run python week1/02_tool_calling.py
"""
import ast
import json
import operator as op
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv

load_dotenv()


# ------------------------------------------------------------------ 工具实现
# 注意：这里刻意用 AST 白名单而不是 eval()。生产环境里工具执行必须沙箱化，
# 这条本身就是面试加分项——"你怎么做工具的安全边界"。
_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv}


def safe_eval(expr: str) -> str:
    """只允许数字和加减乘除，其他语法一律拒绝。"""
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -_eval(node.operand)
        raise ValueError(f"不支持的语法：{ast.dump(node, annotate_fields=False)}")
    try:
        return str(_eval(ast.parse(expr, mode="eval")))
    except Exception as e:
        return f"[工具执行失败] {type(e).__name__}: {e}"


def calculator(expression: str) -> str:
    return safe_eval(expression)


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------------ 工具 Schema
# 这份 JSON 就是给模型看的"说明书"，写得含糊模型就会乱调。
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式。只支持加减乘除和括号，不支持幂运算、函数和其他语法。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如 '12*(3+4)'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的系统日期和时间。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

REGISTRY = {"calculator": calculator, "get_current_time": get_current_time}


# ------------------------------------------------------------------ 客户端
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


def dump(obj):
    for attr in ("model_dump", "dict"):
        if hasattr(obj, attr):
            try:
                return getattr(obj, attr)()
            except Exception:
                pass
    return vars(obj)


def show_messages(messages, title):
    print(f"\n--- {title}（共 {len(messages)} 条）---")
    print(json.dumps(messages, ensure_ascii=False, indent=2, default=str))


# ------------------------------------------------------------------ Agent 循环
def run_loop(client, model, user_msg, tool_choice="auto", max_turns=5, verbose=True):
    """
    一个最小的 Agent 循环。这就是 Agent 的全部骨架：
        while 模型还要工具 -> 执行 -> 把结果 append 回 messages -> 再问
    """
    messages = [{"role": "user", "content": user_msg}]

    for turn in range(1, max_turns + 1):
        if verbose:
            print(f"\n{'='*66}\n第 {turn} 轮\n{'='*66}")
            show_messages(messages, "发出去的 messages")

        resp = client.chat.completions.create(
            model=model, messages=messages, tools=TOOLS, tool_choice=tool_choice
        )
        msg = resp.choices[0].message

        if verbose:
            print("\n--- 模型返回的 message ---")
            print(json.dumps(dump(msg), ensure_ascii=False, indent=2, default=str))

        # 关键一步：把模型的回复变成 dict 后 append 进 messages。
        # 只保留必要的 4 个字段，不要整包塞回去。
        assistant_msg = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_msg)

        # 没有工具调用 = 任务结束，输出最终答案
        if not msg.tool_calls:
            print(f"\n>>> 循环结束（第 {turn} 轮），最终答案：{msg.content}")
            return messages

        # 有工具调用：逐个执行，把结果作为 role=tool 的消息 append
        for tc in msg.tool_calls:
            name = tc.function.name
            # 注意 arguments 是 JSON 字符串，不是对象，必须自己 parse
            try:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except json.JSONDecodeError:
                args = {}
                print(f"  [警告] arguments 解析失败：{tc.function.arguments!r}")

            fn = REGISTRY.get(name)
            result = fn(**args) if fn else f"[错误] 未注册的工具：{name}"
            print(f"\n  >> 调用 {name}({args}) => {result}")

            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": str(result)}
            )

    print(f"\n>>> 达到最大轮数 {max_turns}，强制结束（生产环境必须防这种死循环）")
    return messages


def main():
    client, model = build_client()
    print(f"model = {model}")

    print("\n" + "#" * 66)
    print("# 实验 1 · 单工具调用：看清完整轨迹")
    print("#" * 66)
    run_loop(client, model, "请帮我算一下 123 乘以 456 等于多少")

    print("\n" + "#" * 66)
    print("# 实验 2 · 多工具 + 并行调用")
    print("#" * 66)
    run_loop(client, model, "现在几点了？另外帮我算 2024 乘以 3 是多少")

    print("\n" + "#" * 66)
    print("# 实验 3 · 工具执行报错，看模型能否自我修正")
    print("#" * 66)
    run_loop(client, model, "帮我算 2 的 10 次方（用 ** 或 ^ 表示幂）")

    print("\n" + "#" * 66)
    print("# 实验 4 · tool_choice 对照")
    print("#" * 66)
    for choice in ("none", "required"):
        print(f"\n----- tool_choice='{choice}' -----")
        run_loop(client, model, "你好", tool_choice=choice, max_turns=2, verbose=False)

    print("\n" + "=" * 66)
    print("Day 2 自检（对着上面打印的 messages 回答）")
    print("=" * 66)
    print("  1. tool_calls 里 function.arguments 是什么类型？为什么要自己 json.loads？")
    print("  2. 回传工具结果时那条消息的 role 是什么？为什么必须带 tool_call_id？")
    print("  3. 一轮里返回两个 tool_calls 时，你应该 append 几条 tool 消息？")
    print("  4. 模型要求调用一个你没注册的工具，你的代码应该怎么处理？")
    print("  5. 什么情况下这个 while 循环会停不下来？生产环境怎么防？")
    print("  6. 为什么本脚本用 AST 白名单而不是直接 eval()？")


if __name__ == "__main__":
    main()
