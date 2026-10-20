"""
环境验收脚本 —— Day 0 跑一次，确认 bge-m3 / reranker / milvus-lite / langchain 都能用。
用法:  uv run python scripts/env_smoke_test.py
每一项独立 try/except，某一项失败不影响其他项，最后打印汇总表。
"""
import os
import sys
import time
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

EMB_MODEL_DIR = r"D:\Cache\models\bge-m3"
RERANK_MODEL_DIR = r"D:\Cache\models\bge-reranker-v2-m3"

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {name}" + (f"  -> {detail}" if detail else ""))


def section(title):
    print("\n" + "=" * 62)
    print(title)
    print("=" * 62)


# ---------------------------------------------------------------- 1. 基础
section("1. 基础环境")
record("python", True, sys.version.split()[0])
for mod in ["numpy", "pandas", "pydantic", "openai"]:
    try:
        m = __import__(mod)
        record(mod, True, getattr(m, "__version__", "?"))
    except Exception as e:
        record(mod, False, str(e)[:80])

# ---------------------------------------------------------------- 2. GPU
section("2. GPU / torch")
try:
    import torch

    record("torch", True, torch.__version__)
    cuda = torch.cuda.is_available()
    record("cuda available", cuda, torch.cuda.get_device_name(0) if cuda else "CPU only")
    if cuda:
        free, total = torch.cuda.mem_get_info()
        record("显存", True, f"free {free/1024**3:.1f}G / total {total/1024**3:.1f}G")
        x = torch.randn(2000, 2000, device="cuda")
        y = x @ x
        torch.cuda.synchronize()
        record("cuda 矩阵运算", y.shape == (2000, 2000), "ok")
        del x, y
        torch.cuda.empty_cache()
except Exception as e:
    record("torch", False, str(e)[:120])

# ---------------------------------------------------------------- 3. 模型文件
section("3. 本地模型文件")
for label, path in [("bge-m3", EMB_MODEL_DIR), ("bge-reranker-v2-m3", RERANK_MODEL_DIR)]:
    if not os.path.isdir(path):
        record(f"{label} 目录", False, f"不存在: {path}")
        continue
    files = []
    total = 0
    for root, _, fs in os.walk(path):
        for f in fs:
            p = os.path.join(root, f)
            total += os.path.getsize(p)
            files.append(f)
    record(f"{label} 目录", True, f"{total/1024**3:.2f}G, {len(files)} files")
    need_cfg = "config.json" in files
    record(f"{label} config.json", need_cfg, "" if need_cfg else "模型可能不完整/路径错了")

# ---------------------------------------------------------------- 4. embedding 依赖
section("4. Embedding / Rerank 依赖")
for mod, need in [
    ("transformers", "必需"),
    ("FlagEmbedding", "必需"),
    ("sentence_transformers", "可选"),
]:
    try:
        m = __import__(mod)
        record(f"{mod} ({need})", True, getattr(m, "__version__", "?"))
    except Exception as e:
        record(f"{mod} ({need})", False, f"未安装 -> uv add {mod}")

# ---------------------------------------------------------------- 5. bge-m3 实跑
section("5. bge-m3 实跑")
try:
    from FlagEmbedding import BGEM3FlagModel

    t0 = time.time()
    model = BGEM3FlagModel(EMB_MODEL_DIR, use_fp16=True)
    out = model.encode(["你好，这是一个测试", "RAG 检索增强生成"], return_dense=True)
    vec = out["dense_vecs"]
    record("bge-m3 encode", True, f"shape={vec.shape}, {time.time()-t0:.1f}s")
    sim = float(vec[0] @ vec[1])
    record("bge-m3 相似度合理", -1.0 <= sim <= 1.0, f"cos={sim:.4f}")
except Exception as e:
    record("bge-m3 encode", False, f"{type(e).__name__}: {str(e)[:150]}")

