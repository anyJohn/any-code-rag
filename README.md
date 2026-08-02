# any-code-rag

> 一个基于 FastAPI + ChromaDB 的 RAG（检索增强生成）微服务：读取文本文件 → 自动切片 → 向量化入库 → 语义检索。

## 项目简介

把任意文本文件（Markdown、笔记、文档等）丢进来，服务会按段落切片、用 ChromaDB 内置的 Embedding 模型向量化后存入本地向量库，再通过 HTTP 接口做 Top-K 语义检索，支持按 `source` 元数据过滤。整个链路零外部依赖，开箱即用。

## 技术栈

| 组件 | 作用 |
| --- | --- |
| **Python 3.10+** | 运行时（代码用到了 `str \| None` 等 3.10 语法） |
| **FastAPI** | Web 框架，暴露 `/ingest`、`/query` 等 HTTP 接口 |
| **ChromaDB** | 向量数据库，内置默认 Embedding 模型（`all-MiniLM-L6-v2`），无需单独部署 |
| **Pydantic** | 请求模型校验（FastAPI 自带） |
| **uvicorn** | ASGI 服务器，跑 FastAPI 应用 |

项目目前只有两个文件：`main.py`（路由层）和 `rag_pipeline.py`（入库/检索/切片逻辑）。

## 架构图

### 入库流程（Ingest）

```
┌──────────┐    ┌────────────────┐    ┌────────────────────┐    ┌────────────────┐
│ 文本文件  │ -> │ 读取内容(read) │ -> │ chunk_text 切片     │ -> │ collection.add │
│ CSS.md    │    │  UTF-8         │    │ 按段落累积到上限切片 │    │ documents      │
└──────────┘    └────────────────┘    └────────────────────┘    │ ids           │
                                                                │ metadatas     │
                                                                └──────┬─────────┘
                                                                       ▼
                                                              ┌──────────────────┐
                                                              │  ChromaDB        │
                                                              │  ./chroma_db     │
                                                              │  (持久化到磁盘)   │
                                                              └──────────────────┘
```

切片同时写入三类数据：
- `documents`：切片后的文本
- `ids`：`{file_path}_{i}`，保证可去重
- `metadatas`：`{"source": file_path, "chunk_index": i}`，用于检索时按来源过滤

### 检索流程（Query）

```
┌──────────────┐    ┌─────────────────┐    ┌────────────────────────┐    ┌──────────────┐
│ HTTP /query  │ -> │ 校验 n 是否超出 │ -> │ collection.query        │ -> │ 返回 Top-K   │
│ ?q=...&n=... │    │ collection.count│    │ (ChromaDB 语义搜索)      │    │ documents    │
└──────────────┘    └─────────────────┘    │ 可选 where={source:...} │    │ + metadatas  │
                                           └────────────────────────┘    └──────────────┘
```

## 接口文档

### `POST /ingest` — 入库

读取指定文件，切片后存入 collection。

| 参数 | 位置 | 类型 | 说明 |
| --- | --- | --- | --- |
| `file_path` | query | string | 待入库文件的路径（服务端可访问） |

**示例**
```bash
curl -X POST "http://localhost:8000/ingest?file_path=CSS.md"
```

**返回**
```json
{ "message": "Successfully ingested 12" }
```

### `GET /query` — 语义检索

对已入库内容做 Top-K 语义搜索，可选按来源过滤。

| 参数 | 位置 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `q` | query | string | — (必填) | 查询文本 |
| `n` | query | int | `2` | 返回结果数，超过 collection 总数会报错 |
| `source` | query | string | `null` | 按 `source` 元数据过滤（即原 `file_path`） |

**示例**
```bash
# 基础查询
curl "http://localhost:8000/query?q=盒子模型"

# 指定返回数 + 来源过滤
curl "http://localhost:8000/query?q=盒子模型&n=3&source=CSS.md"
```

**返回**
```json
{
  "query": "盒子模型",
  "result": ["切片1内容...", "切片2内容..."],
  "metadatas": [
    { "source": "CSS.md", "chunk_index": 3 },
    { "source": "CSS.md", "chunk_index": 7 }
  ]
}
```

### `GET /collections` — 列出已入库的 collection

返回当前 ChromaDB 客户端下所有 collection 的名称。

**示例**
```bash
curl "http://localhost:8000/collections"
```
**返回**
```json
{ "collections": ["obsidian_notes"] }
```

### `GET /health` — 健康检查

**示例**
```bash
curl "http://localhost:8000/health"
```
**返回**
```json
{ "status": "ok" }
```

## 快速启动

### 1. 安装依赖

```bash
# 建议先建虚拟环境
python -m venv .venv && source .venv/bin/activate   # fish: source .venv/bin/activate.fish

pip install fastapi uvicorn chromadb pydantic
```

### 2. 启动服务

```bash
python -m uvicorn main:app --reload
```

服务默认跑在 `http://localhost:8000`，交互式文档在 `http://localhost:8000/docs`。

### 3. 测试命令

```bash
# 健康检查
curl "http://localhost:8000/health"

# 入库一个文件（用仓库里的 CSS.md 试）
curl -X POST "http://localhost:8000/ingest?file_path=CSS.md"

# 语义检索
curl "http://localhost:8000/query?q=盒子模型"

# 带来源过滤 + 指定数量
curl "http://localhost:8000/query?q=盒子模型&n=3&source=CSS.md"
```

## 技术选型说明

### 为什么选 ChromaDB？

1. **零外部依赖**：用 `PersistentClient` 直接持久化到本地 `./chroma_db` 目录，不需要起独立的数据库服务（对比 Milvus / Qdrant 都要单独部署）。
2. **内置 Embedding**：`collection.add` 时不传 `embeddings` 就会自动调用默认的 `all-MiniLM-L6-v2`，省去自己管理 Embedding 模型的成本。
3. **API 极简**：`add` / `query` / `count` 几个方法就能跑通完整 RAG 链路，适合作为微服务原型和学习项目。
4. **元数据原生支持**：`where={"source": ...}` 直接做过滤，不用自己维护二级索引。

### 为什么用自定义 `chunk_text`？

通用的按固定字符数切片（如每 500 字一刀）会从句子中间切断，破坏语义完整性。这里采用**按段落累积**的策略：

1. 先按空行（`\n\n`）拆段落，保证段落本身的语义完整；
2. 逐段累加到 `current`，只要拼接后长度 ≤ `max_length`（默认 100）就继续合并；
3. 一旦超长就把 `current` 落盘为一个 chunk，新段落重开一个；
4. 循环结束后把最后剩余的 `current` 也存进去（最容易漏的一步）。

这样每个 chunk 是若干完整段落的组合，既不切断句子，又能在长度上限内尽量打包，检索时召回的片段语义更聚焦。
