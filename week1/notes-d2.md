# Week 1 Day 2 笔记 · Tool Calling 完整机制

日期：2026-10-21
材料：zero2Agent / learn-agent-basic 05（+ 有余力读 06）

---

## 阅读（约 1 小时）

| 篇 | 主题 | 读完要能回答 |
|---|---|---|
| [05-tool-calling-basics](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/05-tool-calling-basics) | Tool Calling 机制 | 一次 tool call 的完整消息序列是什么？schema 怎么约束模型输出？ |

## 动手（约 1.5 小时）

```bash
uv run python week1/02_tool_calling.py
```

**不要只看最终结果，要看每一轮打印出来的 messages 数组怎么变长。** 这是今天唯一的目的。

四个实验：
1. 单工具调用 —— 完整轨迹
2. 多工具 + 并行调用 —— 一次返回两个 tool_calls
3. 工具报错 —— 错误信息回传后模型如何自我修正
4. tool_choice —— auto / required / none 的差异

## 自检（对着打印的 messages 回答）

- [ ] `tool_calls` 里 `function.arguments` 是什么类型？为什么要自己 `json.loads`？
- [ ] 回传工具结果时那条消息的 role 是什么？为什么必须带 `tool_call_id`？
- [ ] 一轮里返回两个 `tool_calls` 时，你应该 append 几条 tool 消息？
- [ ] 模型要求调用一个你没注册的工具，代码该怎么处理？
- [ ] 什么情况下这个 while 循环会停不下来？生产环境怎么防？
- [ ] 为什么脚本用 AST 白名单而不是直接 `eval()`？

---

## 我的答案 / 笔记

### 一次 tool call 的完整消息序列

（手画一遍：system / user / assistant(tool_calls) / tool / assistant，写清楚每条里有什么字段）

### tool_calls 的结构

（id / type / function.name / function.arguments 分别是什么、什么类型）

### 工具 schema 怎么写才能让模型不乱调

（description 写含糊会怎样？required 字段的作用？）

### Agent 循环的骨架

（用自己的话写出那个 while 循环在做什么）

---

## 今天卡住的问题

**为什么 LLM 需要工具？**

- 获取实时数据
- 查询私有数据库
- 读写文件
- 调用内部系统
- 执行代码
- 与外部 API 交互

模型擅长的是理解、推理、生成。

工具解决的是访问外部世界和执行动作。

**关键的是分工：**

模型负责：

- 根据当前输入决定是否调用工具
- 选择工具并生成参数
- 根据工具结果继续决策或组织答案

程序负责：

- 校验模型生成的工具名和参数
- 真正执行工具
- 处理权限、超时、重试和异常
- 把结果按协议返回给模型


role:

- system:系统级规则
- developer:开发者指令
- user:用户提供的目标和内容
- assistant:模型产生的文本、工具请求或其他输出
- tool:在部分 Chat Comoletions 风格协议中表示执行结果，不是模型自己生成的事实。

```json
{
  "id": "chatcmpl_example",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_weather_01",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"city\":\"上海\",\"unit\":\"celsius\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 312,
    "completion_tokens": 28,
    "total_tokens": 340
  }
}
```