# ---------------------------------------------------------------- 6. reranker GPU 实跑
section("6. bge-reranker-v2-m3 实跑 (GPU)")
try:
    from FlagEmbedding import FlagReranker

    t0 = time.time()
    reranker = FlagReranker(RERANK_MODEL_DIR, use_fp16=True)
    scores = reranker.compute_score(
        [["中国的首都是哪里", "北京是中国的首都。"], ["中国的首都是哪里", "上海是经济中心。"]]
    )
    ok = scores[0] > scores[1]
    record("reranker compute_score", True, f"{[round(float(s),3) for s in scores]}, {time.time()-t0:.1f}s")
    record("reranker 排序正确", ok, "相关句得分应高于无关句")
except Exception as e:
    record("reranker", False, f"{type(e).__name__}: {str(e)[:150]}")

# ---------------------------------------------------------------- 7. 向量库
section("7. Milvus-lite")
try:
    from pymilvus import MilvusClient

    db = "./_smoke_milvus.db"
    client = MilvusClient(db)
    coll = "smoke_test"
    if client.has_collection(coll):
        client.drop_collection(coll)
    client.create_collection(collection_name=coll, dimension=8, auto_id=True)
    import random

    rows = [
        {"id": i, "vector": [random.random() for _ in range(8)], "text": f"doc-{i}"}
        for i in range(50)
    ]
    client.insert(collection_name=coll, data=rows)
    res = client.search(
        collection_name=coll,
        data=[[random.random() for _ in range(8)]],
        limit=3,
        output_fields=["text"],
    )
    record("milvus-lite 建库/插入/检索", len(res[0]) == 3, f"top1={res[0][0]['entity']['text']}")
    client.drop_collection(coll)
    try:
        client.close()
    except Exception:
        pass
    # Windows 上 milvus-lite 的 mmap 句柄释放较慢，临时文件清理失败不影响功能，跳过
    for ext in ["", ".lock", ".wal"]:
        p = db + ext
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                print(f"  提示: 临时文件 {p} 被句柄占用, 重启后可手动删除")
except Exception as e:
    record("milvus-lite", False, f"{type(e).__name__}: {str(e)[:150]}")

# ---------------------------------------------------------------- 8. langchain / langgraph
section("8. LangChain / LangGraph / BM25")
for mod in ["langchain", "langchain_core", "langchain_openai", "langchain_milvus", "langgraph"]:
    try:
        m = __import__(mod)
        record(mod, True, getattr(m, "__version__", "?"))
    except Exception as e:
        record(mod, False, str(e)[:80])

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    chunks = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10).split_text(
        "RAG 是检索增强生成，先检索再生成。" * 20
    )
    record("RecursiveCharacterTextSplitter", len(chunks) > 1, f"{len(chunks)} chunks")
except Exception as e:
    record("text_splitter", False, f"{type(e).__name__}: {str(e)[:120]}")

try:
    import jieba
    from rank_bm25 import BM25Okapi

    corpus = ["北京是中华人民共和国的首都，天安门广场位于北京市中心", "上海是中国最大的经济中心城市，外滩是著名景点"]
    bm = BM25Okapi([list(jieba.cut(c)) for c in corpus])
    top = bm.get_top_n(list(jieba.cut("中国的首都是哪里")), corpus, n=1)
    record("rank_bm25 + jieba 中文分词", "北京" in top[0], f"top1={top[0][:12]}...")
except Exception as e:
    record("rank_bm25", False, f"{type(e).__name__}: {str(e)[:120]}")
    print("  提示：中文 BM25 需要先用 jieba 分词 -> uv add jieba")

# ---------------------------------------------------------------- 汇总
section("汇总")
failed = [r for r in results if not r[1]]
print(f"总计 {len(results)} 项，通过 {len(results)-len(failed)}，失败 {len(failed)}\n")
if failed:
    print("需要处理：")
    for name, _, detail in failed:
        print(f"  - {name}: {detail}")
    print("\n常见修复：")
    print("  缺 transformers/FlagEmbedding -> uv add transformers FlagEmbedding")
    print("  缺 jieba                      -> uv add jieba")
    print("  缺 ragas / mcp                -> uv add ragas mcp")
else:
    print("全部通过，可以开始 Week 1。")
