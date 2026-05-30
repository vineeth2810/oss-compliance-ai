from src.rag.retriever import KnowledgeRetriever
from src.inference.qwen_inference import generate_response


SYSTEM_PROMPT = """
You are an OSS compliance and security assistant.

Use the provided context to answer questions about:
- open-source licenses
- compliance obligations
- vulnerabilities
- enterprise OSS policy
- remediation guidance

Answer clearly and accurately.

If the answer is not present in the context,
say that the information is not available.
"""


class ComplianceChatbot:
    def __init__(self):
        self.retriever = KnowledgeRetriever()

    def build_context(self, query, top_k=8):
        results = self.retriever.search(query, top_k=top_k)

        context_parts = []

        for item in results:
            context_parts.append(
                f"Source: {item['source']}\n"
                f"{item['text']}"
            )

        context = "\n\n".join(context_parts)

        return context, results

    def ask(self, query):
        context, sources = self.build_context(query)

        prompt = f"""
{SYSTEM_PROMPT}

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

        answer = generate_response(prompt)

        return {
            "question": query,
            "answer": answer,
            "sources": [
                item["source"]
                for item in sources
            ],
        }
