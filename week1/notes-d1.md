# Week 1 Day 1 笔记 · Agent 是什么 + 模型 API 输入输出

日期：2026-10-20（提前启动）
材料：zero2Agent / learn-agent-basic 01-04
在线阅读（排版更好）：https://onefly.top/zero2Agent

---

## 阅读清单（约 1.5-2 小时）

| 篇 | 标题 | 读完要能回答 |
|---|---|---|
| 01 | [what-is-an-agent](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/01-what-is-an-agent) | Agent 的定义是什么？跟"调一次 LLM"的本质区别在哪？ |
| 02 | [workflow-vs-agent](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/02-workflow-vs-agent) | Workflow 和 Agent 的边界在哪？**面试必考**，要能举出各自适合/不适合的场景 |
| 03 | [core-components](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/03-core-components) | 一个 Agent 系统由哪几部分组成？各自解决什么问题？ |
| 04 | [why-agent-demos-break](https://github.com/ranxi2001/zero2Agent/tree/main/learn-agent-basic/04-why-agent-demos-break) | Demo 能跑、落地就崩的根因有哪些？**这篇最值钱**，面试聊"工程化"全靠它 |

## 动手（约 45 分钟）

1. 把 API key 填进 `.env`（参考 `.env.example`）
2. `uv run python week1/01_api_basics.py`
3. 逐行看打印出来的 REQUEST / RESPONSE JSON，不要跳

## 自检（答不上就回去看 JSON）

- [ ] `choices[i].message.role` 是什么值？为什么是这个值？
- [ ] `usage` 里 prompt_tokens / completion_tokens 分别怎么算出来的？
- [ ] `finish_reason` 有哪几种？各自代表什么情况？
- [ ] system / user / assistant 三种 role 在请求里怎么排？模型只看最后一条吗？
- [ ] 为什么 temperature=0 时两次调用仍可能不完全一致？

---

## 我的答案 / 笔记

（边读边写，用自己的话，不要抄原文）

### 01 什么是 Agent

### 02 Workflow vs Agent（面试必考）

### 03 核心组件

### 04 为什么 demo 能跑、落地就崩

---

## 今天卡住的问题（明天/下次问我）

-
