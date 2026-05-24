from pathlib import Path


def load_markdown_documents(base_path="knowledge_base"):
    documents = []

    base = Path(base_path)

    for file_path in base.rglob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")

            documents.append({
                "source": str(file_path),
                "content": content,
            })

        except Exception:
            continue

    return documents
