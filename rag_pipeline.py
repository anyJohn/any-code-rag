from pathlib import Path  # Python 文件路径库，类似 Node.js 的 path

import chromadb


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


# === 测试代码 ===
def test():
    # 读取同目录下的 CSS.md 文件，指定 utf-8 编码防止中文乱码
    content = Path("CSS.md").read_text(encoding="utf-8")

    # 调用 chunk_text，每个切片最大 30 字符
    result = chunk_text(content, 30)

    # 遍历结果，enumerate 会同时给你索引和值，类似 JS 的 entries()
    for i, chunk in enumerate(result):
        print(f"--- 切片 {i} ---")  # f-string，类似 JS 模板字符串 `--- 切片 ${i} ---`
        print(chunk)
        print()

    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="obsidian_notes")
    collection.add(documents=result, ids=[f"chunk_{i}" for i in range(len(result))])

    results = collection.query(query_texts=["盒子模型是什么"], n_results=2)
    print(results)
