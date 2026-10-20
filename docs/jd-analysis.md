# 北京 AI Agent 实习 JD 关键词分析

> 样本：Boss 直聘 · 北京 · 关键词「agent / AI Agent 开发实习生」，2026-10-20 截图 11 张，去重后有效 JD 12 条。
> 用途：用真实 JD 反推学习优先级，Week 1-4 每周回来对照一次。

## 一、岗位类型分布（12 条）

| 类型 | 数量 | 代表 | 投不投 |
|---|---|---|---|
| Agent 开发 / 工程 | 5 | 四咖速通、睿智合创、快钱支付（Agent 基建）、字节（评测与工程）、百度地图 Agent Harness | **主投** |
| Agent 产品 / 策略 | 5 | 智谱华章、百度地图产品、水滴、宇投数创、好未来 | 不投（产品线，跟路线不匹配） |
| Agent 算法 | 2 | 快手、多模态/后训练类 | 不投（算法线，一个月补不上） |

结论：**接近一半的 "Agent 实习" 岗位其实是产品岗**，投前必须看 JD 正文，别被标题骗了。开发线样本里真正对口的就 4-5 家，要重点盯。

## 二、技术关键词频率（开发类 JD，去重统计）

| 关键词 | 出现次数 | 对应路线 |
|---|---|---|
| LangChain / LangGraph | 5 | Week 3 核心 |
| RAG（知识库 / 检索 / nl2sql） | 5 | Week 2 核心 |
| Prompt Engineering / 提示词工程 | 5 | 贯穿全程 |
| Agent 评测（badcase / golden set / 评测集 / 幻觉率） | 5 | Week 4 核心 |
| 工具调用 / Tool Use / Function Calling | 4 | Week 1 核心 |
| MCP | 3 | Week 3 D19 |
| 工作流引擎 / Workflow / 编排 | 3 | Week 3 |
| FastAPI / 后端服务化 | 3 | Week 3-4（可选加分） |
| Human-in-the-loop / interrupt / checkpoint | 2 | Week 3 D17 |
| 多 Agent 协同 | 2 | Week 3（了解即可，勿过度设计） |
| Dify / 低代码平台 | 2 | 知道是什么即可，不深学 |
| Vibe Coding（Cursor / Claude Code / Trae） | 3 | 日常就用，面试能聊 |
| SQLite / PostgreSQL | 2 | Week 3 checkpoint 用 SQLite |

## 三、硬性要求统计（所有样本）

| 要求 | 分布 | 你的情况 |
|---|---|---|
| 实习时长 | 「3 个月以上」×6，「6 个月」×4 | **你能给 8-12 个月，超过所有 JD 要求** |
| 每周到岗 | 「4 天/周」×7，「5 天/周」×5 | 你能 5 天 |
| 学历 | 本科在读为主；四咖速通明确「2027 届及以后毕业优先」 | 你 2027 届本科毕业 + 985 硕士拟录取，符合 |
| 薪资 | 100-550 元/天（开发类集中在 150-260） | — |

## 四、对口度排序（开发线）

1. **四咖速通 · AI Agent 开发工程师（实习）100-200/天** —— JD 几乎照着我们路线写的：LangGraph 状态管理、interrupt/resume 人工确认、RAG 知识库、MCP、FastAPI、SQLite checkpoint。加分项明确要「读过 LangGraph 源码、搭过 RAG、开源贡献」。**头号目标。**
2. **快钱支付 · AI 产品/工程实习生（Agent 基建）150-200/天** —— 企业级 RAG 知识库 + Agent 框架 + 工作流引擎 + nl2sql，点名 MCP。工程含量高。
3. **睿智合创 · AI Agent 开发实习生 150-200/天** —— LangChain/Dify、提示词、工具调用、多 Agent、评测体系（幻觉率、可追溯性）。金融场景。
4. **字节 · Agent 实习生（评测与工程）200-250/天** —— 偏评测与数据，技术栈 Python/TS + Prompt Engineering，要求熟悉 Cursor/Claude Code。大厂背书，但工程深度一般。
5. **百度 · 地图 Agent Harness 工程师 400-550/天** —— 薪资最高，Harness 方向硬核，但要求也最高，放在第二批。

## 五、对路线的三个印证与修正

1. **「Agent 评测」被严重低估**——12 条 JD 里 5 条明确要评测集 / badcase / golden set 经验。原计划 Week 4 才做评测，修正：**评测从 Week 2 建索引时就开始攒 badcase**，不要堆到最后。
2. **LangGraph 的 checkpoint / HITL 是真实生产需求**（不是教程噱头），Week 3 D17 的 SQLite checkpoint 务必做成能演示的功能。
3. **MCP 已经从「新概念」变成 JD 常规要求**（3/12 出现），Week 3 D19 不能省。

## 六、明确不学的（按 JD 反向确认）

- 模型训练 / SFT / RL / 后训练：只在算法岗 JD 出现，跳过。
- 多模态 / 图像：仅 1 条提及，跳过。
- Java/Go/PHP 后端：后端实习生 JD 的要求，与 Agent 开发无关。
