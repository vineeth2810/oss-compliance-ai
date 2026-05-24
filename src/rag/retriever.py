import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

VECTOR_DB_PATH = "vector_store/faiss.index"
METADATA_PATH = "vector_store/metadata.pkl"


class KnowledgeRetriever:
    def __init__(self):
        self.model = SentenceTransformer(EMBED_MODEL)
        self.index = faiss.read_index(VECTOR_DB_PATH)

        with open(METADATA_PATH, "rb") as f:
            self.metadata = pickle.load(f)

    def search(self, query, top_k=3):
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)

        results = []

        for distance, index in zip(distances[0], indices[0]):
            if index == -1:
                continue

            item = self.metadata[index]

            results.append({
                "source": item["source"],
                "text": item["text"],
                "score": float(distance),
            })

        return results
