from pathlib import Path  # Python 文件路径库，类似 Node.js 的 path

import chromadb
from chromadb import Collection
from chromadb.api import ClientAPI

client: ClientAPI


# 初始化 ChromaDB collection
def init_collection(
    path: str = "./chroma_db", name: str = "obsidian_notes"
) -> Collection:
    global client
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(name=name)
    return collection


# 列出当前已入库的 collection 名称
def get_collections() -> list[str]:
    if not client:
        return []
    return [collection.name for collection in client.list_collections()]


# 将文本文件内容切片后存入 ChromaDB collection
def ingest(collection: Collection, file_path: str, max_length: int = 100) -> dict:
    content = Path(file_path).read_text(encoding="utf-8")

    if not content.strip():
        return {"message": f"File {file_path} is empty"}

    chunks = chunk_text(content, max_length)
    collection.add(
        documents=chunks,
        ids=[f"{file_path}_{i}" for i in range(len(chunks))],
        metadatas=[{"source": file_path, "chunk_index": i} for i in range(len(chunks))],
    )
    return {"message": f"Successfully ingested {len(chunks)}"}


# 将文本按空行拆分为段落，并根据 max_length 切片
def chunk_text(text: str, max_length: int) -> list[str]:
    # 第一步：按空行（两个换行符）拆段落，返回段落列表
    paragraphs = text.split("\n\n")

    # 初始化两个变量
    current = ""  # 当前正在累积的文本，还没存进 chunks 的
    chunks = []  # 结果列表，存最终切片

    # 第二步：遍历每个段落
    for paragraph in paragraphs:
        if current == "":
            # current 是空的，说明是第一个段落，直接放进去
            current = paragraph
        else:
            # 不是第一个段落，要先算拼接后的长度
            # 拼接格式：current + "\n\n" + paragraph，其中 "\n\n" 占 2 个字符
            new_length = len(current) + 2 + len(paragraph)

            if new_length <= max_length:
                # 没超过 max_length，追加到 current
                current = current + "\n\n" + paragraph
            else:
                # 超了，把当前 current 存起来，开启新切片
                chunks.append(current)  # 等价于 JS 的 chunks.push(current)
                current = paragraph  # 新切片从当前段落开始

    # 第三步：循环结束后，把最后剩余的 current 存进去
    # 这步最容易漏——最后一个切片还在 current 里没存
    if current != "":
        chunks.append(current)

    return chunks


def query(
    collection: Collection, q: str, n: int = 2, source: str | None = None
) -> dict:
    if n > collection.count():
        return {
            "message": f"Requested {n} results, exceed the max number of documents in the collection ({collection.count()})"
        }
    if source:
        results = collection.query(
            query_texts=[q], n_results=n, where={"source": source}
        )
    else:
        results = collection.query(query_texts=[q], n_results=n)
    return {
        "query": q,
        "result": results["documents"][0] if results["documents"] else [],
        "metadatas": results["metadatas"][0] if results["metadatas"] else [],
    }
