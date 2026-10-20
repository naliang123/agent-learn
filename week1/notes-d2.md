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

-
