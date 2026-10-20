# agent-learn

30 天 AI Agent / RAG 开发冲刺仓库。目标：从手写 Agent Loop 到本地化 RAG 全链路，再到 LangGraph 编排与 MCP，最后落到可量化的评测与一份能撑住深挖的简历项目。

## 路线

- 完整路线与每日安排：[docs/roadmap-30days.md](docs/roadmap-30days.md)
- 北京 Agent 实习 JD 关键词分析（决定学什么）：[docs/jd-analysis.md](docs/jd-analysis.md)

## 环境

| 项 | 版本 / 位置 |
|---|---|
| Python | 3.13（uv 管理，`.venv`） |
| torch | 2.6.0+cu126（RTX 4060 Laptop 8G，CUDA 可用） |
| Embedding | `D:\Cache\models\bge-m3`（本地，离线） |
| Reranker | `D:\Cache\models\bge-reranker-v2-m3`（本地，GPU 推理） |
| 向量库 | Milvus Lite（嵌入式，无需服务） |
| 稀疏检索 | rank-bm25 + jieba 中文分词 |
| 编排 | LangGraph |
| 协议 | MCP |

## 快速开始

```bash
git clone git@github.com:naliang123/agent-learn.git
cd agent-learn
uv sync                      # 安装全部依赖（torch 走 pytorch cu126 源）
uv run python scripts/env_smoke_test.py   # 环境验收：GPU / 本地模型 / Milvus / LangChain
```

LLM API key 放在 `.env`（见 `.env.example`，不入库）。

## 目录

```
docs/      路线、JD 分析、每周笔记与复盘
scripts/   环境验收等一次性脚本
week1/     Agent 底层：tool calling 消息轨迹、手写 ReAct
week2/     RAG 全链路：切分 / 索引 / 混合检索 / 重排 / 消融实验
week3/     LangGraph 编排、Agentic RAG、MCP
week4/     评测集、失败分析、demo
```
