import pickle
import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

from src.rag.document_loader import load_markdown_documents
from src.rag.chunker import chunk_text
from src.rag.scan_report_loader import load_latest_scan_reports


EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

VECTOR_DB_PATH = "vector_store/faiss.index"
METADATA_PATH = "vector_store/metadata.pkl"


def build_vector_store():
    documents = load_markdown_documents()
    documents.extend(load_latest_scan_reports())

    model = SentenceTransformer(EMBED_MODEL)

    all_chunks = []
    metadata = []

    for doc in documents:
        chunks = chunk_text(doc["content"])

        for chunk in chunks:
            all_chunks.append(chunk)

            metadata.append({
                "source": doc["source"],
                "text": chunk,
            })

    embeddings = model.encode(all_chunks)

    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    faiss.write_index(index, VECTOR_DB_PATH)

    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"Indexed {len(all_chunks)} chunks.")


if __name__ == "__main__":
    build_vector_store()
